from .core import _Timeline, Organizer, Period
from .workshift import Workshift
from .interval import Interval
from .exceptions import OutOfBoundsError, VoidIntervalError
from collections import Iterable
from math import copysign
import warnings



class Timeboard:
    """Your customized calendar.
    
    A Timeboard object consists of two main parts:
        - a timeline of workshifts constructed as specified by timeboard's
        instantiation parameters,
        - a `selector` function used to classify a workshift as on-duty or
        off-duty
        
    Calculations over a timeboard are either workshift-based or interval-based. 
    Execute `get_workshift` or `get_interval` to instantiate 
    a workshift/an interval and then call their appropriate methods to 
    perform calculations. 
    Note that an instance of the timeboard is callable and such call is 
    a wrapper around `get_workshift`. 
    
    Parameters
    ----------
    base_unit_freq : str
        Base unit is a period of time that is the building block of the 
        timeline. Every workshift on the timeline consists of an integer 
        number of base units (currently, of only one base unit). 
        Base unit is defined by `base_unit_freq` pandas-compatible calendar 
        frequency (i.e. 'D' for day). Pandas-native business  periods 
        (i.e. 'BM') are not supported. Support of periods with multipliers 
        (i.e. '3D') is planned but not yet there.
    start : Timestamp-like
        A point in time represented by a string convertible to a timestamp, or
        a pandas Timestamp, or a datetime object. This point in time is used 
        to identify the first base unit of the timeline. The point in time 
        can be located anywhere within this base unit.
    end : Timestamp-like
        Same as `start` but for the last base unit of the timeline.
    layout : Iterable or Organizer
        Define the rules of assigning labels to workshifts. 
        If layout is an Iterable, it is interpreted as a pattern of labels which
        are assigned to workshifts starting from the beginning of the 
        timeline. Application of `layout` is repeated in cycles until the end 
        of the timeline is reached.
        If layout is an Organizer, the timeline is structured according to 
        the rule set by the Organizer.
    amendments : dict-like, optional
        Override labels set according to `layout`.
        The keys of `amendments` are Timestamp-like points in time 
        used to identify workshifts (the point in time may be located 
        anywhere within the workshift). The values of `amendments` are labels 
        which override whatever has been set by `layout` for the 
        corresponding workshifts. 
        If there are several keys in `amendments` which refer to the same 
        workshift, the actual label would be unpredictable, therefore a 
        KeyError is raised.
    selector : function, optional
        Function which takes one argument - label of a workshift. Returns 
        True if this is an on-duty workshift, returns False otherwise. Default 
        selector function returns `bool(label)`.
    workshift_ref : {'start' | 'end'}, optional (default 'start')
        Define what point in time will be used to represent a workshift 
        (the respective point in time will be recorded in `ref` attribute of
        a workshift). Available options: 'start' to use the start 
        time of the workshift, 'end' to use the end time. 
    
    Raises
    ------
    UnsupportedPeriodError (ValueError)
        If `base_unit_freq` is not supported or an Organizer attempted a split
        by a period which is not a multiple of `base_unit_freq`.
    VoidIntervalError (ValueError)
        If an instantiation of an empty timeline is attempted.
    KeyError
        If `amendments` contain several references to the same workshift.
        
    Attributes
    ----------
    base_unit_freq : str
    start_time : Timestamp
        When the first workshift of the timeboard starts.
    end_time : Timestamp
        When the last workshift of the timeboard ends.
    workshift_ref
    selectore : function
        
    See also
    --------
    Organizer - defines rules for setting up timeline's layout
    """
    def __init__(self, base_unit_freq, start, end, layout, amendments={},
                 selector=None, workshifts_ref='start'):
        if isinstance(layout, Organizer):
            org = layout
        elif isinstance(layout, Iterable):
            if len(layout)==1 and isinstance(layout[0],Organizer):
                warnings.warn("Received 'layout' as an Organizer wrapped in "
                              "a list. Probably you do not want a list here.",
                              SyntaxWarning)
            org = Organizer(split_at=[], structure=[layout])
        else:
            raise TypeError("`layout` must be either an iterable "
                            "representing a pattern, "
                            "or an instance of Organizer")

        if not hasattr(amendments, 'iteritems') :
            raise TypeError("`amendments` do not look like a dictionary: "
                            "`iteritems` method is needed but not found.")
        self._custom_selector = selector
        self._timeline = _Timeline(base_unit_freq, start, end)
        self._timeline.organize(org)
        self._timeline.amend(amendments)
        self._base_unit_freq = base_unit_freq
        self._workshift_ref = workshifts_ref
        self._repr = "Timeboard('{}', {}, {}, {})"\
                     .format(base_unit_freq, start, end, layout)

        #TODO: think more about indexing and fast lookups
        self._on_duty_idx = []
        self._off_duty_idx = []
        for i, ws in enumerate(self._timeline):
            if self.selector(ws):
                self._on_duty_idx.append(i)
            else:
                self._off_duty_idx.append(i)

    def __repr__(self):
        return self._repr

    def __str__(self):
        return "Timeboard of '{}': {} -> {}" \
                .format(self.base_unit_freq,
                        str(Period(self.start_time, freq=self.base_unit_freq)),
                        str(Period(self.end_time, freq=self.base_unit_freq)))

    @property
    def base_unit_freq(self):
        return self._base_unit_freq

    @property
    def start_time(self):
        return self._timeline.start_time

    @property
    def end_time(self):
        return self._timeline.end_time

    @property
    def workshift_ref(self):
        return self._workshift_ref

    @property
    def selector(self):

        def default_selector(x):
            return bool(x)

        if self._custom_selector is not None:
           return self._custom_selector
        else:
            return default_selector

    def __call__(self, arg):
        """A wrapper of `get_workshift()`."""
        return self.get_workshift(arg)

    def _locate(self, point_in_time):
        try:
            return self._timeline.frame.get_loc(point_in_time)
        except KeyError:
            return None

    def _handle_out_of_bounds(self, msg=None):
        if msg is None:
            message = "Point in time is outside {}".format(self)
        else:
            message = msg
        raise OutOfBoundsError(message)

    def _handle_void_interval(self, msg=None):
        if msg is None:
            message = "Empty interval is not allowed"
        else:
            message = msg
        raise VoidIntervalError(message)


    def get_workshift(self, point_in_time):
        """Find workshift by timestamp.
        
        Takes a timestamp-like value and returns the workshift which
        contains this timestamp.
        
        Parameters
        ----------
        point_in_time : Timestamp-like
            A string convertible to a timestamp, or a pandas Timestamp, or 
            a datetime object.
            
        Returns
        -------
        Workshift
        
        Raises
        ------
        OutOfBoundsError (LookupError)
            If `point_in_time` is not within the timeboard.
            
        See also
        --------
        timeboard.workshift.Workshift(timeboard, location)
            This is the alternative, low-level approach to instantiating a 
            workshift. You will need to know the absolute position 
            (`location`) of the workshift within the timeline.
        """
        loc = self._locate(point_in_time)
        if loc is None:
            return self._handle_out_of_bounds()
        else:
            return Workshift(self, loc)


    def get_interval(self, interval_ref=None, length=None, period=None,
                     closed='11'):
        """Create interval (a series of workshifts).
        
        A number of techniques to define the interval can be used. They are 
        mutually exclusive. Accepted  parameters are listed below along with 
        the techniques.
        
        - Create an interval from two points in time which refer to the first 
        and the last workshifts of the interval.
        
        Parameters
        ----------
        interval_ref : sequence of (Timestamp-like, Timestamp-like)
            Each element is a string convertible to a timestamp, 
            or a pandas Timestamp, or a datetime object.
        length : parameter must be omitted
        period : parameter must be omitted
        
        - Create an interval of a specific length starting from a 
        workshift refer to by a point in time .
        
        Parameters
        ----------
        interval_ref : Timestamp-like
            A string convertible to a timestamp, or a pandas Timestamp, 
            or a datetime object.
        length : int (!=0)
            Number of workshifts in the interval. If `length` is positive, 
            the interval extends into the future from the workshift 
            referred to by `interval_ref`.  If `length` is negative, 
            the interval extends to the past. Both length=1 and length=-1 
            create the interval containing only one `interval_ref` workshift.
            Zero `length` is not allowed.
        period : parameter must be omitted
        
        - Create an interval aligned with a calendar period. Specify a 
        point in time within the period and a calendar frequency of the period 
        (i.e. 'M' for month). 
        The interval is created only if the boundaries of the calendar period 
        are aligned with workshift boundaries, that is, no workshift has its 
        parts located both within and outside the calendar period.
        The interval will extend from the first to the last workshifts in 
        the calendar period.
        
        Parameters
        ----------
        interval_ref : Timestamp-like
            A string convertible to a timestamp, or a pandas Timestamp, 
            or a datetime object.
        period : str
            A pandas-compatible frequency defining a calendar period (i.e. 
            'M' for month).
        length : parameter must be omitted
        
        - Create an interval from a pandas Period object. The same restriction 
        is applied as with the previous technique.

        Parameters
        ----------
        interval_ref : pandas.Period
        length : parameter must be omitted
        period : parameter must be omitted
        
        - Create the interval that spans the entire timeline.
        
        Parameters
        ----------
        interval_ref : parameter must be omitted
        length : parameter must be omitted
        period : parameter must be omitted
        
        
        Other Parameters
        ----------------
        closed : {'11', '01', '10', '00'}, optional (default '11')
            Interpret the interval definition as closed ('11'), half-open 
            ('01' or '10'), or open ('00'). The symbol of zero indicates 
            whether the returned interval is stripped of the first or the last 
            workshift, or both.  
                  
        Returns
        -------
        Interval
        
        Raises
        ------
        OutOfBoundsError (LookupError)
            If the interval would extend outside the timeline.
            
        VoidIntervalError (ValueError)
            If creation of an empty interval is attempted. This includes the 
            case when the points in time specifying the interval bounds are 
            passed in reverse order.
            
        TypeError
            If the combination of parameters passed to the method is not 
            allowed (is meaningless).
            
        See also
        --------
        timeboard.interval.Interval(timeboard, (location1, location2))
            This is the alternative, low-level approach to instantiating 
            an interval. You will need to know the absolute positions 
            of the first (`location1`) and the last (`location2`) workshifts 
            of the interval within the timeline.
        """

        if length is None and period is None:
            locs = self._get_interval_locs_from_reference(interval_ref)
        elif length is not None and period is None:
            locs = self._get_interval_locs_by_length(interval_ref, length)
        elif period is not None and length is None:
            locs = self._get_interval_locs_by_period(interval_ref, period)
        else:
            raise TypeError("Unacceptable combination of interval reference "
                            "and 'length' or 'period' parameters")

        if locs[0] is None:
            raise OutOfBoundsError('First interval bound is '
                                   'outside {}'.format(self))
        if locs[1] is None:
            raise OutOfBoundsError('Second interval bound is '
                                   'outside {}'.format(self))

        locs = self._strip_interval_locs(locs, closed)

        if locs[0] > locs[1]:
            return self._handle_void_interval()
        else:
            return Interval(self, locs)

    def _get_interval_locs_from_reference(self, interval_ref):
        if interval_ref is None:
            locs = (0, len(self._timeline) - 1)
        elif isinstance(interval_ref, Period):
            locs = (self._locate(interval_ref.start_time),
                    self._locate(interval_ref.end_time))
        else:
            if not hasattr(interval_ref, '__getitem__') or len(interval_ref)<2:
                raise TypeError('Interval reference must be list-like '
                                'of two values '
                                'unless period or length kwarg is provided')
            locs = (self._locate(interval_ref[0]), self._locate(interval_ref[1]))
        return locs

    def _get_interval_locs_by_length(self, start_ref, length):
        if not isinstance(length, int):
            raise TypeError('Interval length = {}: expected integer '
                            'got {}. If you are not using length parameter, '
                            'make sure you passed interval bounds '
                            'as a tuple'.format(length, type(length)))
        if length == 0:
            return self._handle_void_interval('Interval length cannot be zero')
        loc0 = self._locate(start_ref)
        if loc0 is not None:
            return sorted((loc0, loc0 + length - int(copysign(1, length))))
        else:
            return None, None

    def _get_interval_locs_by_period(self, period_ref, period_freq):
        p = Period(period_ref, freq=period_freq)
        return self._locate(p.start_time), self._locate(p.end_time)

    def _strip_interval_locs(self, locs, closed):
        if closed not in ['00', '01', '10', '11']:
            raise ValueError("Unacceptable 'closed' parameter")
        drop_head = closed[0] == '0'
        drop_tail = closed[1] == '0'
        result = locs
        if drop_head:
            result = (result[0] + 1, result[1])
        if drop_tail:
            result = (result[0], result[1] - 1)
        return result
