
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


def evaluate_test_results(test_results, medians):
    show_boxplot(test_results)
    show_heatmaps(medians, args)


def store_results(test_results, medians, args):
    # TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')
    # test_results.to_csv(f'{TEST_RESULTS_DIR}/test_results.csv', index=False)
    # medians.to_csv(f'{TEST_RESULTS_DIR}/medians.csv', index=False)
    if args.store:
        rsync()
        rsync_permanent(args.store)
    else:
        rsync()


# def clean_dataframe(df):
#     df['quic_hs'] = df['aioquic_hs'].combine_first(df['quicgo_hs'])
#     df['quic_conn'] = df['aioquic_conn'].combine_first(df['quicgo_conn'])
#     return df

def create_dataframe_from_object(test):
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


if __name__ == "__main__":
    log_config()
    args = arguments()
    test = get_test_object()

    if args.full:
        logging.info(f"{os.getenv('HOST')}: full execution enabled")

        reset_workdir()
        save_test_cases_config_to_log_file()
        run_tests(test)
        convert_pcap_to_json()
        process_tcp_probe_logs()

    else:
        logging.info("Executing evaluation only")

    get_test_results(test)
    df = create_dataframe_from_object(test)

    median_df = do_statistics(df)
    print(median_df)
    # test_results = clean_dataframe(test_results)
    # evaluate_test_results(test_results, medians)
    # store_results(None, None, args)

    logging.info("All tasks are completed.")
