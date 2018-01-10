from .calendarbase import CalendarBase
from ..core import get_timestamp, get_period
from ..timeboard import Organizer
from itertools import product


def holidays(start_year, end_year, work_on_dec31):
    dates = ['01 Jan', '02 Jan', '03 Jan', '04 Jan', '05 Jan',
             '06 Jan', '07 Jan', '23 Feb', '08 Mar', '01 May',
             '09 May', '12 Jun', '04 Nov']
    if not work_on_dec31:
        dates.append('31 Dec')
    years = range(start_year, end_year + 1)
    return {get_timestamp("{} {}".format(day, year)): 0
            for day, year in product(dates, years)}


def changes(eve_hours):
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
        '31 Dec 2018': 0 }

    return {get_timestamp(k): v for k, v in dates.items()}


class Weekly8x5(CalendarBase):
    """Russian business calendar for 5 days x 8 hours working week.
    
    Workshifts are calendar days. Workshift labels are number of working hours
    per day: 0 for days off, 8 for regular business days, 7 for some pre- or 
    post-holidays business days (see also `short_eves` parameter).
    
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
    work_on_dec31 : bool, optional (default True) 
        If false, the December 31 is always considered a holiday. Otherwise (
        by default) use the official status of each December 31.
    short_eves : bool, optional (default True)
        If false, consider all business days having 8 working hours. 
        Otherwise (by default) use the official reduction to 7 working hours 
        on some pre- or post-holiday business days.
        
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
    import timeboard.calendars.RU as RU
    
    #create a timeboard with official business calendar
    clnd = RU.Weekly8x5()
    
    #inspect calendar parameters
    parameters_dict = RU.Weekly8x5.parameters()
    
    #inspect calendar amendments
    amendments_dict = RU.Weekly8x5.amendments(**kwargs)
    
    #create a calendar with customized span and/or amendments
    clnd = RU.Weekly8x5(**kwargs)
    """

    @classmethod
    def parameters(cls):
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2005'),
            'end': get_timestamp('31 Dec 2018'),
            'layout': Organizer(marker='W', structure=[[8, 8, 8, 8, 8, 0, 0]])
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None,
                   work_on_dec31=True, short_eves=True):

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
