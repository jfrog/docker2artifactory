import logging
import sys

def start_logging():
    level = logging.INFO
    fmt = "%(asctime)s [%(threadName)s] [%(levelname)s]"
    fmt += " (%(name)s:%(lineno)d) - %(message)s"
    formatter = logging.Formatter(fmt)
    logger = logging.getLogger()
    if not len(logger.handlers):
        logger.setLevel(level)
        stdouth = logging.StreamHandler(sys.stdout)
        stdouth.setFormatter(formatter)
        logger.addHandler(stdouth)
    msg = "\n\nDocker Migration Tool - Functional Tests\n\n"
    logger.info('\n' + '='*60 + msg + '='*60 + '\n')
