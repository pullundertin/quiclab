
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


def arguments():
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    modes = ['http', 'aioquic', 'quicgo']
    parser.add_argument('-m', '--mode', choices=modes, type=str,
                        help='modes: http, aioquic, quicgo', default='http')

    parser.add_argument('-s', '--size', type=str,
                        help='size of the file to download', default='1M')

    parser.add_argument('-d', '--delay', type=str,
                        help='network latency in ms', default='0')
    parser.add_argument('-a', '--delay_deviation', type=str,
                        help='network latency deviation in ms', default='0')
    parser.add_argument('-l', '--loss', type=str,
                        help='network loss in %', default='0')
    parser.add_argument('-r', '--rate', type=str,
                        help='network rate in Mbit', default='1000')
    parser.add_argument('-f', '--firewall', type=str,
                        help='block incoming traffic from byte ... to byte ...', default='None')

    parser.add_argument('-w', '--window_scaling', type=str,
                        help='enable/disable receiver window scaling', default='1')
    parser.add_argument('--rmin', type=str,
                        help='minimum recieve window in bytes', default='4096')
    parser.add_argument('--rdef', type=str,
                        help='default recieve window in bytes', default='131072')
    parser.add_argument('--rmax', type=str,
                        help='maximum recieve window in bytes', default='6291456')

    args = parser.parse_args()
    return args


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


def run_client(args):
    command = f'python /scripts/run_client.py --mode {args.mode} --window_scaling {args.window_scaling} --rmin {args.rmin} --rdef {args.rdef} --rmax {args.rmax}'
    client_1.exec_run(command)


def traffic_control(args):
    command = f'python /scripts/traffic_control.py --delay {args.delay} --delay_deviation {args.delay_deviation} --loss {args.loss} --rate {args.rate} --firewall {args.firewall}'
    router_1.exec_run(command)
    router_2.exec_run(command)


def run_server(args):
    command = f'python /scripts/run_server.py --mode {args.mode} --size {args.size}'
    server.exec_run(command)


def shutdown_server(args):
    command = f'python /scripts/stop_server.py --mode {args.mode}'
    server.exec_run(command)


if __name__ == "__main__":

    WORKDIR = "./shared/"
    TICKET_PATH = "./shared/keys/ticket.txt"
    SSH_PUBLIC_KEY_PATH = "../.ssh/mba"
    REMOTE_HOST = "marco@mba:/Users/Marco/shared"
    OUTPUT = "./shared/logs/output.log"

    folders_in_workdir = [
        f'{WORKDIR}/pcap',
        f'{WORKDIR}/qlog_client',
        f'{WORKDIR}/qlog_server',
        f'{WORKDIR}/keys',
        f'{WORKDIR}/tcpprobe']

    log_config()
    reset_workdir(folders_in_workdir)
    args = arguments()
    client_1, router_1, router_2, server = get_docker_container()

    with ThreadPoolExecutor() as executor:

        thread_1 = executor.submit(run_server, args)
        thread_2 = executor.submit(traffic_control, args)
        time.sleep(3)
        thread_3 = executor.submit(run_client, args)
        concurrent.futures.wait([thread_3])

        shutdown_server(args)

        rsync()

    logging.info("All tasks are completed.")
