import os
import logging
import docker
import yaml
import shutil


class Test:
    def __init__(self):
        self.iterations = None
        self.test_cases_compressed = None
        self.test_cases_decompressed = None
        self.control_parameter = None

    def __str__(self):
        return f"Iterations: {self.iterations}\nControl Parameter: {self.control_parameter}\nTest Cases: {self.test_cases_decompressed}"


class TestCases:
    def __init__(self):
        self.test_cases = []

    def add_test_case(self, test_case):
        self.test_cases.append(test_case)

    def __str__(self):
        test_cases = "\n".join(str(test_case) for test_case in self.test_cases)
        return f"Test Cases:\n{test_cases}"


class TestCase:
    def __init__(self, number, config):
        self.number = number
        self.config = config
        self.iteration = None
        self.test_results = None
        self.file_name_prefix = None

    def __str__(self):
        return f"Test Case: {self.number}, Iteration: {self.iteration}, Settings: {self.config}"

    def set_iteration(self, iteration):
        self.iteration = iteration
        self.file_name_prefix = f"Case_{self.number}_Iteration_{self.iteration}_"


def reset_workdir():
    WORKDIR = read_configuration().get("WORKDIR")
    folders = [
        f'{WORKDIR}/boxplots',
        f'{WORKDIR}/heatmaps',
        f'{WORKDIR}/keys',
        f'{WORKDIR}/pcap',
        f'{WORKDIR}/qlog_client',
        f'{WORKDIR}/qlog_server',
        f'{WORKDIR}/test_results',
        f'{WORKDIR}/t_test',
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


def get_test_object():
    with open('./test_cases.yaml', 'r') as file:
        test_configuration = yaml.safe_load(file)
    test = Test()
    test.iterations = test_configuration['iterations']
    test.test_cases_compressed = test_configuration['cases']
    test.control_parameter = get_control_parameter(test.test_cases_compressed)
    test.test_cases_decompressed = decompress_test_cases(test)
    # print(test.__str__())
    return test


def decompress_test_cases(test):
    control_parameter = test.control_parameter
    test_cases_compressed = test.test_cases_compressed
    modes = test_cases_compressed['mode']
    index = 1
    test_cases = TestCases()

    if control_parameter is not None:
        control_parameter_values = test.test_cases_compressed[control_parameter]
        for mode in modes:
            for element in control_parameter_values:
                test_case = {
                    **test_cases_compressed,
                    'mode': mode,
                    control_parameter: element,
                }

                test_cases.add_test_case(TestCase(index, test_case))
                index += 1
    else:
        for mode in modes:
            test_case = {
                **test_cases_compressed,
                'mode': mode,
            }
            test_cases.add_test_case(TestCase(index, test_case))
            index += 1

    return test_cases


def get_control_parameter(test_cases):
    control_parameter = None

    def read_key_value_pairs_and_return_key_with_a_list_as_value():
        for key, value in test_cases.items():
            if isinstance(value, list) and key != 'mode':
                return key

    control_parameter = read_key_value_pairs_and_return_key_with_a_list_as_value()
    return control_parameter


def save_test_cases_config_to_log_file():
    TEST_CASES_CONFIG_FILE = read_configuration().get("TEST_CASES_CONFIG_FILE")
    TEST_CASES_LOG_FILE = read_configuration().get("TEST_CASES_LOG_FILE")
    shutil.copy(TEST_CASES_CONFIG_FILE, TEST_CASES_LOG_FILE)


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
