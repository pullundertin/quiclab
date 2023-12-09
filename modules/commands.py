import subprocess
import logging
from modules.logs import log_config
from modules.prerequisites import get_docker_container


client_1, router_1, router_2, server = get_docker_container()
SSH_PUBLIC_KEY_PATH = "../.ssh/mba"
WORKDIR = "./shared/"
REMOTE_HOST = "marco@mba:/Users/Marco/shared"


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
