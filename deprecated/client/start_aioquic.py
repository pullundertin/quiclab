
import multiprocessing
import time
import socket
import os
import subprocess


def client_request():
    print(f"{os.getenv('HOST')}: sending aioquic request...")

    IP = "172.3.0.5"  # The server's hostname or IP address
    PORT = 4433  # The port used by the server

    # Get environment variables
    KEYS_PATH = os.getenv("KEYS_PATH")
    QLOG_PATH = os.getenv("QLOG_PATH")
    TICKET_PATH = os.getenv("TICKET_PATH")

    # Command to run
    command = [
        "python",
        "/aioquic/examples/http3_client.py",
        "-k",
        f"https://{IP}:{PORT}/data.log",
        f"https://{IP}:{PORT}/data.log",
        "--secrets-log",
        KEYS_PATH,
        "--quic-log",
        QLOG_PATH,
        "--zero-rtt",
        "--session-ticket",
        TICKET_PATH
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"{os.getenv('HOST')}: http connection closed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def firewall_enable():

    # Run iptables command to allow incoming traffic on the specified port
    iptables_rule = f"iptables -I INPUT 1 -p udp -s 172.3.0.5 -m connbytes --connbytes 200000:270000 --connbytes-dir reply --connbytes-mode bytes -j DROP"
    # iptables_rule = f"iptables -I INPUT 1 -p udp -s 172.3.0.5 -m connbytes --connbytes 200000:270000 --connbytes-dir reply --connbytes-mode bytes -j DROP"

    try:
        process_firewall_enable = subprocess.run(
            iptables_rule, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("firewall enabled")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def firewall_disable():

    # Run iptables command to allow incoming traffic on the specified port
    iptables_rule = f"iptables -F"

    try:
        process_firewall_disable = subprocess.run(
            iptables_rule, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("firewall disabled")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    # firewall_enable()
    client_request()
    # firewall_disable()

    # # Start the first process
    # p1 = multiprocessing.Process(target=client_request)
    # p1.start()

    # p3 = multiprocessing.Process(target=firewall_disable)
    # p3.start()

    # Wait for both processes to complete
    # p1.join()
    # p2.join()

    # print("Both processes completed.")
