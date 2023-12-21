import time
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.commands import run_client, traffic_control, run_server, run_server_tracing, stop_server, stop_server_tracing


def run_tests(test):
    def iterate_over_decompressed_test_cases_in_test_object():
        for test_case in (test.test_cases_decompressed.test_cases):
            repeat_the_same_test_case_for_number_of_iterations(test_case)

    def repeat_the_same_test_case_for_number_of_iterations(test_case):
        for iteration in range(test.iterations):
            add_current_number_of_iteration_to_test_case_object(
                test_case, iteration)
            run_test_case(test_case)

    def add_current_number_of_iteration_to_test_case_object(test_case, iteration):
        test_case.set_iteration(iteration + 1)

    iterate_over_decompressed_test_cases_in_test_object()


def get_test_configuration_of_json_file(json_file, test):

    for index, (iteration_prefix, test_case) in enumerate(test.test_cases, start=1):
        if iteration_prefix in json_file:
            return test_case


def run_test_case(test_case):

    try:
        with ThreadPoolExecutor() as executor:
            logging.info(
                f"//////   {test_case.file_name_prefix}{test_case.config['mode']} ///////")
            executor.submit(run_server, test_case)
            time.sleep(1)
            executor.submit(run_server_tracing, test_case)
            executor.submit(traffic_control, test_case)
            time.sleep(3)
            client_process = executor.submit(
                run_client, test_case)
            wait([client_process])
            stop_tracing_process = executor.submit(
                stop_server_tracing, test_case)
            wait([stop_tracing_process])
            executor.submit(stop_server, test_case)
            logging.info(f"//////////////////////////////////////////")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
