import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.logs import log_config
from modules.commands import run_command
import logging
import argparse


def arguments():

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: tcp, aioquic, quicgo')
    parser.add_argument('-s', '--size', type=str,
                        help='size of the file to download')
    parser.add_argument('--file_name_prefix', type=str,
                        help='prefix for pcap files')

    args = parser.parse_args()

    return args


def convert_to_bytes(size_string):
    # Convert to lowercase for case-insensitive comparison
    size_string = size_string.lower()

    multipliers = {
        'm': 1024 * 1024,  # 1 MB = 1024^2 bytes
        'g': 1024 * 1024 * 1024  # 1 GB = 1024^3 bytes
    }

    for unit, multiplier in multipliers.items():
        if size_string.endswith(unit):
            # Remove the unit suffix and convert the number part to an integer
            size = float(size_string.strip('mg').strip()) * multiplier
            return size

    raise ValueError("Invalid unit or format for size string")


def generate_data(file_path, size):
    # command = f'dd if=/dev/zero of=/data/data.log bs=1 count=0 seek={size} status=none'

    # Target file size in bytes (1 MB is approximately 1,048,576 bytes)
    target_file_size = convert_to_bytes(size)

    with open(file_path, 'w') as file:
        total_bytes_written = 0
        number = 0

        while total_bytes_written < target_file_size:
            # Convert number to string and write to file with a hyphen
            number_str = str(number)
            file.write(number_str + '-')

            # Calculate the size of the string in bytes
            bytes_written = len((number_str + '-').encode('utf-8'))
            total_bytes_written += bytes_written

            # Increment the number for the next iteration
            number += 1

    logging.info(f"{os.getenv('HOST')}: Download size {size}.")
    # run_command(command)


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


def tcpdump(file_name_prefix):
    command = f"tcpdump -i eth0 -w $PCAP_PATH/{file_name_prefix}server.pcap -n"
    logging.info(f"{os.getenv('HOST')}: tcpdump started.")
    run_command(command)


if __name__ == "__main__":

    log_config()
    file_path = os.getenv('DATA_PATH')

    try:
        args = arguments()

        with ThreadPoolExecutor() as executor:
            if args.mode == 'tcp':
                thread_1 = executor.submit(tcpprobe)
            thread_2 = executor.submit(tcpdump, args.file_name_prefix)
            thread_3 = executor.submit(generate_data, file_path, args.size)
            wait([thread_2])

    except Exception as e:
        logging.error(f"{os.getenv('HOST')}: Error: {str(e)}")
        raise
