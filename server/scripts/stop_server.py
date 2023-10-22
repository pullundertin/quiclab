import os
import subprocess
import logging
import time
import psutil
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


def tcpdump():
    # Command to run
    command = "pkill -e tcpdump"

    logging.info(f"{os.getenv('HOST')}: tcpdump stopped.")
    run_command(command)


def http():

    # Command to run
    command = "pkill nginx"

    logging.info(f"{os.getenv('HOST')}: server stopped.")
    run_command(command)


def aioquic():

    # Command to run
    command = "pkill -e python /aioquic/examples/http3_server.py"

    logging.info(f"{os.getenv('HOST')}: server stopped.")
    run_command(command)


def test():

    # Command to run
    command = "ls -lah /test"

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

    # test()
    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(kill, 'python')
        thread_2 = executor.submit(kill, 'nginx')
        thread_3 = executor.submit(kill, 'tcpdump')

        concurrent.futures.wait([thread_1, thread_2, thread_3])
