
import logging
import os
from modules.commands import rsync_permanent
from modules.logs import log_config
from modules.prerequisites import get_test_object, arguments, check_if_folders_for_results_exist, delete_old_test_results
from modules.program_steps import generate_new_data, extract_data, read_data, evaluate_data, visualize_data
from modules.statistics import do_statistics

def main():

    test_results_dataframe = None
    median_dataframe = None

    args = arguments()
    print(args)
    log_config(args)

    test = get_test_object(args)
    check_if_folders_for_results_exist()
    delete_old_test_results()

    if args.test:
        logging.info(f"{os.getenv('HOST')}: full execution enabled")
        generate_new_data(test)
    if args.extract:
        logging.info("Executing without running tests")
        extract_data(test)
    else:
        logging.info("Reading data from files")
        test_results_dataframe, median_dataframe = read_data()

    # do_statistics(test_results_dataframe, test)
    if args.evaluate:
        evaluate_data(test_results_dataframe, test)
    if args.viz:
        visualize_data(test_results_dataframe, median_dataframe, test)
    if args.store:
        rsync_permanent(args.store)
    logging.info("All tasks are completed.")


if __name__ == "__main__":
    main()
