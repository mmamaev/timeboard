from ..exceptions import OutOfBoundsError
from ..core import get_timestamp
from ..timeboard import Timeboard


class CalendarBase(object):

    @classmethod
    def amendments(cls, start=None, end=None, custom_amendments=None):
        if custom_amendments is None:
            custom_amendments = {}
        return custom_amendments

    @classmethod
    def parameters(cls):
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2001'),
            'end': get_timestamp('31 Dec 2030'),
            'layout': [1]
        }

    @classmethod
    def _check_time(cls, t):
        if not cls.parameters()['start'] <= t <= cls.parameters()['end']:
            raise OutOfBoundsError("Point in time '{}' is outside calendar {}"
                                   .format(t, cls))

    def __new__(cls, custom_start=None, custom_end=None,
                custom_amendments=None):
        parameters = cls.parameters()
        if custom_start:
            cls._check_time(custom_start)
            parameters['start'] = custom_start
        if custom_end:
            cls._check_time(custom_end)
            parameters['end'] = custom_end
        amendments = cls.amendments(start=parameters['start'],
                                    end=parameters['end'],
                                    custom_amendments=custom_amendments)

        return Timeboard(amendments=amendments, **parameters)
