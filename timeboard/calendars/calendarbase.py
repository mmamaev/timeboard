from ..exceptions import OutOfBoundsError
from ..core import get_timestamp
from ..timeboard import Timeboard


class CalendarBase(object):

    @classmethod
    def parameters(cls):
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2001'),
            'end': get_timestamp('31 Dec 2030'),
            'layout': [1]
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None, **kwargs):
        if custom_amendments is None:
            custom_amendments = {}
        return custom_amendments

    @classmethod
    def _check_time(cls, t):
        if not cls.parameters()['start'] <= t <= cls.parameters()['end']:
            raise OutOfBoundsError("Point in time '{}' is outside calendar {}"
                                   .format(t, cls))

    @classmethod
    def _get_bounds(cls, custom_start=None, custom_end=None):
        if custom_start is None:
            start = get_timestamp(cls.parameters()['start'])
        else:
            start = get_timestamp(custom_start)
            cls._check_time(start)
        if custom_end is None:
            end = get_timestamp(cls.parameters()['end'])
        else:
            end = get_timestamp(custom_end)
            cls._check_time(end)
        return start, end

    def __new__(cls, custom_start=None, custom_end=None,
                custom_amendments=None, **kwargs):
        parameters = cls.parameters()
        parameters['start'], parameters['end'] = cls._get_bounds(
            custom_start, custom_end)
        amendments = cls.amendments(custom_start=parameters['start'],
                                    custom_end=parameters['end'],
                                    custom_amendments=custom_amendments,
                                    **kwargs)

        return Timeboard(amendments=amendments, **parameters)
