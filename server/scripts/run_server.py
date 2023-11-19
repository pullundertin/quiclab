import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import logging
import argparse

# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')

    parser.add_argument('-s', '--size', type=str,
                        help='size of the file to download')

    args = parser.parse_args()

    logging.info(f"{os.getenv('HOST')}: {args.mode} mode enabled")

    return args


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


def generate_data(size):
    command = f'dd if=/dev/zero of=/data/data.log bs=1 count=0 seek={size} status=none'
    logging.info(f"{os.getenv('HOST')}: Download size {size}.")
    run_command(command)


def tcpprobe():
    def delete_existing_trace_file(trace_file_path):
        if os.path.exists(trace_file_path):
            with open(trace_file_path, "w") as trace_file:
                trace_file.write("")
            logging.info(f"{os.getenv('HOST')}: tcpprobe trace resetted.")

    def enable_tracking(tcp_probe_path):
        if os.path.exists(tcp_probe_path):
            with open(tcp_probe_path, "w") as enable_file:
                enable_file.write("1")
            logging.info(f"{os.getenv('HOST')}: tcpprobe enabled.")

    trace_file_path = "/sys/kernel/debug/tracing/trace"
    tcp_probe_path = "/sys/kernel/debug/tracing/events/tcp/enable"
    delete_existing_trace_file(trace_file_path)
    enable_tracking(tcp_probe_path)


def tcpdump():
    command = "tcpdump -i eth0 -w $PCAP_PATH -n"
    logging.info(f"{os.getenv('HOST')}: tcpdump started.")
    run_command(command)


def aioquic():
    command = "python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH"
    logging.info(f"{os.getenv('HOST')}: starting aioquic server...")
    run_command(command)


def quicgo():
    os.chdir("/quic-go/example")
    command = "go run main.go --qlog"
    logging.info(f"{os.getenv('HOST')}: starting quic-go server..")
    run_command(command)


def http():
    tcpprobe()
    command = "nginx"
    logging.info(f"{os.getenv('HOST')}: starting http server...")
    run_command(command)


if __name__ == "__main__":

    try:
        args = arguments()

        with ThreadPoolExecutor() as executor:
            thread_1 = executor.submit(tcpdump)
            thread_2 = executor.submit(generate_data, args.size)
            time.sleep(3)

            if args.mode == "http":
                http()
            elif args.mode == "aioquic":
                aioquic()
            elif args.mode == "quicgo":
                quicgo()

    except Exception as e:
        logging.error(f"{os.getenv('HOST')}: Error: {str(e)}")
        raise
