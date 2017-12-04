from .calendarbase import CalendarBase, nth_weekday_of_month, extend_weekends
from ..core import get_timestamp, get_period
from ..timeboard import Organizer
from itertools import product


def fed_holidays(start_year, end_year, exclusions=None, long_weekends=True,
                 label=0):

    fed_holidays_fixed = {'new_year': '01 Jan',
                          'independence': '04 Jul',
                          'veterans': '11 Nov',
                          'christmas': '25 Dec'}

    fed_holidays_floating = {
        'mlk': (1, 1, 3),
        'presidents': (2, 1, 3),
        'memorial': (5, 1, -1),
        'labor': (9, 1, 1),
        'columbus': (10, 1, 2),
        'thanksgiving': (11, 4, 4),
        'black_friday': (11, 4, 4, 1)
    }

    if exclusions is None:
        exclusions = []
    years = range(start_year, end_year + 1)
    days = [day for holiday, day in fed_holidays_fixed.items()
            if holiday not in exclusions]

    amendments = {"{} {}".format(day, year): 0
                  for day, year in product(days, years)}
    if long_weekends:
        amendments = extend_weekends(amendments, add='nearest')

    floating_dates_to_seek = [date_tuple for holiday, date_tuple
                              in fed_holidays_floating.items()
                              if holiday not in exclusions]
    for year in years:
        amendments.update(
            nth_weekday_of_month(year, floating_dates_to_seek, label))

    return amendments

class Week8x5(CalendarBase):

    @classmethod
    def parameters(cls):
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2000'),
            'end': get_timestamp('31 Dec 2020'),
            'layout': Organizer(split_by='W', structure=[[8, 8, 8, 8, 8, 0, 0]])
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None,
                   exclusions=None, long_weekends=True,):

        start, end = cls._get_bounds(custom_start, custom_end)

        result = fed_holidays(start.year, end.year, exclusions, long_weekends)
        if custom_amendments is not None:
            freq = cls.parameters()['base_unit_freq']
            result.update(
                {get_period(k, freq=freq).start_time: v
                 for k, v in custom_amendments.items()}
            )

        return result
