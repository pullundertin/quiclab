
import logging
from modules.pcap_processing import convert_pcap_to_json, get_statistics
from modules.commands import rsync, rsync_permanent
from modules.logs import log_config
from modules.prerequisites import reset_workdir
from modules.heatmap import show_heatmaps
from modules.boxplot import show_boxplot
from modules.tests import run_tests
import os
import argparse


def arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('--full', action='store_true',
                        help='run full execution')
    parser.add_argument('--store', type=str,
                        help='directory for permanent storage')

    args = parser.parse_args()

    return args



def evaluate_test_results():
    convert_pcap_to_json()
    statistics, medians = get_statistics()
    statistics.to_csv('shared/statistics/statistics.csv', index=False)
    medians.to_csv('shared/statistics/medians.csv', index=False)
    show_boxplot(statistics)
    show_heatmaps(medians)

def store_results(args):
    if args.store:
        rsync()
        rsync_permanent(args.store)
    else:
        rsync()

if __name__ == "__main__":
    log_config()
    args = arguments()

    if args.full:
        logging.info(f"{os.getenv('HOST')}: full execution enabled")

        reset_workdir()
        run_tests()
 
    else:
        logging.info("Executing evaluation only")


    evaluate_test_results()
    store_results(args)

    logging.info("All tasks are completed.")

