
import logging
from modules.data_extraction import get_test_results
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
from modules.histogram import show_histogram
from modules.jains_fairness_index import calculate_jains_fairness_index
import os
import argparse
import pandas as pd
import numpy as np

TEST_CONFIG_COLUMNS = read_configuration().get("TEST_CONFIG_COLUMNS")
TEST_RESULT_COLUMNS = read_configuration().get("TEST_RESULT_COLUMNS")

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

def filter_outliers(df):
    columns_to_check = TEST_RESULT_COLUMNS

    filtered_df = df.copy()

    for column_name in columns_to_check:
        # Filter out rows where the column contains NaN values
        filtered_df = df[pd.notnull(df[column_name])]   

        Q1 = filtered_df[column_name].quantile(0.25)
        Q3 = filtered_df[column_name].quantile(0.75)
        IQR = Q3 - Q1

        # Filter the DataFrame based on the modified non-NaN values and outlier thresholds
        filtered_df = filtered_df[~((filtered_df[column_name] < (Q1 - 1.5 * IQR)) | (filtered_df[column_name] > (Q3 + 1.5 * IQR)))]

    return filtered_df

def check_if_folders_for_results_exist():
    SHARED_DIRECTORIES = read_configuration().get("SHARED_DIRECTORIES")

    for folder in SHARED_DIRECTORIES:
        if not os.path.exists(folder):  
            os.makedirs(folder)  

def delete_old_test_results():
    TEST_RESULTS_DIRECTORIES = read_configuration().get("TEST_RESULTS_DIRECTORIES")

    for folder in TEST_RESULTS_DIRECTORIES:
        if os.path.exists(folder):  
            # List all files in the folder
            files = os.listdir(folder)

            # Iterate through the files and delete each one
            for file_name in files:
                file_path = os.path.join(folder, file_name)
                os.remove(file_path) 

def evaluate_test_results(test_results_dataframe, median_dataframe, test):
    update_program_progress_bar('Evaluate Test Results')
    # test_results_dataframe_without_outliers = filter_outliers(test_results_dataframe)
    control_parameter = test.control_parameter
    if control_parameter is None:
        control_parameter = 'generic_heatmap'
    iterations = test.iterations
    show_histogram(test_results_dataframe, control_parameter)
    show_goodput_graph(test_results_dataframe, control_parameter)
    show_boxplot(test_results_dataframe, test)
    show_heatmaps(median_dataframe, control_parameter)
    if iterations > 2:
        # t_test(test_results_dataframe, control_parameter)
        do_anova(test_results_dataframe, control_parameter)


def store_results(test_results_dataframe, median_dataframe, test, args):
    TEST_RESULTS_DIR = read_configuration().get('TEST_RESULTS_DIR')
    def write_dataframes_to_csv(df, filename):
        df.to_parquet(
            f'{TEST_RESULTS_DIR}/{filename}.parquet', index=False)

    def write_test_object_to_log(test):
        with open(f'{TEST_RESULTS_DIR}/test_object.log', 'w') as file:
            file.write(str(test))

    def sync_shared_folders_with_remote_host(args):
        if args.store:
            rsync()
            rsync_permanent(args.store)
        else:
            rsync()

    update_program_progress_bar('Store Test Results')
    write_dataframes_to_csv(test_results_dataframe, 'test_results')
    write_dataframes_to_csv(median_dataframe, 'medians')
    write_test_object_to_log(test)
    # sync_shared_folders_with_remote_host(args)


def create_dataframe_from_object(test):
    update_program_progress_bar('Create Dataframe')

    list_of_df = []

    def convert_each_test_case_object_into_a_dataframe():
        df = pd.DataFrame()
        for test_case in test.test_cases_decompressed.test_cases:
            df = pd.DataFrame([vars(test_case)])
            streams = df['streams'].iloc[0] if 'streams' in df.columns else None
            
            if streams:
                stream_data = streams.streams
                stream_info = {}
                for stream in stream_data:
                    stream_id = stream.stream_id
                    connection_time = stream.connection_time
                    stream_info[f'Stream_ID_{stream_id}_conn'] = connection_time  
                    goodput = stream.goodput
                    stream_info[f'Stream_ID_{stream_id}_goodput'] = goodput  
                    link_utilization = stream.link_utilization
                    stream_info[f'Stream_ID_{stream_id}_link_utilization'] = link_utilization  

                df = pd.concat([df, pd.DataFrame([stream_info])], axis=1)
        
            list_of_df.append(df)

    def add_each_dataframe_as_new_row_to_a_main_dataframe():
        return pd.concat(list_of_df, axis=0)

    convert_each_test_case_object_into_a_dataframe()
    main_df = add_each_dataframe_as_new_row_to_a_main_dataframe()
    main_df = main_df.drop(columns=['streams'])

    return main_df


def print_all_results_to_cli(test_results_dataframe, median_dataframe, test, args):
    columns_to_print = TEST_CONFIG_COLUMNS + TEST_RESULT_COLUMNS
    if args.results:
        print(test)
        print(test_results_dataframe)
        divider = '\\' * 60 + ' MEDIAN ' + '\\' * 60
        print(divider)
        print(median_dataframe)

        
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

        reset_workdir()
        save_test_cases_config_to_log_file()
        run_tests(test)
        process_tcp_probe_logs()
        get_test_results(test)
        calculate_goodput(test)
        calculate_jains_fairness_index(test)

        test_results_dataframe = create_dataframe_from_object(test)
        median_dataframe = do_statistics(test_results_dataframe)  
        print_all_results_to_cli(test_results_dataframe, median_dataframe, test, args)
        store_results(test_results_dataframe, median_dataframe, test, args)
    else:
        logging.info("Executing evaluation only")
        test_results_dataframe = pd.read_parquet('shared/test_results/test_results.parquet')
        median_dataframe = pd.read_parquet('shared/test_results/medians.parquet')
        print_all_results_to_cli(test_results_dataframe, median_dataframe, None, args)
    
    evaluate_test_results(test_results_dataframe, median_dataframe, test)
    logging.info("All tasks are completed.")

if __name__ == "__main__":
    main()
