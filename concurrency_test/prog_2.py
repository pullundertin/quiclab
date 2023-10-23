import time
import logging


# Configure logging
logging.basicConfig(filename='test.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info('prog_2 started.')
time.sleep(10)
logging.info('prog_2 stopped.')