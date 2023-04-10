import datetime
import logging
import random
import time
from sys import stdout

logger = logging.getLogger("mylogger")
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(stdout)
logger.addHandler(consoleHandler)

iterations = 0
while True:
    time.sleep(1)
    logger.debug(f"from docker {datetime.datetime.now()}")
    error = random.randint(1, 10)
    if error > 3:
        logger.error("Error")
    if iterations >= 20:
        break
    iterations += 1
