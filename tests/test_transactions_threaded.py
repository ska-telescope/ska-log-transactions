"""Tests for the logging transactions module focusing on threads"""
import pytest

from threading import Thread
from collections import Counter

from ska.log_transactions import transaction
from tests.conftest import get_all_record_logs, clear_logger_logs


class ThreadingLogsGenerator:
    """Generate logs by spawning a number of threads and logging in them
    Some uses the transaction context and some not.
    """

    def __init__(self, logger=None, pass_logger=False):
        self.logger = logger
        self.pass_logger = pass_logger

    def thread_with_transaction_exception(self, thread_index):
        logger = self.logger if self.pass_logger else None
        try:
            with transaction(f"Transaction thread [{thread_index}]", logger=logger):
                self.logger.info(
                    f"Transaction thread in transaction [{thread_index}], in transaction"
                )
                raise RuntimeError("An exception has occurred")
        except RuntimeError:
            pass

    def thread_with_transaction(self, thread_index):
        logger = self.logger if self.pass_logger else None
        with transaction(f"Transaction thread [{thread_index}]", logger=logger):
            self.logger.info(f"Transaction thread [{thread_index}], in transaction")
        self.logger.info(f"Thread log [{thread_index}], no transaction")


    def thread_without_transaction(self, thread_index):
        self.logger.info(f"Thread log [{thread_index}], no transaction")

    def get_logs(self):
        clear_logger_logs(self.logger)
        test_threads = []
        for thread_index in range(10):
            thread_in_transaction = Thread(
                target=self.thread_with_transaction, args=(thread_index,)
            )
            thread_no_transaction = Thread(
                target=self.thread_without_transaction, args=(thread_index,)
            )
            thread_exception = Thread(
                target=self.thread_with_transaction_exception, args=(thread_index,)
            )
            test_threads.append(thread_in_transaction)
            test_threads.append(thread_no_transaction)
            test_threads.append(thread_exception)

        for t in test_threads:
            t.start()
        for t in test_threads:
            t.join()

        return get_all_record_logs(self.logger)


@pytest.fixture
def threaded_logs_local_logger(recording_tags_logger):
    tlg = ThreadingLogsGenerator(logger=recording_tags_logger, pass_logger=True)
    return tlg.get_logs()


@pytest.fixture
def threaded_logs_global_logger(recording_tags_logger):
    tlg = ThreadingLogsGenerator(logger=recording_tags_logger, pass_logger=False)
    return tlg.get_logs()


class TestThreadScenarios:
    def test_logs_outside_transaction_has_no_transaction_ids(
        self, threaded_logs_global_logger, threaded_logs_local_logger
    ):
        all_logs = threaded_logs_global_logger + threaded_logs_local_logger
        outside_transaction_logs = [log for log in all_logs if "no transaction" in log]
        assert outside_transaction_logs
        for log in outside_transaction_logs:
            assert "Transaction[" not in log, f"transaction_id should not be in log {log}"

    def test_internal_log_has_no_transaction_id(self, threaded_logs_global_logger):
        all_logs = threaded_logs_global_logger
        internal_logs = [log for log in all_logs if "in transaction" in log]
        assert internal_logs
        for log in internal_logs:
            assert "Transaction[" not in log

    def test_enter_exit_exception_matches(
        self, threaded_logs_global_logger, threaded_logs_local_logger
    ):
        all_logs = threaded_logs_global_logger + threaded_logs_local_logger
        enter_exit_logs = []
        enter_exit_logs += [log for log in all_logs if "Enter[" in log]
        enter_exit_logs += [log for log in all_logs if "Exit[" in log]
        assert enter_exit_logs
        assert len(enter_exit_logs) % 2 == 0

        transaction_id_marker = []
        for log in enter_exit_logs:
            transaction_id_marker.append(
                (get_marker_in_message(log), get_transaction_id_in_message(log))
            )
        # Group enter exit by (transaction_id, marker)
        # Make sure there is only 2 of each
        counter = dict(Counter(transaction_id_marker))
        for items, count in counter.items():
            assert count == 2, f"Found {count} of {items} instead of 2"

        # Make sure there's a enter/exit for every exception
        exception_logs = [log for log in all_logs if "RuntimeError" in log]
        assert exception_logs
        for log in exception_logs:
            assert (
                get_marker_in_message(log),
                get_transaction_id_in_message(log),
            ) in transaction_id_marker

def get_transaction_id_in_message(log_message):
    if "Transaction[" in log_message:
        transaction_index = log_message.index("Transaction[")
        return log_message[transaction_index + 12 : transaction_index + 40]
    return None


def get_marker_in_message(log_message):
    if "marker[" in log_message:
        marker_index = log_message.index("marker[")
        return log_message[marker_index + 7 : marker_index + 12]
    return None