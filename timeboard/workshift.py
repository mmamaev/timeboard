from __future__ import division
from .exceptions import OutOfBoundsError
from .core import get_period, _Schedule
from numpy import searchsorted


class Workshift(object):
    """A period of time during which a business agent is either on or off duty. 
    
    A workshift consists of at least one base unit and may span 
    a number of consecutive base units. 
    
    Each workshift has a label. The label is interpreted by a given schedule 
    to determine whether the workshift is on duty or off duty under this 
    schedule.  The duty statuses of the same workshift can be different 
    under different schedules.
    
    Parameters
    ----------
    timeboard : :py:class:`.Timeboard`
    location : int >=0
        Position of the workshift on the timeline of the timeboard (zero-based).
    schedule : _Schedule, optional
        If not given, the timeboard's default schedule is used. 
        
    Raises
    ------
    OutOfBoundsError
        If `location` points outside the timeboard or is negative.
        
    Attributes
    ----------
    
    start_time : Timestamp
        When the workshift starts (the start time of workshift's first 
        base unit).
    end_time : Timestamp
        When the workshift ends (the end time of workshift's last base unit).
    duration : int >0
        Number of base units in the workshift.
    label
        An application-specific label associated with the workshift. 
        Schedule's `selector` interprets the label to identify the duty status
        of the workshift under this schedule.
    schedule : _Schedule
        Schedule used by workshift's methods unless explicitly redefined in 
        the method call. Use `name` attribute of `schedule` to review its 
        identity.

    See also
    --------
    .Timeboard.get_workshift :
        provides a convenient way 
        to instantiate a workshift from a point in time instead of calling 
        `Workshift()` constructor directly.
    
    Examples
    --------
    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
    >>> ws = tb.workshift.Workshift(clnd, 1)
    >>> ws
    Workshift(1) of 'D' at 2017-10-01
    
    >>> print(ws)
    Workshift(1) of 'D' at 2017-10-01
    <BLANKLINE>
            ws_ref      start  duration        end  label  on_duty
    loc                                                           
    1   2017-10-01 2017-10-01         1 2017-10-01    1.0     True
    """

    def __init__(self, timeboard, location, schedule=None):
        if schedule is None:
            schedule = timeboard.default_schedule
        if not isinstance(schedule, _Schedule):
            raise TypeError('Wrong type of schedule. Expected _Schedule,'
                            ' received {}'.format(type(schedule)))
        try:
            self._label = schedule.label(location)
        except TypeError:
            raise TypeError('Workshift location = `{!r}`: expected '
                            'integer-like '
                            'received {}'.format(location, type(location)))
        except IndexError:
            raise OutOfBoundsError("Workshift location {} "
                                   "is outside timeboard {}".
                                   format(location, timeboard.compact_str))
        self._tb = timeboard
        self._loc = location
        self._schedule = schedule

    def _repr_schedule_label(self):
        schedule_label = self.schedule.name
        if schedule_label == self._tb.default_schedule.name:
            schedule_label = ""
        else:
            schedule_label = ", " + schedule_label
        return schedule_label

    def __repr__(self):

        return "Workshift({}{}) of ".format(
                self._loc, self._repr_schedule_label()) + self.compact_str

    @property
    def compact_str(self):
        duration_str = ''
        if self.duration != 1:
            duration_str = str(self.duration) + 'x'
        return "{}'{}' at {}".format(duration_str,
                                     self._tb.base_unit_freq,
                                     get_period(self.start_time,
                                                freq=self._tb.base_unit_freq))

    def __str__(self):
        return "Workshift({}{}) of ".format(
                self._loc, self._repr_schedule_label()) + self.compact_str + \
               "\n\n{}".format(self._tb.to_dataframe(self._loc, self._loc))

    @property
    def start_time(self):
        # TODO: Refactor. _Timeline methods should not be called from this class
        return self._tb._timeline.get_ws_start_time(self._loc)

    @property
    def end_time(self):
        # TODO: Refactor. _Timeline methods should not be called from this class
        return self._tb._timeline.get_ws_end_time(self._loc)

    @property
    def duration(self):
        # TODO: Refactor. _Timeline methods should not be called from this class
        return self._tb._timeline.get_ws_duration(self._loc)

    @property
    def label(self):
        return self._label

    @property
    def schedule(self):
        return self._schedule

    def to_timestamp(self):
        """The characteristic time used to represent the workshift. 
        
        The rule to calculate the timestamp is defined by `workshift_ref` 
        parameter of the timeboard.
        
        Returns
        -------
        Timestamp
        """
        # TODO: Refactor. _Timeline methods should not be called from this class
        return self._tb._timeline.get_ws_ref_time(self._loc)

    def is_on_duty(self, schedule=None):
        """True if the workshift is on duty under a specific schedule.

        Parameters
        ----------
        schedule : _Schedule, optional
            If `schedule` is not given, the workshift's schedule is used.
            
        Returns
        -------
        bool
        
        """
        if schedule is None:
            schedule = self.schedule
        return schedule.is_on_duty(self._loc)

    def is_off_duty(self, schedule=None):
        """True if the workshift is off duty under a specific schedule.

        Parameters
        ----------
        schedule : _Schedule, optional
            If `schedule` is not given, the workshift's schedule is used.

        Returns
        -------
        bool
        
        """

        if schedule is None:
            schedule = self.schedule
        return schedule.is_off_duty(self._loc)

    def _get_duty_index(self, duty, schedule):
        i_am_on_duty = self.is_on_duty(schedule)
        i_am_off_duty = self.is_off_duty(schedule)
        if (duty == 'on') or (duty == 'same' and i_am_on_duty) or (
                        duty == 'alt' and i_am_off_duty):
            idx = schedule.on_duty_index
        elif (duty == 'off') or (duty == 'same' and i_am_off_duty) or (
                        duty == 'alt' and i_am_on_duty):
            idx = schedule.off_duty_index
        elif duty == 'any':
            idx = schedule.index
        else:
            raise ValueError("Invalid duty {!r}".format(duty))
        return idx

    def rollforward(self, steps=0, duty='on', schedule=None):
        """
        Find a workshift by taking the specified number of steps to the future. 
        
        `duty` parameter selects which workshifts are counted as steps.
        
        Parameters
        ----------
        steps : int, optional (default 0)
        duty : {``'on'``, ``'off'``, ``'same'``, ``'alt'``, ``'any'``}, optional
            - ``'on'`` : (default) step on on-duty workshifts only
            - ``'off'`` : step on off-duty workshifts only
            - ``'same'`` : step only on workshifts with the same duty status 
              as self
            - ``'alt'`` : step only on workshifts with the duty status other 
              than that of self
            - ``'any'`` : step on all workshifts
        schedule : _Schedule, optional
            If `schedule` is not given, the workshift's schedule is used.
    
        Returns
        -------
        Workshift
        
        Raises
        ------
        OutOfBoundsError
            If the method attempted to roll outside the timeboard.

        Notes
        -----
        The method is executed in two stages. The first stage finds the 
        workshift corresponding to step 0. The second stage fulfills the 
        required number of steps (if any) starting from the zero step 
        workshift.
        
        If self has the same duty as specified by `duty` parameter, then 
        the zero step workshift is self, otherwise, it is the first workshift 
        toward the future which conforms to `duty` parameter. If `steps`=0,
        the method terminates here and returns the zero step workshift.
         
        If `steps` is positive, the method counts workshifts toward the future
        stepping only on workshifts with the specified duty and returns the 
        last workshift on which it has stepped. For example, with `steps`=1 the 
        method returns the workshift following the zero step workshift, 
        subject to duty.
        
        If `steps` is negative, the method works in the same way but moving
        toward the past from the zero step workshift. For example, with 
        `steps`=-1 the method returns the workshift preceding the zero step 
        workshift, subject to duty. 
        
        Note that the zero step workshift is sought toward the future 
        even if `steps` is negative.
        
        See also
        --------
        __add__ :  
            ``ws + n`` is the same as ``ws.rollforward(n, duty='on')``
        .rollback : 
            Return a workshift which is in the specified number of steps in
            the past. Methods `rollback` and `rollforward` differ in the 
            definition of the zero step workshift and the default direction 
            of stepping.
            
        Examples
        --------
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        
        In this timeboard odd dates are on duty and even dates are off duty.
        
        >>> ws1 = clnd('05 Oct 2017')
        >>> ws1.is_on_duty()
        True
        >>> ws1.rollforward()
        Workshift(5) of 'D' at 2017-10-05
        >>> ws1.rollforward(1)
        Workshift(7) of 'D' at 2017-10-07
        >>> ws1 + 1
        Workshift(7) of 'D' at 2017-10-07
        >>> ws1.rollforward(-1)
        Workshift(3) of 'D' at 2017-10-03
        >>> ws1.rollforward(duty='off')
        Workshift(6) of 'D' at 2017-10-06
        >>> ws1.rollforward(1, duty='off')
        Workshift(8) of 'D' at 2017-10-08
        >>> ws1.rollforward(-1, duty='off')
        Workshift(4) of 'D' at 2017-10-04
        
        >>> ws0 = clnd('06 Oct 2017')
        >>> ws0.is_off_duty()
        True
        >>> ws0.rollforward()
        Workshift(7) of 'D' at 2017-10-07
        >>> ws0.rollforward(1)
        Workshift(9) of 'D' at 2017-10-09
        >>> ws0 + 1
        Workshift(9) of 'D' at 2017-10-09
        >>> ws0.rollforward(-1)
        Workshift(5) of 'D' at 2017-10-05
        >>> ws0.rollforward(duty='off')
        Workshift(6) of 'D' at 2017-10-06
        >>> ws0.rollforward(1, duty='off')
        Workshift(8) of 'D' at 2017-10-08
        >>> ws0.rollforward(-1, duty='off')
        Workshift(4) of 'D' at 2017-10-04
        
        Note that ``ws0.rollforward(-1)`` and ``ws0 - 1`` produce different 
        results:

        >>> ws0.rollforward(-1)
        Workshift(5) of 'D' at 2017-10-05
        >>> ws0 - 1
        Workshift(3) of 'D' at 2017-10-03
        
        This happens because ``ws0.rollforward(-1)`` assumes the default 
        `duty='on'` and seeks the zero step "on duty" workshift by moving 
        forward from "off duty" self (October 6). Thus the zero step workshift 
        will be October 7. From that point the method takes one "on duty" step 
        to the past and arrives at October 5 which is the result.
        
        On the contrary, ``ws0 - 1`` calls ``ws0.rollback(1, duty='on')`` 
        which seeks the zero step "on duty" workshift by moving backward from
        self. Thus the zero step workshift will be October 5, and one "on duty" 
        step to the past from that will be the result, October 3. 
        """
        if schedule is None:
            schedule = self.schedule
        idx = self._get_duty_index(duty, schedule)

        len_idx = len(idx)
        i = searchsorted(idx, self._loc)
        if i == len_idx or i + steps < 0 or i + steps >= len_idx:
            return self._tb._handle_out_of_bounds(
                "Rollforward of ws {} with steps={}, duty={}, schedule={}.".
                format(self.compact_str, steps, duty, schedule.name))

        return Workshift(self._tb, idx[i + steps], schedule)

    def rollback(self, steps=0, duty='on', schedule=None):
        """
        Find a workshift by taking the specified number of steps to the past. 

        `duty` parameter selects which workshifts are counted as steps.

        Parameters
        ----------
        steps : int, optional (default 0)
        duty : {``'on'``, ``'off'``, ``'same'``, ``'alt'``, ``'any'``}, optional
            - ``'on'`` : (default) step on on-duty workshifts only
            - ``'off'`` : step on off-duty workshifts only
            - ``'same'`` : step only on workshifts with the same duty status 
              as self
            - ``'alt'`` : step only on workshifts with the duty status other 
              than that of self
            - ``'any'`` : step on all workshifts
        schedule : _Schedule, optional
            If `schedule` is not given, the workshift's schedule is used.

        Returns
        -------
        Workshift

        Raises
        ------
        OutOfBoundsError
            If the method attempted to roll outside the timeboard.

        Notes
        -----
        The method is executed in two stages. The first stage finds the 
        workshift at step 0. The second stage fulfills the required number of 
        steps (if any) starting from the zero step workshift.
        
        If self has the same duty as specified by `duty` parameter, then 
        the zero step workshift is self, otherwise, it is the first workshift 
        toward the past which conforms to `duty` parameter. If `steps`=0,
        the method terminates here and returns the zero step workshift.
        
        If `steps` is positive, the method counts workshifts toward the past
        stepping only on workshifts with the specified duty and returns the 
        last workshift on which it has stepped. For example, with `steps`=1 the 
        method returns the workshift preceding the zero step workshift, 
        subject to duty.
        
        If `steps` is negative, the method works in the same way but moving
        toward the future from the zero step workshift. For example, with 
        `steps`=-1 the method returns the workshift following the zero step 
        workshift, subject to duty.
        
        Note that the zero step workshift is sought in the past 
        even if `steps` is negative.

        See also
        --------
        __sub__ :  
            ``ws - n`` is the same as ``ws.rollback(n, duty='on')``
        .rollforward : 
            Return a workshift which is in the specified number of steps in  
            the future. Methods `rollback` and `rollforward` differ in the 
            definition of the zero step workshift and the default direction 
            of stepping.

        Examples
        --------
        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
        
        In this timeboard odd dates are on duty and even dates are off duty.
        
        >>> ws1 = clnd('05 Oct 2017')
        >>> ws1.is_on_duty()
        True
        >>> ws1.rollback()
        Workshift(5) of 'D' at 2017-10-05
        >>> ws1.rollback(1)
        Workshift(3) of 'D' at 2017-10-03
        >>> ws1 - 1
        Workshift(3) of 'D' at 2017-10-03
        >>> ws1.rollback(-1)
        Workshift(7) of 'D' at 2017-10-07
        >>> ws1.rollback(duty='off')
        Workshift(4) of 'D' at 2017-10-04
        >>> ws1.rollback(1, duty='off')
        Workshift(2) of 'D' at 2017-10-02
        >>> ws1.rollback(-1, duty='off')
        Workshift(6) of 'D' at 2017-10-06
        
        >>> ws0 = clnd('06 Oct 2017')
        >>> ws0.is_off_duty()
        True
        >>> ws0.rollback()
        Workshift(5) of 'D' at 2017-10-05
        >>> ws0.rollback(1)
        Workshift(3) of 'D' at 2017-10-03
        >>> ws0 - 1
        Workshift(3) of 'D' at 2017-10-03
        >>> ws0.rollback(-1)
        Workshift(7) of 'D' at 2017-10-07
        >>> ws0.rollback(duty='off')
        Workshift(6) of 'D' at 2017-10-06
        >>> ws0.rollback(1, duty='off')
        Workshift(4) of 'D' at 2017-10-04
        >>> ws0.rollback(-1, duty='off')
        Workshift(8) of 'D' at 2017-10-08
        
        Note that ``ws0.rollback(-1)`` and ``ws0 + 1`` produce different 
        results:
        
        >>> ws0.rollback(-1)
        Workshift(7) of 'D' at 2017-10-07
        >>> ws0 + 1
        Workshift(9) of 'D' at 2017-10-09
        
        This happens because ``ws0.rollback(-1)`` assumes the default 
        `duty='on'` and seeks the zero step "on duty" workshift by moving 
        backwards from "off duty" self (October 6). Thus the zero step 
        workshift will be October 5. From that point the method takes one 
        "on duty" step to the future and arrives at October 7 which is the 
        result.
        
        On the contrary, ``ws0 + 1`` calls ``ws0.rollforward(1, duty='on')`` 
        which seeks the zero step "on duty" workshift by moving forward from
        self. Thus the zero step workshift will be October 7, and one "on duty" 
        step to the future from that will be the result, October 9. 
        """
        # TODO: Optimize rollback and rollforward to comply with DRY?
        if schedule is None:
            schedule = self.schedule
        idx = self._get_duty_index(duty, schedule)

        # TODO: Optimize this search
        len_idx = len(idx)
        i = len_idx - 1
        while i >= 0 and idx[i] > self._loc:
            i -= 1

        if i == -1 or i - steps < 0 or i - steps >= len_idx:
            return self._tb._handle_out_of_bounds(
                "Rollback of ws {} with steps={}, duty={}, schedule={}.".
                format(self.compact_str, steps, duty, schedule.name))

        return Workshift(self._tb, idx[i - steps], schedule)

    def worktime(self, duty='on', schedule=None):
        """Return the work time for the worker with the specified duty.
        
        The source for the work time value is determined by 
        :py:attr:`.Timeboard.worktime_source`.

        Parameters
        ----------
        duty : {``'on'``, ``'off'``, ``'any'``} , optional (default ``'on'``)
            Specify the duty of the worker.
        schedule : _Schedule, optional
            If `schedule` is not given, the interval's schedule is used to 
            determine the duty.

        Returns
        -------
        int or float
            Either workshift's duration or label, depending on the value
            of `worktime_source`. However, if the workshift's duty 
            is not the same as worker's `duty`, zero is returned.

        Raises
        ------
        TypeError
            If `worktime_source`='labels' but the workshift's label is not 
            a number.
            
        Examples
        --------
        By default, the work time equals to workshift's duration:

        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
        ...                     layout=[4, 8, 4, 8],
        ...                     default_selector = lambda label: label>4)
        >>> ws = tb.Workshift(clnd, 3)
        >>> ws.label
        8.0
        >>> ws.duration
        1
        >>> ws.is_on_duty()
        True
        >>> ws.worktime()
        1
        >>> ws.worktime(duty='off')
        0
        >>> ws.worktime(duty='any')
        1

        In the example below, the work time is taken from the labels:

        >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
        ...                     layout=[4, 8, 4, 8],
        ...                     default_selector = lambda label: label>4,
        ...                     worktime_source = 'labels')
        >>> ws = tb.Workshift(clnd, 3)
        >>> ws.worktime()
        8.0
        >>> ws.worktime(duty='off')
        0
        >>> ws.worktime(duty='any')
        8.0
        >>> ws = tb.Workshift(clnd, 2)
        >>> ws.label
        4.0
        >>> ws.is_off_duty()
        True
        >>> ws.worktime()
        0
        >>> ws.worktime(duty='off')
        4.0
        >>> ws.worktime(duty='any')
        4.0
        """
        if schedule is None:
            schedule = self.schedule
        duty_flags = {'on': self.is_on_duty(schedule=schedule),
                      'off': self.is_off_duty(schedule=schedule),
                      'any': True}
        try:
            duty_flag = duty_flags[duty]
        except KeyError:
            raise ValueError("Invalid duty {!r}.".format(duty))
        if duty_flag:
            if self._tb.worktime_source == 'labels':
                try:
                    _ = self.label + 0
                except TypeError:
                    raise TypeError('Workshift label {!r} is expected to '
                                    'indicate work time but it is not '
                                    'a number.')
                return self.label
            elif self._tb.worktime_source == 'duration':
                return self.duration
            else:
                raise RuntimeError("Unrecognized worktime_source={!r}".
                                   format(self._tb.worktime_source))
        else:
            return 0

    def __add__(self, other):
        """``ws + n`` is the same as ``ws.rollforward(n, duty='on')``"""
        if isinstance(other, int):
            return self.rollforward(steps=other, duty='on')
        else:
            return NotImplemented

    def __sub__(self, other):
        """``ws - n`` is the same as ``ws.rollback(n, duty='on')``"""
        if isinstance(other, int):
            return self.rollback(steps=other, duty='on')
        elif isinstance(other, type(self)):
            return NotImplemented
        else:
            return NotImplemented
