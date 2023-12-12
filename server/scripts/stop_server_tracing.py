import os
import subprocess
import logging
import argparse
import psutil
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait


# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: http, aioquic, quicgo')
    parser.add_argument('--iteration', type=str,
                        help='number of iteration')

    args = parser.parse_args()

    return args


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{os.getenv('HOST')}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {os.getenv('HOST')}: {e}")
        logging.info(f"Error {os.getenv('HOST')} output: {e.stderr.decode()}")


def tcpprobe(iteration):
    def cat_trace_file_and_write_to_file():
        with open(output_file_path, "w") as output_file:
            subprocess.run(["cat", trace_file_path],
                           stdout=output_file, stderr=output_file, check=True)
        logging.info(f"{os.getenv('HOST')}: tcpprobe written to file.")

    def process_trace_data():
        command = "python /scripts/converter.py"
        run_command(command)
        logging.info(f"{os.getenv('HOST')}: tcpprobe converted.")

    def disable_tcptrace():
        with open(tcp_probe_enable_path, "w") as enable_file:
            enable_file.write("0")
            logging.info(f"{os.getenv('HOST')}: tcpprobe disabled.")

    trace_file_path = "/sys/kernel/debug/tracing/trace"
    output_file_path = f"/shared/tcpprobe/{iteration}tcptrace.log"
    tcp_probe_enable_path = "/sys/kernel/debug/tracing/events/tcp/enable"
    cat_trace_file_and_write_to_file()
    process_trace_data()
    disable_tcptrace()


def tcpdump():
    command = f"pkill tcpdump"
    run_command(command)


if __name__ == "__main__":

    args = arguments()

    try:
        with ThreadPoolExecutor() as executor:
            thread_1 = executor.submit(tcpdump)
            if args.mode == 'http':
                thread_2 = executor.submit(tcpprobe, args.iteration)
                wait([thread_2])
            wait([thread_1])
            exit()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
