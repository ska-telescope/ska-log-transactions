"""Tests for the logging transactions module focusing on threads"""
from threading import Thread

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
