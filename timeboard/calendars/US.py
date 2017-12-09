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
        exclusions = set()
    else:
        exclusions = set(exclusions)
    years = range(start_year, end_year + 1)
    days = [day for holiday, day in fed_holidays_fixed.items()
            if holiday not in exclusions]

    amendments = {"{} {}".format(day, year): label
                  for day, year in product(days, years)}
    if long_weekends:
        amendments = extend_weekends(amendments, how='nearest')

    floating_dates_to_seek = [date_tuple for holiday, date_tuple
                              in fed_holidays_floating.items()
                              if holiday not in exclusions]
    for year in years:
        amendments.update(
            nth_weekday_of_month(year, floating_dates_to_seek, label))

    return amendments

class Weekly8x5(CalendarBase):
    """United States business calendar for 5 days x 8 hours working week.

        The calendar takes into account the federal holidays. The Black 
        Friday is also considered a holiday. Selected holidays can
        be ignored by adding them to `exclusions`.
        
        Workshifts are calendar days. Workshift labels are number of working 
        hours per day: 0 for days off, 8 for  business days.

        Parameters
        ----------
        custom_start : Timestamp-like, optional
            Point in time referring to the first base unit of the calendar; must 
            be within the calendar span set by `parameters`. By default the 
            calendar starts with the base unit referred to by 'start' element of 
            `Weekly8x5.parameters()`.
        custom_end : Timestamp-like, optional
            Point in time referring to the last base unit of the calendar; must 
            be within the calendar span set by `parameters`. By default the 
            calendar ends with the base unit referred to by 'end' element of 
            `Weekly8x5.parameters()`.
        do_not_amend : bool, optional (default False)
            If set to True, the calendar is created without any amendments.
        only_custom_amendments : bool, optional (default False)
            If set to True, only amendments from `custom_amendments` are applied 
            to the calendar.
        custom_amendments : dict-like
            The alternative amendments if `only_custom_amendments` is true. 
            Otherwise `custom_amendments` are used to update pre-configured 
            amendments (add missing or override existing amendments). 
        exclusions : set-like, optional 
            Holidays to be ignored. The following values are accepted into 
            the set: 'new_year', 'mlk', 'presidents', 'memorial',
            'independence', 'labor', 'columbus', 'veterans', 'thanksgiving',
            'black_friday', 'christmas'.
        long_weekends : bool, optional (default True)
            If false, do not extend weekends if a holiday falls on Saturday or
            Sunday.

        Raises
        ------
        OutOfBoundsError
            If `custom_start` or `custom_end` fall outside the calendar span 
            set by `parameters`

        Returns
        -------
        Timeboard

        Examples
        --------
        import timeboard.calendars.US as US

        #create a timeboard with official business calendar
        clnd = US.Weekly8x5()

        #inspect calendar parameters
        parameters_dict = US.Weekly8x5.parameters()

        #inspect calendar amendments
        amendments_dict = US.Weekly8x5.amendments(**kwargs)

        #create a calendar with customized span and/or amendments
        clnd = US.Weekly8x5(**kwargs)
        """
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
