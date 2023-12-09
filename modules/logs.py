import os
import logging

OUTPUT = "./shared/logs/output.log"


def log_config():
    # clear logs
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)
    # Configure logging
    logging.basicConfig(filename=OUTPUT, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
