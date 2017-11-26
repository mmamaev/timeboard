from .exceptions import OutOfBoundsError, VoidIntervalError
from .core import Period, NaT


class Workshift:
    """A constituent of timeboard. 
    
    Timeboard's timeline is a sequence of workshifts. Each workshift has
    a label which defines whether this workshift is on-duty or off-duty.
    A workshift is made of one or more consecutive base units. 
    
    Parameters
    ----------
    timeboard : instance of Timeboard
    location : int (>=0)
        Position of the workshift on the timeline of the timeboard (zero-based).
        
    Raises
    ------
    OutOfBoundsError (LookupError)
        If `location` points outside the timeboard or is negative.
        
    Attributes
    ----------
    start_time : Timestamp
        When the workshift starts.
    end_time : Timestamp
        When the workshift ends.
    ref : Timestamp
        The characteristic time used to represent the workshift. The rule to
        calculate `ref` is defined by `workshift_ref` parameter of the 
        timeboard.
    duration : int (>0)
        Number of base unit making up the workshift.
    label
        An application-specific label associated with the workshift. 
        Timeboard's `selector` method interprets the label to identify the duty
        of the workshift.
    is_on_duty : bool
        True if the workship is on-duty.
    is_off_duty : bool
        True if the workship is off-duty.
    
    Notes
    -----
    Calling  Timeboard's instance or its `get_workshift` method provides a
    convenient way to instantiate a workshift from a point in time instead of 
    calling Workshift() constructor directly. 
    """

    def __init__(self, timeboard, location):

        if not isinstance(location, int):
            raise TypeError('Workshift location = {}: expected integer '
                            'received '.format(location, type(location)))
        if not 0 <= location <= len(timeboard._timeline):
            raise OutOfBoundsError("Workshift location {} "
                                   "is outside timeboard {}".
                                   format(location, timeboard))
        self._tb = timeboard
        self._loc = location

    @property
    def start_time(self):
        # TODO: Refactor. This class has to know methods of Timeboard only
        return self._tb._timeline.frame[self._loc].start_time

    @property
    def end_time(self):
        # TODO: Refactor. This class has to know methods of Timeboard only
        return self._tb._timeline.frame[self._loc].end_time

    @property
    def ref(self):
        if self._tb.workshift_ref == 'end':
            return self.end_time
        else:
            return self.start_time

    def __repr__(self):
        return "Workshift(tb, {})\ntb={}".format(self._loc, self._tb)

    def __str__(self):
        duration_str = ''
        if self.duration != 1:
            duration_str = str(self.duration)
        return "Workshift '{}{}' at {}".\
                format(duration_str,
                       self._tb.base_unit_freq,
                       Period(self.ref, freq=self._tb.base_unit_freq))

    @property
    def label(self):
        # TODO: Refactor. This class has to know methods of Timeboard only
        return self._tb._timeline.iloc[self._loc]

    @property
    def is_on_duty(self):
        return self._tb.selector(self.label)

    @property
    def is_off_duty(self):
        return not self.is_on_duty

    @property
    def is_void(self):
        return False

    @property
    def duration(self):
        # TODO: Support workshifts containing  variable numbers of BU
        return 1

    def rollforward(self, steps=0, duty='on'):
        """
        Return a workshift which is `steps` workshifts away in the future. 
        
        `duty` parameter selects which workshifts are counted as steps.
        
        Parameters
        ----------
        steps: int, optional (default 0)
        duty: {'on', 'off', 'same', 'alt', 'any'} , optional (default 'on')
            'on' - step on on-duty workshifts only
            'off' - step on off-duty workshifts only
            'same' - step only on workshifts with the same duty status as self
            'alt' - step only on workshifts with the duty status other than 
            that of self
            'any' - step on all workshifts
    
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
        last workshift on which it stepped. For example, with `steps`=1 the 
        method returns the workshift following the zero step workshift, 
        subject to duty.
        
        If `steps` is negative, the method works in the same way but moving
        toward the past from the zero step workshift. For example, with 
        `steps`=-1 the method returns the workshift preceding the zero step 
        workshift, subject to duty.
        
        See also
        --------
        + (__add__) :  `ws + n` is the same as ws.rollforward(n, duty='on')
        rollback : return a workshift from the past
            `rollback` differs from `rollforward` only in the definition of 
            the zero step workshift and the default direction of stepping.
        """
        idx = self._tb._on_duty_idx
        if (duty == 'off') or (duty == 'same' and self.is_off_duty) or (
                        duty == 'alt' and self.is_on_duty):
            idx = self._tb._off_duty_idx
        elif duty == 'any':
            idx = range(len(self._tb._timeline))

        # TODO: optimize this search
        i = 0
        len_idx = len(idx)
        while i < len_idx and idx[i] < self._loc:
            i += 1

        if i == len_idx or i + steps < 0 or i+ steps >= len_idx:
            return self._tb._handle_out_of_bounds()

        return Workshift(self._tb, idx[i + steps])

    def rollback(self, steps=0, duty='on'):
        """
        Return a workshift which is `steps` workshifts away in the past. 
        
        `duty` parameter selects which workshifts are counted as steps.

        Parameters
        ----------
        steps: int, optional (default 0)
        duty: {'on', 'off', 'same', 'alt', 'any'} , optional (default 'on')
            'on' - step on on-duty workshifts only
            'off' - step on off-duty workshifts only
            'same' - step only on workshifts with the same duty status as self
            'alt' - step only on workshifts with the duty status other than 
            that of self
            'any' - step on all workshifts
    
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
        last workshift on which it stepped. For example, with `steps`=1 the 
        method returns the workshift preceding the zero step workshift, 
        subject to duty.
        
        If `steps` is negative, the method works in the same way but moving
        toward the future from the zero step workshift. For example, with 
        `steps`=-1 the method returns the workshift following the zero step 
        workshift, subject to duty.
        
        See also
        --------
        - (__sub__) :  `ws - n` is the same as ws.rollback(n, duty='on')
        rollforward : return a workshift from the future
            `rollforward` differs from `rollback` only in the definition of 
            the zero step workshift and the default direction of stepping.
        """
        # TODO: Optimize rollback and rolloforward to compy with DRY?

        idx = self._tb._on_duty_idx
        if (duty == 'off') or (duty == 'same' and self.is_off_duty) or (
                        duty == 'alt' and self.is_on_duty):
            idx = self._tb._off_duty_idx
        elif duty == 'any':
            idx = range(len(self._tb._timeline))

        # TODO: Optimize this search
        len_idx = len(idx)
        i = len_idx - 1
        while i >= 0 and idx[i] > self._loc:
            i -= 1

        if i == -1 or i - steps < 0 or i - steps >= len_idx:
            return self._tb._handle_out_of_bounds()

        return Workshift(self._tb, idx[i - steps])

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



