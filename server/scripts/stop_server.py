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
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.info(f"Error: {e}")
        logging.info(f"Error output: {e.stderr.decode()}")


def kill(process_name):

    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name']):
        if process.info['pid'] == process_name:
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
    # run_command(command)


def prog_1():

    # Command to run
    command = [
        "pkill",
        "prog_1.sh",
    ]

    logging.info(f"{os.getenv('HOST')}: tcpdump stopped.")
    run_command(command)


def prog_2():

    # Command to run
    command = [
        "pkill",
        "prog_2.sh",
    ]

    logging.info(f"{os.getenv('HOST')}: server stopped.")
    run_command(command)


def kill(process_name):

    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name']):
        if process.info['name'] == process_name:
            parent_pid = process.info['ppid']
            child_pid = process.info['pid']

            # Kill child processes
            try:
                logging.info(f"{os.getenv('HOST')}: {process_name} stopped.")
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

    # # Create a ThreadPoolExecutor with 2 threads
    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(kill, 'python')
        thread_2 = executor.submit(kill, 'nginx')
        thread_3 = executor.submit(kill, 'tcpdump')

        concurrent.futures.wait([thread_1, thread_2, thread_3])
