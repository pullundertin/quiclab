import os
import subprocess


def start_iperf3():
    print(f"{os.getenv('HOST')}: sending iperf request...")

    IP = "172.3.0.5" 

    # Command to run
    command = [
        "iperf3",
        "-R",
        "-c",
        f"{IP}",
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"{os.getenv('HOST')}: quic-go connection closed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    start_iperf3()
