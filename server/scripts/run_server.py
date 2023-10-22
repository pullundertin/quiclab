
import psutil
import time
import socket
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging

# Get environment variables
KEYS_PATH = os.getenv("KEYS_PATH")
QLOG_PATH = os.getenv("QLOG_PATH")
TICKET_PATH = os.getenv("TICKET_PATH")
PCAP_PATH = os.getenv("PCAP_PATH")


# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


def tcpdump():

    # Command to run
    command = [
        "tcpdump -i eth0 -w $PCAP_PATH"
    ]
    logging.info(f"{os.getenv('HOST')}: tcpdump started.")
    return run_command(command)


def aioquic():
    logging.info(f"{os.getenv('HOST')}: starting aioquic server...")

    # Command to run
    command = "python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH"

    return run_command(command)


def quicgo():
    logging.info(f"{os.getenv('HOST')}: starting quic-go server..")

    # Change current working directory
    os.chdir("/quic-go/example")

    # Command to run
    command = [
        "go",
        "run",
        "main.go",
        "--qlog",
    ]

    return run_command(command)


def http():

    command = [
        "nginx",
    ]

    logging.info(f"{os.getenv('HOST')}: starting http server...")
    return run_command(command)


def http2():
    logging.info(f"{os.getenv('HOST')}: starting http/2 server...")

    command = [
        "nginx",
    ]

    return run_command(command)


if __name__ == "__main__":

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(tcpdump)
        time.sleep(2)
        thread_2 = executor.submit(aioquic)

        concurrent.futures.wait([thread_1, thread_2])
