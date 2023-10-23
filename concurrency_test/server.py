
import psutil
import time
import socket
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
import argparse


# Configure logging
logging.basicConfig(filename='test.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {e}")
        logging.info(f"Error output: {e.stderr.decode()}")


def prog_1():
    command = "python prog_1.py"
    run_command(command)


def prog_2():
    command = "python prog_2.py"
    run_command(command)


if __name__ == "__main__":

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(prog_1)
        concurrent.futures.wait([thread_1])
        thread_2 = executor.submit(prog_2)

        # concurrent.futures.wait([thread_2])
