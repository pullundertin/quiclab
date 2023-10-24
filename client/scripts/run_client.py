
import psutil
import time
import socket
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import sys
import logging
import argparse

# Get environment variables
KEYS_PATH = os.getenv("KEYS_PATH")
QLOG_PATH = os.getenv("QLOG_PATH")
TICKET_PATH = os.getenv("TICKET_PATH")
PCAP_PATH = os.getenv("PCAP_PATH")
HOST = os.getenv('HOST')
mode = 'http'
args = None

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
        "http": http,
        "aioquic": aioquic,
        "quicgo": quicgo
    }

    # Call the chosen function based on the string variable
    if mode in function_mapping:
        function_call = function_mapping[mode]
        function_call()
    else:
        logging.info("Function not found.")


def initialize():
    arguments()


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{HOST}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {HOST}: {e}")
        logging.info(f"Error {HOST} output: {e.stderr.decode()}")


def tcpdump():

    # Command to run
    command = "tcpdump -i eth0 -w $PCAP_PATH"

    logging.info(
        f"{HOST}: tcpdump started.")
    run_command(command)


def aioquic():

    IP = "172.3.0.5"
    PORT = 4433

    # Command to run
    command = "python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/data.log https://172.3.0.5:4433/data.log --secrets-log $KEYS_PATH --quic-log $QLOG_PATH --zero-rtt --session-ticket $TICKET_PATH"

    logging.info(f"{HOST}: sending aioquic request...")
    run_command(command)


def quicgo():

    IP = "172.3.0.5"
    PORT = 6121

    # Change current working directory
    os.chdir("/quic-go/example/client")

    # Command to run
    command = f'go run main.go --insecure --keylog {KEYS_PATH} --qlog https://{IP}:{PORT}/data.log'

    logging.info(f"{HOST}: sending quic-go request...")
    run_command(command)


def http():

    IP = '172.3.0.5'
    PORT = 443

    # Set SSLKEYLOGFILE
    os.environ['SSLKEYLOGFILE'] = KEYS_PATH

    # Command to run
    command = "curl -k https://172.3.0.5:443/data.log -o /dev/null https://172.3.0.5:443/data.log -o/dev/null"

    logging.info(f"{HOST}: sending http request...")
    run_command(command)


def kill(process_name):

    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name']):
        if process.info['name'] == process_name:

            try:
                pid = process.info['pid']
                p = psutil.Process(pid)
                p.terminate()
                logging.info(f"{os.getenv('HOST')}: {process_name} stopped.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                logging.info(f"{os.getenv('HOST')} Error: {process_name}")
                pass


if __name__ == "__main__":

    initialize()

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(tcpdump)
        time.sleep(3)
        thread_2 = executor.submit(map_function)

        wait([thread_2])
        logging.info(f'{HOST}: request completed.')

        time.sleep(3)
        kill("tcpdump")
        wait([thread_1])
