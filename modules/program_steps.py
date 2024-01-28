import pandas as pd
from modules.prerequisites import read_configuration, reset_workdir, save_test_cases_config_to_log_file, write_test_object_to_log, create_dataframe_from_object, write_dataframes_to_csv
from modules.tests import run_tests
from modules.converter import process_tcp_probe_logs
from modules.statistics import do_statistics
from modules.qlog_data import get_qlog_data
from modules.pcap_data import get_pcap_data
from modules.system_info import get_system_info
from modules.additional_metrics import calculate_additional_metrics
from modules.heatmap import show_heatmaps
from modules.boxplot import show_boxplot
from modules.goodput import show_goodput_graph
from modules.statistics_new import run_statistics
from modules.progress_bar import update_program_progress_bar


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
    write_dataframes_to_csv(test_results_dataframe,
                            'test_results_dataframe')

def evaluate_data(test_results_dataframe, test):
    statistics_dataframe = do_statistics(test_results_dataframe, test)
    write_dataframes_to_csv(statistics_dataframe, 'statistics_dataframe')
    df = merge_columns_with_the_same_metric(test_results_dataframe)
    run_statistics(df, test)
    return df


def visualize_data(test_results_dataframe, statistics_dataframe, test):
    update_program_progress_bar('Evaluate Test Results')
    control_parameter = test.control_parameter
    if control_parameter is None:
        control_parameter = 'generic_heatmap'
    show_goodput_graph(statistics_dataframe, control_parameter)
    show_boxplot(test_results_dataframe, test)
    show_heatmaps(statistics_dataframe, control_parameter)


def merge_columns_with_the_same_metric(df):
    result_dict = {'hs': ['aioquic_hs', 'quicgo_hs', 'tcp_hs'], 'conn': [
        'aioquic_conn', 'quicgo_conn', 'tcp_conn']}

    for metric, columns in result_dict.items():

        df[f'{metric}'] = df[columns].replace(
            'None', '').sum(1)

        TEST_CONFIG_COLUMNS = read_configuration().get('TEST_CONFIG_COLUMNS')
    return df[TEST_CONFIG_COLUMNS + ['goodput', 'hs', 'conn']]


def read_data():
    test_results_dataframe = pd.read_parquet(
        'shared/test_results/test_results_dataframe.parquet')
    return test_results_dataframe
