
import psutil
import time
import socket
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


def start_tcpdump():
    PCAP_PATH = os.getenv("PCAP_PATH")
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
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def aioquic():
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
        print(f"{os.getenv('HOST')}: aioquic connection closed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


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


def quicgo():
    print(f"{os.getenv('HOST')}: sending quic-go request...")

    IP = "172.3.0.6"  # The server's hostname or IP address
    PORT = 6121  # The port used by the server

    # Get environment variables
    KEYS_PATH = os.getenv("KEYS_PATH")
    QLOG_PATH = os.getenv("QLOG_PATH")
    TICKET_PATH = os.getenv("TICKET_PATH")

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

    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"{os.getenv('HOST')}: quic-go connection closed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def http():
    print(f"{os.getenv('HOST')}: sending http request...")

    IP = "172.3.0.5"
    PORT = 80

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))
        request = f'GET /data.log HTTP/1.1\r\nHost: {IP}\r\nConnection: close\r\n\r\n'
        s.sendall(request.encode())

        tcp_receive_buffer_size = s.getsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF)

        received_data = receive_data(s, buffer_size=tcp_receive_buffer_size)
        # Get the local address (including the port number) of the client socket
        local_address = s.getsockname()

        # Print the local port number
        print(f"Local Port Number: {local_address[1]}")

    print(f"{os.getenv('HOST')}: http connection closed.")


def http2():
    print(f"{os.getenv('HOST')}: sending http/2 request...")

    # Target server and path
    SERVER_HOST = '172.3.0.5:443'
    SERVER_PATH = '/data.log'

    # Get environment variables
    KEYS_PATH = os.getenv("KEYS_PATH")
    QLOG_PATH = os.getenv("QLOG_PATH")
    TICKET_PATH = os.getenv("TICKET_PATH")
    os.environ['SSLKEYLOGFILE'] = KEYS_PATH

    # Command to run
    command = [
        "curl",
        "-k",
        "https://172.3.0.5:443/data.log",
        "-o",
        "/dev/null",
        "https://172.3.0.5:443/data.log",
        "-o",
        "/dev/null"
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"{os.getenv('HOST')}: http/2 connection closed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def kill_process_and_children(process_name):

    print(f"{os.getenv('HOST')}: stopping tcpdump...")
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


if __name__ == "__main__":

    # Create a ThreadPoolExecutor with 2 threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit the functions for execution
        future1 = executor.submit(start_tcpdump)
        future2 = executor.submit(http)

        # Wait for both processes to complete (optional)
        concurrent.futures.wait([future2])
        kill_process_and_children("tcpdump")
