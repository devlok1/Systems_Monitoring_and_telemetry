import json

import requests
import psutil

import platform
import time


# Eventually we will be stepping toward to multi-machine monitoring.
# hence, we cannot use:
# uptime = platform.boot_time()
# since we cannot understand raw Unix timestamp which will be 
# something like 17393472.0 we use time library
# for system uptime
def collect_system():
    uptime_seconds = time.time() - psutil.boot_time()
    return {
        "os": platform.system(),
        "hostname": platform.node(),
        "uptime": uptime_seconds
    }


def collect_cpu():
    frequency = psutil.cpu_freq()

    return {
        "percent": psutil.cpu_percent(interval=1),
        "per_core": psutil.cpu_percent(interval=0),
        "physical_core": psutil.cpu_count(logical=False),
        "logical_core": psutil.cpu_count(logical=True),
        "frequency":{
            "current": frequency.current if frequency else None,
            "min": frequency.min if frequency else None,
            "max": frequency.max if frequency else None,
            },
        }

def collect_memory():
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "percent": memory.percent,
        "used": memory.used,
        "available": memory.available,
        "total": memory.total,
        "cached": getattr(memory,"cached",0),
        "buffers": getattr(memory,"buffers",0),
        "swap": {
            "percent": swap.percent,
            "used": swap.used,
            "free": swap.free,
            "total": swap.total,
            }
        }


def collect_disk():
    disk =  psutil.disk_usage("/")
    return {
        "percent": disk.percent,
        "used": disk.used,
        "free": disk.free,
        "total": disk.total,
    }


def collect_network():
    total = psutil.net_io_counters()
    interfaces = psutil.net_if_stats()
    addresses = psutil.net_if_addrs()
    
    interface_data = []

    for name, stats in interfaces.items():
        ips = []

        for address in addresses.get(name, []):
            if address.family == 2:
                ips.append(address.address)
                
        interface_data.append({
            "name": name,
            "is_up": stats.isup,
            "mtu": stats.mtu,
            "addresses": ips,
        })

    return {
        "bytes_sent": total.bytes_sent,
        "bytes_received": total.bytes_recv,
        "interfaces": interface_data,
    }


def collect_processes():
    processes = []

    for process in psutil.process_iter(["pid","name","cpu_percent","memory_percent","memory_info"]):
    # we use except in case of a process gets disappear when we're looking at them OR in case Windows deny access to certain processes.

        try:
            info = process.info
            memory_info = info.pop("memory_info",None)

            info["memory_bytes"] = (
                memory_info.rss if memory_info else 0
            )

            processes.append(info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(
        key = lambda process: process["cpu_percent"] or 0,
        reverse = True
    )

    return processes[:5]


def collect_metrics():
    return {
        "timestamp": time.time(),
        "system": collect_system(),
        "cpu": collect_cpu(),
        "memory": collect_memory(),
        "disk": collect_disk(),
        "network": collect_network(),
        "processes": collect_processes(),
    }

# in the function display_metrics() && send_telemetry, 
# we pass the collected mtrics in collected metrics 
# defined at the end of the program.  

def display_metrics(metrics):

    print(f"Timestamp : {metrics['timestamp']}")

    print("\n--- System ---")

    print(f"OS:       {metrics['system']['os']}")
    # here , metrics is looking up in the dictionary collected by       python in function collect_system,
    # we get three values in the function os , hostname and uptime.
    # therefore metrics['system']['os'] --> only looks up to system and os and hence prints 
    # OS : Windows
    print(f"Hostname: {metrics['system']['hostname']}")
    print(f"Uptime:   {metrics['system']['uptime']:.0f} seconds")

    print("\n--- Resources ---")
    print(f"CPU:      {metrics['cpu']}%")
    print(f"Memory:   {metrics['memory']['percent']}%")
    print(f"Disk:     {metrics['disk']['percent']}%")

    print("\n--- Network ---")
    print(f"Sent:     {metrics['network']['bytes_sent']} bytes")
    print(f"Received: {metrics['network']['bytes_received']} bytes")

    print("\n--- Top Processes ---")

    for process in metrics["processes"]:
        print(
            f"{process['pid']:>6} | "
            f"{process['name']:<25} | "
            f"CPU: {process['cpu_percent']}% | "
            f"RAM: {process['memory_percent']:.2f}%"
        )


def send_telemetry(metrics):
    try:
        response = requests.post(
            "http://127.0.0.1:8000/telemetry",
            json=metrics,
            timeout=5
        )
    
        print(f"Server response:{response.json()}")

    except requests.RequestException as error:
        print(f"Failed to send telemetry: {error}")
    
    

def run_agent(interval=5):
    while True:
        metrics = collect_metrics()
        #display_metrics(metrics)
        send_telemetry(metrics)

        time.sleep(interval)


if __name__ == "__main__":
    metrics = collect_metrics()
    # json_data = json.dumps(metrics, indent=4)
    # print(json_data)
    # instead we do,
    run_agent()


