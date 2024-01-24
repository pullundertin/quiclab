
import logging
from modules.commands import rsync_permanent
from modules.logs import log_config
from modules.prerequisites import reset_workdir, get_test_object, save_test_cases_config_to_log_file, arguments, check_if_folders_for_results_exist, delete_old_test_results, write_test_object_to_log, create_dataframe_from_object, write_dataframes_to_csv
from modules.heatmap import show_heatmaps
from modules.boxplot import show_boxplot
from modules.tests import run_tests
from modules.converter import process_tcp_probe_logs
from modules.statistics import do_statistics
from modules.anova import do_anova
from modules.goodput import show_goodput_graph
from modules.progress_bar import update_program_progress_bar
from modules.histogram import show_histogram
from modules.qlog_data import get_qlog_data
from modules.pcap_data import get_pcap_data
from modules.system_info import get_system_info
from modules.additional_metrics import calculate_additional_metrics
from modules.prerequisites import read_configuration
from modules.statistics_new import run_statistics
from sci_analysis import analyze
import scikit_posthocs as sp
import matplotlib.pyplot as plt
from matplotlib import gridspec
import seaborn as sns
import os
import pandas as pd


def visualize_data(test_results_dataframe, median_dataframe, test):
    update_program_progress_bar('Evaluate Test Results')
    control_parameter = test.control_parameter
    if control_parameter is None:
        control_parameter = 'generic_heatmap'
    iterations = test.iterations
    # show_histogram(test_results_dataframe, control_parameter)
    # show_goodput_graph(median_dataframe, control_parameter)
    show_boxplot(test_results_dataframe, test)
    # show_heatmaps(median_dataframe, control_parameter)

def merge_columns_with_the_same_metric(df):
    result_dict = {'hs': ['aioquic_hs', 'quicgo_hs', 'tcp_hs'], 'conn': [
        'aioquic_conn', 'quicgo_conn', 'tcp_conn']}

    for metric, columns in result_dict.items():

        df[f'{metric}'] = df[columns].replace(
            'None', '').sum(1)

        TEST_CONFIG_COLUMNS = read_configuration().get('TEST_CONFIG_COLUMNS')
    return df[TEST_CONFIG_COLUMNS + ['goodput', 'hs', 'conn']]


def generate_new_data(test):
    reset_workdir()
    save_test_cases_config_to_log_file()
    get_system_info()
    run_tests(test)

def extract_data(test):
    process_tcp_probe_logs()
    get_pcap_data(test)
    write_test_object_to_log(test, 'pcap')
    get_qlog_data(test)
    write_test_object_to_log(test, 'qlog')
    calculate_additional_metrics(test)

    test_results_dataframe = create_dataframe_from_object(test)
    median_dataframe = do_statistics(test_results_dataframe, test)
    write_dataframes_to_csv(test_results_dataframe,
                            'test_results_dataframe')
    write_dataframes_to_csv(median_dataframe, 'median_dataframe')

def read_data():
    test_results_dataframe = pd.read_parquet(
        'shared/test_results/test_results_dataframe.parquet')
    median_dataframe = pd.read_parquet(
        'shared/test_results/median_dataframe.parquet')
    return test_results_dataframe, median_dataframe
    
def evaluate_data(test_results_dataframe, test):
    df = merge_columns_with_the_same_metric(test_results_dataframe)
    run_statistics(df, test)
    return df

def main():

    test_results_dataframe = None
    median_dataframe = None

    args = arguments()
    log_config(args)

    test = get_test_object(args)
    check_if_folders_for_results_exist()
    delete_old_test_results()

    if args.full:
        logging.info(f"{os.getenv('HOST')}: full execution enabled")
        generate_new_data(test)
        extract_data(test)
        test_results_dataframe, median_dataframe = read_data()
        evaluate_data(test_results_dataframe, test)
    elif args.extract:
        logging.info("Executing without running tests")
        extract_data(test)
        test_results_dataframe, median_dataframe = read_data()
        evaluate_data(test_results_dataframe, test)
        # median_dataframe = do_statistics(test_results_dataframe, test)
    if not args.no_viz:
        visualize_data(test_results_dataframe, median_dataframe, test)
    if args.store:
        rsync_permanent(args.store)
    logging.info("All tasks are completed.")


if __name__ == "__main__":
    main()
