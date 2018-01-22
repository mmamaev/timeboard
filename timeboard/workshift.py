from __future__ import division
from .exceptions import OutOfBoundsError
from .core import get_period
from numpy import searchsorted


class Workshift(object):
    """A period of time during which a business agent is either on or off duty. 
    
    Timeboard's timeline is a sequence of workshifts. A workshift 
    consists of at least one base unit and may span a number of consecutive 
    base units. 
    
    Each workshift has a label. The label is interpreted by a given schedule 
    to determine whether the workshift is on duty or off duty under this 
    schedule.  The duty statuses of the same workshift can be different 
    under different schedules.
    
    Parameters
    ----------
    timeboard : Timeboard
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
        When the workshift starts.
    end_time : Timestamp
        When the workshift ends.
    duration : int >0
        Number of base unit making up the workshift.
    label
        An application-specific label associated with the workshift. 
        Schedule's `selector` interprets the label to identify the duty status
        of the workshift under this schedule.
    schedule : _Schedule
        Schedule used by workshift's methods unless explicitly redefined in 
        the method call. Use `name` attribute of `schedule` to review its 
        identity.
    
    Examples
    --------
    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', layout=[0,1])
    >>> tb.workshift.Workshift(clnd, 1)
    Workshift(1) of 'D' at 2017-10-01
    
    Notes
    -----
    Calling  Timeboard's instance or its `get_workshift` method provides a
    convenient way to instantiate a workshift from a point in time instead of 
    calling Workshift() constructor directly.
    """

    def __init__(self, timeboard, location, schedule=None):
        if schedule is None:
            schedule = timeboard.default_schedule
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

    def __repr__(self):
        return "Workshift({}) of ".format(self._loc) + self.compact_str

    @property
    def compact_str(self):
        duration_str = ''
        if self.duration != 1:
            duration_str = str(self.duration) + 'x'
        return "{}'{}' at {}".\
                format(duration_str,
                       self._tb.base_unit_freq,
                       get_period(self.to_timestamp(),
                                  freq=self._tb.base_unit_freq))

    def __str__(self):
        return "Workshift({}) of ".format(self._loc) + self.compact_str + \
               "\n\n{}".format(self._tb.to_dataframe(self._loc, self._loc))

    @property
    def start_time(self):
        """Timestamp of the start of the workshift"""
        # TODO: Refactor. _Timeline methods should not be called from this class
        return self._tb._timeline.get_ws_start_time(self._loc)

    @property
    def end_time(self):
        """Timestamp of the end of the workshift"""
        # TODO: Refactor. _Timeline methods should not be called from this class
        return self._tb._timeline.get_ws_end_time(self._loc)

    @property
    def duration(self):
        """Number of base units in the workshift"""
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
            raise ValueError("Unrecognized duty {!r}".format(duty))
        return idx

    def rollforward(self, steps=0, duty='on', schedule=None):
        """
        Return a workshift which is `steps` workshifts away in the future. 
        
        `duty` parameter selects which workshifts are counted as steps.
        
        Parameters
        ----------
        steps : int, optional (default 0)
        duty : {'on', 'off', 'same', 'alt', 'any'} , optional (default 'on')
            'on' : step on on-duty workshifts only
            'off' : step on off-duty workshifts only
            'same' : step only on workshifts with the same duty status as self
            'alt' : step only on workshifts with the duty status other than 
            that of self
            'any' : step on all workshifts
        schedule : _Schedule, optional
            If `schedule` is not given, the workshift's schedule is used.
    
        Returns
        -------
        Workshift
        
        Raises
        ------
        OutOfBoundsError (LookupError)
            If the method attempted to roll outside the timeboard.

        Notes
        -----
        The method is executed in two stages. The first stage finds the 
        workshift at step 0. The second stage fulfils the required number of 
        steps (if any) starting from the zero step workshift.
        
        If self has the same duty as specified by `duty` parameter, then 
        the zero step workshift is self, otherwise it is the first workshift 
        toward the future which conforms to `duty` parameter. If `steps`=0,
        the method terminates here and returns the zero step workshift.
         
        If `steps` is positive, the methods counts workshifts toward the future
        stepping only on workshifts with the specified duty, and returns the 
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
        + (__add__) :  `ws + n` is the same as ws.rollforward(n, duty='on')
        rollback : return a workshift from the past
            `rollback` differs from `rollforward` in the definition of 
            the zero step workshift and the default direction of stepping.
        """
        if schedule is None:
            schedule = self.schedule
        idx = self._get_duty_index(duty, schedule)

        len_idx = len(idx)
        i = searchsorted(idx, self._loc)
        if i == len_idx or i + steps < 0 or i + steps >= len_idx:
            return self._tb._handle_out_of_bounds("Rollforward of ws {} with "
                       "steps={}, duty={}, schedule={}"
                       ".".format(self.to_timestamp(), steps, duty,
                                  schedule.name))

        return Workshift(self._tb, idx[i + steps], schedule)

    def rollback(self, steps=0, duty='on', schedule=None):
        """
        Return a workshift which is `steps` workshifts away in the past. 
        
        `duty` parameter selects which workshifts are counted as steps.

        Parameters
        ----------
        steps : int, optional (default 0)
        duty : {'on', 'off', 'same', 'alt', 'any'} , optional (default 'on')
            'on' : step on on-duty workshifts only
            'off' : step on off-duty workshifts only
            'same' : step only on workshifts with the same duty status as self
            'alt' : step only on workshifts with the duty status other than 
            that of self
            'any' : step on all workshifts
        schedule : _Schedule, optional
            If `schedule` is not given, the workshift's schedule is used.
    
        Returns
        -------
        Workshift
        
        Raises
        ------
        OutOfBoundsError (LookupError)
            If the method attempted to roll outside the timeboard.

        Notes
        -----
        The method is executed in two stages. The first stage finds the 
        workshift at step 0. The second stage fulfils the required number of 
        steps (if any) starting from the zero step workshift.
        
        If self has the same duty as specified by `duty` parameter, then 
        the zero step workshift is self, otherwise it is the first workshift 
        toward the past which conforms to `duty` parameter. If `steps`=0,
        the method terminates here and returns the zero step workshift.
         
        If `steps` is positive, the methods counts workshifts toward the past
        stepping only on workshifts with the specified duty, and returns the 
        last workshift on which it has stepped. For example, with `steps`=1 the 
        method returns the workshift preceding the zero step workshift, 
        subject to duty.
        
        If `steps` is negative, the method works in the same way but moving
        toward the future from the zero step workshift. For example, with 
        `steps`=-1 the method returns the workshift following the zero step 
        workshift, subject to duty.
        
        Note that the zero step workshift is sought toward the past 
        even if `steps` is negative.
        
        See also
        --------
        - (__sub__) :  `ws - n` is the same as ws.rollback(n, duty='on')
        rollforward : return a workshift from the future
            `rollforward` differs from `rollback` only in the definition of 
            the zero step workshift and the default direction of stepping.
        """
        # TODO: Optimize rollback and rolloforward to compy with DRY?
        if schedule is None:
            schedule = self.schedule
        idx = self._get_duty_index(duty, schedule)

        # TODO: Optimize this search
        len_idx = len(idx)
        i = len_idx - 1
        while i >= 0 and idx[i] > self._loc:
            i -= 1

        if i == -1 or i - steps < 0 or i - steps >= len_idx:
            return self._tb._handle_out_of_bounds("Rollback of ws {} with "
                       "steps={}, duty={}, schedule={}"
                       ".".format(self.to_timestamp(), steps, duty,
                                  schedule.name))

        return Workshift(self._tb, idx[i - steps], schedule)

    def __add__(self, other):
        """ws + n is the same as ws.rollforward(n, duty='on')"""
        if isinstance(other, int):
            return self.rollforward(steps=other, duty='on')
        else:
            return NotImplemented

    def __sub__(self, other):
        """ws - n is the same as ws.rollback(n, duty='on')"""
        if isinstance(other, int):
            return self.rollback(steps=other, duty='on')
        elif isinstance(other, type(self)):
            return NotImplemented
        else:
            return NotImplemented
