import os
import subprocess
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.converter import convert_log_to_csv
from modules.logs import log_config
from modules.commands import run_command


def arguments():
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: tcp, aioquic, quicgo')
    parser.add_argument('--file_name_prefix', type=str,
                        help='prefix for tcpprobe files')

    args = parser.parse_args()

    return args


def tcpprobe(file_name_prefix):
    def cat_trace_file_and_write_to_file():
        with open(output_file_path, "w") as output_file:
            subprocess.run(["cat", trace_file_path],
                           stdout=output_file, stderr=output_file, check=True)
        logging.info(f"{os.getenv('HOST')}: tcpprobe written to file.")

    def process_trace_data():
        convert_log_to_csv()
        logging.info(f"{os.getenv('HOST')}: tcpprobe converted.")

    def disable_tcptrace():
        with open(tcp_probe_enable_path, "w") as enable_file:
            enable_file.write("0")
            logging.info(f"{os.getenv('HOST')}: tcpprobe disabled.")

    trace_file_path = "/sys/kernel/debug/tracing/trace"
    output_file_path = f"/shared/tcpprobe/{file_name_prefix}tcptrace.log"
    tcp_probe_enable_path = "/sys/kernel/debug/tracing/events/tcp/enable"
    cat_trace_file_and_write_to_file()
    process_trace_data()
    disable_tcptrace()


def tcpdump():
    command = f"pkill tcpdump"
    run_command(command)


if __name__ == "__main__":

    log_config()
    args = arguments()

    try:
        with ThreadPoolExecutor() as executor:
            thread_1 = executor.submit(tcpdump)
            if args.mode == 'tcp':
                thread_2 = executor.submit(tcpprobe, args.file_name_prefix)
                wait([thread_2])
            wait([thread_1])
            exit()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
