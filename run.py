
import time
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import docker
import logging
import statistics
import json
from pcap_processing import convert_pcap_to_json, get_tcp_handshake_time, get_tcp_connection_time
from modules.commands import rsync, run_client, traffic_control, run_server, shutdown_server
from modules.logs import log_config
from modules.prerequisites import reset_workdir, read_configurations, get_docker_container


def main(iteration, args):
    try:
        with ThreadPoolExecutor() as executor:
            thread_1 = executor.submit(run_server, args, PCAP_PATH, iteration)
            thread_2 = executor.submit(traffic_control, args)
            time.sleep(3)
            thread_3 = executor.submit(run_client, args, PCAP_PATH, iteration)
            concurrent.futures.wait([thread_3])
            shutdown_server(args, iteration)

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":

    WORKDIR = "./shared/"
    TICKET_PATH = "./shared/keys/ticket.txt"
    SSH_PUBLIC_KEY_PATH = "../.ssh/mba"
    REMOTE_HOST = "marco@mba:/Users/Marco/shared"
    OUTPUT = "./shared/logs/output.log"
    PCAP_PATH = "./shared/pcap/"
    CONFIG_PATH = "config.yaml"

    folders_in_workdir = [
        f'{WORKDIR}/pcap',
        f'{WORKDIR}/qlog_client',
        f'{WORKDIR}/qlog_server',
        f'{WORKDIR}/keys',
        f'{WORKDIR}/tcpprobe']

    log_config()
    reset_workdir(folders_in_workdir)
    client_1, router_1, router_2, server = get_docker_container()

    args = read_configurations(CONFIG_PATH)
    # logging.info(args)
    # TODO repeat 40 times
    for round in range(2):
        for index, config in enumerate(args, start=1):
            iteration = f"{round}:{index}_"
            main(iteration, config)

    convert_pcap_to_json()
    tcp_handshake_durations = get_tcp_handshake_time()
    tcp_connection_durations = get_tcp_connection_time()

    print('hs_median', statistics.median(tcp_handshake_durations))
    print('hs_min', min(tcp_handshake_durations))
    print('hs_max', max(tcp_handshake_durations))
    print('conn_median', statistics.median(tcp_connection_durations))
    print('con_min', min(tcp_connection_durations))
    print('con_max', max(tcp_connection_durations))
    # get_tcp_rtt_statistics()
    rsync()
    logging.info("All tasks are completed.")
