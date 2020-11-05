from .calendarbase import (
    CalendarBase, nth_weekday_of_month, extend_weekends, from_easter)
from ..core import get_timestamp, get_period
from ..timeboard import Organizer
from itertools import product


def bank_holidays(start_year, end_year, country='england', do_not_observe=None,
                  long_weekends=True, label=0):
    """
    The number of holidays.

    Args:
        start_year: (int): write your description
        end_year: (array): write your description
        country: (str): write your description
        do_not_observe: (todo): write your description
        long_weekends: (str): write your description
        label: (str): write your description
    """

    bank_holidays_fixed = {'new_year': '01 Jan',
                           'new_year2': '02 Jan',
                           'st_patricks': '17 Mar',
                           'orangemens': '12 Jul',
                           'st_andrews': '30 Nov',
                           'christmas': '25 Dec',
                           'boxing': '26 Dec'}

    bank_holidays_floating = {
        'early_may': (5, 1, 1),
        'spring': (5, 1, -1),
        'summer': (8, 1, -1),
    }

    bank_holidays_easter = {
        'good_friday': -2,
        'easter_monday': 1
    }

    if do_not_observe is None:
        do_not_observe = set()
    else:
        do_not_observe = set(do_not_observe)
    if country == 'england':
        do_not_observe |= {'new_year2', 'st_patricks', 'orangemens',
                           'st_andrews'}
    if country == 'scotland':
        bank_holidays_floating['summer'] = (8, 1, 1)
        do_not_observe |= {'st_patricks', 'orangemens', 'easter_monday'}
    if country == 'northern_ireland':
        do_not_observe |= {'new_year2', 'st_andrews'}

    years = range(start_year, end_year + 1)
    days = [day for holiday, day in bank_holidays_fixed.items()
            if holiday not in do_not_observe]

    amendments = {"{} {}".format(day, year): label
                  for day, year in product(days, years)}
    if long_weekends:
        amendments = extend_weekends(amendments, how='next')

    floating_dates_to_seek = [date_tuple for holiday, date_tuple
                              in bank_holidays_floating.items()
                              if holiday not in do_not_observe]
    easter_dates_to_seek = [shift for holiday, shift
                            in bank_holidays_easter.items()
                            if holiday not in do_not_observe]
    for year in years:
        amendments.update(
            nth_weekday_of_month(year, floating_dates_to_seek, label))
        amendments.update(
            from_easter(year, easter_dates_to_seek, 'western', label))

    if 2002 in years:
        try:
            del amendments[get_timestamp('27 May 2002')]
        except KeyError:
            pass
        if 'royal' not in do_not_observe:
            amendments[get_timestamp('03 Jun 2002')] = label
            amendments[get_timestamp('04 Jun 2002')] = label
    if 2011 in years and 'royal' not in do_not_observe:
        amendments[get_timestamp('29 Apr 2011')] = label
    if 2012 in years:
        try:
            del amendments[get_timestamp('28 May 2012')]
        except KeyError:
            pass
        if 'royal' not in do_not_observe:
            amendments[get_timestamp('04 Jun 2012')] = label
            amendments[get_timestamp('05 Jun 2012')] = label

    return amendments


class Weekly8x5(CalendarBase):
    """British business calendar for 5 days x 8 hours working week.

    The calendar takes into account the bank holidays 
    (https://www.gov.uk/bank-holidays) with regard to the country within 
    the UK. Selected holidays can be ignored by adding them to `exclusions`.

    Workshifts are calendar days. Workshift labels are the number of working 
    hours per day: 0 for days off, 8 for  business days.

    Parameters
    ----------
    custom_start : `Timestamp`-like, optional
        Change the first date of the calendar. This date must be within the 
        default calendar range returned by :py:meth:`Weekly8x5.parameters()`. 
        By default, the calendar starts on the date defined by 'start' 
        element of :py:meth:`Weekly8x5.parameters()`.
    custom_end : `Timestamp`-like, optional
        Change the last date of the calendar. This date must be within the 
        default calendar range returned by :py:meth:`Weekly8x5.parameters()`. 
        By default, the calendar ends on the date defined by 'end' 
        element of :py:meth:`Weekly8x5.parameters()`.
    do_not_amend : bool, optional (default False)
        If set to True, the calendar is created without any amendments, 
        meaning that effects of holiday observations are not accounted for.
    only_custom_amendments : bool, optional (default False)
        If set to True, only amendments from `custom_amendments` are applied 
        to the calendar.
    only_custom_amendments : bool, optional (default False)
        If set to True, only amendments from `custom_amendments` are applied 
        to the calendar.
    custom_amendments : dict-like
        The alternative amendments if `only_custom_amendments` is true. 
        Otherwise, `custom_amendments` are used to update pre-configured 
        amendments (add missing or override existing amendments). 
    country : {``'england'``, ``'northern_ireland'``, ``'scotland'``}, optional
        The default is ``'england'`` for England and Wales.
    do_not_observe : set, optional 
        Holidays to be ignored. The following values are accepted into 
        the set: ``'new_year'``, ``'new_year2'`` (for the 2nd of January), 
        ``'st_patricks'``, ``'good_friday'``, ``'easter_monday'``, 
        ``'early_may'``, ``'spring'``, ``'orangemens'`` 
        (for Battle of the Boyne Day on July 12), 
        ``'st_andrews'``, ``'christmas'``, ``'boxing'``, ``'royal'`` 
        (for one-off celebrations in the royal family).
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
    >>> import timeboard.calendars.UK as UK

    Create an official business calendar for the available range of dates:
    
    >>> clnd = UK.Weekly8x5()
    
    Create a 2010-2017 business calendar for Scotland but don't observe 
    St Andrew's Day:
    
    >>> clnd = UK.Weekly8x5(custom_start='01 Jan 2010', 
    ...                     custom_end='31 Dec 2017', 
    ...                     country = 'scotland',
    ...                     do_not_observe = {'st_andrews'})

    Inspect the default calendar range:
    
    >>> params = UK.Weekly8x5.parameters()
    >>> params['start']
    Timestamp('2000-01-01 00:00:00')
    >>> params['end']
    Timestamp('2019-12-31 23:59:59')
    
    """

    @classmethod
    def parameters(cls):
        """
        Returns a dictionary of parameters.

        Args:
            cls: (todo): write your description
        """
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2000'),
            'end': get_timestamp('31 Dec 2020 23:59:59'),
            'layout': Organizer(marker='W', structure=[[8, 8, 8, 8, 8, 0, 0]]),
            'worktime_source': 'labels',
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None, country='england',
                   do_not_observe=None, long_weekends=True):
        """
        Return a list of all gpus.

        Args:
            cls: (todo): write your description
            custom_start: (todo): write your description
            custom_end: (todo): write your description
            custom_amendments: (dict): write your description
            country: (str): write your description
            do_not_observe: (todo): write your description
            long_weekends: (str): write your description
        """
        start, end = cls._get_bounds(custom_start, custom_end)

        result = bank_holidays(start.year, end.year, country, do_not_observe,
                               long_weekends)
        if custom_amendments is not None:
            freq = cls.parameters()['base_unit_freq']
            result.update(
                {get_period(k, freq=freq).start_time: v
                 for k, v in custom_amendments.items()}
            )

        return result
