import os
import logging
import docker
import yaml


def reset_workdir():
    WORKDIR = read_configuration().get("WORKDIR")
    folders = [
        f'{WORKDIR}/pcap',
        f'{WORKDIR}/qlog_client',
        f'{WORKDIR}/qlog_server',
        f'{WORKDIR}/keys',
        f'{WORKDIR}/tcpprobe']

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


def read_test_cases():
    # test_cases = []
    # with open(file_name, 'r') as file:
    #     test_case = {}
    #     for line in file:
    #         line = line.strip()
    #         if line.startswith('Iteration'):
    #             if test_case:
    #                 test_cases.append(test_case)
    #             test_case = {}
    #         elif ': ' in line:
    #             key, value = line.split(': ', 1)
    #             test_case[key.strip()] = value.strip()

    #     if test_case:
    #         test_cases.append(test_case)

    # return test_cases
    with open('./test_cases.yaml', 'r') as file:
        test_cases = yaml.safe_load(file)
    return test_cases


def read_configuration():
    with open('./config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_docker_container():
    host = docker.from_env()
    client_1 = host.containers.get("client_1")
    router_1 = host.containers.get("router_1")
    router_2 = host.containers.get("router_2")
    server = host.containers.get("server")
    return client_1, router_1, router_2, server
