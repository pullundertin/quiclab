import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
import logging
from modules.pcap_processing import convert_pcap_to_json, get_statistics
from modules.commands import rsync, run_client, traffic_control, run_server, run_server_tracing, stop_server, stop_server_tracing
from modules.logs import log_config
from modules.prerequisites import reset_workdir, read_test_cases
from modules.heatmap import show_handshake_heatmap, show_connection_heatmap
import os
import argparse


def arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('--full', action='store_true',
                        help='run full execution')

    args = parser.parse_args()

    return args


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
    test_cases = test_case_settings.get('cases')
    iterations = test_case_settings.get('iterations')

    for index, test_case in enumerate(test_cases, start=1):
        for iteration in range(iterations):
            iteration_prefix = f"case_{index}_iteration_{iteration+1}_"
            run_test_case(iteration_prefix, test_case)


def evaluate_test_results():
    statistics, medians = get_statistics()
    statistics.to_csv('shared/statistics/statistics.csv', index=False)
    medians.to_csv('shared/statistics/medians.csv', index=False)
    # show_handshake_heatmap(medians)
    # show_connection_heatmap(medians)


if __name__ == "__main__":
    log_config()
    args = arguments()

    if args.full:
        logging.info(f"{os.getenv('HOST')}: full execution enabled")

        reset_workdir()
        try:
            with ThreadPoolExecutor() as executor:
                test_process = executor.submit(run_tests)
                wait([test_process])
                convert_pcap_to_json()
                logging.info("Full execution completed.")
        except Exception as e:
            logging.error(
                f"{os.getenv('HOST')}: Error during full execution: {str(e)}")
            raise
    else:
        logging.info("Executing evaluation only")

    try:
        evaluate_test_results()
        rsync()
        logging.info("All tasks are completed.")
    except Exception as e:
        logging.error(
            f"{os.getenv('HOST')}: Error during partial tasks execution: {str(e)}")
        raise
