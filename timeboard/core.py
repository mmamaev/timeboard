from .exceptions import (OutOfBoundsError,
                         VoidIntervalError,
                         UnsupportedPeriodError)
import pandas as pd
from pandas import Period, Timestamp, NaT
from itertools import cycle, dropwhile
from collections import Iterable


def _skiperator(values, direction='forward', skip=0):
    """Build a skip-and-cycle generator
    
    Return a generator that cycles through `values` 
    after having skipped a number of steps at the beginning.
    
    Parameters
    ----------
    values: iterable
    direction: {'forward', 'reverse'}, optional (default 'forward')
        - 'forward' to iterate through values left to right,
        - 'reverse' to iterate right to left.
    skip: int, optional (default 0) 
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

        def counter(_):
            flag = nonlocal_vars['iters'] < skip
            nonlocal_vars['iters'] += 1
            return flag

        return counter

    pattern = values
    if direction == 'reverse': pattern = values[::-1]
    counter = make_counter()
    return dropwhile(counter, cycle(pattern))

def _check_splitby_freq(base_unit_freq, split_by):
    """
    Check if the value of `split_by` from some Organizer can be used 
    with the given `base_unit_freq`, meaning that partitioning of a timeline 
    will not result in a situation when a base unit belongs to more 
    than one span at the same time. 
    
    An example of such ambiguous split is when base_unit_freq='W' and
    split_by='M'. Most likely there will be a base unit (week) that falls into 
    two spans (months) simultaneously.
    
    Return True if `split_by` value is ok.
    """
    # TODO: add support of freq multiplicators, i.e. (D,4D) or (2D,4D)
    #       is_subperiod function does not support this
    return bool(
        pd.tseries.frequencies.is_subperiod(base_unit_freq,split_by)
        # some combinations of arguments result in is_subperiod function
        # returning nothing (NoneType)
        )

def _to_iterable(x):
    if x is None:
        return x
    # TODO: Modify check to make it work for unicode strings
    elif isinstance(x, str):
        return [x]
    elif isinstance(x, Iterable):
        return x
    else:
        return [x]

class _Frame(pd.PeriodIndex) :
    """Ordered sequence of uniform periods of time.
    
    `_Frame` object implements the structure of time in timeboard and 
    serves as the index for timeline. Elements of the frame are timeboard's 
    base units.
    
    Parameters
    ----------
    base_unit_freq: str
        Pandas-compatible calendar frequency (i.e. 'D' for day) defining the 
        constituent period of the frame. Pandas-native business  periods 
        (i.e. 'BM') are not supported. Support of periods with multipliers 
        (i.e. '3D') is planned but not yet there.
    start: Timestamp-like
        A pandas Timestamp, a datetime object, or a string convertible to 
        Timestamp - a point in time defining the first element of the frame 
        (it may be found anywhere with this element).
    end: Timestamp-like
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
    def __new__ (cls, base_unit_freq, start, end) :
        frame = super(_Frame, cls).__new__(cls, start=start, end=end,
                                           freq=base_unit_freq)
        if len(frame) == 0:
            raise VoidIntervalError('Empty frame not allowed '
                  '(make sure the start time precedes the end time)')
        frame._base_unit_freq=base_unit_freq
        return frame

    @property
    def start_time(self):
        return self[0].start_time

    @property
    def end_time(self):
        return self[-1].end_time

    def _locate_subframes(self, span_first, span_last, points_in_time):
        """
        Takes a part of the frame (a "span") in order to partition it into 
        subframes at specified points in time. 
        
        Parameters
        ----------
        span_first: int>=0
            Index of the first element of the span in the frame.
        span_last: int>=0
            Index of the last element of the span in the frame.
        points_in_time: Iterable of Timestamp-like 
            List of points in time referring to frame's elements that will 
            become the first elements of subframes.
            
        Returns
        -------
        list of tuples containing indices of subframe boundaries:    
            [ (subfr0_start, subfr0_end), ... , (subfrN_start, subfr0_end) ]

        
        Notes
        -----
        Any elements of `points_in_time` that do not define a start of 
        a subframe within the span are ignored.
        These are:
          - points referring to a frame's element already designated as the 
          first element of a subframe,
          - points referring to `span_first` element,
          - points outside the span.
        If no usable points are found or `points_in_time` is empty,
        [(span_start, span_end)] is returned. 
        """

        self.check_span(span_first, span_last)
        split_positions = filter(lambda x: span_first < x <= span_last,
                                 map(self._get_loc_wrapper, points_in_time))
        split_positions = sorted(list(set(split_positions)))

        start_positions = split_positions[:]
        start_positions.insert(0, span_first)
        end_positions = map(lambda x:x-1, split_positions)
        end_positions.append(span_last)

        return zip(start_positions, end_positions)

    def check_span(self, span_first, span_last):
        if not ( isinstance(span_first, int) and
                 isinstance(span_last, int) ):
            # Guard against Python 2 which is ok to compare strings and
            # integers, i.e. "20 Feb 2017" > 60 evaluates to True
            raise TypeError("Span boundaries must be of type integer")
        if span_first < 0 or span_last < 0:
            raise OutOfBoundsError("Span boundaries must be non-negative")
        if span_first > len(self) or span_last> len(self):
            raise OutOfBoundsError("Span not within frame")
        if span_first > span_last:
            raise VoidIntervalError("Span cannot be empty")
        return True

    def _get_loc_wrapper(self, x):
        try:
            return self.get_loc(x)
        except KeyError:
            return 0

    def _create_subframes(self, span_first, span_last, points_in_time):
        """ Wrapper around `_locate_subframes`.
        
        Transform returned value of `_locate_subframes` into a list of
         `_Subframe` objects.
         
        Parameters
        ----------
        span_first: int>=0
            Index of the first element of the span in the frame.
        span_last: int>=0
            Index of the last element of the span in the frame.
        points_in_time: Iterable of Timestamp-like 
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
        subframes = map(lambda (first, last): _Subframe(first, last, 0, 0),
                        subframe_boundaries)
        if not subframes:
            subframes = [_Subframe(span_first, span_last, 0, 0)]
        return subframes

    def do_split_by(self, span_first, span_last, split_by):
        """Partition the (part of) frame into calendar periods.
        
        Take a part of the frame (a "span") and partition it into 
        a list of subframes according to the rule set by `split_by` parameter.

        `split_by` parameter defines calendar periods (i.e. weeks), which
        are overlaid on the span 'carving' a list of subframes.
        
        Parameters
        ----------
        span_first: int>=0
            Index of the first element of the span in the frame.
        span_last: int>=0
            Index of the last element of the span in the frame.
        split_by: str
            Pandas-compatible calendar frequency; accepts same values as 
            `base_unit_freq` of timeline (timeboard). 
        
        Raises
        ------
        UnsupportedPeriodError (ValueError)
            If `split_by` defines a period which is not a multiple of 
            `base_unit_freq`.
        
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
        
        For example, if base_unit_freq='D', and the span contains the days
        from 01 Jan until 31 Jan 2017, and split_by='W', the first subframe 
        will contain only one day 01 Jan, Sunday. The first six days of this
        week (26-31 Dec) are outside the span. The number of such fell out
        days are recorded in subframe's `skip_left` attribute. Analogously,
        the last subframe of the span will contain only two days: 
        Mon 30 Jan and Tue 31 Jan. The rest five days of this week fall out of
        the span. This is recorded in `skip_right` attribute which is set, 
        in this subframe, to 5. All subframes in between represent a full week
        each, and their `skip_left` and `skip_right` attributes are zeroed. 
        """
        # TODO: add support of freq multiplicators, i.e. (D by 4D) or (2D by 4D)
        # TODO: reason about freq multiplicators of anchored freqs
        if not _check_splitby_freq(self._base_unit_freq, split_by) :
            raise UnsupportedPeriodError('Ambiguous organizing: '
                             '{} is not a subperiod of {}'.format(
                             self._base_unit_freq, split_by))
        self.check_span(span_first, span_last)
        span_start_ts = self[span_first].start_time
        span_end_ts = self[span_last].end_time
        stencil = _Frame(base_unit_freq=split_by,
                         start=span_start_ts,
                         end=span_end_ts)
        if stencil.start_time < span_start_ts:
            left_dangle = _Frame(base_unit_freq=self._base_unit_freq,
                                 start=stencil.start_time,
                                 end=span_start_ts)
            # TODO: amend use of difference without recast to pd.PeriodIndex
            skipped_units_before = len(pd.PeriodIndex(left_dangle).difference(self[span_first:]))
        else:
            skipped_units_before = 0

        if stencil.end_time > span_end_ts:
            right_dangle = _Frame(base_unit_freq=self._base_unit_freq,
                                  start=span_start_ts,
                                  end=stencil.end_time)
            skipped_units_after = len(pd.PeriodIndex(right_dangle).difference(self[:span_last + 1]))
        else:
            skipped_units_after = 0

        split_points = map(lambda x: x.start_time, stencil)
        subframes = self._create_subframes(span_first, span_last, split_points)
        subframes[0].skip_left = skipped_units_before
        subframes[-1].skip_right = skipped_units_after
        return subframes

    def do_split_at(self, span_first, span_last, split_at):
        """Partition the (part of) frame ar specified points in time.
        
        Take a part of the frame (a "span") and partition it into 
        a list of subframes at points in time listed in `split_at`.

        Parameters
        ----------
        span_first: int>=0
            Index of the first element of the span in the frame.
        span_last: int>=0
            Index of the last element of the span in the frame.
        split_at: Iterable of Timestamp-like 
            List of points in time referring to frame's elements that will 
            become the first elements of subframes.

        Returns
        -------
        list of _Subframe
        
        Notes
        -----
        Any elements of `split_at` that do not define a start of 
        a subframe within the span are ignored.
        These are:
          - points referring to a frame's element already designated as the 
          first element of a subframe,
          - points referring to `span_first` element,
          - points outside the span.
        If no usable points are found or `points_in_time` is empty,
        [(span_start, span_end)] is returned. 
        """
        # TODO: add support of partial point-in-time specifications
        return self._create_subframes(span_first, span_last, split_at)

class _Subframe:
    """Container class defining a subframe within some frame.
    
    Parameters
    ----------
    first: int 
        Index of the first element of subframe within the frame.
    last: int    
        Index of the last element of subframe within the frame
    skip_left: int >=0
        Number of steps to skip if a pattern of labels is applied to  
        this subframe in 'forward' direction (left to right)
    skip_right: int >=0    
        Number of steps to skip if a pattern of labels is applied to 
        this subframe in 'reverse' direction (from right to left)            
    
    Attributes
    ----------
    Same as parameters.
    """
    def __init__(self, first, last, skip_left=0, skip_right=0):
        self.first = first
        self.last = last
        self.skip_left = skip_left
        self.skip_right = skip_right

    def __repr__(self):
        return "{}({},{},{},{])".format(self.__class__, self.first, self.last,
                                        self.skip_left, self.skip_right)

class _Timeline(pd.Series):
    """Period-indexed series of labels.
    
    `_Timeline` object, a timeline,  is the principal data structure of a 
    timeboard. Timeline's index consists of periods representing workshifts 
    of the timeboard, and timeline's data are workshift labels.
    The labels are set by calling `organize` method, and then are adjusted to 
    account for irregular circumstances by calling `amend`. These methods 
    change the timeline in-place.
    
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
    data : optional
        Labels to initialize the timeline with (a single value or an iterable 
        for the full length of the timeline).By default the timeline is 
        initialized with NaN.
        
    Raises
    ------
    UnsupportedPeriodError (ValueError)
        If `base_unit_freq` is not supported or `organize` attempted a split
        by a period which is not a multiple of `base_unit_freq`.
    VoidIntervalError (ValueError)
        If an instantiation of an empty timeline is attempted.
        
    Attributes
    ----------
    frame : _Frame
        A series of periods of time serving as the index of the timeline.
    start_time : Timestamp
        When the first element of the timeline starts.
    end_time : Timestamp
        When the last element of the timeline ends.
    """
    def __init__(self, base_unit_freq, start, end, data=None):
        f = _Frame(base_unit_freq, start, end)
        super(_Timeline, self).__init__(index=f, data=data)
        self._base_unit_freq = base_unit_freq
        self._frame = f


    @property
    def frame(self):
        return self._frame

    @property
    def start_time(self):
        return self._frame.start_time

    @property
    def end_time(self):
        return self._frame.end_time

    def reset(self, value = pd.np.nan):
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
        self.iloc[:] = value

    def amend(self, amendments, not_in_range='ignore'):
        """
        Set labels for specified workshifts overriding any values already set.
        
        Parameters
        ----------
        amendments: dictionary-like 
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
            workshift (the actual label would be unpredictable).
        OutOfBoundsError (LookupError)
            If there is a key in `amendments` referring outside the timeline
            and `not_in_range` parameter value is anything but 'ignore'.

        Note
        ----
        Nothing is returned; the timeline is modified in-place.
        """
        amendments_located={}
        for (point_in_time, value) in amendments.iteritems():
            try:
                loc = self.frame.get_loc(point_in_time)
            except KeyError:
                if not_in_range == 'raise':
                    raise OutOfBoundsError('Amendment {} is outside the '
                                           'timeboard'.format(point_in_time))
                else:
                    continue
            if loc in amendments_located:
                raise KeyError("Amendments contain duplicate reference to "
                               "workshift {}".format(loc))
            amendments_located[loc] = value

        self.iloc[amendments_located.keys()] = amendments_located.values()

    def _apply_pattern(self, pattern, subframe):
        """Set workshift labels from a pattern.
        
        Pattern application is repeated in cycles until the end of the subframe 
        is reached. If `subframe.skip_left`>0, then the respective number of
        idle iterations through pattern is done before a label is set for the 
        first workshift of the subframe. The value of `subframe.skip_right` 
        is currently ignored (reserved for future support of pattern 
        application done in reverse.

        Parameters
        ----------
        pattern: Iterable of labels
        subframe : Subframe
         
        Returns
        -------
        None
        
        Note
        ----
        Nothing is returned; the timeline is modified in-place.
        """
        pattern_iterator = _skiperator(pattern,
                                       direction='forward',
                                       skip=subframe.skip_left)
        # TODO: support both directions (set direction in Organizer?)
        for i in range(subframe.first, subframe.last+1):
            try:
                self.iloc[i] = next(pattern_iterator)
            except StopIteration:
                raise IndexError('Timeline pattern exhausted since {}'.format(i))

    def organize(self, organizer, span_first=None, span_last=None):
        """Set up a layout defined by organizer.
        
        Set workshift labels by imposing a layout defined by `organizer`
        within the specified span of the timeline .

        Parameters
        ----------
        organizer: instance of Organizer 
        span_first: int>=0, optional
            Index of the first workshift of the span on the timeline. 
            By  default this is the first workshift of the timeline.
        span_last: int>=0, optional
            Index of the last workshift of the span on the timeline. 
            By default this is the last workshift of the timeline.
            
        Returns
        -------
        None
        
        Note
        ----
        Nothing is returned; the timeline is modified in-place.
        """
        # TODO: introduce concept of workshifts of varied length (>1 BU per workshift
        # TODO: timeline will contain workshiftd, not base units
        if span_first is None :
            span_first = 0
        if span_last is None :
            span_last = len(self) - 1
        subframe_seq = []
        if organizer.split_by is not None:
            subframe_seq = self.frame.do_split_by(span_first,
                                                  span_last,
                                                  organizer.split_by)
        if organizer.split_at is not None:
            subframe_seq = self.frame.do_split_at(span_first,
                                                  span_last,
                                                  organizer.split_at)

        for subframe, layout in zip(subframe_seq,
                                    cycle(organizer.structure)):
            if isinstance(layout, Organizer):
                self.organize(layout, subframe.first, subframe.last)
            elif isinstance(layout, Iterable):
                self._apply_pattern(layout, subframe)
            else:
                self.reset()
                raise TypeError('Organizer.layout may contain either '
                                'patterns (iterables of values) or  '
                                'other Organizers')


class Organizer:
    """Container class defining rules for setting up timeline's layout.
    
    Parameters
    ----------
    split_by: str
        Pandas-compatible calendar frequency; accepts same values as 
        `base_unit_freq` of timeline (timeboard). 
    split_at: Iterable of Timestamp-like
    structure: Iterable of {Organizer | Iterable}
        An element of `structure` is either another organizer or a pattern.
        Pattern itself is an iterable of workshift labels.
              
    Raises
    ------
    ValueError
        If both `split_by` and `split_at` are specified.
        
    Attributes
    ----------
    Same as parameters.
        
    Notes
    -----
    Firstly, organizer tells how to partition timeline into chunks (spans); 
    this is defined by `split_by` or `split_at` parameter. Given `split_by` 
    parameter, the timeline is partitioned into spans aligned with calendar 
    periods such as days, weeks, months, etc. With `split_at`, the timeline 
    is partitioned at the specified points in time. 
    
    One and only one of `split_by` or `split_at` parameters must be supplied.

    Secondly, organizer tells what to do with each of the identified spans; 
    this is specified by `structure` parameter which is an iterable. For each 
    span a next element is taken from structure. This element is either  
    another organizer or a pattern (an iterable of workshift labels). If it is 
    an organizer, it is used to further partition this span of the 
    timeline into sub-spans. If it is a pattern, the recursive partitioning 
    does not happen. Instead, labels from the pattern are set for the 
    workshifts in the span.  
    
    Once `structure` is exhausted , it is re-enacted in cycles. The same 
    approach applies for pattern when setting workshift labels.
    """
    def __init__(self, split_by=None, split_at=None, structure=None):
        if (split_by is None) == (split_at is None) :
            raise ValueError("One and only one of 'split_by' or 'split_at' "
                             "must be specified ")
        if not isinstance(structure, Iterable):
            raise TypeError("structure parameter must be iterable")
        self._split_by = split_by
        self._split_at = _to_iterable(split_at)
        self._structure = structure

    @property
    def split_by(self):
        return self._split_by

    @property
    def split_at(self):
        return self._split_at

    @property
    def structure(self):
        return self._structure

    def __repr__(self):
        if self.split_by is not None:
            s = "split_by={}".format(self.split_by)
        else:
            s = "split_at={}".format(self.split_at)
        return "Organizer({}, structure={})".format(s, self.structure)

