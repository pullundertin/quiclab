import os
import logging
import argparse
from modules.logs import log_config
from modules.commands import run_command


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')

    args = parser.parse_args()

    return args


def http():
    command = f"pkill nginx"
    logging.info(f"{os.getenv('HOST')}: stopping http server..")
    run_command(command)


def aioquic():
    command = f"pkill python"
    logging.info(f"{os.getenv('HOST')}: stopping aioquic server..")
    run_command(command)


def quicgo():
    command_2 = f"pkill -f ^/tmp/go-build"
    logging.info(f"{os.getenv('HOST')}: stopping quic-go build!..")
    run_command(command_2)
    command = f"pkill go"
    logging.info(f"{os.getenv('HOST')}: stopping quic-go server..")
    run_command(command)


if __name__ == "__main__":

    log_config()

    try:

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
