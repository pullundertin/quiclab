
import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import logging
import statistics
from pcap_processing import convert_pcap_to_json, get_tcp_handshake_time, get_tcp_connection_time
from modules.commands import rsync, run_client, traffic_control, run_server, shutdown_server
from modules.logs import log_config
from modules.prerequisites import reset_workdir, read_test_cases, read_configuration, get_docker_container


def run_test_case(iteration_prefix, test_case):
    try:
        with ThreadPoolExecutor() as executor:
            executor.submit(
                run_server, test_case, iteration_prefix)
            executor.submit(traffic_control, test_case)
            time.sleep(3)
            thread_3 = executor.submit(
                run_client, test_case, iteration_prefix)
            concurrent.futures.wait([thread_3])
            shutdown_server(test_case, iteration_prefix)

    except Exception as e:
        logging.error(f"An error occurred: {e}")


def run_tests():
    for round in range(test_case_settings.get('rounds')):
        for index, test_case in enumerate(test_case_settings.get('iterations'), start=1):
            iteration_prefix = f"{round}:{index}_"
            run_test_case(iteration_prefix, test_case)


if __name__ == "__main__":
    WORKDIR = read_configuration().get("WORKDIR")
    PCAP_PATH = read_configuration().get("PCAP_PATH")
    TEST_CASES = read_configuration().get("TEST_CASES")

    log_config()
    reset_workdir()
    test_case_settings = read_test_cases()
    run_tests()

    convert_pcap_to_json()
    tcp_handshake_durations = get_tcp_handshake_time()
    tcp_connection_durations = get_tcp_connection_time()

    print('hs_median', statistics.median(tcp_handshake_durations))
    print('hs_min', min(tcp_handshake_durations))
    print('hs_max', max(tcp_handshake_durations))
    print('conn_median', statistics.median(tcp_connection_durations))
    print('con_min', min(tcp_connection_durations))
    print('con_max', max(tcp_connection_durations))
    # get_tcp_rtt_statistics()
    rsync()
    logging.info("All tasks are completed.")
