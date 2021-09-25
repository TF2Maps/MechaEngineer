# Std lib imports
from copy import copy
from logging import Formatter
import logging
import sys


def setup_logger(level):
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        "%(levelname)s \u001b[1;30m%(name)s.%(funcName)s:%(lineno)s \u001b[0m'%(message)s'"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("asyncssh").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("databases").setLevel(logging.WARNING)

    log = logging.getLogger('')
    log.setLevel(level)
    log.addHandler(console_handler)


class ColoredFormatter(Formatter):
    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def format(self, record):
        MAPPING = {
            'DEBUG': 36,
            'INFO': 32,
            'WARNING': 33,
            'ERROR': 31,
            'CRITICAL': 41,
        }

        PREFIX = '\033[1;'
        SUFFIX = '\033[0m'

        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = MAPPING.get(levelname, 37)

        colored_levelname = (f'{PREFIX}{seq}m{levelname}{SUFFIX}')
        colored_record.levelname = colored_levelname

        return Formatter.format(self, colored_record)