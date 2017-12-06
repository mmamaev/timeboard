from .calendarbase import (
    CalendarBase, nth_weekday_of_month, extend_weekends, from_easter)
from ..core import get_timestamp, get_period
from ..timeboard import Organizer
from itertools import product

def bank_holidays(start_year, end_year, country = 'england', exclusions=None,
                  long_weekends=True, label=0):

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
        'good_friday' : -2,
        'easter_monday': 1
    }

    if exclusions is None:
        exclusions = set()
    else:
        exclusions = set(exclusions)
    if country == 'england':
        exclusions |= {'new_year2', 'st_parricks', 'orangemens', 'st_andrews'}
    if country == 'scotland':
        bank_holidays_floating['summer'] = (8, 1, 1)
        exclusions |= {'st_patricks', 'orangemens', 'easter_monday'}
    if country == 'northern_ireland':
        exclusions |= {'new_year2', 'st_andrews'}

    years = range(start_year, end_year + 1)
    days = [day for holiday, day in bank_holidays_fixed.items()
            if holiday not in exclusions]

    amendments = {"{} {}".format(day, year): label
                  for day, year in product(days, years)}
    if long_weekends:
        amendments = extend_weekends(amendments, how='next')

    floating_dates_to_seek = [date_tuple for holiday, date_tuple
                              in bank_holidays_floating.items()
                              if holiday not in exclusions]
    easter_dates_to_seek = [shift for holiday, shift
                            in bank_holidays_easter.items()
                            if holiday not in exclusions]
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
        if 'royal' not in exclusions:
            amendments[get_timestamp('03 Jun 2002')] = label
            amendments[get_timestamp('04 Jun 2002')] = label
    if 2011 in years and 'royal' not in exclusions:
        amendments[get_timestamp('29 Apr 2011')] = label
    if 2012 in years:
        try:
            del amendments[get_timestamp('28 May 2012')]
        except KeyError:
            pass
        if 'royal' not in exclusions:
            amendments[get_timestamp('04 Jun 2012')] = label
            amendments[get_timestamp('05 Jun 2012')] = label

    return amendments


class Week8x5(CalendarBase):
    """United Kingdom business calendar for 5 days x 8 hours working week.

        The calendar takes into account the bank holidays 
        (https://www.gov.uk/bank-holidays) with regard to the country within 
        the UK. Selected holidays can be ignored by adding them to `exclusions`.

        Workshifts are calendar days. Workshift labels are number of working 
        hours per day: 0 for days off, 8 for  business days.

        Parameters
        ----------
        custom_start : Timestamp-like, optional
            Point in time referring to the first base unit of the calendar; must 
            be within the calendar span set by `parameters`. By default the 
            calendar starts with the base unit referred to by 'start' element of 
            `Week8x5.parameters()`.
        custom_end : Timestamp-like, optional
            Point in time referring to the last base unit of the calendar; must 
            be within the calendar span set by `parameters`. By default the 
            calendar ends with the base unit referred to by 'end' element of 
            `Week8x5.parameters()`.
        do_not_amend : bool, optional (default False)
            If set to True, the calendar is created without any amendments.
        only_custom_amendments : bool, optional (default False)
            If set to True, only amendments from `custom_amendments` are applied 
            to the calendar.
        custom_amendments : dict-like
            The alternative amendments if `only_custom_amendments` is true. 
            Otherwise `custom_amendments` are used to update pre-configured 
            amendments (add missing or override existing amendments). 
        country: {'england', 'northern_ireland', 'scotland'}, optional
            Default is 'england' for England and Wales.
        exclusions : set-like, optional 
            Holidays to be ignored. The following values are accepted into 
            the set: 'new_year', 'new_year2' (for the 2nd of January), 
            'st_patricks', 'good_friday', 'easter_monday', 'early_may'
            'spring', 'orangemens' (for Battle of the Boyne Day on July 12), 
            'st_andrews', 'christmas', 'boxing', 'royal' (for one-off 
            celebrations in the royal family).
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
        import timeboard.calendars.UK as UK

        #create a timeboard with official business calendar
        clnd = UK.Week8x5()

        #inspect calendar parameters
        parameters_dict = UK.Week8x5.parameters()

        #inspect calendar amendments
        amendments_dict = UK.Week8x5.amendments(**kwargs)

        #create a calendar with customized span and/or amendments
        clnd = UK.Week8x5(**kwargs)
        """

    @classmethod
    def parameters(cls):
        return {
            'base_unit_freq': 'D',
            'start': get_timestamp('01 Jan 2000'),
            'end': get_timestamp('31 Dec 2019'),
            'layout': Organizer(split_by='W', structure=[[8, 8, 8, 8, 8, 0, 0]])
        }

    @classmethod
    def amendments(cls, custom_start=None, custom_end=None,
                   custom_amendments=None, country='england',
                   exclusions=None, long_weekends=True, ):
        start, end = cls._get_bounds(custom_start, custom_end)

        result = bank_holidays(start.year, end.year, country, exclusions,
                               long_weekends)
        if custom_amendments is not None:
            freq = cls.parameters()['base_unit_freq']
            result.update(
                {get_period(k, freq=freq).start_time: v
                 for k, v in custom_amendments.items()}
            )

        return result
