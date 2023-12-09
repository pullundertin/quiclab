import os
import logging
import docker


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
