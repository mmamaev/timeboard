from __future__ import division
from .core import (_Frame, _Timeline, _Schedule,
                   Organizer, get_period, get_timestamp, _is_iterable)
from .workshift import Workshift
from .interval import Interval
from .exceptions import OutOfBoundsError, VoidIntervalError
from collections import namedtuple
from math import copysign
import warnings

OOB_LEFT = -911
OOB_RIGHT = -119
LOC_WITHIN = 0

_Location = namedtuple('_Location', ['position', 'where'])


class Timeboard(object):
    """Custom-built calendar.
    
    Timeboard contains a timeline of workshifts and one or more schedules 
    which endow workshifts with on-duty or off-duty status.
        
    Calculations over a timeboard are either workshift-based or interval-based. 
    Execute `get_workshift` or `get_interval` to instantiate 
    a workshift/an interval and then call their appropriate methods to 
    perform calculations. 
    
    Note that an instance of Timeboard is callable and such call is 
    a wrapper around `get_workshift` or `get_interval` method depending on the 
    arguments. 
    
    Parameters
    ----------
    base_unit_freq : str
        Base unit is a period of time that is the building block of the 
        timeboard's reference frame. Every workshift consists 
        of an integer number of base units. 
        Base unit is defined by `base_unit_freq` pandas-compatible calendar 
        frequency (i.e. 'D' for day  or '8H' for 8 hours regarded as one unit). 
        Pandas-native business  periods (i.e. 'BM') are not supported. 
    start : Timestamp-like
        A point in time referring to the first base unit of the timeboard. 
        The point in time can be located anywhere within this base unit.
        The value may be a pandas Timestamp, or a string convertible 
        to Timestamp, or a datetime object. 
    end : Timestamp-like
        Same as `start` but for the last base unit of the timeboard.
    layout : Iterable or Organizer
        Define how to mark up the timeboard into workshifts. 
        If `layout` is an Iterable, it is interpreted as a pattern of labels. 
        Each base unit becomes a workshift; the workshifts receive labels from
        the pattern. Application of `layout` pattern is repeated in cycles 
        until the end of the timeboard is reached.
        If `layout` is an Organizer, the timeboard is structured according to 
        the rules defined by the Organizer.
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
    workshift_ref : {'start' | 'end'}, optional (default 'start')
        Define what point in time will be used to represent a workshift. 
        The respective point in time will be returned by `to_timestamp()`
        method of a Workshift or by calling `get_timestamp` on a Workshift. 
        Available  options: 'start' to use the start time of the workshift, 
        'end' to use the end time. 
    default_name : str, optional
        The name for the default schedule. If not supplied, 'on_duty' 
        is used.
    default_selector : function, optional
        The selector function for the default schedule. This is 
        the function which takes one argument - label of a workshift, and 
        returns True if this is an on duty workshift, False otherwise. 
        If not supplied, the function that returns `bool(label)` is used.
    default_label : optional
        Label to initialize the timeline with. Normally, this value will be 
        overridden by `layout` unless `layout` is empty or an Organizer has 
        empty `structure` or empty patterns in `structure`. If 
        `default_label` is not specified, the timeline is initialized with NaN.
    
    Raises
    ------
    UnsupportedPeriodError (ValueError)
        If `base_unit_freq` is not supported or an Organizer attempted 
        to partition the reference frame  by a period which is not a multiple 
        of `base_unit_freq`.
    VoidIntervalError (ValueError)
        If an instantiation of a zero-duration timeboard is attempted.
    KeyError
        If `amendments` contain several references to the same workshift.
        
    Attributes
    ----------
    base_unit_freq : str
    start_time : Timestamp
        When the first workshift / base unit of the timeboard starts.
    end_time : Timestamp
        When the last workshift / base unit of the timeboard ends.
    schedules : dict of {str : _Schedule}
        The keys are names of schedules.
    default_schedule : _Schedule
    default_selector : function
        
    See also
    --------
    Organizer
        Define rule for marking up the reference frame into workshifts.
    """
    def __init__(self, base_unit_freq, start, end, layout,
                 amendments=None,
                 default_selector=None,
                 default_name=None,
                 workshift_ref='start',
                 default_label=None):
        if isinstance(layout, Organizer):
            org = layout
        elif _is_iterable(layout):
            if len(layout) == 1 and isinstance(layout[0], Organizer):
                warnings.warn("Received 'layout' as an Organizer wrapped in "
                              "a list. Probably you do not want a list here.",
                              SyntaxWarning)
            org = Organizer(marks=[], structure=[layout])
        else:
            raise TypeError("`layout` must be either an iterable "
                            "representing a pattern, "
                            "or an instance of Organizer")
        if amendments is None:
            amendments = {}
        if not hasattr(amendments, 'items'):
            raise TypeError("`amendments` do not look like a dictionary: "
                            "`items` method is needed but not found.")
        self._custom_selector = default_selector
        self._frame = _Frame(base_unit_freq, start, end)
        self._timeline = _Timeline(frame=self._frame, organizer=org,
                                   workshift_ref=workshift_ref,
                                   data=default_label)
        self._timeline.amend(amendments)
        self._base_unit_freq = base_unit_freq

        if default_name is None:
            default_name = 'on_duty'
        self._default_name = str(default_name)
        self._default_schedule = _Schedule(self._timeline, self._default_name,
                                           self.default_selector)
        self._schedules = {self._default_name : self._default_schedule}

        if _is_iterable(layout):
            org_repr = ""
            org_arg = "{!r}".format(org)
        else:
            org_name = "org_{}".format(id(org))
            repr_objects = org._repr_builder()
            org_repr = "\n".join(["{} = {}".format(k, v)
                                  for k, v in repr_objects.items()]) + "\n"
            org_arg = org_name
        self._repr = "{}Timeboard({!r}, start={!r}, end={!r}, layout={})"\
                     .format(org_repr, base_unit_freq, start, end, org_arg)


    def __repr__(self):
        return self._repr

    @property
    def compact_str(self):
        return "Timeboard of '{}': {} -> {}".format(
            self.base_unit_freq,
            self._frame[0],
            self._frame[-1])

    def __str__(self):
        return self.compact_str + "\n\n{}".format(self.to_dataframe())

    def to_dataframe(self, first_ws=None, last_ws=None):
        """Convert (a part of) timeline into pandas dataframe.

        Each workshift is represented as a row. The dataframe has the 
        following columns:

        'loc' : zero-based position of the workshift on the timeline
        'workshift' : the reference time of the workshift
        'start' : the start time of the workshift
        'end' : the start time of the workshift
        'duration' : the number of base units in the workshift
        'label' : workshift's label
        {schedule_name} : True if the workshift is on duty under this 
        schedule, False otherwise.
        
        Each schedule is presented by its own column.
        
        Parameters
        ----------
        first_ws : int >=0, optional
            The zero-based timeline position of the first workshift to be 
            included into the dataframe. By default the dataframe starts 
            with the first workshift of the timeboard.
        last_ws :  int >=0, optional
            The zero-based timeline position of the last workshift to be 
            included into the dataframe. By default the dataframe ends
            with the last workshift of the timeboard.

        Returns
        -------
        pandas.DataFrame
        """
        if first_ws is None:
            first_ws=0
        if last_ws is None:
            last_ws = len(self._timeline)-1
        assert (first_ws >=0 and last_ws >=0 and first_ws <= last_ws)
        df = self._timeline.to_dataframe(first_ws, last_ws)
        for activity, schedule in self._schedules.items():
            #TODO: refactor to use already computed duty indexes from _Schedule
            df[activity]=list(self._timeline.labels.iloc[
                              first_ws:last_ws+1].apply(
                              schedule._selector))
        return df

    @property
    def base_unit_freq(self):
        return self._base_unit_freq

    @property
    def start_time(self):
        return self._frame.start_time

    @property
    def end_time(self):
        return self._frame.end_time

    @property
    def default_selector(self):

        def _default_selector(x):
            return bool(x)

        if self._custom_selector is not None:
            return self._custom_selector
        else:
            return _default_selector

    @property
    def schedules(self):
        return self._schedules

    @property
    def default_schedule(self):
        return self._default_schedule

    def __call__(self, *args, **kwargs):
        """A wrapper of `get_workshift()` or `get_interval()`."""
        if len(args) == 1 and len(kwargs) == 0:
            try:
                return self.get_workshift(args[0])
            except OutOfBoundsError:
                raise
            except:
                pass
        try:
            return self.get_interval(*args, **kwargs)
        except:
            raise

    def _locate(self, point_in_time, by_ref=None):
        """Find workshift location by timestamp.
        
        Parameters
        ----------
        point_in_time : Timestamp-like
        by_ref : {'before' | 'after'}, optional
            If not specified, search for the workshift which contains the 
            given point in time.
            If specified, search for the workshift whose reference time is 
            either before or after the given point in time. The both options 
            accept the workshift whose reference time is equal to the point 
            in time.
        
        Returns 
        -------
        _Location 
            _Location is a namedtuple of two fields:
            position: {int >=0, None}
            where: {LOC_WITHIN, OOB_RIGHT, OOB_LEFT}
            If the workshift is found, its zero-based position on the 
            timeline is returned in `position` field and `LOC_WITHIN` constant 
            is returned in `where` field. 
            Otherwise `position` field  is set to `None` and `where` field 
            contains indication whether the point in time is located to the 
            future of all workshifts (`where=OOB_RIGHT`) or to the past 
            (`where=OOB_LEFT`)
        """
        pit_ts = get_timestamp(point_in_time)
        get_ws_pos_function = self._timeline.get_ws_position
        if by_ref == 'before':
            get_ws_pos_function = self._timeline.get_ws_pos_by_ref_before
        elif by_ref == 'after':
            get_ws_pos_function = self._timeline.get_ws_pos_by_ref_after

        try:
            loc = get_ws_pos_function(pit_ts)
            if loc < 0:
                raise RuntimeError("_Frame.get_loc returned negative {}"
                                   " for PiT {}".format(loc, point_in_time))
            return _Location(loc, LOC_WITHIN)
        except OutOfBoundsError:
            if pit_ts < self.start_time:
                return _Location(None, OOB_LEFT)
            elif pit_ts > self.end_time:
                return _Location(None, OOB_RIGHT)
            elif by_ref == 'before':
                return _Location(None, OOB_LEFT)
            elif by_ref == 'after':
                return _Location(None, OOB_RIGHT)
            else:
                raise RuntimeError("PiT {} is within frame but _Frame.get_loc"
                                   " raised KeyError".format(point_in_time))

    def _handle_out_of_bounds(self, msg=None):
        if msg is None:
            message = "Point in time is outside {}".format(self.compact_str)
        else:
            message = msg
        raise OutOfBoundsError(message)

    def _handle_void_interval(self, msg=None):
        if msg is None:
            message = "Empty interval is not allowed"
        else:
            message = msg
        raise VoidIntervalError(message)

    def get_workshift(self, point_in_time, schedule=None):
        """Get workshift by timestamp.
        
        Take a timestamp-like value and return the workshift which
        contains this timestamp.
        
        Parameters
        ----------
        point_in_time : Timestamp-like
            An object convertible to Timestamp. If it has `to_timestamp()` 
            method, then the method's return value is used. Otherwise it is a 
            string convertible to a timestamp, or a pandas Timestamp, or 
            a datetime object.
        schedule : _Schedule, optional
            Schedule to be used in calculations with the workshift unless a 
            schedule is explicitly redefined for a specific calculation. 
            By default the timeboard's default schedule is used.
        
        Returns
        -------
        Workshift
        
        Raises
        ------
        OutOfBoundsError (LookupError)
            If `point_in_time` is not within the timeboard.
            
        Notes
        -----
        An instance of Timeboard is callable. If it is called with a single 
        non-keyword argument, the call is passed to `get_workshift`. (And 
        should the call  fail, `get_interval` is tried instead.) Call 
        `get_workshift` explicitly if you want to pass additional arguments.

        See also
        --------
        timeboard.workshift.Workshift(timeboard, location: int, schedule=None)
            An alternative approach to instantiating a workshift by the 
            position (`location`) of the workshift within the timeline.

        Examples
        --------
        >>> clnd = Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> clnd.get_workshift('01 Oct 2017')
        Workshift(1) of 'D' at 2017-10-01
        
        # shortcut
        >>> clnd('01 Oct 2017')
        Workshift(1) of 'D' at 2017-10-01
        """
        if schedule is None:
            schedule = self.default_schedule
        loc = self._locate(point_in_time)
        if loc.position is None:
            return self._handle_out_of_bounds()
        else:
            return Workshift(self, loc.position, schedule)

    def get_interval(self, interval_ref=None, length=None, period=None,
                     clip_period=True, closed='11', schedule=None):
        """Create interval on the timeline.
        
        A number of techniques to define the interval can be used. They are 
        mutually exclusive. Accepted  parameters are listed below along with 
        the techniques.
        
            1. Create the interval from two points in time which refer to 
            the first and the last workshifts of the interval.
        
            Parameters
            ----------
            interval_ref : sequence of (Timestamp-like, Timestamp-like)
                Each element is an object convertible to a timestamp, such as
                a string, or a pandas Timestamp, or a datetime object.
            length : parameter must be omitted
            period : parameter must be omitted
            
            2. Create an interval of a specific length starting from a 
            workshift referred to by a point in time .
        
            Parameters
            ----------
            interval_ref : Timestamp-like
                An object convertible to a timestamp, such as
                a string, or a pandas Timestamp, or a datetime object.
            length : int (!=0)
                Number of workshifts in the interval. If `length` is positive, 
                the interval extends into the future from the workshift 
                referred to by `interval_ref`.  If `length` is negative, 
                the interval extends to the past. Both length=1 and length=-1 
                create the interval containing only the `interval_ref` 
                workshift. Zero `length` is not allowed.
            period : parameter must be omitted
        
            3. Create the interval from a calendar period identified by 
            a point in time within the period and a calendar frequency 
            of the period (i.e. 'M' for month). 
        
            The interval will contain all workshifts belonging to the 
            specified calendar period. Workshift reference time is used to 
            identify the period where the workshift belongs. Hence the 
            situation when a workshift extends over a boundary between  
            calendar periods is handled by finding out which of the periods 
            contain the workshift reference time. 
            
            If the calendar period extends beyond the timeline, `clip_period` 
            parameter is consulted. If it is True, then the calendar period is 
            clipped at the bound(s) of the timeline, meaning that only the part 
            of the period falling inside the timeline is considered. If 
            `clip_period` is False, OutOfBoundsError is raised.
            
            If the period has been clipped or the period boundary is not 
            aligned with workshifts, the start or end time of the produced 
            interval will be different from that of the period.
        
            Parameters
            ----------
            interval_ref : Timestamp-like
                An object convertible to a timestamp, such as
                a string, or a pandas Timestamp, or a datetime object.
            period : str
                A pandas-compatible frequency defining a calendar period (i.e. 
                'M' for month).
            length : parameter must be omitted
            clip_period : bool, optional (default True)
                If True, clip a calendar period at the bound(s) of the timeline.
            
            4. Create the interval from a calendar period identified by a 
            pandas Period object. 
            
            The same considerations are applied as for technique 3.
    
            Parameters
            ----------
            interval_ref : pandas.Period
            length : parameter must be omitted
            period : parameter must be omitted
            clip_period : bool, optional (default True)
                If True, clip a calendar period at the bound(s) of the timeline.
            
            5. Create the interval that spans the entire timeline.
            
            Parameters
            ----------
            interval_ref : parameter must be omitted
            length : parameter must be omitted
            period : parameter must be omitted
        
        
        Parameters valid for any option
        -------------------------------
        closed : {'11', '01', '10', '00'}, optional (default '11')
            Interpret the interval definition as closed ('11'), half-open 
            ('01' or '10'), or open ('00'). The symbol of zero indicates 
            whether the returned interval is stripped of the first or the last 
            workshift, or both.  
            
            If the interval was created by clipping a calendar period, `closed`
            is not honored for the clipped end(s). The element of `closed` 
            representing the clipped end is reset to '1'.
                  
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
            
            
        Notes
        -----
        - If you attempt to create an interval from two points in time or by 
        length, and the interval would extend beyond the timeline, 
        OutOfBoundsError is always raised. `clip_period` is effective only if
        you are creating the interval from a calendar period.
        
        - An instance of Timeboard is callable. If it is called with 
        arguments not suitable for `get_workshift` method, it will pass the 
        call to `get_interval`. To instantiate an interval this way, all 
        techniques may be used except technique 4. (An instance of Timeboard
        called with a pandas Period will return a workshift containing the 
        start time of the period because pandas Period has `to_timestamp` 
        method.)
        
        See also
        --------
        timeboard.interval.Interval(timeboard, (location1: int, location2: 
        int), schedule=None)
            The alternative approach to instantiating an interval. You will 
            need to know the positions of the first (`location1`) and the last 
            (`location2`) workshifts of the interval within the timeline.
        
        Examples
        --------
        
        >>> clnd = Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> clnd.get_interval(('02 Oct 2017', '08 Oct 2017'))
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
        
        # shortcut 
        >>> clnd(('02 Oct 2017', '08 Oct 2017'))
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
        
        >>> clnd.get_interval('02 Oct 2017', length=7)
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
        
        # shortcut
        >>> clnd('02 Oct 2017', length=7)
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

        >>> clnd.get_interval('05 Oct 2017', period='W')
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
        
        # shortcut
        >>> clnd('05 Oct 2017', period='W')
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]      
        
        >>> import pandas as pd
        >>> p = pd.Period('05 Oct 2017', freq='W')
        >>> clnd.get_interval(p)
        Interval(2, 8): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
        
        # NO shortcut!
        >>> clnd(p)
        Workshift(2) of 'D' at 2017-10-02
        
        >>> clnd.get_interval()
        Interval(0, 15): 'D' at 2017-09-30 -> 'D' at 2017-10-15 [16]
        
        # shortcut
        >>> clnd()
        Interval(0, 15): 'D' at 2017-09-30 -> 'D' at 2017-10-15 [16]
        """

        if closed not in ['00', '01', '10', '11']:
            raise ValueError("Unacceptable 'closed' parameter")
        drop_head = closed[0] == '0'
        drop_tail = closed[1] == '0'

        if schedule is None:
            schedule = self.default_schedule

        if length is None and period is None:
            try:
                locs = self._get_interval_locs_from_reference(
                    interval_ref, drop_head, drop_tail)
            except TypeError:
                try:
                    p = get_period(interval_ref, freq=None)
                except:
                    raise TypeError('Could not interpret the provided interval '
                                    'reference. Expected a sequence of two '
                                    'Timestamp-like, or a Period-like, or None.'
                                    ' Received: `{!r}`'.format(interval_ref))
                else:
                    locs = self._get_interval_locs_by_period(
                        p, None, clip_period, drop_head, drop_tail)

        elif length is not None and period is None:
            locs = self._get_interval_locs_by_length(
                interval_ref, length, drop_head, drop_tail)
        elif period is not None and length is None:
            locs = self._get_interval_locs_by_period(
                interval_ref, period, clip_period, drop_head, drop_tail)
        else:
            raise TypeError("Unacceptable combination of interval reference "
                            "and 'length' or 'period' parameters")

        if locs[0].position is None and locs[1].position is None:
            if clip_period and locs[0].where > locs[1].where:
                return self._handle_void_interval(
                    "Attempted to create reversed overlapping interval "
                    "referenced by `{}` within {}".format(interval_ref,
                                                          self.compact_str))
            else:
                raise OutOfBoundsError("Interval referenced by `{}` is "
                                       "completely outside {}".
                                       format(interval_ref, self.compact_str))
        if locs[0].position is None:
            raise OutOfBoundsError("The 1st bound of interval referenced by `{}` "
                                   "is outside {}".format(interval_ref,
                                                          self.compact_str))
        if locs[1].position is None:
            raise OutOfBoundsError("The 2nd bound of interval referenced by `{}` "
                                   "is outside {}".format(interval_ref,
                                                          self.compact_str))
        if locs[0].position > locs[1].position:
            return self._handle_void_interval(
                    "Attempted to create interval with reversed indices "
                    "({}, {}) within {}".
                    format(locs[0].position, locs[1].position, self.compact_str))

        return Interval(self, (locs[0].position, locs[1].position), schedule)

    def _get_interval_locs_from_reference(self, interval_ref,
                                          drop_head, drop_tail):
        if interval_ref is None:
            locs = [_Location(0, LOC_WITHIN),
                    _Location(len(self._timeline) - 1, LOC_WITHIN)]
        elif hasattr(interval_ref, '__getitem__') and len(interval_ref) >= 2 \
                and not isinstance(interval_ref, str):
            locs = [self._locate(interval_ref[0]),
                    self._locate(interval_ref[1])]
        else:
            raise TypeError("Could not get interval bounds from the provided "
                            "reference. Expected a sequence of two "
                            "Timestamp-like or None. Received `{!r}`".
                            format(interval_ref))
        return self._strip_interval_locs(locs, drop_head, drop_tail)

    def _get_interval_locs_by_length(self, start_ref, length,
                                     drop_head, drop_tail):
        if not isinstance(length, int):
            raise TypeError('Interval length = `{!r}`: expected integer '
                            'got {}. If you are not using length parameter, '
                            'make sure you passed interval bounds '
                            'as a tuple'.format(length, type(length)))
        if length == 0:
            return self._handle_void_interval('Interval length cannot be zero')
        loc0 = self._locate(start_ref)
        if loc0.position is None:
            return [loc0, loc0]
        indices = sorted([loc0.position,
                         loc0.position + length - int(copysign(1, length))])
        return self._strip_interval_locs(
                    [_Location(indices[0], LOC_WITHIN),
                     _Location(indices[1], LOC_WITHIN)],
                    drop_head, drop_tail)

    def _get_interval_locs_by_period(self, period_ref, period_freq,
                                     clip_period, drop_head, drop_tail):
        p = get_period(period_ref, freq=period_freq)
        locs = [self._locate(p.start_time, by_ref='after'),
                self._locate(p.end_time, by_ref='before')]
        position0 = locs[0].position
        position1 = locs[1].position
        if clip_period:
            if locs[0].where == OOB_LEFT and locs[1].where != OOB_LEFT:
                position0 = 0
                drop_head = False
            if locs[1].where == OOB_RIGHT and locs[0].where != OOB_RIGHT:
                position1 = len(self._timeline) - 1
                drop_tail = False
        return self._strip_interval_locs(
                                         [_Location(position0, locs[0].where),
                                          _Location(position1, locs[1].where)],
                                         drop_head, drop_tail)

    def _strip_interval_locs(self, locs, drop_head, drop_tail):
        result0 = locs[0].position
        result1 = locs[1].position
        if drop_head and locs[0].position is not None:
            result0 += 1
        if drop_tail and locs[1].position is not None:
            result1 -= 1
        return [_Location(result0, locs[0].where),
                _Location(result1, locs[1].where)]
