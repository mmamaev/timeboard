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
                         VoidIntervalError,
                         UnsupportedPeriodError)

__version__ = "0.0"