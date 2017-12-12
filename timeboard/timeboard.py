from __future__ import division
from .core import (_Frame, _Timeline, _Schedule,
                   Organizer, get_period, get_timestamp)
from .workshift import Workshift
from .interval import Interval
from .exceptions import OutOfBoundsError, VoidIntervalError
from collections import Iterable, Sequence, namedtuple
from math import copysign
import warnings

OOB_LEFT = -911
OOB_RIGHT = -119
LOC_WITHIN = 0

_Location = namedtuple('_Location', ['index', 'where'])


class Timeboard(object):
    """Your customized calendar.
    
    A Timeboard object consists of the following parts:
        - the reference frame of base units of time extending from the 
        beginning to the end of the timeboard's span;
        - the timeline of workshifts constructed upon the reference frame as 
        specified by parameters,
        - one or more schedules which endow workshifts with on-duty or 
        off-duty status.
        
    Calculations over a timeboard are either workshift-based or interval-based. 
    Execute `get_workshift` or `get_interval` to instantiate 
    a workshift/an interval and then call their appropriate methods to 
    perform calculations. 
    Note that an instance of the timeboard is callable and such call is 
    a wrapper around `get_workshift` or `get_interval` whichever will seem 
    more appropriate.. 
    
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
    defautl_selector : function, optional
        Function which takes one argument - label of a workshift. Returns 
        True if this is an on-duty workshift, returns False otherwise. Default 
        selector function returns `bool(label)`.
    workshift_ts : {'start' | 'end'}, optional (default 'start')
        Define what point in time will be used to represent a workshift. 
        The respective point in time will be returned by `to_timestamp{}`
        method of a workshift or by calling `get_timestamp` on a workshift. 
        Available  options: 'start' to use the start time of the workshift, 
        'end' to use the end time. 
    
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
    workshift_ts
    selector : function
        
    See also
    --------
    Organizer - defines rules for setting up timeline's layout
    """
    def __init__(self, base_unit_freq, start, end, layout, amendments=None,
                 default_selector=None, workshift_ts='start'):
        if isinstance(layout, Organizer):
            org = layout
        elif isinstance(layout, Sequence):
            if len(layout) == 1 and isinstance(layout[0], Organizer):
                warnings.warn("Received 'layout' as an Organizer wrapped in "
                              "a list. Probably you do not want a list here.",
                              SyntaxWarning)
            org = Organizer(split_at=[], structure=[layout])
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
        self._timeline = _Timeline(frame=self._frame)
        self._timeline.organize(org)
        self._timeline.amend(amendments)
        self._base_unit_freq = base_unit_freq
        self._workshift_ts = workshift_ts
        self._repr = "Timeboard({!r}, {!r}, {!r}, {!r})"\
                     .format(base_unit_freq, start, end, layout)

        default_schedule = _Schedule(self._timeline, '_default',
                                     self.default_selector)
        self._schedules = {'_default' : default_schedule}

    def __repr__(self):
        return self._repr

    def __str__(self):
        return "Timeboard of '{}': {} -> {}".format(
            self.base_unit_freq,
            str(get_period(self.start_time, freq=self.base_unit_freq)),
            str(get_period(self.end_time, freq=self.base_unit_freq)))

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
    def workshift_ts(self):
        return self._workshift_ts

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

    def _locate(self, point_in_time):
        """Find base unit by timestamp
        
        Parameters
        ----------
        point_in_time : Timestamp-like
        
        Returns 
        -------
        _Location 
            _Location is a namedtuple of two fields:
            index: {int >=0, None}
            where: {LOC_WITHIN, OOB_RIGHT, OOB_LEFT}
            If the base unit is found, its index in the timeline is returned
            in `index` field and `LOC_WITHIN` constant is returned in `where` 
            field. 
            If `point_in_time` is outside the timeline, `index` field 
            is set to `None` and `where` field contains indication whether 
            the point in time is in the future(`where=OOB_RIGHT`) or in the 
            past (`where=OOB_LEFT`)
            
        """
        try:
            pit_ts = get_timestamp(point_in_time)
        except:
            raise

        try:
            loc = self._timeline.frame.get_loc(pit_ts)
            if loc < 0:
                raise RuntimeError("_Frame.get_loc returned negative {}"
                                   " for PiT {}".format(loc, point_in_time))
            return _Location(loc, LOC_WITHIN)
        except KeyError:
            if pit_ts < self.start_time:
                return _Location(None, OOB_LEFT)
            elif pit_ts > self.end_time:
                return _Location(None, OOB_RIGHT)
            else:
                raise RuntimeError("PiT {} is within frame but _Frame.get_loc"
                                   " raised KeyError".format(point_in_time))

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

    def get_workshift(self, point_in_time, schedule=None):
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
        if schedule is None:
            schedule = self._schedules['_default']
        loc = self._locate(point_in_time)
        if loc.index is None:
            return self._handle_out_of_bounds()
        else:
            return Workshift(self, loc.index, schedule)

    def get_interval(self, interval_ref=None, length=None, period=None,
                     clip_period=True, closed='11', schedule=None):
        """Create interval on the timeline.
        
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
        If the calendar period extends beyond the timeline, `clip_period` 
        parameter is consulted. If it is True, then the calendar period is 
        clipped at the bound(s) of the timeline, meaning that only the part of 
        the period falling inside the timeline is considered. If 
        `clip_period` is False, OutOfBoundsError is raised.
        
        Parameters
        ----------
        interval_ref : Timestamp-like
            A string convertible to a timestamp, or a pandas Timestamp, 
            or a datetime object.
        period : str
            A pandas-compatible frequency defining a calendar period (i.e. 
            'M' for month).
        length : parameter must be omitted
        clip_period : bool, optional (default True)
            If True, clip a calendar period at the bound(s) of the timeline.
        
        - Create an interval from a pandas Period object. The same restriction 
        is applied as with the previous technique.

        Parameters
        ----------
        interval_ref : pandas.Period
        length : parameter must be omitted
        period : parameter must be omitted
        clip_period : bool, optional (default True)
            If True, clip a calendar period at the bound(s) of the timeline.
        
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
            
            
        Notes
        -----
        If you attempt to create an interval from two points in time or by 
        length, and the interval would extend beyond the timeline, 
        OutOfBoundsError is always raised. `clip_period` is effective only if
        you are creating the interval from a calendar period.
        
        If the interval was created by clipping a calendar period, `closed` 
        is not honored for the clipped end(s) (i.e. the `closed` indicator for
        the clipped end is reset to '1').
            
        See also
        --------
        timeboard.interval.Interval(timeboard, (location1, location2))
            This is the alternative, low-level approach to instantiating 
            an interval. You will need to know the absolute positions 
            of the first (`location1`) and the last (`location2`) workshifts 
            of the interval within the timeline.
        """

        if closed not in ['00', '01', '10', '11']:
            raise ValueError("Unacceptable 'closed' parameter")
        drop_head = closed[0] == '0'
        drop_tail = closed[1] == '0'

        if schedule is None:
            schedule = self._schedules['_default']

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
                                    ' Received: {}'.format(interval_ref))
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

        if locs[0].index is None and locs[1].index is None:
            if clip_period and locs[0].where > locs[1].where:
                return self._handle_void_interval(
                    "Attempted to create reversed overlapping interval "
                    "referenced by '{}' within {}".format(interval_ref, self))
            else:
                raise OutOfBoundsError("Interval referenced by '{}' is "
                                       "completely outside {}".
                                       format(interval_ref, self))
        if locs[0].index is None:
            raise OutOfBoundsError("The 1st bound of interval referenced by '{}' "
                                   "is outside {}".format(interval_ref, self))
        if locs[1].index is None:
            raise OutOfBoundsError("The 2nd bound of interval referenced by '{}' "
                                   "is outside {}".format(interval_ref, self))
        if locs[0].index > locs[1].index:
            return self._handle_void_interval(
                    "Attempted to create interval with reversed indices "
                    "({}, {}) within {}".
                    format(locs[0].index, locs[1].index, self))

        return Interval(self, (locs[0].index, locs[1].index), schedule)

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
                            "Timestamp-like or None. Received {}".
                            format(interval_ref))
        return self._strip_interval_locs(locs, drop_head, drop_tail)

    def _get_interval_locs_by_length(self, start_ref, length,
                                     drop_head, drop_tail):
        if not isinstance(length, int):
            raise TypeError('Interval length = {}: expected integer '
                            'got {}. If you are not using length parameter, '
                            'make sure you passed interval bounds '
                            'as a tuple'.format(length, type(length)))
        if length == 0:
            return self._handle_void_interval('Interval length cannot be zero')
        loc0 = self._locate(start_ref)
        if loc0.index is None:
            return [loc0, loc0]
        indices = sorted([loc0.index,
                         loc0.index + length - int(copysign(1, length))])
        return self._strip_interval_locs(
                    [_Location(indices[0], LOC_WITHIN),
                     _Location(indices[1], LOC_WITHIN)],
                    drop_head, drop_tail)

    def _get_interval_locs_by_period(self, period_ref, period_freq,
                                     clip_period, drop_head, drop_tail):
        p = get_period(period_ref, freq=period_freq)
        locs = [self._locate(p.start_time), self._locate(p.end_time)]
        result0 = locs[0].index
        result1 = locs[1].index
        if clip_period:
            if locs[0].where == OOB_LEFT and locs[1].where != OOB_LEFT:
                result0 = 0
                drop_head = False
            if locs[1].where == OOB_RIGHT and locs[0].where != OOB_RIGHT:
                result1 = len(self._timeline) - 1
                drop_tail = False
        return self._strip_interval_locs(
                                         [_Location(result0, locs[0].where),
                                          _Location(result1, locs[1].where)],
                                         drop_head, drop_tail)

    def _strip_interval_locs(self, locs, drop_head, drop_tail):
        result0 = locs[0].index
        result1 = locs[1].index
        if drop_head and locs[0].index is not None:
            result0 += 1
        if drop_tail and locs[1].index is not None:
            result1 -= 1
        return [_Location(result0, locs[0].where),
                _Location(result1, locs[1].where)]
