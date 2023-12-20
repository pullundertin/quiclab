import time
import logging
from modules.prerequisites import read_test_cases

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.commands import run_client, traffic_control, run_server, run_server_tracing, stop_server, stop_server_tracing


def find_keys_with_list_values(data):
    key_with_list = None
    for key, value in data['cases'].items():
        if isinstance(value, list) and key != 'mode':
            key_with_list = key
    return key_with_list

def generate_test_cases(test_case_settings):
    independent_variable = find_keys_with_list_values(test_case_settings)
    iterations = test_case_settings.get('iterations')
    cases = test_case_settings['cases']
    modes = test_case_settings['cases']['mode']
    index = 1
    test_cases = []

    if independent_variable is not None:
        independent_variables = test_case_settings['cases'][independent_variable]
        for mode in modes:
            for element in independent_variables:
                for iteration in range(iterations):
                    iteration_prefix = f"case_{index}_iteration_{iteration+1}_"
                    test_case = {
                        **cases,
                        'mode': mode,
                        independent_variable: element,
                    }
                    test_cases.append((iteration_prefix, test_case))
                index += 1
    else:
        for mode in modes:
            for iteration in range(iterations):
                iteration_prefix = f"case_{index}_iteration_{iteration+1}_"
                test_case = {
                    **cases,
                    'mode': mode,
                }
                test_cases.append((iteration_prefix, test_case))
            index += 1

    return test_cases

def run_tests():
    test_case_settings = read_test_cases()
    test_cases = generate_test_cases(test_case_settings)

    for index, (iteration_prefix, test_case) in enumerate(test_cases, start=1):
        run_test_case(iteration_prefix, test_case)

def get_test_configuration_of_json_file(json_file):
    test_case_settings = read_test_cases()
    test_cases = generate_test_cases(test_case_settings)

    for index, (iteration_prefix, test_case) in enumerate(test_cases, start=1):
        if iteration_prefix in json_file:
            return test_case

def run_test_case(iteration_prefix, test_case):
    try:
        with ThreadPoolExecutor() as executor:
            logging.info(
                f"//////   TEST {iteration_prefix}{test_case['mode']} ///////")
            executor.submit(run_server, test_case)
            time.sleep(1)
            executor.submit(run_server_tracing, test_case, iteration_prefix)
            executor.submit(traffic_control, test_case)
            time.sleep(3)
            client_process = executor.submit(
                run_client, test_case, iteration_prefix)
            wait([client_process])
            stop_tracing_process = executor.submit(
                stop_server_tracing, test_case, iteration_prefix)
            wait([stop_tracing_process])
            executor.submit(stop_server, test_case)
            logging.info(f"//////////////////////////////////////////")
    except Exception as e:
        logging.error(f"An error occurred: {e}")