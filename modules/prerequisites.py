import os
import docker
import yaml
import shutil
import argparse
import pandas as pd

from modules.classes import Test, TestCase, TestCases
from modules.progress_bar import update_program_progress_bar


def arguments():
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('--test', action='store_true',
                        help='run tests')
    parser.add_argument('--store', type=str,
                        help='directory for permanent storage')
    parser.add_argument('--results', action='store_true',
                        help='print resulting dataframe')
    parser.add_argument('--extract', action='store_true',
                        help='extract data from data sources')
    parser.add_argument('--evaluate', action='store_true',
                        help='evaluate test results')
    parser.add_argument('--viz', action='store_true',
                        help='generate visualization')

    args = parser.parse_args()

    return args


def check_if_folders_for_results_exist():
    SHARED_DIRECTORIES = read_configuration().get("SHARED_DIRECTORIES")

    for folder in SHARED_DIRECTORIES:
        if not os.path.exists(folder):
            os.makedirs(folder)


def delete_old_test_results():
    TEST_RESULTS_DIRECTORIES = read_configuration().get("TEST_RESULTS_DIRECTORIES")

    for folder in TEST_RESULTS_DIRECTORIES:
        if os.path.exists(folder):
            files = os.listdir(folder)
            for file_name in files:
                file_path = os.path.join(folder, file_name)
                os.remove(file_path)


def reset_workdir():
    update_program_progress_bar('Reset')

    WORKDIR = read_configuration().get("WORKDIR")
    LOG_PATH = read_configuration().get("LOG_PATH")

    for root, dirs, files in os.walk(WORKDIR):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path != LOG_PATH:
                os.remove(file_path)


def get_test_object(args):
    def get_test_object_from_config_or_log_file_depending_on_full_run(args):
        if args.test:
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
                number_of_control_parameter_values = len(
                    array_of_control_parameters)
            else:
                number_of_control_parameter_values = 1
            return number_of_control_parameter_values

        total_number_of_test_cases = get_number_of_modes(
            test) * get_number_of_control_parameter_values(control_parameter)
        test.update_total_number_of_test_cases(total_number_of_test_cases)

    config = get_test_object_from_config_or_log_file_depending_on_full_run(
        args)

    with open(config, 'r') as file:
        test_configuration = yaml.safe_load(file)
    test = Test()
    test.iterations = test_configuration['iterations']
    test.test_cases_compressed = test_configuration['cases']
    test.control_parameter, test.control_parameter_values = get_control_parameter(
        test.test_cases_compressed)
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


def write_dataframes_to_csv(df, filename):
    TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')
    df.to_parquet(
        f'{TEST_RESULTS_DIR}/{filename}.parquet', index=False)


def write_test_object_to_log(test, filename):
    TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')
    with open(f'{TEST_RESULTS_DIR}/{filename}.log', 'w') as file:
        file.write(str(test))


def create_dataframe_from_object(test):
    update_program_progress_bar('Create Dataframe')

    list_of_df = []

    def convert_each_test_case_object_into_a_dataframe():
        for test_case in test.test_cases_decompressed.test_cases:
            df = pd.DataFrame([vars(test_case)])
            streams = df['streams'].iloc[0] if 'streams' in df.columns else None

            if streams:
                stream_data = streams.streams
                stream_info = {}
                for stream in stream_data:
                    stream_id = stream.stream_id
                    connection_time = stream.connection_time
                    stream_info[f'Stream_ID_{stream_id}_conn'] = connection_time
                    goodput = stream.goodput
                    stream_info[f'Stream_ID_{stream_id}_goodput'] = goodput
                    link_utilization = stream.link_utilization
                    stream_info[f'Stream_ID_{stream_id}_link_utilization'] = link_utilization

                df = pd.concat([df, pd.DataFrame([stream_info])], axis=1)

            list_of_df.append(df)

    def add_each_dataframe_as_new_row_to_a_main_dataframe():
        return pd.concat(list_of_df, axis=0)

    convert_each_test_case_object_into_a_dataframe()
    main_df = add_each_dataframe_as_new_row_to_a_main_dataframe()
    main_df = main_df.drop(columns=['streams'])

    return main_df
