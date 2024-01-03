import os
import logging
from modules.prerequisites import read_configuration

LOG_PATH = read_configuration().get("LOG_PATH")


def log_config(args):
    if args.full:
        # clear logs
        if os.path.exists(LOG_PATH):
            os.remove(LOG_PATH)
    # Configure logging
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
