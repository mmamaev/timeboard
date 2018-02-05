from __future__ import division
from .exceptions import (OutOfBoundsError,
                         VoidIntervalError,
                         UnacceptablePeriodError)
from .workshift import Workshift
from .core import _Frame, _Schedule


class Interval(object):
    """A sequence of workshifts within the timeboard.
    
    Interval is defined by two positions on the timeline which are
    the zero-based sequence numbers of the first and the last workshifts 
    of the interval. An interval can contain one or more workshifts; the
    empty interval is not allowed.
    
    Duty status of the workshifts within the interval is interpreted by the 
    given schedule.
    
    In addition to the methods defined for intervals, you can use an interval 
    as a generator that yields the workshifts.
    
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
    labels : list 
        List of workshift labels in the interval.
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
       
    >>> ivl.labels
    [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    
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
    """

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
        if locs[0] > locs[1]:
            raise VoidIntervalError('Attempted to create void interval with '
                                    '{!r}'.format(locs))
        self._tb = timeboard
        self._loc = locs
        self._length = self._loc[1] - self._loc[0] + 1
        if schedule is None:
            self._schedule = timeboard.default_schedule
        else:
            self._schedule = schedule
        if not isinstance(self._schedule, _Schedule):
            raise TypeError('Wrong type of schedule. Expected _Schedule,'
                            ' received {}'.format(type(schedule)))

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
    def labels(self):
        return list(self._tb._timeline[self._loc[0]: self._loc[1]+1])

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

    def _ws_generator(self):
        for i in range(self._loc[0], self._loc[1]+1):
            yield Workshift(self._tb, i, schedule=self.schedule)

    def __next__(self):
        return next(self._ws_generator_activated)

    def next(self):
        return self.__next__()

    def __iter__(self):
        self._ws_generator_activated = self._ws_generator()
        return self

    def __len__(self):
        return self._length

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
                "No {} {!r} workshifts in the interval {}".
                format(n, duty, self.compact_str))

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

    # noinspection PyPep8Naming
    def count_periods(self, period, duty='on', schedule=None):
        """Return how many calendar periods fit into the interval.
        
        The interval is sliced into calendar periods of the specified frequency
        and then each slice of the interval is compared to its corresponding 
        period duty-wise. That is to say, the count of workshifts in the 
        interval's slice is divided by the total count of workshifts in the 
        period containing this slice but only workshifts with the specified 
        duty are counted. The quotients for each period are summed to produce 
        the return value of the method.
        
        If a period does not contain workshifts of the required duty,
        it contributes zero to the returned value.
        
        Regardless of the period frequency, the method returns 0.0 if there 
        are no workshifts with the specified duty in the interval.

        Parameters
        ----------
        period : str
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
            If `period` is not valid for this method or is shorter than (some)
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
        if period not in SUPPORTED_PERIODS:
            raise UnacceptablePeriodError('Period {!r} is not supported'.
                                          format(period))
        if schedule is None:
            schedule = self.schedule
        try:
            ivl_duty_start_ts = self.first(duty, schedule).to_timestamp()
            ivl_duty_end_ts = self.last(duty, schedule).to_timestamp()
        except OutOfBoundsError:
            return 0.0

        period_index = _Frame(start=self.start_time,
                              end=self.end_time,
                              base_unit_freq=period)
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
                    "workshifts in interval {!r}".format(period, self))
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

    def sum(self, duty='on', schedule=None):
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
            When the type of labels does not define `sum`.
            
        Examples
        --------
        >>> clnd = tb.Timeboard('D', '01 Oct 2017', '10 Oct 2017',
        ...                     layout=[1, 2],
        ...                     default_selector=lambda label: label > 1)
        >>> ivl = clnd()
        
        In this interval there are ten workshifts: five with label `1` that are 
        off duty and five with label `2` that are on duty.
        
        >>> ivl.sum()
        10.0
        >>> ivl.sum(duty='off')
        5.0
        >>> ivl.sum(duty='any')
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

    def where(self, ws, duty='same'):
        # TODO: Interval.where
        raise NotImplementedError

    def where_period(self, reference, period, duty='same'):
        # TODO: Interval.where_period
        raise NotImplementedError
