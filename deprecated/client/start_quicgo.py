
import os
import subprocess


def client_request():
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


if __name__ == "__main__":

    client_request()
