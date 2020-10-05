"""Tests for the logging transactions module focusing on threads"""
import asyncio

from ska.log_transactions import async_transaction
from tests.conftest import get_all_record_logs, clear_logger_logs


class AsyncLogsGenerator:
    """Generate logs by spawning a number of threads and logging in them
    Some uses the transaction context and some not.
    """

    def __init__(self, logger=None, pass_logger=False):
        self.logger = logger
        self.pass_logger = pass_logger

    async def async_with_transaction_exception(self, thread_index):
        logger = self.logger if self.pass_logger else None
        try:
            async with async_transaction(f"Transaction thread [{thread_index}]", logger=logger):
                self.logger.info(
                    f"Transaction thread in transaction [{thread_index}], in transaction"
                )
                raise RuntimeError("An exception has occurred")
        except RuntimeError:
            pass

    async def async_with_transaction(self, thread_index):
        logger = self.logger if self.pass_logger else None
        async with async_transaction(f"Transaction thread [{thread_index}]", logger=logger):
            self.logger.info(f"Transaction thread [{thread_index}], in transaction")
        self.logger.info(f"Thread log [{thread_index}], no transaction")

    async def async_without_transaction(self, thread_index):
        self.logger.info(f"Thread log [{thread_index}], no transaction")

    async def run_all_transactions(self):
        coros = []
        for coro_index in range(10):
            coros.append(self.async_with_transaction_exception(coro_index))
            coros.append(self.async_with_transaction(coro_index))
            coros.append(self.async_without_transaction(coro_index))
        await asyncio.gather(*coros)

    def get_logs(self):
        clear_logger_logs(self.logger)
        asyncio.run(self.run_all_transactions())
        return get_all_record_logs(self.logger)
