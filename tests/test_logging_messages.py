import pytest

from collections import Counter

from .transactions_threaded import ThreadingLogsGenerator
from .transactions_async import AsyncLogsGenerator


@pytest.fixture
def async_logs_local_logger(request, recording_tags_logger):
    tlg = AsyncLogsGenerator(logger=recording_tags_logger, pass_logger=True)
    return tlg.get_logs()


@pytest.fixture
def async_logs_global_logger(request, recording_tags_logger):
    tlg = AsyncLogsGenerator(logger=recording_tags_logger, pass_logger=False)
    return tlg.get_logs()


@pytest.fixture
def threaded_logs_local_logger(request, recording_tags_logger):
    tlg = ThreadingLogsGenerator(logger=recording_tags_logger, pass_logger=True)
    return tlg.get_logs()


@pytest.fixture
def threaded_logs_global_logger(request, recording_tags_logger):
    tlg = ThreadingLogsGenerator(logger=recording_tags_logger, pass_logger=False)
    return tlg.get_logs()


class TestTransactionScenarios:
    def test_async_transaction_logs(self, async_logs_global_logger, async_logs_local_logger):
        all_logs = async_logs_global_logger + async_logs_local_logger
        self.check_logs_outside_transaction_has_no_transaction_ids(all_logs)
        self.check_internal_log_has_no_transaction_id(all_logs)
        self.check_enter_exit_exception_matches(all_logs)

    def test_transaction_logs(self, threaded_logs_global_logger, threaded_logs_local_logger):
        all_logs = threaded_logs_global_logger + threaded_logs_local_logger
        self.check_logs_outside_transaction_has_no_transaction_ids(all_logs)
        self.check_internal_log_has_no_transaction_id(all_logs)
        self.check_enter_exit_exception_matches(all_logs)

    def check_logs_outside_transaction_has_no_transaction_ids(self, all_logs):
        outside_transaction_logs = [log for log in all_logs if "no transaction" in log]
        assert outside_transaction_logs
        for log in outside_transaction_logs:
            assert "Transaction[" not in log, f"transaction_id should not be in log {log}"

    def check_internal_log_has_no_transaction_id(self, all_logs):
        internal_logs = [log for log in all_logs if "in transaction" in log]
        assert internal_logs
        for log in internal_logs:
            assert "Transaction[" not in log

    def check_enter_exit_exception_matches(self, all_logs):
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
        return log_message[transaction_index + 12:transaction_index + 40]
    return None


def get_marker_in_message(log_message):
    if "marker[" in log_message:
        marker_index = log_message.index("marker[")
        return log_message[marker_index + 7:marker_index + 12]
    return None
