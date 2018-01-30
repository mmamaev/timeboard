from .calendarbase import CalendarBase, nth_weekday_of_month, extend_weekends
from ..core import get_timestamp, get_period
from ..timeboard import Organizer
from itertools import product


def fed_holidays(start_year, end_year, do_not_observe=None, long_weekends=True,
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

    if do_not_observe is None:
        do_not_observe = set()
    else:
        do_not_observe = set(do_not_observe)
    years = range(start_year, end_year + 1)
    days = [day for holiday, day in fed_holidays_fixed.items()
            if holiday not in do_not_observe]

    amendments = {"{} {}".format(day, year): label
                  for day, year in product(days, years)}
    if long_weekends:
        amendments = extend_weekends(amendments, how='nearest')

    floating_dates_to_seek = [date_tuple for holiday, date_tuple
                              in fed_holidays_floating.items()
                              if holiday not in do_not_observe]
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
    custom_start : `Timestamp`-like, optional
        Change the first date of the calendar. This date must be within 
        the default calendar range returned by :py:meth:`Weekly8x5.parameters()`. 
        By default the calendar starts on the date defined by 'start' 
        element of :py:meth:`Weekly8x5.parameters()`.
    custom_end : `Timestamp`-like, optional
        Change the last date of the calendar. This date must be within 
        the default calendar range returned by :py:meth:`Weekly8x5.parameters()`. 
        By default the calendar ends on the date defined by 'end' 
        element of :py:meth:`Weekly8x5.parameters()`.
    do_not_amend : bool, optional (default False)
        If set to True, the calendar is created without any amendments, 
        meaning that effects of holiday observations are not accounted for.
    only_custom_amendments : bool, optional (default False)
        If set to True, only amendments from `custom_amendments` are applied 
        to the calendar.
    custom_amendments : dict-like
        The alternative amendments if `only_custom_amendments` is true. 
        Otherwise `custom_amendments` are used to update pre-configured 
        amendments (add missing or override existing amendments). 
    do_not_observe : set, optional 
        Holidays to be ignored. The following values are accepted into 
        the set: ``'new_year'``, ``'mlk'`` for Martin Luther King Jr. Day, 
        ``'presidents'``, ``'memorial'``, ``'independence'``, ``'labor'``, 
        ``'columbus'``, ``'veterans'``, 
        ``'thanksgiving'``, ``'black_friday'``, ``'christmas'``.
    long_weekends : bool, optional (default True)
        If false, do not extend weekends if a holiday falls on Saturday or
        Sunday.

    Raises
    ------
    OutOfBoundsError
        If `custom_start` or `custom_end` fall outside the calendar range 
        returned by :py:meth:`Weekly8x5.parameters()`
    
    Returns
    -------
    :py:class:`.Timeboard`
    
    Methods
    -------
    parameters() : dict
        This class method returns a dictionary of :py:class:`.Timeboard` 
        parameters used for building the calendar. 

    Examples
    --------
    >>> import timeboard.calendars.US as US

    Create an official business calendar for the available range of dates:
    
    >>> clnd = US.Weekly8x5()
    
    Create a 2010-2017 business calendar with Black Friday a working day:
    
    >>> clnd = US.Weekly8x5(custom_start='01 Jan 2010', 
                            custom_end='31 Dec 2017', 
                            do_not_observe = {'black_friday'})


    Inspect the default calendar range:
    
    >>> params = US.Weekly8x5.parameters()
    >>> params['start']
    Timestamp('2000-01-01 00:00:00')
    >>> params['end']
    Timestamp('2020-12-31 00:00:00')
    
    """

    @classmethod
    def parameters(cls):
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2000'),
            'end': get_timestamp('31 Dec 2020 23:59:59'),
            'layout': Organizer(marker='W', structure=[[8, 8, 8, 8, 8, 0, 0]])
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None, do_not_observe=None,
                   long_weekends=True):

        start, end = cls._get_bounds(custom_start, custom_end)

        result = fed_holidays(start.year, end.year, do_not_observe,
                              long_weekends)
        if custom_amendments is not None:
            freq = cls.parameters()['base_unit_freq']
            result.update(
                {get_period(k, freq=freq).start_time: v
                 for k, v in custom_amendments.items()}
            )

        return result
