# -*- coding: utf-8 -*-

"""Tests for the logging transactions module."""
import json
import os

import pytest
import concurrent.futures

from unittest.mock import patch, MagicMock

from ska.log_transactions import transaction
from ska.log_transactions.transactions import TransactionIdGenerator, TransactionParamsError
from tests.conftest import (
    get_first_record_and_log_message,
    get_last_record_and_log_message,
    get_all_record_logs,
    get_second_record_and_log_message,
)


class TestTransactionIdGeneration:
    """Tests for :class:`~ska.logging.transaction` related to ID generation."""

    def test_error_if_params_type_is_not_mapping(self):
        parameters = []
        with pytest.raises(TransactionParamsError):
            with transaction("name", parameters):
                pass

    parameters = {"other": "config", "transaction_id": "xyz123", "other_transaction_id_key": "def789"}
    @pytest.mark.parametrize("input_args, txn_id", 
    [
        ({"name":"name", "params":parameters, "transaction_id":"abc1234"}, "abc1234"),
        ({"name":"name", "params":parameters, "transaction_id_key":"other_transaction_id_key"}, "def789"),
        ({"name":"name", "params":parameters, "transaction_id":"abc1234", "transaction_id_key":"other_transaction_id_key"}, "abc1234"),
    ])
    def test_preference_order(self, input_args, txn_id):
        with transaction(**input_args) as transaction_id:
            assert transaction_id == txn_id

    def test_new_id_generated_if_invalid_ids_passed_in_params(self, id_generator_stub):
        parameters = {
            "other": "config",
            "transaction_id": 54321,
        }
        with transaction("name", parameters, transaction_id=12345) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_new_id_generated_if_id_is_empty(self, id_generator_stub):
        parameters = {"transaction_id": "", "other": "config"}
        with transaction("name", parameters) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_new_id_generated_if_id_is_none(self, id_generator_stub):
        parameters = {"transaction_id": None, "other": "config"}
        with transaction("name", parameters) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_new_id_generated_if_id_is_only_white_space(self, id_generator_stub):
        parameters = {"transaction_id": "\t\n \r\n", "other": "config"}
        with transaction("name", parameters) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_new_id_generated_if_id_is_not_string_type(self, id_generator_stub):
        parameters = {"transaction_id": 1234.5, "other": "config"}
        with transaction("name", parameters) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_new_id_generated_if_id_is_not_present(self, id_generator_stub):
        parameters = {"other": "config"}
        with transaction("name", parameters) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_new_id_generated_if_params_empty(self, id_generator_stub):
        parameters = {}
        with transaction("name", parameters) as transaction_id:
            assert transaction_id == id_generator_stub.last_id

    def test_id_provider_only_used_once_for_one_new_id(self, id_generator_stub):
        parameters = {}
        with transaction("name", parameters):
            assert id_generator_stub.call_count == 1

    def test_id_provider_not_used_for_existing_valid_id(self, id_generator_stub):
        parameters = {"transaction_id": "abc1234"}
        with transaction("name", parameters):
            assert id_generator_stub.call_count == 0


class TestTransactionLogging:
    """Tests for :class:`~ska.logging.transaction` related to logging."""

    def test_name_and_id_and_params_in_context_handler(self, recording_logger):
        parameters = {"other": ["config", 1, 2, 3.0]}
        with transaction("name", parameters) as transaction_id:
            pass
        _, first_log_message = get_first_record_and_log_message(recording_logger)
        _, second_log_message = get_second_record_and_log_message(recording_logger)
        _, last_log_message = get_last_record_and_log_message(recording_logger)

        # __enter__ log message
        assert "Generated transaction ID" in first_log_message
        assert "Enter" in second_log_message
        assert "name" in second_log_message
        assert "other" in second_log_message
        assert transaction_id in second_log_message
        assert json.dumps(parameters) in second_log_message

        # __exit__ log message
        assert "Exit" in last_log_message
        assert "name" in last_log_message
        assert transaction_id in last_log_message

    def test_exception_logs_transaction_id_and_command(self, recording_logger):
        parameters = {"other": ["config", 1, 2, 3.0]}
        with pytest.raises(RuntimeError):
            with transaction("name", parameters) as transaction_id:
                raise RuntimeError("Something went wrong")

        record_logs = get_all_record_logs(recording_logger)
        for log_msg in record_logs:
            if "RuntimeError" in log_msg and transaction_id in log_msg and "name" in log_msg:
                return

        assert 0, f"RuntimeError and transaction tag not found in exception logs: {record_logs}"

    def test_specified_logger(self):
        logger = MagicMock()
        parameters = {}
        with transaction("name", parameters, logger=logger) as transaction_id:
            logger.info("A message")
        for i, message in enumerate(["Generated", "Enter", "A message", "Exit"]):
            assert logger.info.call_args_list[i].starts_with(message)
        assert logger.info.call_count == 4, f"Log calls incorrect {logger.info.call_args_list}"


class TestTransactionIdGenerator:
    """Tests for :class:`~ska.log_transactions.transactions.TransactionIdGenerator`."""

    def test_local_id_generator_increments_on_next(self, monkeypatch):
        monkeypatch.delenv("SKUID_URL", raising=False)
        generator = TransactionIdGenerator()

        assert generator.next()
        assert generator.next() != generator.next()

    def test_remote_id_generator_increments_on_next(self, monkeypatch):
        monkeypatch.setenv("SKUID_URL", "endpoint/to/skuid-client")

        with patch("ska.skuid.client.requests.get") as mocked_req:
            response = MagicMock()
            response.json.side_effect = [
                json.dumps({"transaction_id": 1}),
                json.dumps({"transaction_id": 2}),
                json.dumps({"transaction_id": 3}),
            ]
            mocked_req.return_value = response
            generator = TransactionIdGenerator()

            assert generator.next() == 1
            assert generator.next() == 2
            assert generator.next() == 3
