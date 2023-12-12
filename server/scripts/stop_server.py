import os
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait


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


def http():
    command = f"pkill nginx"
    run_command(command)


def aioquic():
    command = f"pkill python"
    run_command(command)


def quicgo():
    command_2 = f"pkill -f ^/tmp/go-build"
    run_command(command_2)
    command = f"pkill go"
    run_command(command)


if __name__ == "__main__":

    try:

        with ThreadPoolExecutor() as executor:
            thread_1 = executor.submit(http)
            thread_3 = executor.submit(quicgo)
            thread_2 = executor.submit(aioquic)
            wait([thread_1, thread_2, thread_3])

    except Exception as e:
        logging.error(f"{os.getenv('HOST')}: Error: {str(e)}")
        raise
