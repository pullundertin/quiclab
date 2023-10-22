
import psutil
import time
import socket
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
import argparse

# Get environment variables
KEYS_PATH = os.getenv("KEYS_PATH")
QLOG_PATH = os.getenv("QLOG_PATH")
TICKET_PATH = os.getenv("TICKET_PATH")
PCAP_PATH = os.getenv("PCAP_PATH")
HOST = os.getenv("HOST")


# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the flag value in your script
    if args.mode:
        global mode
        mode = args.mode
        logging.info(f'{HOST}: {args.mode} mode enabled')
    else:
        logging.info('http mode enabled')


def map_function():
    # Create a dictionary that maps string keys to functions
    function_mapping = {
        "http2": http2,
        "aioquic": aioquic,
        "quicgo": quicgo
    }

    # Call the chosen function based on the string variable
    if mode in function_mapping:
        function_call = function_mapping[mode]
        function_call()
    else:
        print("Function not found.")


def initialize():
    arguments()
    map_function()


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

    initialize()

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(tcpdump)
        time.sleep(2)
        thread_2 = executor.submit(map_function)

        concurrent.futures.wait([thread_1, thread_2])
