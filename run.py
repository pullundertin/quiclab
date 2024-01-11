
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

import os
import pandas as pd





def evaluate_test_results(test_results_dataframe, median_dataframe, test):
    update_program_progress_bar('Evaluate Test Results')
    control_parameter = test.control_parameter
    if control_parameter is None:
        control_parameter = 'generic_heatmap'
    iterations = test.iterations
    show_histogram(test_results_dataframe, control_parameter)
    show_goodput_graph(test_results_dataframe, control_parameter)
    show_boxplot(test_results_dataframe, test)
    show_heatmaps(median_dataframe, control_parameter)
    if iterations > 2:
        do_anova(test_results_dataframe, control_parameter)


        
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
        get_system_info()
        run_tests(test)
        process_tcp_probe_logs()
        get_pcap_data(test)
        write_test_object_to_log(test)
        get_qlog_data(test)
        write_test_object_to_log(test)
        calculate_additional_metrics(test)

        test_results_dataframe = create_dataframe_from_object(test)
        median_dataframe = do_statistics(test_results_dataframe)  
        write_dataframes_to_csv(test_results_dataframe, 'test_results_dataframe')
        write_dataframes_to_csv(median_dataframe, 'median_dataframe')
    else:
        logging.info("Executing evaluation only")
        test_results_dataframe = pd.read_parquet('shared/test_results/test_results.parquet')
        median_dataframe = pd.read_parquet('shared/test_results/medians.parquet')
    
    evaluate_test_results(test_results_dataframe, median_dataframe, test)
    if args.store:
        rsync_permanent(args.store)
    logging.info("All tasks are completed.")




if __name__ == "__main__":
    main()
