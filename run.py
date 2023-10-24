
import psutil
import time
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import docker
import logging
import argparse


# Variable names todo configuration file
WORKDIR = "./shared/"
TICKET_PATH = "./shared/keys/ticket.txt"
SSH_PUBLIC_KEY_PATH = "../.ssh/mba"
REMOTE_HOST = "marco@192.168.2.9:/Users/Marco/shared"
OUTPUT = "./shared/logs/output.log"
mode = 'http'

args = None

# Create a Docker client
host = docker.from_env()

client_1 = host.containers.get("client_1")
server = host.containers.get("server")


def log_config():
    # clear logs
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)
    # Configure logging
    logging.basicConfig(filename=OUTPUT, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def reset_workdir():
    # Define folders to delete files from
    folders = [f'{WORKDIR}/pcap',
               f'{WORKDIR}/qlog_client',
               f'{WORKDIR}/qlog_server',
               f'{WORKDIR}/keys',
               f'{WORKDIR}/tcpprobe']

    # Loop through folders and delete files
    for folder in folders:
        # Check if the folder exists
        if os.path.exists(folder):
            # List all files in the folder and delete them
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logging.info(f"File '{file_path}' deleted.")
                except Exception as e:
                    logging.info(f"Error: {e}")

        else:
            logging.info(f"Folder '{folder}' not found.")


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    modes = ['http', 'aioquic', 'quicgo']
    parser.add_argument('-m', '--mode', choices=modes, type=str,
                        help='modes: http, aioquic, quicgo')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the flag value in your script
    if args.mode:
        global mode
        mode = f'{args.mode}'


def initialize():
    log_config()
    reset_workdir()
    arguments()


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(process.stdout.decode())
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on Docker Host: {e}")
        logging.info(f"Error Docker Host output: {e.stderr.decode()}")


def rsync():

    command = f'rsync -ahP --delete {WORKDIR} -e ssh -i {SSH_PUBLIC_KEY_PATH} {REMOTE_HOST}'
    run_command(command)


def run_client():

    command = f'python /scripts/run_client.py --mode {mode}'

    client_1.exec_run(command)


def run_server():

    command = f'python /scripts/run_server.py --mode {mode}'

    server.exec_run(command)


def shutdown_server():

    command = f'python /scripts/stop_server.py --mode {mode}'

    server.exec_run(command)


if __name__ == "__main__":

    initialize()

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(run_server)
        time.sleep(3)
        thread_2 = executor.submit(run_client)

        # Wait for client request to complete
        concurrent.futures.wait([thread_2])

        shutdown_server()
        concurrent.futures.wait([thread_1])

        rsync()

    logging.info("All tasks are completed.")
