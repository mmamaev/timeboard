******************
Doing Calculations
******************

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: none


Calendar calculations are performed either with an individual workshift or with an interval of workshifts. 

Also each calculation is based on a specific schedule as one needs to reason about duty statuses of workshifts involved.

Therefore, to carry out a calculation you need to obtain either a workshift or an interval and indicate which schedule you will be using.

The import statement to run the examples::

    >>> import timeboard as tb

Obtaining a Workshift
=====================

Most likely you will want to identify a workshift by a timestamp which represents a point in time somewhere within the workshift. This is done by calling :py:meth:`.Timeboard.get_workshift` . The result returned will be an instance of :py:class:`.Workshift`. ::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
                            layout=[0, 1, 0, 2])
    >>> clnd.get_workshift('01 Oct 2017')
    Workshift(1) of 'D' at 2017-10-01

Even simpler, you get the same result by calling the instance of :py:class:`~.Timeboard` which will invoke :py:meth:`get_workshift` for you::

    >>> clnd('01 Oct 2017')
    Workshift(1) of 'D' at 2017-10-01

Alternatively, you can call :py:meth:`~timeboard.Workshift` constructor directly if you know the workshift's position on the timeline. 

    >>> tb.Workshift(clnd, 1)
    Workshift(1) of 'D' at 2017-10-01

All the above examples do not specify which schedule to use in calculations.
In this case the default schedule of the timeboard will be used. 

If you intend to base your calculation on another schedule you may pass it in `schedule` parameter of :py:meth:`~.Timeboard.get_workshift` method or :py:meth:`~timeboard.Workshift` constructor::

    >>> sdl = clnd.add_schedule(name='my_schedule', 
                                selector=lambda label: label>1)
    >>> clnd.get_workshift('01 Oct 2017', schedule=sdl)
    Workshift(1, my_schedule) of 'D' at 2017-10-01
    >>> tb.Workshift(clnd, 1, sdl)
    Workshift(1, my_schedule) of 'D' at 2017-10-01


.. note:: You cannot obtain a workshift by calling the instance of :py:class:`~.Timeboard` if you want to specify the schedule.`

Alternatively, you may pass `schedule` parameter to `Workshift` or `Interval` method which you call to perform the calculation.


Workshift-based calculations
============================

=============== ===============================================================
Method          Result
=============== ===============================================================
|is_on_duty|    Find out if the workshift is on duty

|is_off_duty|   Find out if the workshift is off duty

|rollforward|   Return a workshift which is in the specified number of steps in
                the future.

|rollback|      Return a workshift which is in the specified number of steps in
                the past.
=============== ===============================================================

.. |is_on_duty| replace:: :py:meth:`~timeboard.Workshift.is_on_duty`

.. |is_off_duty| replace:: :py:meth:`~timeboard.Workshift.is_off_duty`

.. |rollforward| replace:: :py:meth:`~timeboard.Workshift.rollforward`

.. |rollback| replace:: :py:meth:`~timeboard.Workshift.rollback`


Each of the above methods must use some schedule to identify workshift's duty.
The schedule is selected as follows:

- if a schedule is explicitly given as method's parameter, then use this schedule;

- else use the schedule supplied as a parameter of this workshift when it has been instantiated;

- if no such parameter was given to the workshift constructor, use the default schedule of the timeboard.

Determining duty
----------------

Examples::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
                            layout=[0, 1, 0, 2])
    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
                                        selector=lambda label: label>1)

    >>> ws1 = clnd.get_workshift('01 Oct 2017')
    >>> ws2 = clnd.get_workshift('01 Oct 2017', schedule=my_schedule)

Workshift of '01 Oct 2017' has label ``1``. Its duty under the default schedule::

    >>> ws1.is_on_duty()
    True
    >>> ws2.is_on_duty(schedule=clnd.default_schedule)
    True

and under "my_schedule"::

    >>> ws1.is_on_duty(schedule=my_schedule)
    False
    >>> ws2.is_on_duty()
    False


Rolling forward and back
------------------------

The methods :py:meth:`~timeboard.Workshift.rollforward` and :py:meth:`~timeboard.Workshift.rollback` allow to identify the workshift which is located in a specified distance from the current workshift.

Actually the methods do not roll, they step. The distance is measured in number of steps with regard to a certain duty. It means that, when taking steps, the methods tread only on the workshifts with this duty, ignoring all others.

`rollforward` and `rollback` operate in the same manner except for the direction of time. You specify the number of steps and the duty to tread on. The default values are ``steps=0, duty='on'``. The algorithm has two stages. 

**Stage 1.** If you call a method omitting the number of steps (same as ``steps=0``) it finds the closest workshift with the required duty. ::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
                            layout=[0, 1, 0, 2])
    >>> print(clnd)
    Timeboard of 'D': 2017-09-30 -> 2017-10-11

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2017-09-30 2017-09-30         1 2017-09-30    0.0    False
    1   2017-10-01 2017-10-01         1 2017-10-01    1.0     True
    2   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    3   2017-10-03 2017-10-03         1 2017-10-03    2.0     True
    4   2017-10-04 2017-10-04         1 2017-10-04    0.0    False
    5   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    6   2017-10-06 2017-10-06         1 2017-10-06    0.0    False
    7   2017-10-07 2017-10-07         1 2017-10-07    2.0     True
    8   2017-10-08 2017-10-08         1 2017-10-08    0.0    False
    9   2017-10-09 2017-10-09         1 2017-10-09    1.0     True
    10  2017-10-10 2017-10-10         1 2017-10-10    0.0    False
    11  2017-10-11 2017-10-11         1 2017-10-11    2.0     True

    >>> clnd('05 Oct 2017').rollforward()
    Workshift(5) of 'D' at 2017-10-05
    >>> clnd('06 Oct 2017').rollforward()
    Workshift(7) of 'D' at 2017-10-07
    >>> clnd('05 Oct 2017').rollback()
    Workshift(5) of 'D' at 2017-10-05
    >>> clnd('06 Oct 2017').rollback()
    Workshift(5) of 'D' at 2017-10-05

A method returns the self workshift if its duty is the same as the duty sought. Otherwise it returns the next (`rollforward`) or the previous (`rollback`) workshift with the required duty. The example above illustrates this behavior for ``duty='on'``, the example below - for ``duty='off'``::

    >>> clnd('05 Oct 2017').rollforward(duty='off')
    Workshift(6) of 'D' at 2017-10-06
    >>> clnd('06 Oct 2017').rollforward(duty='off')
    Workshift(6) of 'D' at 2017-10-06
    >>> clnd('05 Oct 2017').rollback(duty='off')
    Workshift(4) of 'D' at 2017-10-04
    >>> clnd('06 Oct 2017').rollback(duty='off')
    Workshift(6) of 'D' at 2017-10-06

The result of stage 1 is called the "zero step workshift".

**Stage 2.** If the number of steps is not zero, a method begins with executing stage 1. After the zero step workshift has been found the method takes the required number of steps in the appropriate direction treading only on the workshifts with the specified duty::

    >>> clnd('05 Oct 2017').rollforward(2)
    Workshift(9) of 'D' at 2017-10-09
    >>> clnd('06 Oct 2017').rollforward(2)
    Workshift(11) of 'D' at 2017-10-11
    >>> clnd('05 Oct 2017').rollback(2)
    Workshift(1) of 'D' at 2017-10-01
    >>> clnd('06 Oct 2017').rollback(2)
    Workshift(1) of 'D' at 2017-10-01

    >>> clnd('05 Oct 2017').rollforward(2, duty='off')
    Workshift(10) of 'D' at 2017-10-10
    >>> clnd('06 Oct 2017').rollforward(2, duty='off')
    Workshift(10) of 'D' at 2017-10-10
    >>> clnd('05 Oct 2017').rollback(2, duty='off')
    Workshift(0) of 'D' at 2017-09-30
    >>> clnd('06 Oct 2017').rollback(2, duty='off')
    Workshift(2) of 'D' at 2017-10-02

.. note:: If you don't care about the duty and want to step on all workshifts, use ``duty='any'``. This way the zero step workshift is always self.

As with the other methods, you can override the workshift's schedule in method's parameter. Take note that the returned workshift will have the schedule used by the method::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
                                        selector=lambda label: label>1)
    >>> ws = clnd('05 Oct 2017').rollforward(schedule=my_schedule)
    >>> ws
    Workshift(7, my_schedule) of 'D' at 2017-10-07
    >>> ws.rollforward(1)
    Workshift(11, my_schedule) of 'D' at 2017-10-11


Using operators `+` and `-`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add or subtract an integer number to/from a workshift. This is the same as calling, accordingly, `rollforward` or `rollback` with ``duty='on'``. ::

    # under default schedule
    >>> clnd('05 Oct 2017') + 1
    Workshift(7) of 'D' at 2017-10-07
    >>> clnd('06 Oct 2017') - 1
    Workshift(3) of 'D' at 2017-10-03

    # under my_schedule
    >>> ws = clnd.get_workshift('05 Oct 2017', schedule=my_schedule)
    >>> ws + 1
    Workshift(11, my_schedule) of 'D' at 2017-10-11


Caveats
^^^^^^^

`steps` can take a negative value. The method will step in the opposite direction, however the algorithm of seeking zero step workshift does not change. Therefore, the results of `rollforward` with negative `steps` and `rollback` with the same but positive value of `steps` may differ::

    >>> clnd('06 Oct 2017').rollforward(-1)
    Workshift(5) of 'D' at 2017-10-05
    >>> clnd('06 Oct 2017').rollback(1)
    Workshift(3) of 'D' at 2017-10-03

As the workshift of October 6 is off duty while method's duty is "on" by default, the method must seek the zero step workshift. In doing that,  `rollforward` looks in the future and finds October 7, while `rollback` looks in the past and find October 5. Then both methods take one "on duty" step to the past and arrive at the results shown above.

The analogous behavior takes place with ``rollback(-n)`` and ``rollforward(n)``::

    >>> clnd('05 Oct 2017').rollback(-1, duty='off')
    Workshift(6) of 'D' at 2017-10-06
    >>> clnd('05 Oct 2017').rollforward(1, duty='off')
    Workshift(8) of 'D' at 2017-10-08

There is no such discrepancy if method's duty is the same as workshift's duty.


Obtaining an Interval
=====================

To instantiate an interval which is defined by points in time or by a calendar period call :py:meth:`.Timeboard.get_interval`. This method takes several combinations of parameters. In most cases you can also use a shortcut by calling the instance of :py:class:`~.Timeboard` which will invoke :py:meth:`get_interval` for you. 

Obtaining an interval from two points in time::
    
    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', 
                            layout=[0, 1, 0, 2])
    >>> clnd.get_interval(('02 Oct 2017', '08 Oct 2017'))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    
    # Shortcut: 
    
    >>> clnd(('02 Oct 2017', '08 Oct 2017'))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    
Building an interval of a specified length::
    
    >>> clnd.get_interval('02 Oct 2017', length=7)
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    
    # Shortcut:
    
    >>> clnd('02 Oct 2017', length=7)
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]


Obtaining an interval from a calendar period::
    
    >>> clnd.get_interval('05 Oct 2017', period='W')
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    
    # Shortcut:
    
    >>> clnd('05 Oct 2017', period='W')
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]      
    
You can also build an interval directly from `pandas.Period` object but the shortcut is not available::
    
    >>> import pandas as pd
    >>> p = pd.Period('05 Oct 2017', freq='W')
    >>> clnd.get_interval(p)
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    
    # NO shortcut!
    
    >>> clnd(p)
    Workshift(2) of 'D' at 2017-10-02
    

Finally, you can convert the entire timeline into the interval::
    
    >>> clnd.get_interval()
    Interval((0, 15)): 'D' at 2017-09-30 -> 'D' at 2017-10-15 [16]
    
    # Shortcut:
    
    >>> clnd()
    Interval((0, 15)): 'D' at 2017-09-30 -> 'D' at 2017-10-15 [16]


Alternatively, you can call :py:meth:`~timeboard.Interval` constructor directly if you know the sequence numbers of the first and the last workshifts of the interval on the timeline::

    >>> tb.Interval(clnd, (2,8))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

All the above examples do not specify which schedule to use in calculations.
In this case the default schedule of the timeboard will be used. 

If you intend to base your calculation on another schedule you may pass it in `schedule` parameter of any method you use to instantiate an interval::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
                                      selector=lambda label: label>1)
    >>> clnd(('02 Oct 2017', '08 Oct 2017'), schedule=my_schedule)
    Interval((2, 8), my_schedule): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    >>> tb.Interval(clnd, (2,8), schedule=my_schedule)
    Interval((2, 8), my_schedule): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

Caveats
-------

There are a few caveats when you instantiate an interval from a calendar period.

Period extends beyond timeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the calendar period extends beyond the timeline, the interval is created as the intersection of the timeline and the calendar period. ::

    >>> clnd('Oct 2017', period='M')
    Interval(1, 15): 'D' at 2017-10-01 -> 'D' at 2017-10-15 [15]
        
There is a parameter called `clip_period` which determines how this situation is handled. By default ``clip_period=True`` which results in the behavior illustrated above. If it is set to False, `PartialOutOfBoundsError` is raised::

    >>> clnd('Oct 2017', period='M', clip_period=False)
    -----------------------------------------------------------------------
    PartialOutOfBoundsError               Traceback (most recent call last)
    ...
    PartialOutOfBoundsError: The right bound of interval referenced by `Oct 2017` is outside Timeboard of 'D': 2017-09-30 -> 2017-10-15

.. _workshift-straddling-1:

Workshift straddles period boundary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following timeboard::

    >>> clnd = tb.Timeboard('12H', '01 Oct 2017 21:00', '03 Oct 2017',
                            layout=[1])
    >>> print(clnd)

                  workshift               start  duration                 end
    loc                                                                      
    0   2017-10-01 21:00:00 2017-10-01 21:00:00         1 2017-10-02 08:59:59
    1   2017-10-02 09:00:00 2017-10-02 09:00:00         1 2017-10-02 20:59:59
    2   2017-10-02 21:00:00 2017-10-02 21:00:00         1 2017-10-03 08:59:59

    # columns "label" and "on_duty" have been omitted to fit the output
    # to the page

Suppose we want to build an interval corresponding to the day of October 2. The workshifts at locations 0 and 2 straddle the boundaries of the day: they partly lay within October 2 and partly - without. 

This ambiguity is solved with :py:class:`.Timeboard`\ .\ :py:attr:`workshift_ref` attribute. The workshift is considered a member of the calendar period where its reference timestamp belongs. By default ``workshift_ref='start'`` as you can see in column 'workshift' in the output above. Hence, workshift's membership in a calendar period is determined by its start time. In our timeboard, consequently, workshift 0 belongs to October 1 while workshift 2 stays with October 2::

    >>> clnd('02 Oct 2017', period='D')
    Interval((1, 2)): '12H' at 2017-10-02 09:00 -> '12H' at 2017-10-02 21:00 [2]

If ``workshift_ref='end'``, then the end time of workshift is used as the indicator of period membership. In this way, workshift 0 becomes a member of  October 2 while workshift 2 goes with with October 3::

    >>> clnd = tb.Timeboard('12H', '01 Oct 2017 21:00', '03 Oct 2017',
                            layout=[1], 
                            workshift_ref='end')
    >>> print(clnd)
    Timeboard of '12H': 2017-10-01 21:00 -> 2017-10-02 21:00

                  workshift               start  duration                 end
    loc                                                                      
    0   2017-10-02 08:59:59 2017-10-01 21:00:00         1 2017-10-02 08:59:59
    1   2017-10-02 20:59:59 2017-10-02 09:00:00         1 2017-10-02 20:59:59
    2   2017-10-03 08:59:59 2017-10-02 21:00:00         1 2017-10-03 08:59:59

    # columns "label" and "on_duty" have been omitted to fit the output
    # to the page

    >>> clnd('02 Oct 2017', period='D')
    Interval((0, 1)): '12H' at 2017-10-01 21:00 -> '12H' at 2017-10-02 09:00 [2]


Period too short for workshifts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a corner case you can try to obtain an interval from a period which is shorter than the workshifts in this area of the timeline. For example, in a timeboard with daily workshifts you seek an interval defined by an hour::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '05 Oct 2017', layout=[1])
    >>> ivl = clnd.get_interval('02 Oct 2017 00:00', period='H')

However meaningless, this operation is handled according to the same logic of attributing a workshift to the period as discussed in the previous section. In this timeboard the workshift reference time is its start time (the default setting). The hour starting at 02 Oct 2017 00:00 contains the reference time of the daily workshift of October 2. Hence, technically this one day workshift is the member of that one hour period and, therefore, becomes the only element of the sought interval::

    >>> print(ivl)
    Interval((2, 2)): 'D' at 2017-10-02 -> 'D' at 2017-10-02 [1]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    2   2017-10-02 2017-10-02         1 2017-10-02    1.0     True

On the other hand, if you try to obtain an interval from another hour of the same day, `VoidIntervalError` will be raised as no workshift has it reference time within that hour::

    >>> clnd.get_interval('02 Oct 2017 01:00', period='H')
    ---------------------------------------------------------------------------
    VoidIntervalError                         Traceback (most recent call last)
    ...
    VoidIntervalError: Attempted to create reversed or void interval referenced by `02 Oct 2017 01:00` within Timeboard of 'D': 2017-09-30 -> 2017-10-05


Interval-based calculations
===========================

=============== ===============================================================
Method          Result
=============== ===============================================================
|nth|           Find n-th workshift with the specified duty in the interval.

|first|         Find the first workshift with the specified duty in 
                the interval.

|last|          Find the last workshift with the specified duty in 
                the interval.

|count|         Count workshifts with the specified duty in the interval.

|count_periods| How many calendar periods fit into the interval (duty-aware).
=============== ===============================================================

.. |nth| replace:: :py:meth:`~timeboard.Interval.nth`

.. |first| replace:: :py:meth:`~timeboard.Interval.first`

.. |last| replace:: :py:meth:`~timeboard.Interval.last`

.. |count| replace:: :py:meth:`~timeboard.Interval.count`

.. |count_periods| replace:: :py:meth:`~timeboard.Interval.count_periods`

All methods are duty-aware meaning that they "see" only workshifts with the specified duty ignoring the others.

Consequently, each of the above methods must use some schedule to identify workshift's duty. The schedule is selected as follows:

- if a schedule is explicitly given as method's parameter, then use this schedule;

- else use the schedule supplied as a parameter of this interval when it has been instantiated;

- if no such parameter was given to the interval constructor, use the default schedule of the timeboard.

.. note:: If you don't care about the duty and want to take into account all workshifts in the interval, use ``duty='any'``. 

Counting workshifts
-------------------

Examples::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', 
                            layout=[0, 1, 0, 2])
    >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
    >>> print(ivl)
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    2   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    3   2017-10-03 2017-10-03         1 2017-10-03    2.0     True
    4   2017-10-04 2017-10-04         1 2017-10-04    0.0    False
    5   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    6   2017-10-06 2017-10-06         1 2017-10-06    0.0    False
    7   2017-10-07 2017-10-07         1 2017-10-07    2.0     True
    8   2017-10-08 2017-10-08         1 2017-10-08    0.0    False

With ``duty='on'``::

    >>> ivl.first()
    Workshift(3) of 'D' at 2017-10-03
    >>> ivl.nth(1)
    Workshift(5) of 'D' at 2017-10-05
    >>> ivl.last()
    Workshift(7) of 'D' at 2017-10-07
    >>> ivl.count()
    3

With ``duty='off'``::

    >>> ivl.first(duty='off')
    Workshift(2) of 'D' at 2017-10-02
    >>> ivl.nth(1, duty='off')
    Workshift(4) of 'D' at 2017-10-04
    >>> ivl.last(duty='off')
    Workshift(8) of 'D' at 2017-10-08
    >>> ivl.count(duty='off')
    4

With ``duty='on'`` under another schedule::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
                                        selector=lambda label: label>1)
    >>> ivl.nth(1, schedule=my_schedule)
    Workshift(7, my_schedule) of 'D' at 2017-10-07
    >>> ivl.count(duty='on', schedule=my_schedule)
    2

Not taking the duty into account::

    >>> ivl.first(duty='any')
    Workshift(2) of 'D' at 2017-10-02
    >>> ivl.nth(1, duty='any')
    Workshift(3) of 'D' at 2017-10-03
    >>> ivl.last(duty='any')
    Workshift(8) of 'D' at 2017-10-08
    >>> ivl.count(duty='any')
    7


Counting periods
----------------

Call :py:meth:`~timeboard.Interval.count_periods` to find out how many calendar periods of the specific frequency fit into the interval. As with the other methods, duty of workhifts is taken into account. The method returns a float number.

To obain the result, the interval is sliced into calendar periods of the given frequency and then each slice of the interval is compared to its corresponding period duty-wise. That is to say, the count of workshifts in the interval's slice is divided by the total count of workshifts in the  period containing this slice but only workshifts with the specified duty are counted. The quotients for each period are summed to produce the return value of the method.
        
If some period does not contain workshifts of the required duty, it contributes zero to the returned value.
        
Regardless of the period frequency, the method returns 0.0 if there are no workshifts with the specified duty in the interval.

Examples::

    >>> clnd = tb.Timeboard('H', '01 Oct 2017', '08 Oct 2017 23:59', 
                            layout=[0, 1, 0, 2])
    >>> ivl = clnd(('01 Oct 2017 13:00', '02 Oct 2017 23:59'))

Interval `ivl` spans two days: it contains 11 of 24 workshifts of 
October 1, and all 24 workshifts of October 2::

     >>> ivl.count_periods('D', duty='any')
     1.4583333333333333
     >>> 11.0/24 + 24.0/24
     1.4583333333333333

The timeboard's `layout` defines that all workshifts taking place on even hours are off duty, and those on odd hours are on duty. The first workshift of the interval (01 October 13:00 - 13:59) is on duty. Hence, the interval contains 6 of 12 on duty workshifts of October 1, and all 12 on duty workshifts of October 2::

    >>> ivl.count_periods('D')
    1.5
    >>> 6.0/12 + 12.0/12
    1.5

The interval contains 5 of 12 off duty workshifts of October 1, and all 12 off duty workshifts of October 2. 

    >>> ivl.count_periods('D', duty='off')
    1.4166666666666667
    >>> 5.0/12 + 12.0/12
    1.4166666666666667

If we change the schedule to `my_schedule`, on duty workshifts will start only at 3, 7, 11, 15, 19, and 23 o'clock yielding 6 on duty workshifts per day. Interval `ivl` will contain 3/6 + 6/6 on duty days and 8/18 + 18/18 off duty days::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
                                        selector=lambda label: label>1)
    >>> ivl.count_periods('D', schedule=my_schedule)
    1.5
    >>> 3.0/6 + 6.0/6
    1.5
    >>> ivl.count_periods('D', duty='off', schedule=my_schedule)
    1.4444444444444444
    >>> 8.0/18 + 18.0/18
    1.4444444444444444

Note that an interval containing exactly one calendar period with regard to some duty may be larger than this period, as well as smaller::

    # Interval of 25 hours
    >>> ivl = clnd(('01 Oct 2017 00:00', '02 Oct 2017 00:59'))
    >>> ivl
    Interval((0, 24)): 'H' at 2017-10-01 00:00 -> 'H' at 2017-10-02 00:00 [25]
    >>> ivl.count_periods('D')
    1.0

    # Interval of 23 hours
    >>> ivl = clnd(('01 Oct 2017 01:00', '01 Oct 2017 23:59'))
    >>> ivl
    Interval((1, 23)): 'H' at 2017-10-01 01:00 -> 'H' at 2017-10-01 23:00 [23]
    >>> ivl.count_periods('D')
    1.0


Caveats
-------

Period extends beyond timeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the timeboard and two intervals::

    >>> clnd = tb.Timeboard('H', '01 Oct 2017', '08 Oct 2017 23:59', 
                            layout=[0, 1, 0, 2])
    >>> ivl1 = clnd(('02 Oct 2017 00:00', '02 Oct 2017 23:59'))
    >>> ivl2 = clnd(('01 Oct 2017 13:00', '02 Oct 2017 23:59'))

We can count how many weeks are in interval `ivl1` but not in `ivl2`. 

All workshifts of `ivl1` belong to the week of October 2 - 8 which is situated entirely within the timeboard. On the other hand, in `ivl2` there are the workshifts belonging to the week of September 25 - October 1. This week extends beyond the timeboard. We may not guess what layout *could* be applied to the workshifts of Sep 25 - Sep 30 if the week were included in the timeboard entirely. We are not authorized to extrapolate the existing layout outside the timeboard. Moreover, for some complex layouts any attempt of extrapolation would be ambiguous. ::

        >>> ivl1.count_periods('W')
        0.14285714285714285
        >>> ivl2.count_periods('W')
        ----------------------------------------------------------------------
        PartialOutOfBoundsError              Traceback (most recent call last)
        ...
        PartialOutOfBoundsError: The left bound of interval or period referenced by `2017-09-25/2017-10-01` is outside Timeboard of 'H': 2017-10-01 00:00 -> 2017-10-08 23:00


Workshift straddles period boundary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This case is analogous to already reviewed  
:ref:`issue <workshift-straddling-1>` of contructing an interval from a calendar period. :py:class:`.Timeboard`\ .\ :py:attr:`workshift_ref` attribute  is used to identify workshift's membership in a period. 

Period too short for workshifts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you try to count periods which are shorter than (some) of the workshifts in the interval, you are likely to encounter a period which does not contain *any* workshift's reference whatever the duty. This makes any result meaningless and, concequently, `UnacceptablePeriodError` is raised. 

You may accidentally run into this issue in two situations:

- You use compound workshifts and while most of the workshifts (usually those covering the working time) are of one size, there are a few workshifts (usually those covering the closed time) which are much larger. Trying to count periods, you have in mind the smaller workshifts. If a larger one gets into the interval and your period is not long enough, you will find yourself with UnacceptablePeriodError.

- You have misinterpreted the purpose of :py:meth:`count_periods` method and try to use it as a general time counter. For example, in a timeboard with workhifts of varying duration measured in hours, you want to find out how many clock hours there are in an interval. In order to do that use `pandas.Timedelta` tools with `start_time` and `end_time` attributes of workshifts and intervals.
