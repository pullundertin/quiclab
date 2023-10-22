
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
        logging.info(f"{HOST}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {HOST}: {e}")
        logging.info(f"Error {HOST} output: {e.stderr.decode()}")


def tcpdump():

    # Command to run
    command = "tcpdump -i eth0 -w $PCAP_PATH"

    logging.info(
        f"{HOST}: tcpdump started and stored to {os.getenv('PCAP_PATH')}")

    return run_command(command)


def aioquic():
    logging.info(f"{HOST}: sending aioquic request...")

    IP = "172.3.0.5"
    PORT = 4433

    # Command to run
    command = "python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/data.log https://172.3.0.5:4433/data.log --secrets-log $KEYS_PATH --quic-log $QLOG_PATH --zero-rtt --session-ticket $TICKET_PATH"

    return run_command(command)


def quicgo():
    logging.info(f"{HOST}: sending quic-go request...")

    IP = "172.3.0.6"
    PORT = 6121

    # Change current working directory
    os.chdir("/quic-go/example/client")

    # Command to run
    command = [
        "go",
        "run",
        "main.go",
        "--insecure",
        "--keylog",
        KEYS_PATH,
        "--qlog",
        f"https://{IP}:{PORT}/demo/tiles",
        # QLOG_PATH,
    ]
    return run_command(command)


def receive_data(socket_obj, buffer_size=None):
    if buffer_size is None:
        buffer_size = socket_obj.getsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF)

    data = b''

    while True:
        chunk = socket_obj.recv(buffer_size)
        if not chunk:
            break
        data += chunk

    return data


def http():
    logging.info(f"{HOST}: sending http request...")
    logging.info(f'http request pid: {os.getpid()}')
    IP = "172.3.0.5"
    PORT = 80

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))
        request = f'GET /data.log HTTP/1.1\r\nHost: {IP}\r\nConnection: close\r\n\r\n'
        s.sendall(request.encode())

        tcp_receive_buffer_size = s.getsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF)

        received_data = receive_data(s, buffer_size=tcp_receive_buffer_size)
        # # Get the local address (including the port number) of the client socket
        # local_address = s.getsockname()

        # # logging.info the local port number
        # logging.info(f"Local Port Number: {local_address[1]}")
        logging.info(received_data)

    logging.info(f"{HOST}: http connection closed.")


def http2():
    logging.info(f"{HOST}: sending http/2 request...")

    IP = '172.3.0.5'
    PORT = 443

    # Set SSLKEYLOGFILE
    os.environ['SSLKEYLOGFILE'] = KEYS_PATH

    # Command to run
    command = "curl -k https://172.3.0.5:443/data.log -o /dev/null https://172.3.0.5:443/data.log -o/dev/null"

    return run_command(command)


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
        time.sleep(2)
        thread_2 = executor.submit(map_function)

        wait([thread_2])
        logging.info('client_1: request has been ended')

        time.sleep(3)
        kill("tcpdump")
        wait([thread_1])
        logging.info('client_1: tcpdump has been shut down')
