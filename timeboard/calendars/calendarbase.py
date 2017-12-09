from __future__ import division
from ..exceptions import OutOfBoundsError
from ..core import get_timestamp
from ..timeboard import Timeboard
from pandas import PeriodIndex
import datetime
from dateutil.easter import easter


def nth_weekday_of_month(year, dates_to_seek, label=0, errors='ignore'):
    """Calculate holiday dates anchored to n-th weekday of a month.
    
    This function is to be used to build a (part of) `amendments` dictionary 
    for a day-based calendar.
    
    Parameters
    ----------
    year : int
    dates_to_seek : iterable of tuples (month, weekday, n, [shift])
        month : int 1..12 (January is 1)
        weekday : int 1..7 (Monday is 1)
        n : int -5..5 (n=1 the for first weekday in the month, n=-1 for the 
        last. n=0 is not allowed)
        shift: int, optional - number of days to add to the found weekday, 
        may be negative (default 0).
    label : optional (default 0)
    errors : {'ignore', 'raise'}, optional (default 'ignore')
        What to do if the requested date does not exist (i.e. there are less 
        than n such weekdays in the month).
        
    Raises
    ------
    OutOfBoundsError
        If the requested date does not exist and `errors='raise'`
        
    Returns
    -------
    dict 
        Dictionary suitable for `amendments` parameter of Timeboard with 
        `base_unit_freq='D'`. The keys are timestamps. The values of the 
        dictionary are set to the value of `label`.
        
    Example
    -------
    Create amendments for US Memorial Day and Labor Day in 2017
    
    >>> nth_weekday_of_month(2017, [(5, 1, -1), (9, 1, 1)])
    {Timestamp('2017-05-29 00:00:00'): 0, Timestamp('2017-09-04 00:00:00'): 0}
    """
    months = PeriodIndex(start=datetime.date(year, 1, 1),
                         end=datetime.date(year, 12, 31), freq='M')
    weekday_freq = {1: 'W-SUN', 2: 'W-MON', 3: 'W-TUE', 4: 'W-WED',
                    5: 'W-THU', 6: 'W-FRI', 7: 'W-SAT'}
    amendments = {}
    for date_tuple in dates_to_seek:
        month, weekday, n = date_tuple[0:3]
        assert month in range(1, 13)
        assert weekday in range(1, 8)
        assert n in range(1, 6) or n in range(-5, 0)
        try:
            shift = date_tuple[3]
        except IndexError:
            shift = 0
        if n > 0:
            n -= 1
        weeks = PeriodIndex(start=months[month - 1].start_time,
                            end=months[month - 1].end_time,
                            freq=weekday_freq[weekday])
        if weeks[0].start_time < months[month - 1].start_time:
            weeks = weeks[1:]
        try:
            week_starting_on_our_day = weeks[n]
        except IndexError:
            if errors == 'raise':
                raise OutOfBoundsError("There is no valid  date for "
                                       "year={}, month-{}, weekday={}, n={}.".
                                       format(year, month, weekday, n))
        else:
            amendments[week_starting_on_our_day.start_time +
                       datetime.timedelta(days=shift)] = label

    return amendments


def extend_weekends(amendments, how='nearest', label=None, weekend=None):
    """Make a weekday a day off if a holiday falls on the weekend.
    
    This function is to be used to update a (part of) `amendments` dictionary 
    for a day-based calendar.
    
    Parameters
    ----------
    amendments: dict
    how : {'previous', 'next', 'nearest'}, optional (default 'nearest')
        Which weekday to make a day off: a weekday preceding the weekend, 
        a weekday following the weekend, or a weekday nearest to the holiday.
        If there is a tie with 'nearest', it works the same way as 'next'.
    label : optional (default None)
    weekend: list, optional 
        Weekdays constituting weekend, Monday is 0, Sunday is 6. Days must be 
        consecutive: i.e. if weekend is on Sunday and Monday, weekend=[6,0], 
        NOT weekend=[0,6]. By default weekend is Saturday and Sunday.
    
    Returns
    -------
    dict
        Updated `amendments` dictionary with new days off, if any. The keys 
        are timestamps (both for the old and the new elements.) The values 
        of the newly added days are set to the value of `label` if given;
        otherwise the label of the corresponding holiday is used.
    
    Notes
    -----
    If a weekday has been already declared a day off because of another holiday
    taking place on the same weekend or it is a holiday by itself, the next 
    weekday in the direction specified by `how` parameter will be made 
    a day off. 
    """
    assert how in ['previous', 'next', 'nearest']
    if weekend is None:
        weekend = [5, 6]  # Saturday and Sunday
    amendments = {get_timestamp(k): v for k, v in amendments.items()}
    for holiday in sorted(amendments.keys()):
        day_of_week = holiday.weekday()
        try:
            loc_in_wend = weekend.index(day_of_week)
        except ValueError:
            continue
        if label is None:
            _label = amendments[holiday]
        else:
            _label = label
        if how == 'previous':
            first_step = -(loc_in_wend+1)
            step = -1
        elif how == 'next':
            first_step = len(weekend) - loc_in_wend
            step = 1
        elif how == 'nearest':
            if loc_in_wend < len(weekend) // 2:
                first_step = -(loc_in_wend + 1)
                step = -1
            else:
                first_step = len(weekend) - loc_in_wend
                step = 1
        new_day = holiday + datetime.timedelta(days=first_step)
        while new_day in amendments:
            new_day += datetime.timedelta(days=step)
        amendments[new_day] = _label

    return amendments


def from_easter(year, shifts, easter_type='western', label=0):
    """Calculate holiday dates anchored to Easter.

    This function is to be used to build a (part of) `amendments` dictionary 
    for a day-based calendar.

    Parameters
    ----------
    year : int
    shifts : iterable of int
        List of holidays whose dates are to be found. The holidays are
        denominated in their distance from Easter. For example,
        -2 is Good Friday, 1 is Monday after Easter, 0 is Easter itself.
    easter_type: {'western', 'orthodox'}, optional (default 'western')
    label : optional (default 0)

    Returns
    -------
    dict 
        Dictionary suitable for `amendments` parameter of Timeboard with 
        `base_unit_freq='D'`. The keys are timestamps. The values of the 
        dictionary are set to the value of `label`.
        
    Example
    -------
    Create amendments for Good Friday and Easter Monday in 2017:
    
    >>> from_easter(2017, [-2, 1])
    {Timestamp('2017-04-14 00:00:00'): 0, Timestamp('2017-04-17 00:00:00'): 0}
    """
    assert easter_type in ['western', 'orthodox']
    if easter_type == 'western':
        _easter_type = 3
    elif easter_type == 'orthodox':
        _easter_type = 2
    easter_date = easter(year, _easter_type)
    amendments = {
        get_timestamp(easter_date + datetime.timedelta(days=shift)): label
        for shift in shifts}
    return amendments


class CalendarBase(object):
    """Template for pre-configured calendars.
    
    To prepare a ready-to-use customized calendar subclass CalendarBase and
    override `parameters` and `amendments` class methods.
    
    `parameters` class method must return a dictionary of parameters to 
    instantiate a Timeboard except `amendments`.
    
    `amendments` class method must return a dictionary suitable for 
    `amendments` parameter of a Timeboard. 
    
    Parameters
    ----------
    custom_start : Timestamp-like, optional
        Point in time referring to the first base unit of the calendar; must 
        be within the calendar span set by `parameters`. By default the 
        calendar starts with the base unit referred to by 'start' element of 
        `parameters`.
    custom_end : Timestamp-like, optional
        Point in time referring to the last base unit of the calendar; must 
        be within the calendar span set by `parameters`. By default the 
        calendar ends with the base unit referred to by 'end' element of 
        `parameters`.
    do_not_amend : bool, optional (default False)
        If set to True, the calendar is created without any amendments.
    only_custom_amendments : bool, optional (default False)
        If set to True, only amendments from `custom_amendments` are applied 
        to the calendar.
    custom_amendments : dict-like
        Additional or alternative amendments (depends on 
        `only_custom_amendments` flag).
    **additional_kwargs, optional 
        Additional parameters which are passed to your `amendments` 
        method.
    
    Notes
    -----
    If both `do_not_amend` and `only_custom_amendments` are false (the 
    default setting), `amendments` class method is called to receive 
    amendments for the timeboard. The `custom_start`, `custom_end`, 
    `custom_amendments` parameters are passed to `amendments` method along 
    with `**additional_kwargs`. The use of this parameters is up to your 
    implementation.
    
    The `custom_start` and `custom_end`, if specified, are used as 
    timeboard `start` and `end` parameters instead of the namesake 
    elements of `parameters`.
    
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
    class MyCalendar(CalendarBase):
        @classmethod
        def parameters(cls):
            return {
                'base_unit_freq': ? ,
                'start': ? ,
                'end': ? ,
                'layout': ?
                ...
        }
        
        @classmethod
        def amendments(cls, custom_start=None, custom_end=None,
                       custom_amendments=None, your_parameter=?):
            calculate_amendments
            return dict

    #inspect calendar parameters
    parameters_dict = MyCalendar.parameters()
    
    #inspect calendar amendments
    amendments_dict = MyCalendar.amendments(**kwargs)
    
    #create a timeboard with your calendar
    clnd = MyCalendar(**kwargs)
    """
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
                   custom_amendments=None, **additional_kwargs):
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
                do_not_amend=False, only_custom_amendments=False,
                custom_amendments=None, **additional_kwargs):
        parameters = cls.parameters()
        parameters['start'], parameters['end'] = cls._get_bounds(
            custom_start, custom_end)
        if do_not_amend:
            amendments = {}
        elif only_custom_amendments:
            amendments = custom_amendments
        else:
            amendments = cls.amendments(custom_start=parameters['start'],
                                        custom_end=parameters['end'],
                                        custom_amendments=custom_amendments,
                                        **additional_kwargs)

        return Timeboard(amendments=amendments, **parameters)
