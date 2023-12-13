import os
from modules.commands import run_command
from concurrent.futures import ThreadPoolExecutor
import logging
import argparse
from modules.logs import log_config


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')

    args = parser.parse_args()

    logging.info(f"{os.getenv('HOST')}: {args.mode} mode enabled")

    return args


def aioquic():
    command = "python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH_SERVER"
    # command = "python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH_SERVER --retry"
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
    log_config()

    try:
        with ThreadPoolExecutor() as executor:

            args = arguments()

            if args.mode == "http":
                http()
            elif args.mode == "aioquic":
                aioquic()
            elif args.mode == "quicgo":
                quicgo()

    except Exception as e:
        logging.error(f"{os.getenv('HOST')}: Error: {str(e)}")
        raise
