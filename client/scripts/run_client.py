
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
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Wait for the external script to finish
        stdout, stderr = process.communicate()

        return (process.pid)
    except subprocess.CalledProcessError as e:
        logging.info(f"Error: {e}")
        logging.info(f"Error output: {e.stderr.decode()}")


def tcpdump():

    # Command to run
    command = "tcpdump -i eth0 -w $PCAP_PATH"

    logging.info(
        f"{os.getenv('HOST')}: tcpdump started and stored to {os.getenv('PCAP_PATH')}")

    return run_command(command)


def aioquic():
    logging.info(f"{os.getenv('HOST')}: sending aioquic request...")

    IP = "172.3.0.5"
    PORT = 4433

    # Command to run
    command = "python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/data.log https://172.3.0.5:4433/data.log --secrets-log $KEYS_PATH --quic-log $QLOG_PATH --zero-rtt --session-ticket $TICKET_PATH"

    return run_command(command)


def quicgo():
    logging.info(f"{os.getenv('HOST')}: sending quic-go request...")

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
    logging.info(f"{os.getenv('HOST')}: sending http request...")
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

    logging.info(f"{os.getenv('HOST')}: http connection closed.")


def http2():
    logging.info(f"{os.getenv('HOST')}: sending http/2 request...")

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
            parent_pid = process.info['ppid']
            child_pid = process.info['pid']

            # Kill child processes
            try:
                parent = psutil.Process(child_pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                psutil.wait_procs(
                    [child for child in parent.children(recursive=True)], timeout=5)

                # Kill the parent process
                parent.terminate()
                parent.wait(timeout=5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass


def prog_1():

    command = [
        '/prog_1.sh'
    ]

    logging.info(f'client tcpdump {os.getpid()}')
    return run_command(command)


def prog_2():

    command = [
        '/prog_2.sh'
    ]
    logging.info(f'client request {os.getpid()}')
    return run_command(command)


if __name__ == "__main__":

    # pid_1 = tcpdump()
    # logging.info('client tcpdump started.')
    # time.sleep(2)
    # pid_2 = http2()
    # logging.info('client request started.')
    # # logging.info(f'client.pid: {pid}')

    # os.waitpid(pid_2, 0)
    # logging.info('client request done.')

    # kill(pid_1)
    # logging.info('client tcpdump stopped.')
    # # kill(pid_2)

    # Create a ThreadPoolExecutor with 2 threads
    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(tcpdump)
        time.sleep(2)
        thread_2 = executor.submit(aioquic)

        wait([thread_2])
        logging.info('client_1: request has been ended')

        time.sleep(3)
        kill("tcpdump")
        wait([thread_1])
        logging.info('client_1: tcpdump has been shut down')
    # http2()
