import os
import logging
import docker
import yaml
import shutil
from modules.classes import Test, TestCase, TestCases
from modules.progress_bar import update_program_progress_bar


def reset_workdir():
    update_program_progress_bar('Reset')

    WORKDIR = read_configuration().get("WORKDIR")
    folders = [
        f'{WORKDIR}/anova',
        f'{WORKDIR}/boxplots',
        f'{WORKDIR}/downloads',
        f'{WORKDIR}/heatmaps',
        f'{WORKDIR}/keys',
        f'{WORKDIR}/pcap',
        f'{WORKDIR}/qlog_client',
        f'{WORKDIR}/qlog_server',
        f'{WORKDIR}/t_test',
        f'{WORKDIR}/tcpprobe',
        f'{WORKDIR}/test_results',
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


def get_test_object(args):
    def get_test_object_from_config_or_log_file_depending_on_full_run(args):
        if args.full:
            return read_configuration().get("TEST_CASES_CONFIG_FILE")
        else:
            return read_configuration().get("TEST_CASES_LOG_FILE")

    def update_total_number_of_test_cases(control_parameter):
        def get_number_of_modes(test):
            array_of_modes = test.test_cases_compressed['mode']
            number_of_modes = len(array_of_modes)
            return number_of_modes
        
        def get_number_of_control_parameter_values(control_parameter):
            if control_parameter is not None:
                array_of_control_parameters = test.test_cases_compressed[control_parameter]
                number_of_control_parameter_values = len(array_of_control_parameters)
            else:
                number_of_control_parameter_values = 1
            return number_of_control_parameter_values
        
        total_number_of_test_cases = get_number_of_modes(test) * get_number_of_control_parameter_values(control_parameter)
        test.update_total_number_of_test_cases(total_number_of_test_cases)

    config = get_test_object_from_config_or_log_file_depending_on_full_run(
        args)

    with open(config, 'r') as file:
        test_configuration = yaml.safe_load(file)
    test = Test()
    test.iterations = test_configuration['iterations']
    test.test_cases_compressed = test_configuration['cases']
    test.control_parameter, test.control_parameter_values = get_control_parameter(test.test_cases_compressed)
    update_total_number_of_test_cases(test.control_parameter)
    test.test_cases_decompressed = decompress_test_cases(test)
    return test


def decompress_test_cases(test):
    control_parameter = test.control_parameter
    test_cases_compressed = test.test_cases_compressed
    iterations = test.iterations
    modes = test_cases_compressed['mode']
    index = 1
    test_cases = TestCases()

    if control_parameter is not None:
        control_parameter_values = test.test_cases_compressed[control_parameter]
        for mode in modes:
            for element in control_parameter_values:
                for iteration in range(iterations):
                    test_case = {
                        **test_cases_compressed,
                        'iteration': iteration + 1,
                        'mode': mode,
                        control_parameter: element,
                    }

                    test_cases.add_test_case(TestCase(index, test_case))
                index += 1
    else:
        for mode in modes:
            for iteration in range(iterations):
                test_case = {
                    **test_cases_compressed,
                    'iteration': iteration + 1,
                    'mode': mode,
                }
                test_cases.add_test_case(TestCase(index, test_case))
            index += 1

    return test_cases


def get_control_parameter(test_cases):
    def read_key_value_pairs_and_return_key_with_a_list_as_value():
        for key, value in test_cases.items():
            if isinstance(value, list) and key != 'mode':
                return key, value

        return None, None

    control_parameter, control_parameter_values = read_key_value_pairs_and_return_key_with_a_list_as_value()
    return control_parameter, control_parameter_values


def save_test_cases_config_to_log_file():
    update_program_progress_bar('Save Config')

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
