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
    return psutil.cpu_percent(interval = 1)


def collect_memory():
    memory = psutil.virtual_memory()
    return {
        "percent": memory.percent,
        "used": memory.used,
        "available": memory.available,
        "total": memory.total,
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
    network = psutil.net_io_counters()
    return {
        "bytes_sent": network.bytes_sent,
        "bytes_received": network.bytes_recv,
    }


def collect_processes():
    processes = []

    for process in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
    # we use except in case of a process gets disappear when we're looking at them OR in case Windows deny access to certain processes.

        try:
            processes.append(process.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(
        key = lambda process: process["cpu_percent"] or 0,
        reverse = True
    )

    return processes[:5]


def collect_metrics():
    return {
        "system": collect_system(),
        "cpu": collect_cpu(),
        "memory": collect_memory(),
        "disk": collect_disk(),
        "network": collect_network(),
        "processes": collect_processes(),
    }

# in this function , we pass the collected mtrics in collected metrics defined at the end of the program.  

def display_metrics(metrics):
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


def run_agent(interval = 5):
    while True:
        metrics = collect_metrics()
        display_metrics(metrics)

        time.sleep(interval)


if __name__ == "__main__":
    run_agent()

