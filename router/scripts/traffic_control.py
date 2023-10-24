

import psutil
import time
import socket
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import re
import logging
import argparse

# Get environment variables
KEYS_PATH = os.getenv("KEYS_PATH")
QLOG_PATH = os.getenv("QLOG_PATH")
TICKET_PATH = os.getenv("TICKET_PATH")
PCAP_PATH = os.getenv("PCAP_PATH")
HOST = os.getenv('HOST')
global burst
global limit

# Configure logging
logging.basicConfig(filename='/shared/logs/output.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def arguments():

    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-d', '--delay', type=str,
                        help='network latency in ms')
    parser.add_argument('-a', '--delay_deviation', type=str,
                        help='network latency deviation in ms')
    parser.add_argument('-l', '--loss', type=str,
                        help='network loss in %')
    parser.add_argument('-r', '--rate', type=str,
                        help='network rate in Mbit')

    global args
    args = parser.parse_args()


def initialize():
    arguments()
    reset_settings()


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"{HOST}: {process.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on {HOST}: {e}")
        logging.info(f"Error {HOST} output: {e.stderr.decode()}")


def tcpdump():

    # Command to run
    command = "tcpdump -i eth0 -w $PCAP_PATH"

    logging.info(
        f"{HOST}: tcpdump started.")
    run_command(command)


def kill(process_name):

    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name']):
        if process.info['name'] == process_name:

            try:
                pid = process.info['pid']
                p = psutil.Process(pid)
                p.terminate()
                logging.info(f"{os.getenv('HOST')}: {process_name} stopped.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                logging.info(f"{os.getenv('HOST')} Error: {process_name}")
                pass


def reset_settings():
    # reset netem and tbf settings
    command = 'tc qdisc del dev eth0 root'
    run_command(command)


def netem_settings():
    # TODO change eth0/eth1 on router_1
    command = f'tc qdisc add dev eth0 root handle 1: netem delay {args.delay} {args.delay_deviation} loss {args.loss}'
    run_command(command)


def tbf_settings():
    # convert rate from Mbits to bits
    rate_in_bits = int(args.rate) * 1000000
    burst = int(rate_in_bits/2)
    limit = rate_in_bits + burst/2

    command = f'tc qdisc add dev eth0 parent 1: handle 2: tbf rate {rate_in_bits} burst {burst} limit {limit}'
    run_command(command)


def log_settings():

    tc_settings = subprocess.check_output(
        ["tc", "qdisc", "show", "dev", "eth0"]).decode("utf-8")

    # Regular expressions for extracting values
    limit_pattern = r'limit (\d+)'
    delay_pattern = r'delay (\d+\w+)\s+(\d+\w+)?'
    loss_pattern = r'loss (\d+%)'
    rate_pattern = r'rate (\d+\w+)'
    burst_pattern = r'burst (\d+)'

    # Extract values using regular expressions
    limit_match = re.search(limit_pattern, tc_settings)
    delay_match = re.search(delay_pattern, tc_settings)
    loss_match = re.search(loss_pattern, tc_settings)
    rate_match = re.search(rate_pattern, tc_settings)
    burst_match = re.search(burst_pattern, tc_settings)

    # Check if matches were found and extract values
    log_limit = limit_match.group(1) if limit_match else None
    log_delay = delay_match.group(1) if delay_match else None
    log_delay_deviation = delay_match.group(2) if delay_match else None
    log_loss = loss_match.group(1) if loss_match else None
    log_rate = rate_match.group(1) if rate_match else None
    log_burst = burst_match.group(1)

    # # Convert log_delay, rate, and burst values to milliseconds if needed
    # if 'ms' not in log_delay:
    #     # Convert log_delay to milliseconds if the unit is not already in milliseconds
    #     delay_value, delay_unit = re.match(r'(\d+)(\w+)', log_delay).groups()
    #     if delay_unit == 's':
    #         log_delay = str(int(delay_value) * 1000) + 'ms'

    # if 'ms' not in rate:
    #     # Convert rate to Mbps if the unit is not already in Mbps
    #     rate_value, rate_unit = re.match(r'(\d+)(\w+)', rate).groups()
    #     if rate_unit == 'Mbit':
    #         rate = rate_value + 'Mbps'

    # Log extracted values
    logging.info(f'{HOST}: Limit: {log_limit}')
    logging.info(f'{HOST}: Delay: {log_delay}')
    logging.info(f'{HOST}: Delay Deviation: {log_delay_deviation}')
    logging.info(f'{HOST}: Loss: {log_loss}')
    logging.info(f'{HOST}: Rate: {log_rate}')
    logging.info(f'{HOST}: Burst: {int(log_burst)/1000000} Mbps')


if __name__ == "__main__":

    initialize()
    netem_settings()
    tbf_settings()
    log_settings()
    # tcpdump()

    # with ThreadPoolExecutor() as executor:

    #     thread_1 = executor.submit(tcpdump)
    #     time.sleep(3)
    #     thread_2 = executor.submit(map_function)

    #     wait([thread_2])
    #     logging.info(f'{HOST}: request completed.')

    #     time.sleep(3)
    #     kill("tcpdump")
    #     wait([thread_1])
