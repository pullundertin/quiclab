import os
import logging

LOG_PATH = os.getenv('LOG_PATH')


def log_config():
    # Configure logging
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
