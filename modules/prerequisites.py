import os
import logging
import docker
import yaml


def reset_workdir():
    WORKDIR = read_configuration().get("WORKDIR")
    folders = [
        f'{WORKDIR}/heatmaps',
        f'{WORKDIR}/keys',
        f'{WORKDIR}/pcap',
        f'{WORKDIR}/qlog_client',
        f'{WORKDIR}/qlog_server',
        f'{WORKDIR}/statistics',
        f'{WORKDIR}/tcpprobe',
    ]

    def delete_file(file_path):
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"File '{file_path}' deleted.")
        except Exception as e:
            logging.error(f"Error deleting file '{file_path}': {e}")

    def delete_files_in_folder(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            delete_file(file_path)

    def delete_files_in_folders(folders):
        for folder in folders:
            if os.path.exists(folder):
                delete_files_in_folder(folder)
            else:
                logging.info(f"Folder '{folder}' not found.")

    delete_files_in_folders(folders)


def read_test_cases():
    with open('./test_cases.yaml', 'r') as file:
        test_cases = yaml.safe_load(file)
    return test_cases


def read_configuration():
    with open('./.env', 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_docker_container():
    host = docker.from_env()
    client_1 = host.containers.get("client_1")
    router_1 = host.containers.get("router_1")
    router_2 = host.containers.get("router_2")
    server = host.containers.get("server")
    return client_1, router_1, router_2, server
