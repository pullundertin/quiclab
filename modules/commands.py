import subprocess
import logging
from modules.prerequisites import get_docker_container, read_configuration
from datetime import datetime


client_1, router_1, router_2, server = get_docker_container()
SSH_PUBLIC_KEY_PATH = read_configuration().get("SSH_PUBLIC_KEY_PATH")
WORKDIR = read_configuration().get("WORKDIR")
REMOTE_HOST = read_configuration().get("REMOTE_HOST")
REMOTE_DIR = read_configuration().get("REMOTE_DIR")
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
    command = f"rsync -ahP --delete --exclude=downloads {WORKDIR}/ '-e ssh -i {SSH_PUBLIC_KEY_PATH}' {REMOTE_HOST}:{REMOTE_DIR}"
    run_command(command)


def rsync_permanent(permanent_storage_dir):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime('%y%m%d_%H%M%S')
    command = f"rsync -ahP --exclude=downloads {WORKDIR}/ '-e ssh -i {SSH_PUBLIC_KEY_PATH}' {REMOTE_HOST}:{permanent_storage_dir}/{formatted_datetime}/"
    print(
        f'\n\nResults have been stored to {permanent_storage_dir}{formatted_datetime}.')
    run_command(command)


def run_client(test_case):
    command = f"python /scripts/run_client.py --mode {test_case.mode} --window_scaling {test_case.window_scaling} --rmin {test_case.rmin} --rdef {test_case.rdef} --rmax {test_case.rmax} --migration {test_case.migration} --file_name_prefix {test_case.file_name_prefix} --number_of_streams {test_case.number_of_streams}"
    client_1.exec_run(command)


def traffic_control(test_case):
    command = f"python /scripts/traffic_control.py --delay {test_case.delay} --delay_deviation {test_case.delay_deviation} --loss {test_case.loss} --rate {test_case.rate} --firewall {test_case.firewall}"
    router_1.exec_run(command)
    router_2.exec_run(command)


def run_server(test_case):
    command = f"python /scripts/run_server.py --mode {test_case.mode}"
    server.exec_run(command)


def run_server_tracing(test_case):
    command = f"python /scripts/run_server_tracing.py --mode {test_case.mode} --size {test_case.size} --file_name_prefix {test_case.file_name_prefix}"
    server.exec_run(command)


def stop_server(test_case):
    command = f"python /scripts/stop_server.py --mode {test_case.mode}"
    server.exec_run(command)


def stop_server_tracing(test_case):
    command = f"python /scripts/stop_server_tracing.py --mode {test_case.mode} --file_name_prefix {test_case.file_name_prefix}"
    server.exec_run(command)
