import time
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from modules.commands import run_client, traffic_control, run_server, run_server_tracing, stop_server, stop_server_tracing
from modules.progress_bar import update_test_progress_bar, update_program_progress_bar
from modules.prerequisites import reset_workdir

def run_tests(test):
    update_program_progress_bar('Run Tests')

    def iterate_over_decompressed_test_cases_in_test_object():
        test_cases = test.test_cases_decompressed.test_cases
        number_of_iterations = test.iterations
        for test_case in (test_cases):
            update_test_progress_bar(test_case.number, test.total_number_of_test_cases,
                                     test_case.iteration, number_of_iterations)
            run_test_case(test_case, test)

    iterate_over_decompressed_test_cases_in_test_object()


def run_test_case(test_case, test):

    try:
        with ThreadPoolExecutor() as executor:
            logging.info(
                f"//////   {test_case.file_name_prefix}{test_case.mode} ///////")
            executor.submit(run_server, test_case)
            time.sleep(1)

            if test_case.mode == 'aioquic' and test_case.zero_rtt and test_case.iteration == 1:
                print('testrun')
                time.sleep(5)
                one_rtt_request = executor.submit(run_client, test_case)
                wait([one_rtt_request])
                delete_pcap_and_qlogs = executor.submit(reset_workdir)
                wait([delete_pcap_and_qlogs])

            executor.submit(run_server_tracing, test_case)
            executor.submit(traffic_control, test_case)
            time.sleep(3)
            client_process = executor.submit(
                run_client, test_case)
            wait([client_process])
            stop_tracing_process = executor.submit(
                stop_server_tracing, test_case)
            wait([stop_tracing_process])
            if (test_case.mode == 'aioquic' and test_case.zero_rtt and test_case.iteration < test.iterations):
                print('server don\'t stop')
                return
            executor.submit(stop_server, test_case)
            logging.info(f"//////////////////////////////////////////")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
