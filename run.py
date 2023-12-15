import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import logging
from modules.pcap_processing import convert_pcap_to_json, get_statistics
from modules.commands import rsync, run_client, traffic_control, run_server, run_server_tracing, stop_server, stop_server_tracing
from modules.logs import log_config
from modules.prerequisites import reset_workdir, read_test_cases, read_configuration
import os


def run_test_case(iteration_prefix, test_case):
    try:
        with ThreadPoolExecutor() as executor:
            logging.info(
                f"//////   TEST CASE {iteration_prefix}{test_case['mode']} ///////")
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


def run_tests():
    test_case_settings = read_test_cases()
    test_cases = test_case_settings.get('iterations')
    rounds = test_case_settings.get('rounds')

    for index, test_case in enumerate(test_cases, start=1):
        for round in range(rounds):
            iteration_prefix = f"case_{index}_iteration_{round+1}_"
            run_test_case(iteration_prefix, test_case)


if __name__ == "__main__":
    config = read_configuration()
    WORKDIR = config.get("WORKDIR")
    PCAP_PATH = config.get("PCAP_PATH")
    TEST_CASES = config.get("TEST_CASES")

    log_config()
    reset_workdir()

    try:
        with ThreadPoolExecutor() as executor:
            test_process = executor.submit(run_tests)
            wait([test_process])
            convert_pcap_to_json()
            get_statistics()
            rsync()
            logging.info("All tasks are completed.")

    except Exception as e:
        logging.error(f"{os.getenv('HOST')}: Error: {str(e)}")
        raise
