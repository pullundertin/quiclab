import os
import logging
import docker
import yaml
import shutil
import re
from modules.progress_bar import update_program_progress_bar


class Test:
    def __init__(self):
        self.iterations = None
        self.test_cases_compressed = None
        self.test_cases_decompressed = TestCases()
        self.control_parameter = None
        self.control_parameter_values = None
        self.total_number_of_test_cases = 0

    def update_total_number_of_test_cases(self, total_number_of_test_cases):
        setattr(self, 'total_number_of_test_cases', total_number_of_test_cases)

    def __str__(self):
        return f"Iterations: {self.iterations}\nControl Parameter: {self.control_parameter}, Control Parameter Values: {self.control_parameter_values}\nNumber of Test Cases: {self.total_number_of_test_cases}\nTest Cases: {self.test_cases_decompressed}"


class TestCases:
    def __init__(self):
        self.test_cases = []

    def add_test_case(self, test_case):
        self.test_cases.append(test_case)

    def __str__(self):
        test_cases = "\n".join(str(test_case) for test_case in self.test_cases)
        return f"\n{test_cases}"

    def map_file_to_test_case(self, json_file):
        matching_test_case = None
        # Extracting Number and Iteration from the JSON file name using regular expressions
        match = re.match(r'.*Case_(\d+)_Iteration_(\d+)_', json_file)
        if match:
            extracted_number = int(match.group(1))
            extracted_iteration = int(match.group(2))

            # Searching for the matching TestCase object
            matching_test_case = next((test_case for test_case in self.test_cases if test_case.number ==
                                      extracted_number and test_case.iteration == extracted_iteration), None)

        return matching_test_case

    def map_qlog_file_to_test_case_by_dcid(self, qlog_file):
        matching_test_case = None
        for test_case in self.test_cases:
            dcid = test_case.dcid
            dcid_hex = test_case.dcid_hex
            if dcid != None and (dcid in qlog_file or dcid_hex in qlog_file):
                matching_test_case = test_case
        return matching_test_case


class TestCase:
    def __init__(self, number, config):
        self.number = number
        self.iteration = config['iteration']
        self.file_name_prefix = f"Case_{self.number}_Iteration_{self.iteration}_"
        self.mode = config['mode']
        self.size = config['size']
        self.delay = config['delay']
        self.delay_deviation = config['delay_deviation']
        self.loss = config['loss']
        self.rate = config['rate']
        self.firewall = config['firewall']
        self.window_scaling = config['window_scaling']
        self.rmin = config['rmin']
        self.rdef = config['rdef']
        self.rmax = config['rmax']
        self.migration = config['migration']
        self.parallel = config['parallel']
        self.generic_heatmap = config['generic_heatmap']
        self.goodput = None
        self.tcp_rtt = None
        self.tcp_hs = None
        self.tcp_conn = None
        self.quic_min_rtt = None
        self.quic_smoothed_rtt = None
        self.aioquic_hs = None
        self.aioquic_conn = None
        self.quicgo_hs = None
        self.quicgo_conn = None
        self.quic_hs = None
        self.quic_conn = None
        self.dcid = None
        self.dcid_hex = None

    def __str__(self):
        return f"""
        Test Case: {self.number}, 
        Iteration: {self.iteration}, 

        Settings: 
        Mode: {self.mode}
        Size: {self.size}
        Delay: {self.delay}
        Delay Deviation: {self.delay_deviation}
        Loss: {self.loss}
        Rate: {self.rate}
        Firewall: {self.firewall}
        Window Scaling: {self.window_scaling}
        Receive Window Min: {self.rmin}
        Receive Window Default: {self.rdef}
        Receive Window Max: {self.rmax}
        Connection Migration: {self.migration}
        Parallel Download: {self.parallel}
        Generic: {self.generic_heatmap}

        Test Results:
        Goodput: {self.goodput}

        TCP RTT: {self.tcp_rtt}
        TCP Handshake Time: {self.tcp_hs}
        TCP Connection Time: {self.tcp_conn}

        QUIC DCID: {self.dcid}
        QUIC DCID hex: {self.dcid_hex}
        QUIC Min RTT: {self.quic_min_rtt}
        QUIC Smoothed RTT: {self.quic_smoothed_rtt}
        QUIC Handshake Time: {self.quic_hs}
        QUIC Connection Time: {self.quic_conn}
        # AIOQUIC Handshake Time: {self.aioquic_hs}
        # QUIC-GO Handshake Time: {self.quicgo_hs}
        # AIOQUIC Connection Time: {self.aioquic_conn}
        # QUIC-GO Connection Time: {self.quicgo_conn}
        """

    def store_test_results_for(self, test_results):
        for key, value in test_results.items():
            setattr(self, key, value)

    def update_quic_rtt_data_from_qlog(self, min_rtt_values, smoothed_rtt_values):
        self.quic_min_rtt = min_rtt_values
        self.quic_smoothed_rtt = smoothed_rtt_values

    def update_goodput(self, goodput):
        setattr(self, 'goodput', goodput)


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
