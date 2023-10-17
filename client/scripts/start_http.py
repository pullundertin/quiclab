import socket
import threading
import time
import os

# Client code


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


def client():
    print(f"{os.getenv('HOST')}: sending http request...")

    IP = "172.3.0.5"  # The server's hostname or IP address
    PORT = 80  # The port used by the server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))
        request = f'GET /data.log HTTP/2\r\nHost: {IP}\r\nConnection: close\r\n\r\n'
        s.sendall(request.encode())

        tcp_receive_buffer_size = s.getsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF)

        received_data = receive_data(s, buffer_size=tcp_receive_buffer_size)
        # Get the local address (including the port number) of the client socket
        local_address = s.getsockname()

        # Print the local port number
        print(f"Local Port Number: {local_address[1]}")

    print(f"{os.getenv('HOST')}: http connection closed.")


# Start multiple client threads
client_threads = []
for _ in range(5):  # Create 5 client threads
    client_thread = threading.Thread(target=client)
    client_thread.start()
    client_threads.append(client_thread)

# Wait for all client threads to complete
for client_thread in client_threads:
    client_thread.join()
