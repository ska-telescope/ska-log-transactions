# -*- coding: utf-8 -*-

"""Module init code."""

__all__ = ("transaction", "async_transaction")
__author__ = "Anton Joubert"
__email__ = "ajoubert+ska@ska.ac.za"


from .transactions import Transaction as transaction, AsyncTransaction as async_transaction


# BEGIN VERSION CHECK
# Get package version when locally imported from repo or via -e develop install
try:
    import katversion as _katversion
except ImportError:  # pragma: no cover
    import time as _time

    __version__ = "0.0+unknown.{}".format(_time.strftime("%Y%m%d%H%M"))
else:  # pragma: no cover
    __version__ = _katversion.get_version(__path__[0])
# END VERSION CHECK
