import platform
import psutil
import logging
from modules.prerequisites import read_configuration


SYSTEM_INFO_TXT_PATH = read_configuration().get("SYSTEM_INFO_TXT_PATH")


def get_system_info():
    # Get CPU information
    cpu_info = {
        "Physical cores": psutil.cpu_count(logical=False),
        "Total cores": psutil.cpu_count(logical=True),
        "Max Frequency": f"{psutil.cpu_freq().max:.2f}Mhz",
        "Min Frequency": f"{psutil.cpu_freq().min:.2f}Mhz",
        "Current Frequency": f"{psutil.cpu_freq().current:.2f}Mhz",
        "CPU Usage Per Core": [f"{x:.2f}%" for x in psutil.cpu_percent(percpu=True)],
        "Total CPU Usage": f"{psutil.cpu_percent()}%",
    }

    # Information about the platform
    platform_info = {
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Node": platform.node(),
        "Platform": platform.platform(),
        "Processor": platform.processor(),
        "Python Build": platform.python_build(),
        "Python Compiler": platform.python_compiler(),
        "Python Implementation": platform.python_implementation(),
        "Python Version": platform.python_version(),
        "System": platform.system(),
        "Release": platform.release(),
        "Version": platform.version(),
    }

    # Get RAM information
    ram = psutil.virtual_memory()
    ram_info = {
        "Total": f"{ram.total >> 30}GB",
        "Available": f"{ram.available >> 30}GB",
        "Used": f"{ram.used >> 30}GB",
        "Percentage Used": f"{ram.percent}%",
    }

    # Writing the output to a file
    with open(SYSTEM_INFO_TXT_PATH, 'w') as file:
        # Writing CPU information
        file.write("---- CPU Information ----\n")
        for key, value in cpu_info.items():
            file.write(f"{key}: {value}\n")

        # Writing platform information
        file.write("\n---- Platform Information ----\n")
        for key, value in platform_info.items():
            file.write(f"{key}: {value}\n")

        # Writing RAM information
        file.write("\n---- RAM Information ----\n")
        for key, value in ram_info.items():
            file.write(f"{key}: {value}\n")

    logging.info("Information written to system_info.txt file.")
