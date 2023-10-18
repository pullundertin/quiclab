import os
import subprocess


def start_server():
    print(f"{os.getenv('HOST')}: starting quic-go server..")

    # Get environment variables
    KEYS_PATH = os.getenv("KEYS_PATH")
    QLOG_PATH = os.getenv("QLOG_PATH")
    TICKET_PATH = os.getenv("TICKET_PATH")

    # Change current working directory
    os.chdir("/quic-go/example")

    # Command to run
    command = [
        "go",
        "run",
        "main.go",
        "--qlog",
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


if __name__ == "__main__":

    start_server()
