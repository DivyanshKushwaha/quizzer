import logging
import os
import sys
import uuid
from pythonjsonlogger import jsonlogger

LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "logs", "app.log")


class FeatureFilter(logging.Filter):
    def __init__(self, feature: str):
        super().__init__()
        self.feature = feature

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'feature'):
            record.feature = self.feature
        return True


def setup_logger(name: str = "Marketing Engineeer Logs", feature: str = "general") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

        # File handler (JSON formatted)
        file_handler = logging.FileHandler(LOG_FILE_PATH)
        file_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d '
            '%(feature)s %(process)d %(thread)d %(funcName)s %(module)s %(exc_info)s'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(FeatureFilter(feature))
        logger.addHandler(file_handler)

        # Console handler (human-readable format)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s | %(name)s | %(feature)s | %(message)s'
        )
        stream_handler.setFormatter(stream_formatter)
        stream_handler.addFilter(FeatureFilter(feature))
        logger.addHandler(stream_handler)

    return logger


def get_logger(name: str = __name__, feature: str = "general") -> logging.Logger:
    return setup_logger(name, feature)


logger = setup_logger()
