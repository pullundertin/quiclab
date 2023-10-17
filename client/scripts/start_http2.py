
import os
import threading
import subprocess

# Number of concurrent requests to make
NUM_REQUESTS = 10

# Target server and path
SERVER_HOST = '172.3.0.5:443'
SERVER_PATH = '/data.log'


def client_request():
    print(f"{os.getenv('HOST')}: sending http request...")

    IP = "172.3.0.5"  # The server's hostname or IP address
    PORT = 443  # The port used by the server

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
        "/dev/null"
        "https://172.3.0.5:443/data.log",
        "-o",
        "/dev/null"
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"{os.getenv('HOST')}: http connection closed.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


# Create 5 client threads
threads = []
for _ in range(1):
    thread = threading.Thread(target=client_request)
    threads.append(thread)
    thread.start()

# Wait for all client threads to complete
for thread in threads:
    thread.join()


# import asyncio
# from aioquic.asyncio import QuicConnectionProtocol
# from aioquic.h3.connection import H3Connection
# from aioquic.quic.configuration import QuicConfiguration


# async def http2_request():
#     # Set up the QUIC configuration
#     config = QuicConfiguration(
#         is_client=True,
#         # ALPN (Application-Layer Protocol Negotiation) for HTTP/2
#         alpn_protocols=["h2"],
#     )

#     # Establish a QUIC connection to the server
#     quic_protocol = QuicConnectionProtocol(
#         configuration=config,
#         create_protocol=asyncio.create_task,
#     )

#     # Connect to the server
#     transport, protocol = await asyncio.get_event_loop().create_connection(
#         lambda: quic_protocol,
#         'example.com',
#         443,  # Default port for HTTPS
#     )

#     # Set up the HTTP/2 connection
#     h3_protocol = H3Connection(
#         protocol=quic_protocol,
#         quic_connection=quic_protocol,
#     )

#     # Send an HTTP/2 request
#     stream_id = h3_protocol.get_next_available_stream_id()
#     headers = [
#         (":method", "GET"),
#         (":authority", "example.com"),
#         (":path", "/path/to/resource"),
#     ]

#     h3_protocol.send_headers(stream_id, headers, end_stream=True)

#     # Wait for the response headers and body
#     response_headers = await h3_protocol.recv_headers(stream_id)
#     response_body = await h3_protocol.recv_data(stream_id)

#     # Print the response
#     print("Response Headers:", response_headers)
#     print("Response Body:", response_body)

#     # Close the connection
#     quic_protocol.close()
#     await quic_protocol.wait_closed()

# if __name__ == "__main__":
#     asyncio.run(http2_request())
