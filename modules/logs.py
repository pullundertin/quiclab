import os
import logging
from modules.prerequisites import read_configuration

OUTPUT_PATH = read_configuration().get("OUTPUT_PATH")


def log_config():
    # clear logs
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)
    # Configure logging
    logging.basicConfig(filename=OUTPUT_PATH, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
