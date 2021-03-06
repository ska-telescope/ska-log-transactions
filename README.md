# SKA Transaction Logging utility

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-log-transactions/badge/?version=latest)](https://ska-telescope-ska-log-transactions.readthedocs.io/en/latest/?badge=latest)

## Logging Transaction IDs

A transaction context handler is available to inject ids fetched from the the skuid service into logs. The transaction id will be logged on entry and exit of the context handler. In the event of an exception, the transaction id will be logged with the exception stack trace. The ID generated depends on whether or not the SKUID_URL environment variable is set.

### Example

```python
from ska.log_transactions import transaction

def command(self, parameter_json):
    parameters = json.reads(parameter_json)
    with transaction('My Command', parameters) as transaction_id:
        # ...
        parameters['transaction_id'] = transaction_id
        device.further_command(json.dumps(parameters))
        # ...

```

### Asynchronous Example

```python
from ska.log_transactions import async_transaction

async def command(self, parameter_json):
    parameters = json.reads(parameter_json)
    async with async_transaction('My Command', parameters) as transaction_id:
        # ...
        parameters['transaction_id'] = transaction_id
        await device.further_command(json.dumps(parameters))
        # ...

```

### Custom logger example

By default the context handler logs to the `ska.transaction` logger with default formatting.
A custom logger can be used by passing it in via an optional argument.

```python
import logging
from ska.log_transactions import transaction

custom_logger = logging.getLogger(__name__)

def command(self, parameter_json):
    parameters = json.reads(parameter_json)
    with transaction('My Command', parameters, logger=custom_logger) as transaction_id:
        # ...
        parameters['transaction_id'] = transaction_id
        device.further_command(json.dumps(parameters))
        # ...

```

### Log messages

Log message formats:

- On Entry:
  - Transaction[id]: Enter[name] with parameters [arguments] marker[marker]
- On Exit:
  - Transaction[id]: Exit[name] marker[marker]
- On exception:
  - Transaction[id]: Exception[name] marker[marker]
    -- Stacktrace --

The marker can be used to match entry/exception/exit log messages.

#### Example ska formatted logs for successful transaction

```

1|2020-10-01T12:49:31.119Z|INFO|Thread-210|log_entry|transactions.py#154||Transaction[txn-local-20201001-981667980]: Enter[Command] with parameters [{}] marker[52764]
1|2020-10-01T12:49:31.129Z|INFO|Thread-210|log_exit|transactions.py#154||Transaction[txn-local-20201001-981667980]: Exit[Command] marker[52764]
```

#### Example ska formatted logs for failed transaction

```
1|2020-10-01T12:51:35.588Z|INFO|Thread-204|log_entry|transactions.py#154||Transaction[txn-local-20201001-354400050]: Enter[Transaction thread [7]] with parameters [{}] marker[21454]
1|2020-10-01T12:51:35.598Z|ERROR|Thread-204|log_exit|transactions.py#149||Transaction[txn-local-20201001-354400050]: Exception[Transaction thread [7]] marker[21454]
Traceback (most recent call last):
  File "python_file.py", line 27, in thread_with_transaction_exception
    raise RuntimeError("An exception has occurred")
RuntimeError: An exception has occurred
1|2020-10-01T12:51:35.601Z|INFO|Thread-204|log_exit|transactions.py#154||Transaction[txn-local-20201001-354400050]: Exit[Transaction thread [7]] marker[21454]
```

## Requirements

The system used for development needs to have Python 3 and `pip` installed.

## Install

### From source

- Clone the repo

```bash
git clone git@gitlab.com:ska-telescope/ska-log-transactions.git
```

- Install requirements

```bash
 python3 -m pip install -r requirements.txt --extra-index-url https://nexus.engageska-portugal.pt/repository/pypi/simple
```

- Install the package

```bash
 python3 -m pip install .
```

### From the Nexus PyPI

```bash
 python3 -m pip install ska-log-transactions --extra-index-url https://nexus.engageska-portugal.pt/repository/pypi/simple
```

## Testing

- Install the test requirements

```bash
 python3 -m pip install -r requirements-test.txt
```

- Run the tests

```bash
tox
```

- Lint

```bash
tox -e lint
```

## Writing documentation

The documentation generator for this project is derived from SKA's [SKA Developer Portal repository](https://github.com/
ska-telescope/developer.skatelescope.org)

The documentation can be edited under `./docs/src`

### Build the documentation

- Install the test requirements

```bash
 python3 -m pip install -r requirements-test.txt
```

- Build docs

 ```bash
tox -e docs
```

The documentation can then be consulted by opening the file `./docs/build/html/index.html`
