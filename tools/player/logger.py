import logging
import sys
import os

class IndentFormatter(logging.Formatter):
    def __init__(self, fmt=None, indent_char=' ', indent_level=0):
        super().__init__(fmt)
        self.indent_char = indent_char
        self.indent_level = indent_level

    def format(self, record):
        indentation = self.indent_char * self.indent_level
        record.msg = indentation + str(record.msg)
        return super().format(record)

def get_logger(name, level=logging.INFO, log_file=None, indent_level=0):
    """
    Initializes and returns a logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = IndentFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', indent_level=indent_level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
