# -*- coding: utf-8 -*-

"""This module provides the transaction logging mechanism."""
import json
import logging
import os

from random import randint
from typing import Mapping, Optional, Text

from ska.skuid.client import SkuidClient


class TransactionBase:
    """Transaction context handler.

    Provides:
    - Transaction ID:
      - Re-use existing transaction ID, if available
      - If no transaction ID, or empty or None, then generate a new ID
      - context handler returns the transaction ID used
    - Log messages on entry, exit, and exception

    .. Examples::

       def command(self, parameter_json):
           parameters = json.reads(parameter_json)
           with transaction('My Command', parameters) as transaction_id:
               # ...
               parameters['transaction_id'] = transaction_id
               device.further_command(json.dumps(pars))
               # ...

       def command(self, parameter_json):
           parameters = json.reads(parameter_json)
           with transaction('My Command', parameters, transaction_id="123") as transaction_id:
               # ...
               parameters['transaction_id'] = transaction_id
               device.further_command(json.dumps(pars))
               # ...

       def command(self, parameter_json):
           parameters = json.reads(parameter_json)
           parameters["txn_id_key"] = 123
           with transaction('My Command', parameters, transaction_id_key="txn_id_key")
               as transaction_id:
               # ...
               parameters['transaction_id'] = transaction_id
               device.further_command(json.dumps(pars))
               # ...

    Log message formats:
       On Entry:
           Transaction[id]: Enter[name] with parameters [arguments] marker[marker]
       On Exit:
           Transaction[id]: Exit[name] marker[marker]
       On exception:
           Transaction[id]: Exception[name] marker[marker]
           Stacktrace
    """

    def __init__(
        self,
        name: str,
        params: dict = {},
        transaction_id: str = "",
        transaction_id_key: str = "transaction_id",
        logger: Optional[logging.Logger] = None,  # pylint: disable=E1101
    ):
        """Create the transaction context handler.

        A new transaction ID is generated if none is passed in via `transaction_id` or
        in `params`.

        If there is a transaction ID in `params` and `transaction_id` is also passed in
        then the passed in `transaction_id` will take precedence.

        However, if both transaction IDs provided in `params` and `transaction_id` are deemed
        invalid (not a string or an empty string), then a new transaction ID will be generated.

        By default the key `transaction_id` will be used to get a transaction ID out of
        `params`. If a different key is required then `transaction_id_key` can be
        specified.

        Parameters
        ----------
        name : str
            A description for the context. This is usually the Tango device command.
        params : dict, optional
            The parameters will be logged and will be used to retrieve the transaction
            ID if `transaction_id` is not passed in, by default {}
        transaction_id : str, optional
            The transaction ID to be used for the context, by default ""
        transaction_id_key : str, optional
            The key to use to get the transaction ID from params,
            by default "transaction_id"
        logger : logging.Logger, optional
            The logger to use for logging, by default None.
            If no logger is specified a new one named `ska.transaction` will be used.

        Raises
        ------
        TransactionParamsError
            If the `params` passed is not valid.
        """
        if not isinstance(params, Mapping):
            raise TransactionParamsError("params must be dict-like (Mapping)")

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("ska.transaction")  # pylint: disable=E1101
        self._name = name
        self._params = params
        self._transaction_id_key = transaction_id_key

        self._transaction_id = self._get_id_from_params_or_generate_new_id(transaction_id)

        # Used to match enter and exit when multiple devices calls the same command
        # on a shared device simultaneously
        self._random_marker = str(randint(0, 99999)).zfill(5)

        if transaction_id and params.get(self._transaction_id_key):
            self.logger.info(
                f"Received 2 transaction IDs {transaction_id} and"
                f" {params.get(transaction_id_key)}, using {self._transaction_id}"
            )

    def log_entry(self):
        """Log the entry message
        """
        params_json = json.dumps(self._params)
        self.logger.info(
            f"Transaction[{self._transaction_id}]: Enter[{self._name}] "
            f"with parameters [{params_json}] "
            f"marker[{self._random_marker}]"
        )

    def log_exit(self, exc_type):
        """Log the exit message and exception if it occurs

        Parameters
        ----------
        exc_type : exception_type
            The exception type
        """
        if exc_type:
            self.logger.exception(
                f"Transaction[{self._transaction_id}]: Exception[{self._name}] "
                f"marker[{self._random_marker}]"
            )

        self.logger.info(
            f"Transaction[{self._transaction_id}]: Exit[{self._name}] "
            f"marker[{self._random_marker}]"
        )

        if exc_type:
            raise  # pylint: disable=E0704

    def _get_id_from_params_or_generate_new_id(self, transaction_id):
        """At first use the transaction_id passed or use the transaction_id_key to get the
        transaction ID from the parameters or generate a new one if it's not there.

        Parameters
        ----------
        transaction_id : [String]
            [The transaction ID]

        Returns
        -------
        [String]
            [transaction ID]
        """
        _transaction_id = (
            transaction_id if transaction_id else self._params.get(self._transaction_id_key)
        )
        if not self._is_valid_id(_transaction_id):
            _transaction_id = self._generate_new_id()
            self.logger.info(f"Generated transaction ID {_transaction_id}")
        return _transaction_id

    def _is_valid_id(self, transaction_id):
        """Check if the ID is valid

        Parameters
        ----------
        transaction_id : [String]
            [The transaction ID]

        Returns
        -------
        [bool]
            [Whether the ID is valid or not]
        """
        if isinstance(transaction_id, Text) and transaction_id.strip():
            return True
        return False

    def _generate_new_id(self):
        """Use TransactionIdGenerator to generate a new transaction ID

        Returns
        -------
        [String]
            [The newly generated transaction ID]
        """
        id_generator = TransactionIdGenerator()
        return id_generator.next()  # pylint: disable=E1102


class Transaction(TransactionBase):
    def __enter__(self):
        """Context handler entry

        Returns
        -------
        String
            The transaction ID
        """
        self.log_entry()
        return self._transaction_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context handler exit

        Parameters
        ----------
        exc_type : exception_type
            The exception type
        exc_val : exception_value
            The exception value
        exc_tb : exception_traceback
            The exception traceback
        """
        self.log_exit(exc_type)


class AsyncTransaction(TransactionBase):
    async def __aenter__(self):
        """Asynchronous context handler entry

        Returns
        -------
        String
            The transaction ID
        """
        self.log_entry()
        return self._transaction_id

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context handler exit

        Parameters
        ----------
        exc_type : exception_type
            The exception type
        exc_val : exception_value
            The exception value
        exc_tb : exception_traceback
            The exception traceback
        """
        self.log_exit(exc_type)


class TransactionIdGenerator:
    """
    TransactionIdGenerator retrieves a transaction id from skuid.
    Skuid may fetch the id from the service if the SKUID_URL is set or
    alternatively generate one.
    """

    def __init__(self):
        if os.environ.get("SKUID_URL"):
            client = SkuidClient(os.environ["SKUID_URL"])
            self._get_id = client.fetch_transaction_id
        else:
            self._get_id = SkuidClient.get_local_transaction_id

    def next(self):
        return self._get_id()


class TransactionParamsError(TypeError):
    """Invalid data type for transaction parameters."""
