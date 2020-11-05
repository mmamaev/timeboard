from .calendarbase import CalendarBase
from ..core import get_timestamp, get_period
from ..timeboard import Organizer
from itertools import product


def holidays(start_year, end_year, work_on_dec31):
    """
    Return a list of holidays.

    Args:
        start_year: (int): write your description
        end_year: (todo): write your description
        work_on_dec31: (todo): write your description
    """
    dates = ['01 Jan', '02 Jan', '03 Jan', '04 Jan', '05 Jan',
             '06 Jan', '07 Jan', '23 Feb', '08 Mar', '01 May',
             '09 May', '12 Jun', '04 Nov']
    if not work_on_dec31:
        dates.append('31 Dec')
    years = range(start_year, end_year + 1)
    return {get_timestamp("{} {}".format(day, year)): 0
            for day, year in product(dates, years)}


def changes(eve_hours):
    """
    Changes hours hours hours.

    Args:
        eve_hours: (todo): write your description
    """
    x = eve_hours
    dates = {
        '10 Jan 2005': 0, '22 Feb 2005': x, '05 Mar 2005': x, '07 Mar 2005': 0,
        '02 May 2005': 0, '10 May 2005': 0, '14 May 2005': 8, '13 Jun 2005': 0,
        '03 Nov 2005': x,
        '09 Jan 2006': 0, '22 Feb 2006': x, '24 Feb 2006': 0, '26 Feb 2006': 8,
        '07 Mar 2006': x, '06 May 2006': x, '08 May 2006': 0, '03 Nov 2006': x,
        '06 Nov 2006': 0,
        '08 Jan 2007': 0, '22 Feb 2007': x, '07 Mar 2007': x, '28 Apr 2007': x,
        '30 Apr 2007': 0, '08 May 2007': x, '09 Jun 2007': x, '11 Jun 2007': 0,
        '05 Nov 2007': 0, '29 Dec 2007': x, '31 Dec 2007': 0,
        '08 Jan 2008': 0, '22 Feb 2008': x, '25 Feb 2008': 0, '07 Mar 2008': x,
        '10 Mar 2008': 0, '30 Apr 2008': x, '02 May 2008': 0, '04 May 2008': 8,
        '08 May 2008': x, '07 Jun 2008': 8, '11 Jun 2008': x, '13 Jun 2008': 0,
        '01 Nov 2008': x, '03 Nov 2008': 0, '31 Dec 2008': x,
        '08 Jan 2009': 0, '09 Jan 2009': 0, '11 Jan 2009': 8, '09 Mar 2009': 0,
        '30 Apr 2009': x, '08 May 2009': x, '11 May 2009': 0, '11 Jun 2009': x,
        '03 Nov 2009': x, '31 Dec 2009': x,
        '08 Jan 2010': 0, '22 Feb 2010': 0, '27 Feb 2010': x, '30 Apr 2010': x,
        '03 May 2010': 0, '10 May 2010': 0, '11 Jun 2010': x, '14 Jun 2010': 0,
        '03 Nov 2010': x, '05 Nov 2010': 0, '13 Nov 2010': 8, '31 Dec 2010': x,
        '10 Jan 2011': 0, '22 Feb 2011': x, '05 Mar 2011': x, '07 Mar 2011': 0,
        '02 May 2011': 0, '13 Jun 2011': 0, '03 Nov 2011': x,
        '09 Jan 2012': 0, '22 Feb 2012': x, '07 Mar 2012': x, '09 Mar 2012': 0,
        '11 Mar 2012': 8, '28 Apr 2012': x, '30 Apr 2012': 0, '05 May 2012': 8,
        '07 May 2012': 0, '08 May 2012': 0, '12 May 2012': x, '09 Jun 2012': x,
        '11 Jun 2012': 0, '05 Nov 2012': 0, '29 Dec 2012': x, '31 Dec 2012': 0,
        '08 Jan 2013': 0, '22 Feb 2013': x, '07 Mar 2013': x, '30 Apr 2013': x,
        '02 May 2013': 0, '03 May 2013': 0, '08 May 2013': x, '10 May 2013': 0,
        '11 Jun 2013': x, '31 Dec 2013': x,
        '08 Jan 2014': 0, '24 Feb 2014': x, '07 Mar 2014': x, '10 Mar 2014': 0,
        '30 Apr 2014': x, '02 May 2014': 0, '08 May 2014': x, '11 Jun 2014': x,
        '13 Jun 2014': 0, '03 Nov 2014': 0, '31 Dec 2014': x,
        '08 Jan 2015': 0, '09 Jan 2015': 0, '09 Mar 2015': 0, '30 Apr 2015': x,
        '04 May 2015': 0, '08 May 2015': x, '11 May 2015': 0, '11 Jun 2015': x,
        '03 Nov 2015': x, '31 Dec 2015': x,
        '08 Jan 2016': 0, '20 Feb 2016': x, '22 Feb 2016': 0, '07 Mar 2016': 0,
        '02 May 2016': 0, '03 May 2016': 0, '13 Jun 2016': 0, '03 Nov 2016': x,
        '22 Feb 2017': x, '24 Feb 2017': 0, '07 Mar 2017': x, '08 May 2017': 0,
        '03 Nov 2017': x, '06 Nov 2017': 0,
        '08 Jan 2018': 0, '22 Feb 2018': x, '07 Mar 2018': x, '09 Mar 2018': 0,
        '28 Apr 2018': x, '30 Apr 2018': 0, '02 May 2018': 0, '08 May 2018': x,
        '09 Jun 2018': x, '11 Jun 2018': 0, '05 Nov 2018': 0, '29 Dec 2018': x,
        '31 Dec 2018': 0,
        '08 Jan 2019': 0, '22 Feb 2019': x, '07 Mar 2019': x, '30 Apr 2019': x,
        '02 May 2019': 0, '03 May 2019': 0, '08 May 2019': x, '10 May 2019': 0,
        '11 Jun 2019': x, '31 Dec 2019': x,
        '08 Jan 2020': 0, '24 Feb 2020': 0, '09 Mar 2020': 0, '30 Apr 2020': x,
        '04 May 2020': 0, '05 May 2020': 0, '08 May 2020': x, '11 May 2020': 0,
        '11 Jun 2020': x, '03 Nov 2020': x, '31 Dec 2020': x,
        '08 Jan 2021': 0, '20 Feb 2021': x, '22 Feb 2021': 0, '30 Apr 2021': x,
        '03 May 2021': 0, '10 May 2021': 0, '11 Jun 2021': x, '14 Jun 2021': 0,
        '03 Nov 2021': x, '05 Nov 2021': 0, '31 Dec 2021': 0,
    }

    return {get_timestamp(k): v for k, v in dates.items()}


class Weekly8x5(CalendarBase):
    """Russian official calendar for 5 days x 8 hours working week.
    
    Workshifts are calendar days. Workshift labels are the number of working 
    hours per day: 0 for days off, 8 for regular business days, 7 for some 
    pre- or post-holiday business days (see also `short_eves` parameter).
    
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
    custom_amendments : dict-like
        The alternative amendments if `only_custom_amendments` is true. 
        Otherwise, `custom_amendments` are used to update pre-configured 
        amendments (add missing or override existing amendments). 
    work_on_dec31 : bool, optional (default True) 
        If False, the December 31 is always considered a holiday. Otherwise 
        use the official status of each December 31, which is the default 
        behavior.
    short_eves : bool, optional (default True)
        If False, consider all business days having 8 working hours. 
        Otherwise assume the official reduction of the working day to 7 
        hours on some pre- or post-holiday business days, which is the 
        default behavior.
        
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
    >>> import timeboard.calendars.RU as RU
    
    Create an official business calendar for the available range of dates:
    
    >>> clnd = RU.Weekly8x5()
    
    Create a business calendar for years 2010-2017, ignoring short eves 
    and making December 31 always a day off:
    
    >>> clnd = RU.Weekly8x5(custom_start='01 Jan 2010', 
    ...                     custom_end='31 Dec 2017', 
    ...                     work_on_dec31 = False,
    ...                     short_eves = False)
    
    Inspect the default calendar range:
    
    >>> params = RU.Weekly8x5.parameters()
    >>> params['start']
    Timestamp('2005-01-01 00:00:00')
    >>> params['end']
    Timestamp('2018-12-31 23:59:59')
    
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
            'start': get_timestamp('01 Jan 2005'),
            'end': get_timestamp('31 Dec 2021 23:59:59'),
            'layout': Organizer(marker='W', structure=[[8, 8, 8, 8, 8, 0, 0]]),
            'worktime_source': 'labels',
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None,
                   work_on_dec31=True, short_eves=True):
        """
        Return a list of particles for a given frequency.

        Args:
            cls: (todo): write your description
            custom_start: (todo): write your description
            custom_end: (todo): write your description
            custom_amendments: (dict): write your description
            work_on_dec31: (todo): write your description
            short_eves: (bool): write your description
        """

        start, end = cls._get_bounds(custom_start, custom_end)

        if short_eves:
            eve_hours = 7
        else:
            eve_hours = 8
        result = changes(eve_hours)
        result.update(holidays(start.year, end.year, work_on_dec31))
        if custom_amendments is not None:
            freq = cls.parameters()['base_unit_freq']
            result.update(
                {get_period(k, freq=freq).start_time: v
                 for k, v in custom_amendments.items()}
            )

        return result
