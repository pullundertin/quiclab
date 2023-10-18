import os
import subprocess
PCAP_PATH = os.getenv("PCAP_PATH")


def start_tcpdump():
    print(f"{os.getenv('HOST')}: starting tcpdump...")

    # Command to run
    command = [
        "tcpdump",
        "-i",
        "eth0",
        "-w",
        f"{PCAP_PATH}",
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    start_tcpdump()
