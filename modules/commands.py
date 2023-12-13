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
    command = f"rsync -ahP --delete {WORKDIR}/ '-e ssh -i {SSH_PUBLIC_KEY_PATH}' {REMOTE_HOST}"
    run_command(command)


def run_client(test_case, iteration_prefix):
    command = f"python /scripts/run_client.py --mode {test_case.get('mode')} --window_scaling {test_case.get('window_scaling')} --rmin {test_case.get('rmin')} --rdef {test_case.get('rdef')} --rmax {test_case.get('rmax')} --migration {test_case.get('migration')} --pcap {PCAP_PATH}/ --iteration {iteration_prefix}"
    client_1.exec_run(command)


def traffic_control(test_case):
    command = f"python /scripts/traffic_control.py --delay {test_case.get('delay')} --delay_deviation {test_case.get('delay_deviation')} --loss {test_case.get('loss')} --rate {test_case.get('rate')} --firewall {test_case.get('firewall')}"
    router_1.exec_run(command)
    router_2.exec_run(command)


def run_server(test_case):
    command = f"python /scripts/run_server.py --mode {test_case['mode']}"
    server.exec_run(command)


def run_server_tracing(test_case, iteration_prefix):
    command = f"python /scripts/run_server_tracing.py --mode {test_case['mode']} --size {test_case.get('size')} --pcap {PCAP_PATH} --iteration {iteration_prefix}"
    server.exec_run(command)


def stop_server(test_case):
    command = f"python /scripts/stop_server.py --mode {test_case['mode']}"
    server.exec_run(command)


def stop_server_tracing(test_case, iteration_prefix):
    command = f"python /scripts/stop_server_tracing.py --mode {test_case['mode']} --iteration {iteration_prefix}"
    server.exec_run(command)
