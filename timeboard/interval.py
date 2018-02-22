from __future__ import division
from .exceptions import (OutOfBoundsError,
                         VoidIntervalError,
                         UnacceptablePeriodError)
from .workshift import Workshift
from .core import _Frame, _Schedule,  VOID_TIME


class _BaseInterval(object):
    """Parent class for Interval and VoidInternal"""
    def __init__(self, timeboard, bounds, schedule=None):

        def handle_bound(bound):
            if isinstance(bound, Workshift):
                loc = bound._loc
            elif isinstance(bound, int):
                loc = bound
            else:
                raise TypeError('Interval bound = {}: expected integer or '
                                'Workshift, received {}'.
                                format(bound, type(bound)))
            if not 0 <= loc < len(timeboard._timeline):
                raise OutOfBoundsError(
                    "Interval bound {} is outside timeboard {}".
                    format(bound, timeboard.compact_str))
            return loc

        if not hasattr(bounds, '__getitem__'):
            raise TypeError("`bounds` parameter must be list-like")

        try:
            bound0 = bounds[0]
            bound1 = bounds[1]
        except IndexError:
            raise IndexError("`bounds` value must contain two items")

        locs = (handle_bound(bound0), handle_bound(bound1))
        self._tb = timeboard
        self._loc = locs
        try:
            is_void = self.__class__.IS_VOID
        except AttributeError:
            is_void = False
        if is_void:
            if locs[0] <= locs[1]:
                raise VoidIntervalError(
                    'Attempted to instantiate void interval with valid '
                    'locations:'
                    ' {!r}'.format(locs))
            self._length = 0
        else:
            if locs[0] > locs[1]:
                raise VoidIntervalError(
                    'Attempted to create empty interval with {!r}'.format(locs))
            self._length = locs[1] - locs[0] + 1

        if schedule is None:
            self._schedule = timeboard.default_schedule
        else:
            self._schedule = schedule
        if not isinstance(self._schedule, _Schedule):
            raise TypeError('Wrong type of schedule. Expected _Schedule,'
                            ' received {}'.format(type(schedule)))


class Interval(_BaseInterval):
    """A sequence of workshifts within the timeboard.
    
    Interval is defined by two positions on the timeline which are
    the zero-based sequence numbers of the first and the last workshifts 
    of the interval. An interval can contain one or more workshifts; the
    empty interval is not allowed.
    
    Duty status of the workshifts within the interval is interpreted by the 
    given schedule.
    
    In addition to the methods defined for intervals, you can use interval 
    as a generator that yields the workshifts of the interval, from the
    first to the last.
    
    Parameters
    ----------
    timeboard : :py:class:`.Timeboard`
    bounds : tuple(int, int) or tuple(Workshift, Workshift)
        The two elements of `bounds` provide the positions of the first and 
        the last workshifts of the interval within the timeline. The element's 
        type is either non-negative integer or :py:class:`.Workshift`.
    schedule : _Schedule, optional
        If not given, the timeboard's default schedule is used. 
    
    Raises
    ------
    VoidIntervalError
        If `bounds` are in the reverse order.
    OutOfBoundsError
        If any of `bounds` points outside the timeboard.
        
    Attributes
    ----------
    start_time : Timestamp
        When the first workshift of the interval starts.
    end_time : Timestamp
        When the last workshift of the interval ends.
    length : int >0
        Number of workshifts in the interval. You can also call `len()` 
        function for an interval which returns the same value. 
    schedule : _Schedule
        Schedule used by interval's methods unless explicitly redefined in 
        the method call. Use `name` attribute of `schedule` to review its 
        identity.
        
    Examples
    --------
    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
    >>> ivl = tb.interval.Interval(clnd, (2,9))
    >>> ivl
    Interval((2, 9)): 'D' at 2017-10-02 -> 'D' at 2017-10-09 [8]
    
    >>> len(ivl)
    8
    >>> for ws in ivl: 
    ...     print (ws.start_time, "\t", ws.label)
    2017-10-02 00:00:00 	 0.0
    2017-10-03 00:00:00 	 1.0
    2017-10-04 00:00:00 	 0.0
    2017-10-05 00:00:00 	 1.0
    2017-10-06 00:00:00 	 0.0
    2017-10-07 00:00:00 	 1.0
    2017-10-08 00:00:00 	 0.0
    2017-10-09 00:00:00 	 1.0    

    The following operations consume memory to hold the data for 
    the entire interval.
       
    >>> list(ivl)
    [Workshift(2) of 'D' at 2017-10-02,
     Workshift(3) of 'D' at 2017-10-03,
     Workshift(4) of 'D' at 2017-10-04,
     Workshift(5) of 'D' at 2017-10-05,
     Workshift(6) of 'D' at 2017-10-06,
     Workshift(7) of 'D' at 2017-10-07,
     Workshift(8) of 'D' at 2017-10-08,
     Workshift(9) of 'D' at 2017-10-09] 
    
    >>> print(ivl)
    Interval((2, 9)): 'D' at 2017-10-02 -> 'D' at 2017-10-09 [8]
    <BLANKLINE>
         workshift      start  duration        end  label  on_duty
    loc                                                           
    2   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    3   2017-10-03 2017-10-03         1 2017-10-03    1.0     True
    4   2017-10-04 2017-10-04         1 2017-10-04    0.0    False
    5   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    6   2017-10-06 2017-10-06         1 2017-10-06    0.0    False
    7   2017-10-07 2017-10-07         1 2017-10-07    1.0     True
    8   2017-10-08 2017-10-08         1 2017-10-08    0.0    False
    9   2017-10-09 2017-10-09         1 2017-10-09    1.0     True        
    
    See also
    --------
    .Timeboard.get_interval :
        provides convenient ways to instantiate an interval instead of 
        calling `Interval()` constructor directly. Moreover, in many cases, 
        you can shortcut a :py:meth:`get_interval` call by calling 
        the instance of :py:class:`Timeboard` itself.
    .workshifts
        Return the generator that yields workshifts with the specified duty.
    """

    def _repr_schedule_label(self):
        schedule_label = self.schedule.name
        if schedule_label == self._tb.default_schedule.name:
            schedule_label = ""
        else:
            schedule_label = ", " + schedule_label
        return schedule_label

    @property
    def compact_str(self):
        return "Interval({!r}{}): {} -> {} [{}]".format(
            self._loc,
            self._repr_schedule_label(),
            Workshift(self._tb, self._loc[0]).compact_str,
            Workshift(self._tb, self._loc[1]).compact_str,
            self._length,
        )

    def __repr__(self):
        return self.compact_str

    def __str__(self):
        return self.compact_str + "\n\n{}".format(self.to_dataframe())

    @property
    def start_time(self):
        # TODO: Refactor. This class has to know methods of Timeboard only
        return self._tb._timeline.get_ws_start_time(self._loc[0])

    @property
    def end_time(self):
        # TODO: Refactor. This class has to know methods of Timeboard only
        return self._tb._timeline.get_ws_end_time(self._loc[1])

    @property
    def length(self):
        """Number of workshifts in the interval."""
        return self._length

    @property
    def schedule(self):
        return self._schedule

    def to_dataframe(self):
        """Convert interval into `pandas.Dataframe`.

        Each workshift is represented as a row. The dataframe has the 
        following columns:

        ================ =====================================================
        Column           Explanation
        ================ =====================================================
        'loc'            zero-based position of the workshift on the timeline
        'workshift'      the reference time of the workshift
        'start'          the start time of the workshift
        'end'            the start time of the workshift
        'duration'       the number of base units in the workshift
        'label'          workshift's label
        ================ =====================================================                 

        Returns
        -------
        pandas.DataFrame
        """
        return self._tb.to_dataframe(self._loc[0], self._loc[1])

    def _find_my_bounds_in_idx(self, idx):
        # TODO: optimize this search
        left_bound = 0
        len_idx = len(idx)
        while left_bound < len_idx and idx[left_bound] < self._loc[0]:
            left_bound += 1
        if left_bound == len_idx:
            return None, None
        right_bound = len(idx) - 1
        while right_bound >= left_bound and idx[right_bound] > self._loc[1]:
            right_bound -= 1
        if right_bound < left_bound:
            return None, None
        return left_bound, right_bound

    def _get_duty_idx(self, duty, schedule):
        _duty_idx = {
            'on': schedule.on_duty_index,
            'off': schedule.off_duty_index,
            'any': schedule.index
        }

        try:
            duty_idx = _duty_idx[duty]
        except KeyError:
            raise ValueError('Invalid `duty` parameter {!r}'.format(duty))
        if duty != 'any':
            duty_idx_bounds = self._find_my_bounds_in_idx(duty_idx)
        else:
            duty_idx_bounds = self._loc
        return duty_idx, duty_idx_bounds

    def workshifts(self, duty='on', schedule=None):
        """
        Return the generator that yields workshifts with the specified duty.
        
        The workshifts are yielded in order from the first to the last.
        
        Parameters
        ----------
        duty : {``'on'``, ``'off``', ``'any``'} , optional (default ``'on'``)
            Duty of the workshifts to be yielded. If ``duty='on'``,
            off duty workshifts are skipped, and vice versa. If ``duty='any'``,
            every workshift in the interval is yielded.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.

        Returns
        -------
        generator

        Examples
        --------
        
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> ivl = tb.interval.Interval(clnd, (2,9))
        >>> ivl
        Interval((2, 9)): 'D' at 2017-10-02 -> 'D' at 2017-10-09 [8]
        
        >>> for ws in ivl.workshifts(): 
        ...     print (ws.start_time, "\t", ws.label)    
        2017-10-03 00:00:00 	 1
        2017-10-05 00:00:00 	 1
        2017-10-07 00:00:00 	 1
        2017-10-09 00:00:00 	 1

        >>> list(ivl.workshifts(duty='off'))
        [Workshift(2) of 'D' at 2017-10-02,
         Workshift(4) of 'D' at 2017-10-04,
         Workshift(6) of 'D' at 2017-10-06,
         Workshift(8) of 'D' at 2017-10-08]
        """

        if schedule is None:
            schedule = self.schedule
        duty_idx, duty_idx_bounds = self._get_duty_idx(duty, schedule)
        if duty_idx_bounds[0] is None or duty_idx_bounds[1] is None:
            raise StopIteration
        for i in duty_idx[duty_idx_bounds[0] : duty_idx_bounds[1] + 1]:
            yield Workshift(self._tb, i, schedule=schedule)

    def __next__(self):
        return next(self._ws_generator_activated)

    def next(self):
        return self.__next__()

    def __iter__(self):
        self._ws_generator_activated = self.workshifts(duty='any')
        return self

    def __len__(self):
        return self.length

    def nth(self, n, duty='on', schedule=None):
        """Return n-th workshift with the specified duty in the interval.

        Parameters
        ----------
        n : int
            Zero-based sequence number of the workshift with the specified
            duty within the interval. 
            Negative values count from the end toward the beginning of 
            the interval (`n=-1` returns the last workshift with the specified
            duty). 
        duty : {``'on'``, ``'off``', ``'any``'} , optional (default ``'on'``)
            Duty of workshifts to be counted. If ``duty='on'``,
            off duty workshifts are ignored, and vice versa. If ``duty='any'``,
            all workshifts are counted whatever the duty.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.

        Returns
        -------
        :py:class:`.Workshift`

        Raises
        ------
        OutOfBoundsError
            If the requested workshift does not exist within the interval.

        Examples
        --------
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
        >>> ivl.nth(1)
        Workshift(5) of 'D' at 2017-10-05
        >>> ivl.nth(1, duty='off')
        Workshift(4) of 'D' at 2017-10-04
        >>> ivl.nth(1, duty='any')
        Workshift(3) of 'D' at 2017-10-03
        >>> ivl.nth(10)
        -----------------------------------------------------------------------
        OutOfBoundsError                      Traceback (most recent call last)
          ...
        OutOfBoundsError: Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 
        2017-10-08 [7] contains not enough on-duty workshifts for n=10  
        """
        if schedule is None:
            schedule = self.schedule
        duty_idx, duty_idx_bounds = self._get_duty_idx(duty, schedule)
        if duty_idx_bounds[0] is None or duty_idx_bounds[1] is None:
            return self._tb._handle_out_of_bounds(
                'Duty {!r} not found in interval {}'.format(duty,
                                                            self.compact_str))

        if n >= 0:
            loc_in_duty_idx = duty_idx_bounds[0] + n
        else:
            loc_in_duty_idx = duty_idx_bounds[1] + n + 1

        if (loc_in_duty_idx < duty_idx_bounds[0] or
                    loc_in_duty_idx > duty_idx_bounds[1]):
            return self._tb._handle_out_of_bounds(
                "{!r} contains not enough {}-duty workshifts for n={}".
                format(self, duty, n))

        return Workshift(self._tb, duty_idx[loc_in_duty_idx], schedule)

    def first(self, duty='on', schedule=None):
        """Return the first workshift with the specified duty in the interval.
        
        Same as ``nth(0, duty, schedule)``
        
        Examples
        --------
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
        >>> ivl.first()
        Workshift(3) of 'D' at 2017-10-03
        >>> ivl.first(duty='off')
        Workshift(2) of 'D' at 2017-10-02
        >>> ivl.first(duty='any')
        Workshift(2) of 'D' at 2017-10-02
        
        See also
        --------
        .nth :
            Return n-th workshift with the specified duty in the interval.
        """
        return self.nth(0, duty, schedule)

    def last(self, duty='on', schedule=None):
        """Return the last workshift with the specified duty in the interval.

        Same as ``nth(-1, duty, schedule)``

        Examples
        --------
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
        >>> ivl.last()
        Workshift(7) of 'D' at 2017-10-07
        >>> ivl.last(duty='off')
        Workshift(8) of 'D' at 2017-10-08
        >>> ivl.last(duty='any')
        Workshift(8) of 'D' at 2017-10-08

        See also
        --------
        .nth :
            Return n-th workshift with the specified duty in the interval.
        """
        return self.nth(-1, duty, schedule)

    def count(self, duty='on', schedule=None):
        """Return the count of interval's workshifts with the specified duty.
        
        Parameters
        ----------
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of workshifts to be counted. If ``duty='on'``,
            off-duty workshifts are ignored, and vice versa. If ``duty='any'``,
            all workshifts are counted whatever the duty.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.
            
        Returns
        -------
        int >=0
        
        Examples
        --------
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
        >>> ivl.count()
        3
        >>> ivl.count(duty='off')
        4
        >>> ivl.count(duty='any')
        7
        """
        if schedule is None:
            schedule = self.schedule
        _, duty_idx_bounds = self._get_duty_idx(duty, schedule)

        if duty_idx_bounds[0] is None or duty_idx_bounds[1] is None:
            return 0
        else:
            return duty_idx_bounds[1] - duty_idx_bounds[0] + 1

    def overlap(self, other, schedule=None):
        """Create the interval that is the intersection of two intervals.
        
        Parameters
        ----------
        other : Interval
        schedule : _Schedule, optional
            The schedule to be attached to the created interval.
            If `schedule` is not given, self's schedule is used. 
            The schedule attached to `other` is ignored in any case.
    
        Returns
        -------
        Interval
            The intersection of `self` and `other` intervals.
        
        Notes
        -----
        If the intervals do not overlap, a special object representing a void
        interval is returned. You can call the same methods on a void interval 
        as on a normal interval. Note that `start_time` and `end_time` 
        properties of a void interval return the null value (`pandas.NaT`).
        
        You can also use `*` (multiplication) operator with two intervals 
        to obtain their intersection. The resulting interval will get the
        schedule of the first operand.
        
        Examples
        --------
        
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        >>> ivl = tb.interval.Interval(clnd, (2,9))
        >>> other = tb.interval.Interval(clnd, (8,11))
        >>> ivl.overlap(other)
        Interval((8, 9)): 'D' at 2017-10-08 -> 'D' at 2017-10-09 [2]
        
        The use of `*` operator:
        
        >>> ivl * other
        Interval((8, 9)): 'D' at 2017-10-08 -> 'D' at 2017-10-09 [2]
        
        The case of no overlap:
        
        >>> other = tb.interval.Interval(clnd, (10,11))
        >>> void_ivl = ivl.overlap(other)
        >>> void_ivl
        Interval ((10, 9)): void [0]
        >>> len(void_ivl)
        0
        >>> void_ivl.count()
        0
        >>> list(void_ivl)
        []
        >>> void_ivl.start_time
        NaT
        >>> void_ivl.first(duty='any')
        -----------------------------------------------------------------------
        OutOfBoundsError                      Traceback (most recent call last)
          ...
        OutOfBoundsError: No workshifts in void interval Interval ((10, 9)): 
        void [0]
        
        """
        if schedule is None:
            schedule = self.schedule
        new_ivl_loc = (max(self._loc[0], other._loc[0]),
                       min(self._loc[1], other._loc[1]))
        try:
            return Interval(self._tb, new_ivl_loc, schedule=schedule)
        except VoidIntervalError:
            return _VoidInterval(self._tb, new_ivl_loc, schedule=schedule)

    def __mul__(self, other):
        """``x * y`` is the same as ``x.overlap(y)``
        """
        return self.overlap(other)

    # noinspection PyPep8Naming
    def count_periods(self, freq, duty='on', schedule=None):
        """Return how many calendar periods fit into the interval.
        
        The interval is sliced into calendar periods of the specified frequency
        and then each slice of the interval is compared to its corresponding 
        period duty-wise: the workshift count in the interval's slice is 
        divided by the total count of workshifts in the 
        period containing this slice; only workshifts with the specified 
        duty are counted. 
        
        The quotients for each period are summed to produce the return value 
        of the method.
        
        If a period does not contain workshifts of the required duty,
        it contributes zero to the returned value.
        
        Regardless of the period frequency, the method returns 0.0 if there 
        are no workshifts with the specified duty in the interval.

        Parameters
        ----------
        freq : str
            `pandas`-compatible frequency of calendar periods to be counted 
            (i.e. ``'M'`` for month). `pandas`-native business periods 
            (i.e. 'BM'), as well as  periods with multipliers (i.e. '3M'), 
            are not applicable.
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of workshifts to be accounted for. 
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.
            
        Returns
        -------
        float
            
        Raises
        ------
        OutOfBoundsError
            If the calendar period containing the first or the last 
            workshift of the interval (subject to duty) extends outside 
            the timeboard.
        UnacceptablePeriodError
            If `freq` is not valid for this method or is shorter than (some)
            workshifts in the interval.
        
        Examples
        --------
        >>> clnd = tb.Timeboard('H', '01 Oct 2017', '08 Oct 2017 23:59', 
        ...                     layout=[0,1])
        >>> ivl = clnd(('01 Oct 2017 11:00', '02 Oct 2017 23:59'))
        
        Interval `ivl` spans two days: it contains 13 of 24 workshifts of 
        October 1 and all 24 workshifts of October 2. 
        
        >>> ivl.count_periods('D', duty='any')
        1.5416666666666665
        >>> 13/24 + 24/24
        1.5416666666666665
        
        The timeboard's `layout` defines that all workshifts taking place on 
        even hours are off duty, and those on odd hours are on duty. 
        The first workshift of the interval (01 October 11:00 - 11:59) is 
        on duty. Hence, the interval contains 7 of 12 on duty workshifts 
        of October 1, and all 12 on duty workshifts of October 2.
        
        >>> ivl.count_periods('D')
        1.5833333333333335
        >>> 7/12 + 12/12
        1.5833333333333335
         
        The interval contains 6 of 12 off duty workshifts of October 1, 
        and all 12 off duty workshifts of October 2. 
        
        >>> ivl.count_periods('D', duty='off')
        1.5
        >>> 6/12 + 12/12
        1.5
        
        Note that we cannot count how many weeks are in this interval. The 
        workshifts of the interval belong to the weeks of Sep 25 - Oct 1 and 
        Oct 2 - Oct 8. The first of these extends beyond the timeboard. 
        We may not guess what layout *could* be applied to the workshifts of
        Sep 25 - Sep 30 if the week were included in the timeboard entirely.
        We are not authorized to extrapolate the existing layout outside the 
        timeboard. Moreover, for some complex layouts, any attempt at 
        extrapolation would be ambiguous.
        
        >>> ivl.count_periods('W')
        OutOfBoundsError                     Traceback (most recent call last)
          ...
        OutOfBoundsError: The 1st bound of interval or period referenced by 
        `2017-09-25/2017-10-01` is outside Timeboard of 'H': 2017-10-01 00:00 
        -> 2017-10-03 23:00
        """
        SUPPORTED_PERIODS = ('S', 'T', 'min', 'H', 'D', 'W', 'M', 'Q', 'A', 'Y')
        # TODO: support shifted periods (i.e. W-TUE, A-MAR)
        if freq not in SUPPORTED_PERIODS:
            raise UnacceptablePeriodError('Period {!r} is not supported'.
                                          format(freq))
        period_index = _Frame(start=self.start_time,
                              end=self.end_time,
                              base_unit_freq=freq)

        if schedule is None:
            schedule = self.schedule
        try:
            ivl_duty_start_ts = self.first(duty, schedule).to_timestamp()
            ivl_duty_end_ts = self.last(duty, schedule).to_timestamp()
        except OutOfBoundsError:
            return 0.0

        period_duty_count = []
        period_intervals = []
        for p in period_index:
            try:
                period_ivl = self._tb.get_interval(
                                p,
                                clip_period=False,
                                schedule=schedule
                             )
            except OutOfBoundsError:
                period_intervals.append(None)
                period_duty_count.append(None)
            except VoidIntervalError:
                raise UnacceptablePeriodError(
                    "Attempted to count periods {} that are shorter than "
                    "workshifts in interval {!r}".format(freq, self))
            else:
                period_intervals.append(period_ivl)
                period_duty_count.append(period_ivl.count(duty=duty,
                                                          schedule=schedule))

        first_period_with_duty_loc = period_index.get_loc(ivl_duty_start_ts)
        first_period_ivl = period_intervals[first_period_with_duty_loc]
        len_of_1st_period = period_duty_count[first_period_with_duty_loc]

        last_period_with_duty_loc = period_index.get_loc(ivl_duty_end_ts)
        last_period_ivl = period_intervals[last_period_with_duty_loc]
        len_of_last_period = period_duty_count[last_period_with_duty_loc]

        if ivl_duty_end_ts <= period_index[first_period_with_duty_loc].end_time:
            ivl_units_in_only_period = self.count(duty=duty, schedule=schedule)
            return ivl_units_in_only_period / len_of_1st_period

        result = 0.0
        ivl_units_in_1st_period = self._tb.get_interval(
            (ivl_duty_start_ts, first_period_ivl.end_time),
            clip_period=False,
            schedule=schedule
        ).count(duty=duty, schedule=schedule)
        result += ivl_units_in_1st_period / len_of_1st_period

        ivl_units_in_last_period = self._tb.get_interval(
            (last_period_ivl.start_time, ivl_duty_end_ts),
            clip_period=False,
            schedule=schedule
        ).count(duty=duty, schedule=schedule)
        result += ivl_units_in_last_period / len_of_last_period

        full_periods_in_ivl = last_period_with_duty_loc - \
            first_period_with_duty_loc - 1
        if full_periods_in_ivl > 0:
            result += sum(map(lambda x: x > 0,
                              period_duty_count[first_period_with_duty_loc+1:
                                                last_period_with_duty_loc])
                          )

        return result

    def what_portion_of(self, other, duty='on', schedule=None):
        """What portion of the other interval this interval takes up.

        The method returns the ratio of the workshift count in the intersection 
        of the two intervals to the workshift count in the `other` interval.
        Only workshifts with the specified duty are counted. 
        
        If the two intervals do not overlap or their intersection contains no
        workshifts with the specified duty, zero is returned.

        Parameters
        ----------
        other : Interval
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of workshifts to be accounted for. 
        schedule : _Schedule, optional
            If `schedule` is not given, self's schedule is used. 
            The schedule attached to `other` is ignored in any case.

        Returns
        -------
        float
        
        Notes
        -----
        You can also use `/` (division) operator.  
        ``x / y`` is the same as ``x.what_portion_of(y)``

        Examples
        --------
        >>> clnd = tb.Timeboard('D', '02 Oct 2017', '15 Oct 2017',
        ...                     layout=[1, 1, 1, 1, 1, 0, 0])
        >>> week1 = clnd('02 Oct 2017', period='W')
        
        `week1` contains five working days and two days off.
        
        >>> ivl = clnd(('05 Oct 2017', '07 Oct 2017'))
        
        `ivl` takes up days Thursday through Saturday of `week1` (two
        working days and one day off).

        >>> ivl.what_portion_of(week1)
        0.4
        >>> 2 / 5 # working days
        0.4
        
        >>> ivl.what_portion_of(week1, duty='off')
        0.5
        >>> 1 / 2 # days off
        0.5
        
        >>> ivl.what_portion_of(week1, duty='any')
        0.42857142857142855
        >>> 3 / 7 # all days
        0.42857142857142855
        
        Using `/` (division) operator calls `what_portion_of()` with the 
        default parameter values (so, the duty is 'on'):
        
        >>> ivl / week1
        0.4
        
        `ivl` and `week2` do not overlap:
        
        >>> week2 = clnd('09 Oct 2017', period='W')
        >>> ivl.what_portion_of(week2, duty='any')
        0.0
        
        `decade` includes the entire `week1` and extends beyond.
        
        >>> decade = clnd(('02 Oct 2017', '11 Oct 2017'))
        >>> decade.what_portion_of(week1)
        1.0
        
        >>> weekend = clnd(('07 Oct 2017', '08 Oct 2017'))
        
        All days of `weekend` are also the days of `week1` but they are not 
        working days, so:
        
        >>> weekend.what_portion_of(week1)
        0.0
        
        However, `weekend` contains all off duty days of `week1`:
        
        >>> weekend.what_portion_of(week1, duty='off')
        1.0
        """
        if schedule is None:
            schedule = self.schedule

        intersection = self.overlap(other, schedule=schedule)
        x_duty_count = intersection.count(duty=duty)
        if x_duty_count == 0:
            return 0.0
        else:
            return x_duty_count / other.count(duty=duty, schedule=schedule)

    def __truediv__(self, other):
        """``x / y`` is the same as ``x.what_portion_of(y)``
        """
        return self.what_portion_of(other)

    def __div__(self, other):
        """``x / y`` is the same as ``x.what_portion_of(y)``
        """
        return self.what_portion_of(other)

    def _sum_labels(self, duty='on', schedule=None):
        """Return the sum of labels of workshifts with the specified duty.
        
        Parameters
        ----------
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of workshifts whose labels are to be summed up. 
            If ``duty='on'``, off-duty workshifts are ignored, and vice versa. 
            If ``duty='any'``, all workshifts' labels are summed whatever 
            the duty.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.
            
        Returns
        -------
        Result of applying `sum` operation to labels. If labels are numbers, 
        the arithmetic sum is returned. If labels are strings, they are 
        concatenated.
        
        Raises
        ------
        TypeError
            When the type of the labels does not define `sum`.
            
        Examples
        --------
        >>> clnd = tb.Timeboard('D', '01 Oct 2017', '10 Oct 2017',
        ...                     layout=[1, 2],
        ...                     default_selector=lambda label: label > 1)
        >>> ivl = clnd()
        
        In this interval there are ten workshifts: five with label `1` that are 
        off duty and five with label `2` that are on duty.
        
        >>> ivl._sum_labels()
        10.0
        >>> ivl._sum_labels(duty='off')
        5.0
        >>> ivl._sum_labels(duty='any')
        15.0
        
        """
        if schedule is None:
            schedule = self.schedule
        duty_idx, duty_idx_bounds = self._get_duty_idx(duty, schedule)

        if duty_idx_bounds[0] is None or duty_idx_bounds[1] is None:
            return 0
        else:
            return self._tb._timeline[duty_idx[duty_idx_bounds[0]:
                                               duty_idx_bounds[1]+1]].sum()

    def total_duration(self, duty='on', schedule=None):
        """Return the total duration of workshifts with the specified duty.

        Parameters
        ----------
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of workshifts whose durations are counted. 
            If ``duty='on'``, off-duty workshifts are ignored, and vice versa. 
            If ``duty='any'``, durations of all workshifts are counted whatever 
            the duty.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.

        Returns
        -------
        int
            Total count of base units in the workshifts with the specified duty.
        
        Examples
        --------
        
        >>> org = tb.Organizer(marks = ['03 Oct 2017', '07 Oct 2017', 
        ...                             '09 Oct 2017'], 
        ...                    structure=[0,1]) 
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
        ...                     layout=org)
        >>> ivl = clnd()
        >>> print (ivl)
        Interval((0, 3)): 3x'D' at 2017-09-30 -> 3x'D' at 2017-10-09 [4]
        <BLANKLINE>
             workshift      start  duration        end  label  on_duty
        loc                                                           
        0   2017-09-30 2017-09-30         3 2017-10-02    0.0    False
        1   2017-10-03 2017-10-03         4 2017-10-06    1.0     True
        2   2017-10-07 2017-10-07         2 2017-10-08    0.0    False
        3   2017-10-09 2017-10-09         3 2017-10-11    1.0     True
        >>> ivl.total_duration()
        7
        >>> ivl.total_duration(duty='off')
        5
        >>> ivl.total_duration(duty='any')
        12
        """
        if schedule is None:
            schedule = self.schedule
        duty_idx, duty_idx_bounds = self._get_duty_idx(duty, schedule)

        if duty_idx_bounds[0] is None or duty_idx_bounds[1] is None:
            return 0
        else:
            return self._tb._timeline.get_durations_for_ws_array(
                duty_idx[duty_idx_bounds[0]:duty_idx_bounds[1]+1]).sum()

    def worktime(self, duty='on', schedule=None):
        """Return the total work time of workshifts with the specified duty.
        
        The source for work time values is determined by 
        :py:attr:`.Timeboard.worktime_source`.

        Parameters
        ----------
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of workshifts whose work times are counted. 
            If ``duty='on'``, off-duty workshifts are ignored, and vice versa. 
            If ``duty='any'``, work times of all workshifts are counted 
            whatever the duty.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used.

        Returns
        -------
        int or float
            The sum of work times of the workshifts with the specified duty or 
            zero if the interval does not contain workshifts with this duty.
            
        Raises
        ------
        TypeError
            If `worktime_source`='labels' but the labels could be summed up 
            to a number.
            
        Examples
        --------
        By default, workshift's work time equals to workshift's duration:

        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
        ...                     layout=[4, 8, 4, 8],
        ...                     default_selector = lambda label: label>4)
        >>> ivl = tb.Interval(clnd, (1, 3))
        >>> print (ivl)
        Interval((1, 3)): 'D' at 2017-10-01 -> 'D' at 2017-10-03 [3]
        <BLANKLINE>
             workshift      start  duration        end  label  on_duty
        loc                                                           
        1   2017-10-01 2017-10-01         1 2017-10-01    8.0     True
        2   2017-10-02 2017-10-02         1 2017-10-02    4.0    False
        3   2017-10-03 2017-10-03         1 2017-10-03    8.0     True
        >>> ivl.worktime()
        2
        >>> ivl.worktime(duty='off')
        1
        >>> ivl.worktime(duty='any')
        3
    
        In the example below, the work time is taken from the labels:
    
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
        ...                     layout=[4, 8, 4, 8],
        ...                     default_selector = lambda label: label>4,
        ...                     worktime_source = 'labels')
        >>> ivl = tb.Interval(clnd, (1, 3))
        >>> ivl.worktime()
        16.0
        >>> ivl.worktime(duty='off')
        4.0
        >>> ivl.worktime(duty='any')
        20.0
        """
        if self._tb.worktime_source == 'labels':
            result = self._sum_labels(duty=duty, schedule=schedule)
            try:
                result + 0
            except TypeError:
                raise TypeError('Workshift labels are expected to indicate '
                                'work time but could not be summed up '
                                'to a number.')
        elif self._tb.worktime_source == 'duration':
            result = self.total_duration(duty=duty, schedule=schedule)
        else:
            raise RuntimeError("Unrecognized worktime_source={!r}".
                               format(self._tb.worktime_source))
        return result


class _VoidInterval(Interval):
    """
    Empty interval containing no workshifts.
    
    `_VoidInterval` is returned by `Interval.overlap()` when the intervals 
    do not overlap. It is not supposed to be instantiated directly. 
    
    An attempt to create an empty interval with `Timeboard.get_interval()` or 
    by calling `Interval()` constructor will raise `VoidIntervalError`.
    
    Attributes
    ----------
    start_time : `pandas.NaT`
    end_time : `pandas.NaT`
    length : 0
    schedule : _Schedule
        Schedule is retained for the attribute compatibility with normal 
        intervals.

    """

    IS_VOID = True

    @property
    def compact_str(self):
        return "Interval ({!r}{}): void [0]".format(
            self._loc, self._repr_schedule_label())

    def __repr__(self):
        return self.compact_str

    def __str__(self):
        return self.compact_str

    @property
    def start_time(self):
        return VOID_TIME

    @property
    def end_time(self):
        return VOID_TIME

    def to_dataframe(self):
        raise NotImplementedError

    def workshifts(self, *args, **kwargs):
        raise StopIteration
        yield

    def nth(self, *args, **kwargs):
        return self._tb._handle_out_of_bounds(
            "No workshifts in void interval {}".
            format(self.compact_str))

    def count(self, *args, **kwargs):
        return 0

    def overlap(self, other, schedule=None):
        if schedule is None:
            schedule = self.schedule
        return _VoidInterval(self._tb, self._loc, schedule=schedule)

    def count_periods(self, *args, **kwargs):
        return 0.0

    def what_portion_of(self, other, *args, **kwargs):
        return 0.0

    def total_duration(self, *args, **kwargs):
        return 0

    def worktime(self, *args, **kwargs):
        return 0.0
