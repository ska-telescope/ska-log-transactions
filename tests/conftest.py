"""
A module defining pytest fixtures for testing ska.logging.
"""
import logging

import pytest

from ska.logging import configure_logging


@pytest.fixture
def reset_logging():
    """Cleanup logging module's state after each test (at least try to)."""
    yield
    manager = logging.root.manager
    manager.disabled = logging.NOTSET
    for logger in list(manager.loggerDict.values()) + [logging.root]:
        if isinstance(logger, logging.Logger):
            logger.setLevel(logging.NOTSET)
            logger.propagate = True
            logger.disabled = False
            logger.filters.clear()
            handlers = logger.handlers.copy()
            for handler in handlers:
                # Copied from `logging.shutdown`.
                try:
                    handler.acquire()
                    handler.flush()
                    handler.close()
                except (OSError, ValueError):
                    pass
                finally:
                    handler.release()
                logger.removeHandler(handler)


class AppendHandler(logging.Handler):
    """Handler that keeps a history of the records and formatted log messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logs = []
        self.records = []

    def emit(self, record):
        self.records.append(record)
        self.logs.append(self.format(record))


"""Override configuration for recording loggers"""
RECORDER_OVERRIDES = {
    "handlers": {"recorder": {"()": AppendHandler, "formatter": "default"}},
    "root": {"handlers": ["console", "recorder"]},
}


@pytest.fixture
def default_logger():
    """Return user logger instance with default configuration."""
    configure_logging()
    yield logging.getLogger("ska.test.app")


@pytest.fixture
def recording_logger():
    """Return user logger, including a recording handler.

    The additional handler has the name "recorder".  It uses the default formatter,
    and stores all formatted output strings as a list in its `logs` attribute.
    It also keeps a list of the raw log records in its `records` attribute.

    Note:  we use this instead of pytest's `caplog` fixture because we cannot change
    the formatter that it uses.
    """
    configure_logging(overrides=RECORDER_OVERRIDES)
    yield logging.getLogger("ska.logger")


@pytest.fixture
def recording_tags_logger():
    """Return user logger like :func:`recording_logger`, but including tags filter."""

    class MyFilter(logging.Filter):
        def filter(self, record):
            record.tags = "key1:value1,key2:value2"
            return True

    configure_logging(tags_filter=MyFilter, overrides=RECORDER_OVERRIDES)
    yield logging.getLogger("ska.logger")


def get_first_record_and_log_message(logger):
    recorder = get_named_handler(logger, "recorder")
    record = recorder.records[0]
    log_message = recorder.logs[0]
    return record, log_message


def get_second_record_and_log_message(logger):
    recorder = get_named_handler(logger, "recorder")
    record = recorder.records[1]
    log_message = recorder.logs[1]
    return record, log_message

def get_last_record_and_log_message(logger):
    recorder = get_named_handler(logger, "recorder")
    record = recorder.records[-1]
    log_message = recorder.logs[-1]
    return record, log_message

def get_all_record_logs(logger):
    recorder = get_named_handler(logger, "recorder")
    return recorder.logs

def get_named_handler(logger, name):
    """Search up through logger hierarchy to find a handler with the specified name."""
    while logger:
        for handler in logger.handlers:
            if handler.name == name:
                return handler
        logger = logger.parent


@pytest.fixture
def id_generator_stub(mocker):
    """Replace the standard transactions.TransactionIdGenerator with a simple stub implementation."""

    class TransactionIdGeneratorStub:
        last_id = "NOT SET"
        call_count = 0

        def next(self):
            TransactionIdGeneratorStub.last_id = "XYZ-789"
            TransactionIdGeneratorStub.call_count += 1
            return TransactionIdGeneratorStub.last_id

    mocker.patch('ska.log_transactions.transactions.TransactionIdGenerator', TransactionIdGeneratorStub)
    yield TransactionIdGeneratorStub
