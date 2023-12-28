
import logging
from modules.data_extraction import convert_pcap_to_json, get_test_results
from modules.commands import rsync, rsync_permanent
from modules.logs import log_config
from modules.prerequisites import reset_workdir, read_configuration, get_test_object, save_test_cases_config_to_log_file
from modules.heatmap import show_heatmaps
from modules.boxplot import show_boxplot
from modules.tests import run_tests
from modules.converter import process_tcp_probe_logs
from modules.statistics import do_statistics
from modules.t_test import t_test
from modules.anova import do_anova
from modules.goodput import calculate_goodput, show_goodput_graph
from modules.progress_bar import update_program_progress_bar
import os
import argparse
import pandas as pd


def arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('--full', action='store_true',
                        help='run full execution')
    parser.add_argument('--store', type=str,
                        help='directory for permanent storage')
    parser.add_argument('--results', action='store_true',
                        help='print resulting dataframe')

    args = parser.parse_args()

    return args


def evaluate_test_results(test_results_dataframe, median_dataframe, test):
    update_program_progress_bar('Evaluate Test Results')

    control_parameter = test.control_parameter
    if control_parameter is None:
        control_parameter = 'generic_heatmap'
    iterations = test.iterations
    show_goodput_graph(median_dataframe, control_parameter)
    show_boxplot(test_results_dataframe, test)
    show_heatmaps(median_dataframe, control_parameter)
    if iterations > 2:
        t_test(test_results_dataframe, control_parameter)
        do_anova(test_results_dataframe, control_parameter)


def store_results(test_results_dataframe, median_dataframe, args):
    def write_dataframes_to_csv(test_results_dataframe, median_dataframe):
        TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')
        test_results_dataframe.to_csv(
            f'{TEST_RESULTS_DIR}/test_results.csv', index=False)
        median_dataframe.to_csv(f'{TEST_RESULTS_DIR}/medians.csv', index=False)

    def sync_shared_folders_with_remote_host(args):
        if args.store:
            rsync()
            rsync_permanent(args.store)
        else:
            rsync()

    update_program_progress_bar('Store Test Results')
    if test_results_dataframe is not None and median_dataframe is not None:
        write_dataframes_to_csv(test_results_dataframe, median_dataframe)
    sync_shared_folders_with_remote_host(args)


def create_dataframe_from_object(test):
    update_program_progress_bar('Create Dataframe')

    list_of_df = []

    def convert_each_test_case_object_into_a_dataframe():
        df = pd.DataFrame()
        for test_case in test.test_cases_decompressed.test_cases:
            df = pd.DataFrame([vars(test_case)])
            list_of_df.append(df)

    def add_each_dataframe_as_new_row_to_a_main_dataframe():
        return pd.concat(list_of_df, axis=0)

    convert_each_test_case_object_into_a_dataframe()
    main_df = add_each_dataframe_as_new_row_to_a_main_dataframe()
    return main_df


def print_all_results_to_cli(test_results_dataframe, median_dataframe):
    columns_to_print = ['mode', 'size', 'delay', 'delay_deviation', 'loss', 'rate', 'migration', 'goodput',
                        'tcp_hs', 'aioquic_hs', 'quicgo_hs', 'tcp_conn', 'aioquic_conn', 'quicgo_conn']
    if args.results:
        print(test_results_dataframe[columns_to_print])
        print("\\\\\\\\\\\\\\\\ MEDIAN \\\\\\\\\\\\\\\\\\\\")
        print(median_dataframe[columns_to_print])


if __name__ == "__main__":
    test_results_dataframe = None
    median_dataframe = None

    log_config()
    args = arguments()

    test = get_test_object(args)

    if args.full:
        logging.info(f"{os.getenv('HOST')}: full execution enabled")

        reset_workdir()
        save_test_cases_config_to_log_file()
        run_tests(test)
        # TODO copy lsquic keys into client.key
        convert_pcap_to_json()
        process_tcp_probe_logs()

    else:
        logging.info("Executing evaluation only")

    get_test_results(test)
    print(test)
    # calculate_goodput(test)
    # test_results_dataframe = create_dataframe_from_object(test)
    # median_dataframe = do_statistics(test_results_dataframe)
    # print_all_results_to_cli(test_results_dataframe, median_dataframe)
    # evaluate_test_results(test_results_dataframe, median_dataframe, test)

    store_results(None, None, args)

    logging.info("All tasks are completed.")
