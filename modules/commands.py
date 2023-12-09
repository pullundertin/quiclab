import subprocess
import logging
from modules.prerequisites import get_docker_container, read_configuration


client_1, router_1, router_2, server = get_docker_container()
SSH_PUBLIC_KEY_PATH = read_configuration().get("SSH_PUBLIC_KEY_PATH")
WORKDIR = read_configuration().get("WORKDIR")
REMOTE_HOST = read_configuration().get("REMOTE_HOST")
PCAP_PATH = read_configuration().get("PCAP_PATH")


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


def run_client(args, iteration):
    command = f"python /scripts/run_client.py --mode {args.get('mode')} --window_scaling {args.get('window_scaling')} --rmin {args.get('rmin')} --rdef {args.get('rdef')} --rmax {args.get('rmax')} --migration {args.get('migration')} --pcap {PCAP_PATH} --iteration {iteration}"
    client_1.exec_run(command)


def traffic_control(args):
    command = f"python /scripts/traffic_control.py --delay {args.get('delay')} --delay_deviation {args.get('delay_deviation')} --loss {args.get('loss')} --rate {args.get('rate')} --firewall {args.get('firewall')}"
    router_1.exec_run(command)
    router_2.exec_run(command)


def run_server(args, iteration):
    command = f"python /scripts/run_server.py --mode {args.get('mode')} --size {args.get('size')} --pcap {PCAP_PATH} --iteration {iteration}"
    server.exec_run(command)


def shutdown_server(args, iteration):
    command = f"python /scripts/stop_server.py --mode {args.get('mode')} --iteration {iteration}"
    server.exec_run(command)
