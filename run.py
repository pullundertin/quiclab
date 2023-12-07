
import time
import os
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import docker
import logging
import argparse


def log_config():
    # clear logs
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)
    # Configure logging
    logging.basicConfig(filename=OUTPUT, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def reset_workdir(folders):

    def list_and_delete_files_in_folder(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logging.info(f"File '{file_path}' deleted.")
            except Exception as e:
                logging.info(f"Error: {e}")

    def loop_through_folders_and_delete_files(folders):
        for folder in folders:
            if os.path.exists(folder):
                list_and_delete_files_in_folder(folder)
            else:
                logging.info(f"Folder '{folder}' not found.")

    loop_through_folders_and_delete_files(folders)


def read_configurations(file_name):
    configurations_list = []
    with open(file_name, 'r') as file:
        config = {}
        for line in file:
            line = line.strip()
            if line.startswith('Iteration'):
                if config:
                    configurations_list.append(config)
                config = {}
            elif ': ' in line:
                key, value = line.split(': ', 1)
                config[key.strip()] = value.strip()

        if config:
            configurations_list.append(config)

    return configurations_list


def get_docker_container():
    host = docker.from_env()
    client_1 = host.containers.get("client_1")
    router_1 = host.containers.get("router_1")
    router_2 = host.containers.get("router_2")
    server = host.containers.get("server")
    return client_1, router_1, router_2, server


def run_command(command):
    try:
        process = subprocess.run(
            command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(process.stdout.decode())
    except subprocess.CalledProcessError as e:
        logging.info(f"Error on Docker Host: {e}")
        logging.info(f"Error Docker Host output: {e.stderr.decode()}")


def rsync():
    command = f'rsync -ahP --delete {WORKDIR} -e ssh -i {SSH_PUBLIC_KEY_PATH} {REMOTE_HOST}'
    run_command(command)


def run_client(args, pcap_path, iteration):
    command = f"python /scripts/run_client.py --mode {args.get('mode')} --window_scaling {args.get('window_scaling')} --rmin {args.get('rmin')} --rdef {args.get('rdef')} --rmax {args.get('rmax')} --migration {args.get('migration')} --pcap {pcap_path} --iteration {iteration}"
    client_1.exec_run(command)


def traffic_control(args):
    command = f"python /scripts/traffic_control.py --delay {args.get('delay')} --delay_deviation {args.get('delay_deviation')} --loss {args.get('loss')} --rate {args.get('rate')} --firewall {args.get('firewall')}"
    router_1.exec_run(command)
    router_2.exec_run(command)


def run_server(args, pcap_path, iteration):
    command = f"python /scripts/run_server.py --mode {args.get('mode')} --size {args.get('size')} --pcap {pcap_path} --iteration {iteration}"
    server.exec_run(command)


def shutdown_server(args, iteration):
    command = f"python /scripts/stop_server.py --mode {args.get('mode')} --iteration {iteration}"
    server.exec_run(command)


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

    configs = read_configurations(CONFIG_PATH)

    for index, config in enumerate(configs, start=1):
        main(index, config)

    rsync()
    logging.info("All tasks are completed.")
