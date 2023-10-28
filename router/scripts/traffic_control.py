import os
import subprocess
import re
import logging
import argparse


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


def tcpdump():

    command = "tcpdump -i eth0 -w $PCAP_PATH -n"
    logging.info(
        f"{os.getenv('HOST')}: tcpdump started.")
    run_command(command)


def reset_settings():
    # reset netem and tbf settings
    command = 'tc qdisc del dev eth0 root'
    run_command(command)


def netem_settings(delay, delay_deviation, loss):
    # TODO change eth0/eth1 on router_1
    command = f"tc qdisc add dev eth0 root handle 1: netem delay {delay} {delay_deviation} loss {loss}"
    run_command(command)


def tbf_settings(rate):
    # convert rate from Mbits to bits
    rate_in_bits = int(rate) * 1000000
    burst = int(rate_in_bits/2)
    limit = rate_in_bits + burst/2

    command = f"tc qdisc add dev eth0 parent 1: handle 2: tbf rate {rate_in_bits} burst {burst} limit {limit}"
    run_command(command)


def log_settings():

    tc_settings = subprocess.check_output(
        ["tc", "qdisc", "show", "dev", "eth0"]).decode("utf-8")

    # Regular expressions for extracting values
    limit_pattern = r'limit (\d+)'
    delay_pattern = r'delay (\d+\w+)\s+(\d+\w+)?'
    loss_pattern = r'loss (\d+\.\d+|\d+)%'
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

    # Log extracted values
    logging.info(f"{os.getenv('HOST')}: Limit: {log_limit}")
    logging.info(f"{os.getenv('HOST')}: Delay: {log_delay}")
    logging.info(
        f"{os.getenv('HOST')}: Delay Deviation: {log_delay_deviation}")
    logging.info(f"{os.getenv('HOST')}: Loss: {log_loss}%")
    logging.info(f"{os.getenv('HOST')}: Rate: {log_rate}")
    logging.info(f"{os.getenv('HOST')}: Burst: {int(log_burst)/1000000} Mbps")


if __name__ == "__main__":

    args = arguments()
    reset_settings()
    netem_settings(args.delay, args.delay_deviation, args.loss)
    tbf_settings(args.rate)
    log_settings()
