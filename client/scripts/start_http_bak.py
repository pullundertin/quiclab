
import multiprocessing
import time
import socket
import os
import subprocess


# Define two functions for the processes

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


def client_request():
    print(f"{os.getenv('HOST')}: sending http request...")

    IP = "172.3.0.5"  # The server's hostname or IP address
    PORT = 80  # The port used by the server

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


def firewall_enable():

    # Run iptables command to allow incoming traffic on the specified port
    iptables_rule = f"iptables -I INPUT 1 -p tcp -s 172.3.0.5 -m connbytes --connbytes 200000:270000 --connbytes-dir reply --connbytes-mode bytes -j DROP"

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
