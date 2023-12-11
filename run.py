import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
from modules.pcap_processing import convert_pcap_to_json, get_statistics
from modules.commands import rsync, run_client, traffic_control, run_server, shutdown_server
from modules.logs import log_config
from modules.prerequisites import reset_workdir, read_test_cases, read_configuration


def run_test_case(iteration_prefix, test_case):
    try:
        with ThreadPoolExecutor() as executor:
            executor.submit(run_server, test_case, iteration_prefix)
            executor.submit(traffic_control, test_case)
            time.sleep(3)
            thread_3 = executor.submit(run_client, test_case, iteration_prefix)
            concurrent.futures.wait([thread_3])
            shutdown_server(test_case, iteration_prefix)

    except Exception as e:
        logging.error(f"An error occurred: {e}")


def run_tests():
    test_case_settings = read_test_cases()
    test_cases = test_case_settings.get('iterations')
    rounds = test_case_settings.get('rounds')

    for round in range(rounds):
        for index, test_case in enumerate(test_cases, start=1):
            iteration_prefix = f"{round}:{index}_"
            run_test_case(iteration_prefix, test_case)


if __name__ == "__main__":
    config = read_configuration()
    WORKDIR = config.get("WORKDIR")
    PCAP_PATH = config.get("PCAP_PATH")
    TEST_CASES = config.get("TEST_CASES")

    log_config()
    # reset_workdir()
    # run_tests()
    # convert_pcap_to_json()
    get_statistics()
    rsync()
    logging.info("All tasks are completed.")
