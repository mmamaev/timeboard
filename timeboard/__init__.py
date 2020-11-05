"""
timeboard performs calendar calculations over business schedules 
such as business days or work shifts.

See http://timeboard.readthedocs.io
"""
from .timeboard import Timeboard
from .core import Organizer, Marker, RememberingPattern
from .interval import Interval
from .workshift import Workshift
from .exceptions import (OutOfBoundsError,
                         PartialOutOfBoundsError,
                         VoidIntervalError,
                         UnacceptablePeriodError)

import os

PKG_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def read_from(path):
    """
    Read the contents of a file.

    Args:
        path: (str): write your description
    """
    with open(os.path.join(PKG_ROOT_DIR, path)) as f:
        return f.read().strip()

__version__ = read_from('VERSION.txt')