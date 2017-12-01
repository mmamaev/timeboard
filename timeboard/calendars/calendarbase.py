from ..exceptions import OutOfBoundsError
from ..core import get_timestamp
from ..timeboard import Timeboard


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
