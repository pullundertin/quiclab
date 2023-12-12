import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import logging
import argparse

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


def aioquic():
    command = "python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH"
    # command = "python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH --retry"
    logging.info(f"{os.getenv('HOST')}: starting aioquic server...")
    run_command(command)


def quicgo():
    os.chdir("/quic-go/example")
    command = "go run main.go --qlog"
    logging.info(f"{os.getenv('HOST')}: starting quic-go server..")
    run_command(command)


def http():
    command = "nginx"
    logging.info(f"{os.getenv('HOST')}: starting http server...")
    run_command(command)


if __name__ == "__main__":

    try:
        with ThreadPoolExecutor() as executor:

            executor.submit(http)
            executor.submit(quicgo)
            executor.submit(aioquic)

    except Exception as e:
        logging.error(f"{os.getenv('HOST')}: Error: {str(e)}")
        raise
