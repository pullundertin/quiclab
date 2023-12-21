import time
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.commands import run_client, traffic_control, run_server, run_server_tracing, stop_server, stop_server_tracing


def run_tests(test):
    def iterate_over_decompressed_test_cases_in_test_object():
        for test_case in (test.test_cases_decompressed.test_cases):
            run_test_case(test_case)

    iterate_over_decompressed_test_cases_in_test_object()


def run_test_case(test_case):

    try:
        with ThreadPoolExecutor() as executor:
            logging.info(
                f"//////   {test_case.file_name_prefix}{test_case.mode} ///////")
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
