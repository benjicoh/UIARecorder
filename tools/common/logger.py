import sys
import os
import logging
import colorlog

class IndentFormatter(logging.Formatter):
    def __init__(self, fmt=None, indent_char=' ', indent_level=0):
        super().__init__(fmt)
        self.indent_char = indent_char
        self.indent_level = indent_level

    def format(self, record):
        indentation = self.indent_char * self.indent_level
        record.msg = indentation + str(record.msg)
        return super().format(record)

class IndentAndColorFormatter(colorlog.ColoredFormatter):
    def __init__(self, *args, indent_char=' ', indent_level=0, **kwargs):
        super().__init__(*args, **kwargs)
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

    # Console handler with color and indentation
    ch = colorlog.StreamHandler(sys.stdout)
    console_formatter = IndentAndColorFormatter(
        '%(asctime)s - %(filename)s:%(lineno)d - %(log_color)s%(levelname)s%(reset)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%',
        indent_level=indent_level
    )
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)

    # File handler with indentation but no color
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        fh = logging.FileHandler(log_file)
        file_formatter = IndentFormatter(
            '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
            indent_level=indent_level
        )
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

    return logger
