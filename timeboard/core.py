from __future__ import division
from .exceptions import (OutOfBoundsError,
                         VoidIntervalError,
                         UnsupportedPeriodError)
from .when import (from_start_of_each,
                   nth_weekday_of_month,
                   from_easter_western, from_easter_orthodox)
import pandas as pd
import numpy as np
from numpy import nonzero, arange
from itertools import cycle, dropwhile
from collections import Iterable, OrderedDict
import re
import six
#import timeit

SMALLEST_TIMEDELTA = pd.Timedelta(1, unit='s')

def get_timestamp(arg):
    try:
        return arg.to_timestamp()
    except AttributeError:
        return pd.Timestamp(arg)

def get_period(period_ref, freq=None, honor_period=True):
    if isinstance(period_ref, pd.Period) and honor_period:
        return period_ref
    elif freq is None:
        raise TypeError("Expected a frequency for period_ref, got None")
    else:
        return pd.Period(get_timestamp(period_ref), freq=freq)

def get_freq_delta(freq):
    # Starting on 01 Jul 2016 gives the longest timedeltas for freq  based
    # on 'M', 'Q', 'A'
    pi = pd.PeriodIndex(start='01 Jul 2016', freq=freq, periods=2)
    return pi[1].start_time - pi[0].start_time

def _is_iterable(obj):
    return (isinstance(obj, Iterable) and
            not isinstance(obj, six.string_types))

def _to_iterable(x):
    if x is None:
        return x
    if _is_iterable(x):
        return x
    else:
        return [x]

def _skiperator(values, skip=0):
    """Build a skip-and-cycle generator
    
    Return a generator that cycles through `values` 
    after having skipped a number of steps at the beginning.
    
    Parameters
    ----------
    values : iterable
    skip : int, optional (default 0) 
        Number of steps to skip at the beginning.

    Notes
    -----
    After the skip we start to yield results while iterating through the 
    rest of `values`. All the following cycles are iterations through 
    the whole of `values` yielding all elements without skipping.
        
    Returns
    -------
    generator
    """
    def make_counter():
        nonlocal_vars = {'iters': 0}

        def _counter(_):
            flag = nonlocal_vars['iters'] < skip
            nonlocal_vars['iters'] += 1
            return flag

        return _counter

    pattern = values
    counter = make_counter()
    return dropwhile(counter, cycle(pattern))


def _check_groupby_freq(base_unit_freq, group_by_freq):
    """Check if frame's base unit may be grouped in periods of given frequency.
    
    Pass the value of `each` attribute from some Marker as `group_by_freq`
    to check if it can be used with the given `base_unit_freq`, 
    meaning that partitioning of a timeline will not result in a situation 
    when a base unit belongs to more than one span at the same time. 
    
    An example of such ambiguous partitioning is when `base_unit_freq='W'` and
    `marker.each='M'`. Most likely there will be a base unit (week) that falls 
    into two spans (months) simultaneously.
    
    Parameters
    ----------
    base_unit_freq : str
        pandas-compatible period frequency for smaller periods.
    group_by_freq : str
        pandas-compatible period frequency for periods used as groups of the 
        smaller periods.
    
    Returns
    -------
    True if `group_by_freq` can be used for grouping, False otherwise.
    """
    if bool(
        pd.tseries.frequencies.is_subperiod(base_unit_freq, group_by_freq)
        # Some combinations of arguments result in is_subperiod function
        # returning nothing (NoneType)
        ):
        return True
    else:
        # is_subperiod does not support frequency multiplicators,
        # i.e. (D,4D) or (2D,4D). So we will handle this manually.
        try:
            get_freq_delta(group_by_freq)  # make sure this is a valid freq
        except ValueError:
            return False
        bu_match = re.match(r"(^\d*)([A-Z-]+)", base_unit_freq)
        gb_match = re.match(r"(^\d*)([A-Z-]+)", group_by_freq)
        if bu_match and gb_match:
            if bu_match.group(1) == '':
                bu_freq_factor = 1
            else:
                bu_freq_factor = int(bu_match.group(1))
            if gb_match.group(1) == '':
                gb_freq_factor = 1
            else:
                gb_freq_factor = int(gb_match.group(1))
            if bu_freq_factor == 1 and gb_freq_factor == 1:
                # there is no freq multipliers, hence we drop the case
                return False
            bu_freq_denomination = bu_match.group(2)
            gb_freq_denomination = gb_match.group(2)

            if bu_freq_denomination == gb_freq_denomination:
                return gb_freq_factor % bu_freq_factor == 0
            elif bu_freq_factor == 1:
                return _check_groupby_freq(bu_freq_denomination,
                                           gb_freq_denomination)
            else:
                # there can be the possibility of valid splitting
                # but it depends on the alignment of the frame's start_time
                # which we do not check here
                # For example '12H' frame can be partitioned by 'D' only if it
                # starts at 00:00 or 12:00;
                # see more examples in test_splits::TestMultipliedFreqSplitBy
                return False
        else:
            return False


class _Frame(pd.PeriodIndex):
    """Timeboard's reference frame.
    
    Frame is an ordered sequence of uniform periods of time (called base 
    units) which define the extent of the timeboard and the smallest duration 
    of anything happening within the timeboard. Workshifts are aligned 
    with base units; each workshift comprises one or more base units. 
    
    Parameters
    ----------
    base_unit_freq : str
        Pandas-compatible calendar frequency (i.e. 'D' for day or '8H' for 
        8 hours regarded as one unit) defining the constituent period of 
        the frame. Pandas-native business periods (i.e. 'BM') are not supported. 
    start : Timestamp-like
        A pandas Timestamp, a datetime object, or a string convertible to 
        Timestamp - a point in time defining the first element of the frame 
        (it may be found anywhere with this element).
    end : Timestamp-like
        Same as start but for the last element of the frame.
    
    Raises
    ------
    VoidIntervalError (ValueError)
        If the time of `start` precedes the time of `end`.
    
    Attributes
    ----------
    start_time : Timestamp
        The start time of the first element of the frame.
    end_time : Timestamp
        The end time of the last element of the frame.
        
    Notes
    -----
    If the timestamp of `start` and that of `end` refer to the same base unit, 
    then the frame will contain only one element, this base unit.
    Frame must contain at least one element. Empty frames are not allowed. 
    """
    def __new__(cls, base_unit_freq=None, start=None, end=None, **kwargs):
        if base_unit_freq is not None :
            _freq = base_unit_freq
        else:
            _freq = kwargs['freq']

        frame = super(_Frame, cls).__new__(cls, start=start, end=end,
                                           freq=_freq)
        if len(frame) == 0:
            raise VoidIntervalError("Empty frame not allowed "
                "(make sure the start time precedes the end time)")
        if frame[0].start_time > frame[-1].start_time:
            raise RuntimeError("Frame is invalid: starts on {}, ends on {}. "
                               "Make sure that your time range is "
                               "supported (22 Sep 1677 seems to be the "
                               "earliest possible day)"
                               ".".format(frame[0].start_time,
                                          frame[-1].start_time))
        frame._base_unit_freq = _freq
        frame._start_times = frame.to_timestamp(how='start')
        return frame

    @property
    def start_time(self):
        return self[0].start_time

    @property
    def end_time(self):
        return self[-1].end_time

    @property
    def start_times(self):
        return self._start_times

    def _locate_subframes(self, span_first, span_last, points_in_time):
        """
        Takes a part of the frame (a "span") in order to partition it into 
        subframes at specified points in time. 
        
        Parameters
        ----------
        span_first : int>=0
            Position of the first base unit of the span in the frame.
        span_last : int>=0
            Position of the last base unit of the span in the frame.
        points_in_time : Iterable of Timestamp-like 
            List of points in time referring to frame's elements that will 
            become the first elements of subframes.
            
        Returns
        -------
        list of tuples containing indices of subframe boundaries :    
            [ (subfr0_start, subfr0_end), ... , (subfrN_start, subfr0_end) ]

        
        Notes
        -----
        Any elements of `points_in_time` that do not define a start of 
        a subframe within the span are ignored.
        These are:
          - points referring to a base unit already designated as the 
          first element of a subframe,
          - points referring to `span_first` base unit,
          - points outside the span.
        If no usable points are found or `points_in_time` is empty,
        [(span_start, span_end)] is returned. 
        """
        #timer0 = timeit.default_timer()
        self.check_span(span_first, span_last)
        # TODO: SPEED UP.
        # This computation takes 0.3s for 100 Years Standard Week 8x5
        #loc_list = [self.get_loc(t, 0) for t in points_in_time]
        split_positions = self.get_loc_vectorized(points_in_time,
                                                  span_first=span_first,
                                                  span_last=span_last)
        #timer1 = timeit.default_timer()
        # split_positions = [int(x)
        #                    for x in loc_list if span_first < x <= span_last]
        #timer2 = timeit.default_timer()
        split_positions = sorted(list(set(split_positions)))
        #timer3 = timeit.default_timer()

        start_positions = split_positions[:]
        start_positions.insert(0, span_first)
        end_positions = [x-1 for x in split_positions]
        end_positions.append(span_last)
        #timer4 = timeit.default_timer()
        # print "_locate_subframe timers:\n\t1: {:.5f}\n\t2: {:.5f}\n\t3: {:.5f}"\
        #       "\n\t4: {:.5f}".format(timer1-timer0, timer2-timer1,
        #                              timer3-timer2, timer4-timer3)

        return zip(start_positions, end_positions)

    def check_span(self, span_first, span_last):
        try:
            _ = self[span_first]
            _ = self[span_last]
        except IndexError:
            raise OutOfBoundsError("Span ({}, {}) not within frame"
                                   ".".format(span_first, span_last))
        except ValueError:
            raise TypeError("Expected integer indices, received "
                            "`{}` and `{}`".format(type(span_first),
                                                   type(span_last)))
        if span_first < 0 or span_last < 0:
            raise OutOfBoundsError("Span boundaries must be non-negative")
        if span_first > span_last:
            raise VoidIntervalError("Span cannot be empty")

        return True

    def get_loc(self, timestamp, not_in_range=None, *kwargs):
        if timestamp > self.end_time or timestamp < self.start_time:
            if not_in_range is None:
                raise KeyError("Timestamp {} is out of bounds")
            else:
                return not_in_range
        return int(np.searchsorted(self.start_times, timestamp, side='right')
                   - 1)

    def get_loc_vectorized(self, timestamps, not_in_range=0, span_first=None,
                           span_last=None):
        start_times = self.start_times.append(
            pd.DatetimeIndex([self.start_times[-1] + SMALLEST_TIMEDELTA]))
        if span_first is None:
            span_first = 0
        if span_last is None:
            span_last = len(self)-1
        arr = np.searchsorted(start_times,
                              np.array(timestamps, dtype='datetime64[ns]'),
                              side='right')-1
        # result = np.where((arr>span_first) & (arr<=span_last),
        #                   arr, [not_in_range])
        result = arr[np.nonzero((arr>span_first) & (arr<=span_last))[0]]
        return result

    def _create_subframes(self, span_first, span_last, points_in_time):
        """ Wrapper around `_locate_subframes`.
        
        Transform returned value of `_locate_subframes` into a list of
         `_Subframe` objects.
         
        Parameters
        ----------
        span_first : int>=0
            Position of the first base unit of the span in the frame.
        span_last : int>=0
            Position of the last base unit of the span in the frame.
        points_in_time : Iterable of Timestamp-like 
            List of points in time referring to frame's elements that will 
            become the first elements of subframes.
            
        Returns
        -------
        list of _Subframe
        
        See also
        --------
        _locate_subframes
        """
        subframe_boundaries = self._locate_subframes(span_first,
                                                     span_last,
                                                     points_in_time)
        subframes = [_Subframe(first, last, 0, 0)
                     for first, last in subframe_boundaries]
        if not subframes:
            subframes = [_Subframe(span_first, span_last, 0, 0)]
        return subframes

    def partition_with_marker(self, span_first, span_last, marker):
        """Partition the (part of) frame on the marks produced by `Marker`.
        
        Parameters
        ----------
        span_first : int>=0
            Position of the base unit which begins the part of the  frame  
            to be partitioned.
        span_last : int>=0
            Position of the base unit which ends the part of the  frame  
            to be partitioned.
        marker : Marker
        
        Raises
        ------
        UnsupportedPeriodError (ValueError)
            If `marker` uses a period which is not guaranteed to be a 
            multiple of frame's `base_unit_freq` aligned with boundaries of
            base units.
        
        Returns
        -------
        list of _Subframe
        
        Notes
        -----
        The first or the last of the subframes may come out as incomplete 
        calendar periods since the span may start or end in the middle of a 
        calendar period. The number of base units in the first or the last 
        calendar periods which fall outside the span is stored in `skip_left`
        attribute of the first subframe or in `skip_right` attribute of 
        the last subframe, respectively.
        
        For example, if `base_unit_freq`='D', and the span contains the days
        from 01 Jan until 31 Jan 2017, and `marker.each`='W', the first 
        subframe will contain only one day 01 Jan, Sunday. 
        The first six days of this week (26-31 Dec) are outside the span. 
        The number of such fell out days (6) is recorded in subframe's 
        `skip_left` attribute. 
        
        Analogously, the last subframe of the span will contain only two days: 
        Mon 30 Jan and Tue 31 Jan. The rest five days of this week fall out of
        the span. This is recorded in `skip_right` attribute which is set, 
        in this subframe, to 5. All subframes in between represent a full week
        each, and their `skip_left` and `skip_right` attributes are zeroed. 
        """
        if not _check_groupby_freq(self._base_unit_freq, marker.each):
            raise UnsupportedPeriodError('Ambiguous organizing: '
                                         '{} is not a subperiod of {}'
                                         .format(self._base_unit_freq,
                                                 marker.each))
        self.check_span(span_first, span_last)
        span_start_ts = self[span_first].start_time
        span_end_ts = self[span_last].end_time
        left_dangle_undefined = False
        right_dangle_undefined = False

        at_points = pd.DatetimeIndex([])
        if marker.at:
            envelope_margin = 1
            envelope_start_ts = span_start_ts - \
                                envelope_margin * get_freq_delta(marker.each)
            envelope_end_ts = span_end_ts + \
                              envelope_margin * get_freq_delta(marker.each)
            stencil = _Frame(base_unit_freq=marker.each,
                             start=envelope_start_ts,
                             end=envelope_end_ts)

            for kwargs in marker.at:
                at_points = at_points.append(
                                 marker.how(stencil,
                                            normalize_by=self._base_unit_freq,
                                            **kwargs)
                            )
            at_points = pd.DatetimeIndex(np.sort(at_points))
            at_points = at_points[
                max([0,np.searchsorted(at_points,
                                       span_start_ts,
                                       side='right') - 1]):
                min([len(at_points),
                    np.searchsorted(at_points, span_end_ts) + 1])]

            if len(at_points) > 0:
                left_stencil_bound = min([at_points[0], span_start_ts])
                left_dangle_undefined = at_points[0] > span_start_ts
                right_stencil_bound = max([span_end_ts,
                                          at_points[-1] - SMALLEST_TIMEDELTA])
                right_dangle_undefined = at_points[-1] < span_end_ts
                split_points = at_points
            else:
                return [_Subframe(span_first, span_last, -1, -1)]

        else:
            stencil = _Frame(base_unit_freq=marker.each,
                             start=span_start_ts,
                             end=span_end_ts)
            left_stencil_bound = stencil[0].start_time
            right_stencil_bound = stencil[-1].end_time
            split_points = stencil.to_timestamp(how='start')

        if left_dangle_undefined:
            skipped_units_before = -1
        elif left_stencil_bound < span_start_ts:
            left_dangle = pd.PeriodIndex(freq=self._base_unit_freq,
                                         start=left_stencil_bound,
                                         end=span_start_ts)
            skipped_units_before = len(left_dangle.
                                       difference(self[span_first:]))
        else:
            skipped_units_before = 0

        if right_dangle_undefined:
            skipped_units_after = -1
        elif right_stencil_bound > span_end_ts:
            right_dangle = pd.PeriodIndex(freq=self._base_unit_freq,
                                          start=self[span_last].start_time,
                                          end=right_stencil_bound)
            skipped_units_after = len(right_dangle.
                                      difference(self[:span_last + 1]))
        else:
            skipped_units_after = 0
        subframes = self._create_subframes(span_first, span_last, split_points)
        subframes[0].skip_left = skipped_units_before
        subframes[-1].skip_right = skipped_units_after
        return subframes

    def partition_at_marks(self, span_first, span_last, marks):
        """Partition the (part of) frame at specified points in time.
        
        Take a part of the frame (a "span") and partition it into 
        subframes starting on the base units referred to by  
        points in time listed in `marks`.

        Parameters
        ----------
        span_first : int>=0
            Position of the base unit which begins the part of the  frame  
            to be partitioned.
        span_last : int>=0
            Position of the base unit which ends the part of the  frame  
            to be partitioned.
        marks: Iterable of Timestamp-like 
            List of points in time referring to base units that will 
            become the first elements of subframes. A point in time may fall 
            anywhere within the base unit.

        Returns
        -------
        list of _Subframe
        
        Notes
        -----
        Any elements of `marks` that do not define a start of 
        a subframe within the span are ignored.
        These are:
          - points referring to a base unit already designated as the 
          first element of a subframe,
          - points referring to `span_first` base unit,
          - points outside the span.
        If no usable points are found or `points_in_time` is empty,
        [(span_start, span_end)] is returned. 
        """
        return self._create_subframes(span_first, span_last,
                                      [get_timestamp(m) for m in marks])


class _Subframe:
    """Container class defining a subframe within some frame.
    
    Parameters
    ----------
    first : int 
        Position of the first base unit of subframe within the frame.
    last : int    
        Position of the last base unit of subframe within the frame.
    skip_left : int >=0 or -1
        Number of steps to skip if a pattern of labels is applied to  
        this subframe in 'forward' direction (left to right). 
        If this number could not be calculated `skip_left` equals negative one.
    skip_right : int >=0 or -1
        Number of steps to skip if a pattern of labels is applied to 
        this subframe in 'reverse' direction (from right to left). 
        If this number could not be calculated, `skip_right` equals negative 
        one.           
    
    Attributes
    ----------
    Same as parameters. The attributes are mutable.
    """
    def __init__(self, first, last, skip_left=0, skip_right=0):
        self.first = first
        self.last = last
        self.skip_left = skip_left
        self.skip_right = skip_right

    def __repr__(self):
        return "{}({},{},{},{})".format(self.__class__, self.first, self.last,
                                        self.skip_left, self.skip_right)


class _Timeline(object):
    """Timeline organizes the frame into labeled workshifts.
    
    Parameters
    ----------
    frame : _Frame
    organizer : Organizer, optional
        Rules defining how to mark up the frame into workshifts and set their 
        labels.
    data : optional
        Labels to initialize the timeline (a single value or an iterable 
        for the full length of the timeline).By default the timeline is 
        initialized with NaN. This parameter is only useful when 
        `organizer` is not given.
        
    Raises
    ------
    UnsupportedPeriodError (ValueError)
        If `base_unit_freq` is not supported or Organizer required to 
        partition the frame in periods whose frequency is not a multiple of 
        `base_unit_freq`.
    VoidIntervalError (ValueError)
        If an instantiation of an empty timeline is attempted.
        
    Attributes
    ----------
    frame : _Frame
        The frame upon which the timeline is built.
    start_time : Timestamp
        When the first workshift starts.
    end_time : Timestamp
        When the last workshift ends.
    """
    def __init__(self, frame, organizer=None, workshift_ref=None, data=None):
        self._frame = frame
        self._frameband = pd.Series(index=frame, data=arange(len(frame)))
        self._wsband = pd.Series(index=arange(len(frame)), data=data)
        if organizer is not None:
            self._organize(organizer)
        if workshift_ref is None:
            self._workshift_ref = 'start'
        else:
            self._workshift_ref = workshift_ref

    @property
    def frame(self):
        return self._frame

    @property
    def start_time(self):
        return self._frame.start_time

    @property
    def end_time(self):
        return self._frame.end_time

    def __len__(self):
        return len(self._wsband)

    def __getitem__(self, n):
        return self._wsband.iloc[n]

    def _get_ws_first_baseunit(self, n):
        return self._wsband.index[n]

    def _get_ws_last_baseunit(self, n):
        # first check if the workshift exists
        try:
            self._wsband.iloc[n]
        except:
            raise
        last_base_unit = len(self._frameband) - 1
        try:
            last_base_unit = self._wsband.index[n+1]-1
        except IndexError:
            pass
        return last_base_unit

    def get_ws_start_time(self, n):
        """The start time of the n-th workshift.
        
        Parameters
        ----------
        n : int
            Zero-based sequence number of a workshift on the timeline.
            
        Returns
        -------
        Timestamp
        """
        return self._frameband.index[self._get_ws_first_baseunit(n)].start_time

    def get_ws_end_time(self, n):
        """The end time of the n-th workshift.
        
        Parameters
        ----------
        n : int
            Zero-based sequence number of a workshift on the timeline.
            
        Returns
        -------
        Timestamp
        """
        return self._frameband.index[self._get_ws_last_baseunit(n)].end_time

    def get_ws_ref_time(self, n):
        """The reference time of the n-th workshift.
        
        Calculated as defined by timeboard's `workshift_ref` attribute.

        Parameters
        ----------
        n : int
            Zero-based sequence number of a workshift on the timeline.

        Returns
        -------
        Timestamp
        """
        if self._workshift_ref == 'end' :
            return self.get_ws_end_time(n)
        else:
            return self.get_ws_start_time(n)

    def get_ws_duration(self, n):
        """The duration of the n-th workshift counted in base units.
        
        Parameters
        ----------
        n : int
            Zero-based sequence number of a workshift on the timeline.
            
        Returns
        -------
        int >0
        """
        return self._get_ws_last_baseunit(n) - \
               self._get_ws_first_baseunit(n) + 1

    def get_ws_position(self, point_in_time):
        """Get position of the workshift which contains the given point in time.
        
        Parameters
        ----------
        point_in_time : Timestamp-like
            
        Returns
        -------
        int >=0
            Zero-based sequence number of a workshift on the timeline.
            
        Raises
        ------
        OutOfBoundsError
            If the point in time is not within the timeline.
        """
        try:
            base_unit = self.frame.get_loc(get_timestamp(point_in_time))
        except KeyError:
            raise OutOfBoundsError("Point in time {} is not within the "
                                   "timeline".format(point_in_time))
        ws_idx = self._frameband.iloc[base_unit]
        return self._wsband.index.get_loc(ws_idx)

    def get_ws_pos_by_ref_after(self, point_in_time):
        """Find the workshift with reference time on or after the point in time.
        
        If there is no workshift whose reference time is exactly equal 
        to the given point in time, return the position of the earliest 
        workshift whose reference time is in the future of the point in time.
        
        Parameters
        ----------
        point_in_time : Timestamp-like

        Returns
        -------
        int >=0
            Zero-based sequence number of a workshift on the timeline.

        Raises
        ------
        OutOfBoundsError
            If the point in time is not within the timeline or there is no 
            workshift whose reference time is on or after the point in time.
        """

        point_in_time = get_timestamp(point_in_time)
        candidate = self.get_ws_position(point_in_time)
        while True:
            try:
                ref_time = self.get_ws_ref_time(candidate)
            except IndexError:
                raise OutOfBoundsError("No workshift with reference time "
                                       "after {}".format(point_in_time))
            if ref_time >= point_in_time:
                break
            candidate += 1

        return candidate

    def get_ws_pos_by_ref_before(self, point_in_time):
        """Find the workshift with reference time on or before the point in time.

        If there is no workshift whose reference time is exactly equal 
        to the given point in time, return the position of the latest 
        workshift whose reference time is in the past of the point in time.

        Parameters
        ----------
        point_in_time : Timestamp-like

        Returns
        -------
        int >=0
            Zero-based sequence number of a workshift on the timeline.

        Raises
        ------
        OutOfBoundsError
            If the point in time is not within the timeline or there is no 
            workshift whose reference time is on or before the point in time.
        """
        point_in_time = get_timestamp(point_in_time)
        candidate = self.get_ws_position(point_in_time)
        while True:
            try:
                ref_time = self.get_ws_ref_time(candidate)
            except IndexError:
                raise OutOfBoundsError("No workshift with reference time "
                                       "before {}".format(point_in_time))
            if ref_time <= point_in_time:
                break
            if candidate <=0:
                raise OutOfBoundsError("No workshift with reference time "
                                       "before {}".format(point_in_time))
            candidate -= 1

        return candidate


    @property
    def labels(self):
        return self._wsband

    def reset(self, value=pd.np.nan):
        """Set all workshift labels on the timeline to the specified value.
        
        Parameters
        ----------
        value : optional (default NaN) 
        
        Returns
        -------
        None
        
        Note
        ----
        Nothing is returned; the timeline is modified in-place.

        """
        self._wsband.iloc[:] = value

    def amend(self, amendments, not_in_range='ignore'):
        """
        Set labels for specified workshifts overriding any values already set.
        
        Parameters
        ----------
        amendments : dictionary-like 
            The keys of `amendments` are Timestamp-like points in time 
            used to identify workshifts (the point in time may be located 
            anywhere within the workshift). The values of `amendments` are 
            labels to be set for the corresponding workshifts. 

                            
        Other parameters
        ----------------
        not_in_range : optional (default 'ignore')
            See `Raises` section.
        
        Returns
        -------
        None
        
        Raises
        ------
        KeyError
            If there are several keys in `amendments` which refer to the same 
            workshift (the final label would be unpredictable).
        OutOfBoundsError (LookupError)
            If there is a key in `amendments` referring outside the timeline
            and `not_in_range` parameter value is anything but 'ignore'.

        Note
        ----
        Nothing is returned; the timeline is modified in-place.
        """
        amendments_located = {}
        for (point_in_time, value) in amendments.items():
            try:
                loc = self.get_ws_position(point_in_time)
            except OutOfBoundsError:
                if not_in_range == 'raise':
                    raise OutOfBoundsError('Amendment {} is outside the '
                                           'timeboard'.format(point_in_time))
                else:
                    continue
            if loc in amendments_located:
                raise KeyError("Amendments key {!r} is a duplicate reference "
                               "to workshift {}".format(point_in_time, loc))
            amendments_located[loc] = value

        self._wsband.iloc[list(amendments_located.keys())] = \
            list(amendments_located.values())

    def _apply_pattern(self, pattern, subframe):
        """Set workshift labels from a pattern.
        
        Pattern application is repeated in cycles until the end of the subframe 
        is reached. If `subframe.skip_left`>0, then the respective number of
        idle iterations through pattern is done before a label is set for the 
        first workshift of the subframe. The value of `subframe.skip_right` 
        is currently ignored (reserved for future support of pattern 
        application done in reverse).

        Parameters
        ----------
        pattern : Iterable of labels
        subframe : Subframe
         
        Returns
        -------
        None
        
        Note
        ----
        Nothing is returned; the timeline is modified in-place.
        """
        # TODO: support both directions (set direction in Organizer?)
        if not pattern:
            raise IndexError("Received empty pattern for {}".format(subframe))
        if subframe.skip_left<0:
            raise OutOfBoundsError("Attemted to apply forward pattern to {}, "
                                   "where left dangle could not be "
                                   "calculated".format(subframe))
        pattern_iterator = _skiperator(pattern,
                                       skip=subframe.skip_left)
        self._wsband.loc[subframe.first: subframe.last] = [
            next(pattern_iterator)
            for i in range(subframe.first, subframe.last+1)
        ]

        # THIS VERSION IS 100 TIMES SLOWER!!!
        # for i in range(subframe.first, subframe.last+1):
        #     try:
        #         self.iloc[i] = next(pattern_iterator)
        #     except StopIteration:
        #         raise IndexError('Timeline pattern exhausted since {}'.format(i))

    def _organize(self, organizer, span_first=None, span_last=None):
        """Mark up the frame to create workshifts.
        
        Partition the specified span of the frame into workshifts and set 
        workshift labels as prescribed by `organizer`.

        Parameters
        ----------
        organizer : Organizer 
        span_first : int>=0, optional
            Index of the first base unit of the span of the frame. 
            By  default this is the first base unit of the frame.
        span_last : int>=0, optional
            Index of the last base unit of the span of the frame.. 
            By default this is the last base unit of the frame.
            
        Returns
        -------
        None
        
        Note
        ----
        Nothing is returned; the timeline is modified in-place.
        """
        if span_first is None:
            span_first = 0
        if span_last is None:
            span_last = len(self) - 1
        subframe_seq = []
        #timer0 = timeit.default_timer()
        if organizer.marker is not None:
            subframe_seq = self.frame.partition_with_marker(span_first, span_last,
                                                            organizer.marker)
        if organizer.marks is not None:
            subframe_seq = self.frame.partition_at_marks(span_first, span_last,
                                                         organizer.marks)
        #timer1 = timeit.default_timer()
        #timer2 = None
        # TODO: SPEED UP.
        # This loop takes 0.7s for 100 Years Standard Week 8x5
        for subframe, layout in zip(subframe_seq,
                                    cycle(organizer.structure)):
            #if timer2 is None: timer2 = timeit.default_timer()

            if isinstance(layout, Organizer):
                self._organize(layout, subframe.first, subframe.last)
            elif _is_iterable(layout):
                self._apply_pattern(layout, subframe)
            else:
                # make compound workshift from the subframe, use layout as label
                self._wsband.loc[subframe.first] = layout
                self._wsband.drop(index=arange(subframe.first+1,
                                               subframe.last+1), inplace=True)
                self._frameband.iloc[subframe.first:
                                     subframe.last+1] = subframe.first
        # timer3 = timeit.default_timer()
        # print "_organize ({},{})\n\tsplit: {:.5f}\n\tstructure init: {:.5f}" \
        #     "\n\tstructure run: {:.5f}".format(span_first, span_last,
        #                     timer1-timer0, timer2-timer1, timer3-timer2)

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
        
        Parameters
        ----------
        first_ws : int >=0, optional
            The zero-based timeline position of the first workshift to be 
            included into the dataframe. By default the dataframe starts 
            with the first workshift of the timeline.
        last_ws :  int >=0, optional
            The zero-based timeline position of the last workshift to be 
            included into the dataframe. By default the dataframe ends
            with the last workshift of the timeline.
        
        Returns
        -------
        pandas.DataFrame
        """
        if first_ws is None:
            first_ws=0
        if last_ws is None:
            last_ws = len(self._wsband)-1
        assert (first_ws >=0 and last_ws >=0 and first_ws <= last_ws)
        if last_ws == len(self._wsband)-1 :
            ws_bounds = np.concatenate((np.array(self._wsband.index[first_ws:]),
                                      [len(self.frame)]))
        else:
            ws_bounds = np.array(self._wsband.index[first_ws: last_ws+2])
        durations = [ws_bounds[i+1] - ws_bounds[i]
                     for i in range(len(ws_bounds)-1)]
        start_times = self.frame[ws_bounds[:-1]].to_timestamp(how='start')
        end_times = self.frame[ws_bounds[1:]-1].to_timestamp(how='end')
        if self._workshift_ref == 'end':
            ref_times = end_times
        else:
            ref_times = start_times
        data = {'loc' : range(first_ws, last_ws+1),
                'workshift' : ref_times,
                'start' : start_times,
                'end' : end_times,
                'duration' : durations,
                'label' : np.array(self.labels.iloc[first_ws:last_ws+1]),
                }
        return pd.DataFrame(data=data,
                            columns=['loc','workshift', 'start',
                                     'duration', 'end', 'label']
                            ).set_index('loc')

class _Schedule(object):
    """Duty schedule of workshifts.

    For a given timeline, define the duty status of 
    the workshifts by applying a selector function to workshift's labels. 

    Parameters
    ----------
    timeline : _Timeline
    name : str
        A descriptive name for the schedule.
    selector : function
        Function taking one argument (workshift's label) and returning True 
        if the workshift with this label is on duty, and False if it is off 
        duty.

    Attributes
    ----------
    name : str
    index : numpy ndarray
        Ascending list of all schedule's workshift positions on the timeline.
    on_duty_index : numpy ndarray
        Ascending list of schedule's on-duty workshift positions on the 
        timeline.
    off_duty_index : numpy ndarray
        Ascending list of schedule's off-duty workshift positions on the 
        timeline.

    Examples
    --------
    If a timeline consists of four workshifts, and the schedule's selector 
    defines workshifts 0 and 2 as on duty, and the rest as off duty, 
    the schedules's attributes are  as follows::
        index = np.array([0, 1, 2, 3])
        on_duty_index = np.array([0, 2])
        off_duty_index = np.array([1, 3])
    """

    def __init__(self, timeline, name, selector):
        self._timeline = timeline
        self._name = str(name)
        self._selector = selector

        on_duty_bool_index = self._timeline.labels.apply(self._selector)
        self._on_duty_index = nonzero(on_duty_bool_index)[0]
        self._off_duty_index = nonzero(~on_duty_bool_index)[0]

    @property
    def name(self):
        return self._name

    @property
    def on_duty_index(self):
        return self._on_duty_index

    @property
    def off_duty_index(self):
        return self._off_duty_index

    @property
    def index(self):
        return arange(len(self._timeline))

    def label(self, n):
        return self._timeline[n]

    def is_on_duty(self, n):
        return self._selector(self._timeline[n])

    def is_off_duty(self, n):
        return not self.is_on_duty(n)


class Organizer(object):
    """Container class which defines the layout of the timeline.
    
    `Organizer` tells how to organize a frame into a timeline, that is, how 
    to create workshifts and label them.
    
    Parameters
    ----------
    marker : Marker or str
        A `Marker` or a pandas-compatible calendar frequency (accepts same 
        kind of values as `base_unit_freq` of timeboard). Under the hood
        `marker=freq` is silently converted  to `marker=Marker(each=freq)`.
    marks : Iterable of Timestamp-like
    structure : Iterable 
        An element of `structure` is either another `Organizer`, or 
        a single workshift label, or a pattern. Pattern is an iterable of 
        workshift labels, such as an explicit list of labels or an instance of 
        `RememberingPattern`.
              
    Raises
    ------
    ValueError
        If both `marker` and `marks` are specified.
        
    Attributes
    ----------
    Same as parameters.
        
    Notes
    -----
    Firstly, organizer tells how to partition timeboard's frame into chunks 
    (spans). Secondly, organizer defines how to organize each span into 
    workshifts and what labels they will receive.
    
    Spans created by organizer begin on base units referred to by points in 
    time called marks. The locations of the marks are defined by either 
    `marker` or `marks` parameter. 
    
    Given `marker` parameter, the mark locations are computed according to 
    the rules set by the `Marker` object passed as the value of `marker`. 
    
    If, instead, `marks` is given, it is a list of explicitly specified 
    points in time which will serve as marks. 
    
    One and only one of `marker` or `marks` parameters must be supplied.

    What to do with each of the identified spans is specified by `structure` 
    parameter which is an iterable. For each span a next element is taken 
    from `structure`. This element is either another `Organizer`, or a pattern 
    (an iterable of workshift labels), or a single label.
    
    If an element of `structure` is an `Organizer`, it is used to further 
    partition this span into sub-spans. 
    
    If it is a pattern, the recursive partitioning does not happen. Instead, 
    each base unit of the span becomes a workshift. The labels for these 
    workshifts are taken from the pattern. 
    
    If the element of `structure` is some other single value, it is considered 
    a label. In this case the whole span becomes a single workshift which 
    receives this label. Such a compound workshift comprises several base units 
    (unless the span itself consists of a single base unit).
    
    Once `structure` is exhausted , it is re-enacted in cycles. The same 
    approach applies for pattern when setting workshift labels.
    
    See also
    --------
    Marker
        Define rules to calculate locations of marks upon the frame.
    RememeberingPattern
        Keep track of assigned labels across invocations.

    """
    def __init__(self, marker=None, marks=None, structure=None):
        if (marker is None) == (marks is None):
            raise ValueError("One and only one of 'marker' or 'marks' "
                             "must be specified ")
        if not _is_iterable(structure):
            raise TypeError("structure parameter must be iterable")
        self._marker = marker
        self._marks = marks
        if marker is not None and not isinstance(marker, Marker):
            self._marker = Marker(marker)
        self._marks = _to_iterable(marks)
        self._structure = structure

    @property
    def marker(self):
        return self._marker

    @property
    def marks(self):
        return self._marks

    @property
    def structure(self):
        return self._structure

    def _repr_builder(self, repr_objects=None):
        """Auxiliary function generation of __repr__ mock code.
        
        Generate __repr__ strings for auxiliary objects used to create this 
        organizer and store them in the ordered dictionary. The order of the 
        dictionary keys preserves the order in which the auxiliary objects 
        are to be instantiated. The last element is the code to instantiate 
        self.
        
        The dictionary key is object's name assembled as "{type}_{id}", where 
        {type} is 'org' for Organizer, 'mrk' for Marker, 'rp' for 
        RememberingPattern, and {id} is object's id. 
        
        The value is the code instantiating this object's. The code may refer 
        to objects already included in the dictionary.
        
        Parameters
        ----------
        repr_objects : OrderedDict
            Already created dictionary of objects' __repr__ strings (for 
            recursive organizing).
            
        Returns
        -------
        OrderedDict
        """
        if repr_objects is None:
            repr_objects =  OrderedDict()
        my_name = "org_{}".format(id(self))
        if my_name in repr_objects:
            return repr_objects

        if self.marker is not None:
            if self.marker.at:
                marker_name = "mrk_{}".format(id(self.marker))
                if marker_name not in repr_objects:
                   repr_objects[marker_name] = "{!r}".format(self.marker)
                arg_m = "marker={}".format(marker_name)
            else:
                arg_m = "marker={!r}".format(self.marker)
        else:
            arg_m = "marks={!r}".format(self.marks)

        elem_reprs = []
        for elem in self.structure:
            if isinstance(elem, Organizer):
                org_name = "org_{}".format(id(elem))
                if org_name not in repr_objects:
                    repr_objects = elem._repr_builder(repr_objects)
                elem_reprs.append(org_name)
            elif isinstance(elem, RememberingPattern):
                rp_name = "rp_{}".format(id(elem))
                if rp_name not in repr_objects:
                   repr_objects[rp_name] = "{!r}".format(elem)
                elem_reprs.append(rp_name)
            else:
                elem_reprs.append("{!r}".format(elem))
        arg_s = "[" + ", ".join(elem_reprs) + "]"
        repr_objects[my_name] = "Organizer({}, structure={})".format(arg_m,
                                                                    arg_s)
        return repr_objects

    def __repr__(self):
        repr_objects = self._repr_builder()
        _, my_line = repr_objects.popitem()
        my_object_lines = ""
        for obj_name, obj_repr in repr_objects.items():
            my_object_lines += "{} = {}\n".format(obj_name, obj_repr)
        return my_object_lines + my_line


class Marker(object):
    """Container class defining the markup of a timeboard's frame.
    
    Markup is an ordered sequence of marks placed at points of time 
    calculated as specified by parameters of a `Marker`.
    
    Parameters
    ----------
    each : str
        Pandas-compatible calendar frequency; accepts same values as 
        `base_unit_freq` of timeline (timeboard).
    at : list of dict, optional
        Each dictionary is a collection of keyword arguments used for calling 
        `how` function. 
    how : str or function, optional
        'from_start_of_each' (default) : keyword arguments in `at` define an 
        offset (number of hours, days, etc.) from the start of `each` period.
        'from_easter_western' : keyword arguments in `at` define an offset 
        from the Western Easter in `each` period.
        'from_easter_orthodox' :  keyword arguments in `at` define an offset 
        from the Orthodox Easter in `each` period.
        'nth_weekday_of_month' : keyword arguments in `at` define N-th weekday 
        of M-th month from the start of `each` period.
        
        The above strings are effectively substituted by their name-sake 
        functions from module `when`.
        
        Alternatively, a user-defined function may be supplied as the value of 
        `how`. The function must conform to the signature 
        def fun(pandas.PeriodIndex, 'normalize_by': str, **kwargs) -> 
        pandas.DatetimeIndex.
        
    Attributes
    ----------
    Same as parameters.
    
    Notes
    -----
    The markup defined by a `Marker` is to be applied to a span, which is a 
    part of a timeboard's frame, or to the whole frame. Locations of marks are 
    calculated as follows. 
    
    In each calendar period of frequency `each` located partly or wholly within 
    the span find points in time defined by `at` parameter. Each dictionary in 
    `at` list is a collection of keyword arguments which defines one point in 
    time. Hence, the number of points sought in each `each` period is equal 
    to the length of `at` list. 
    
    The interpretation of keyword arguments stored in `at` is defined by 
    parameter `how`. 
    
    The location of every point in time which has been calculated by the above 
    procedure is inspected. If it is within the `each` period in which it was 
    being sought and within the span, the point becomes a mark. Otherwise 
    it is ignored.
    
    If `at` parameter is not provided or `at` list is empty, the marks are 
    set on the start times of calendar periods specified by `each`.
    
    `Organizer` uses markup defined by `Marker` to partition the frame into 
    subframes. The first subframe always starts on the first base unit 
    of the span. The second subframe starts on the base unit which contains 
    the first mark. The last subframe starts on the base unit containing 
    the last mark and ends on the last base unit of the span. If no marks 
    have been set, only one subframe is created which contains the whole span.
    
    Examples
    --------
    `Marker(each='W')`
        Mark a span by weeks (set a mark on each Monday at 00:00).
        
    `Marker(each='W', at=[{'days': 2}, {'days': 5}])  `
        Set a mark on each Wednesday and each Saturday at 00:00. Note that 
        there is no mark on Monday because now `at` list is not empty but 
        Monday is not explicitly specified in the list.
        
    `Marker(each='W', at=[{'days': 0}, {'days': 2}, {'days': 5}])`
        Set a mark on each Monday, Wednesday, and Saturday at 00:00.  
        
    `Marker(each='W', at=[{'days': 7}])`
        No marks will be set. Adding 7 days to the start of the week 
        places the candidate point into the next week, i.e. outside the current 
        'each' period, hence this point is not a valid mark.
        
    `Marker(each='D')`
        Mark a span by days (set a mark at each midnight).
          
    `Marker(each='D', at=[{'hours': 9}, {'hours':18}])`
        Set marks at 09:00 and 18:00 on each day (but not at the 
        midnight).
        
    `Marker(each='M', at=[{'days': 30}])`
        Set a mark on the beginning of the 31st day of each month. If there 
        is no 31st day, there will be no mark in this month. For example, 
        if the span is a calendar year, marks will be set on Jan 31, 
        Mar 31, May 31, Jul 31, Aug 31, Oct 31, and Dec 31.
    
    ::
    Marker(each='A', 
           at=[{'month': 5, 'week': -1, 'weekday': 1},
               {'month': 9, 'week': 1, 'weekday': 1}],
           how='nth_weekday_of_month')
        
        Set marks on the last Monday in May and the first Monday in 
        September of each year.
    """

    def __init__(self, each, at=None, how='from_start_of_each'):
        self._each = each
        self._at = at
        how_functions = {
            'from_start_of_each': from_start_of_each,
            'nth_weekday_of_month': nth_weekday_of_month,
            'from_easter_western': from_easter_western,
            'from_easter_orthodox': from_easter_orthodox,
        }
        if not callable(how):
            self._how = how_functions[how]
            self._how_str = how
        else:
            self._how = how
            self._how_str = str(how)

    @property
    def each(self):
        return self._each

    @property
    def at(self):
        return self._at

    @property
    def how(self):
        return self._how

    def __repr__(self):
        at_how_repr = ""
        if self.at:
            at_how_repr = ", at={!r}, how={!r}".format(self.at, self._how_str)
        return "Marker(each={!r}{})".format(self.each, at_how_repr)


class RememberingPattern(object):
    """Pattern keeping track of assigned labels across invocations.
    
    Parameters
    ----------
    labels : iterable
        An iterable of workshift labels
    """
    def __init__(self, labels):
        self._labels = labels
        self._label_generator = cycle(labels)

    def __next__(self):
        return next(self._label_generator)

    def next(self):
        return self.__next__()

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._labels)

    def __getitem__(self, i):
        return self._labels[i]

    def __repr__(self):
        return "RememberingPattern({!r})".format(self._labels)