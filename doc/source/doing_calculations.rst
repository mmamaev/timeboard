******************
Doing Calculations
******************

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: none


Calendar calculations are performed either with an individual workshift or with an interval of workshifts. 

Also, each calculation is based on a specific schedule in order to reason about duty statuses of workshifts involved.

Therefore, to carry out a calculation you need to obtain either a workshift or an interval and indicate which schedule you will be using.

The import statement to run the examples::

    >>> import timeboard as tb

Obtaining a Workshift
=====================

Most likely you will want to identify a workshift by a timestamp which represents a point in time somewhere within the workshift. This is done by calling :py:meth:`.Timeboard.get_workshift` . The result returned will be an instance of :py:class:`.Workshift`. ::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> clnd.get_workshift('01 Oct 2017')
    Workshift(1) of 'D' at 2017-10-01

Even simpler, you get the same result by calling the instance of :py:class:`~.Timeboard` which will invoke :py:meth:`get_workshift` for you::

    >>> clnd('01 Oct 2017')
    Workshift(1) of 'D' at 2017-10-01

The argument passed to :py:meth:`get_workshift` is `Timestamp`-like meaning it may be a timestamp, or a string convertible to timestamp, or an object which implement `to_timestamp()` method.

Alternatively, you can call :py:meth:`~timeboard.Workshift` constructor directly if you know the workshift's position on the timeline::

    >>> tb.Workshift(clnd, 1)
    Workshift(1) of 'D' at 2017-10-01

Every workshift comes with an attached schedule. This schedule is used in calculations carried out with this workshift unless it is overridden by `schedule` parameter of the method called to perform the calculation. 

By default, a new workshift returned by :py:meth:`~.Timeboard.get_workshift` method or :py:meth:`~timeboard.Workshift` constructor receives the default schedule of the timeboard. You may attach a specific schedule to a new workshift by passing it in `schedule` parameter::

    >>> sdl = clnd.add_schedule(name='my_schedule', 
    ...                         selector=lambda label: label>1)

::

    >>> clnd.get_workshift('01 Oct 2017', schedule=sdl)
    Workshift(1, my_schedule) of 'D' at 2017-10-01
    >>> tb.Workshift(clnd, 1, sdl)
    Workshift(1, my_schedule) of 'D' at 2017-10-01


.. note:: You cannot obtain a workshift by calling the instance of :py:class:`~.Timeboard` if you want to attach the schedule.` Use :py:meth:`~.Timeboard.get_workshift` only.

Besides, a workshift can be obtained as a return value of a method performing a calculation over the timeboard. The schedule attached to this workshift is the schedule used by the method which has produced the workshift.


Workshift-based calculations
============================

=============== ===============================================================
Method          Result
=============== ===============================================================
|is_on_duty|    :ref:`Find out if the workshift is on duty. <find-duty>`

|is_off_duty|   :ref:`Find out if the workshift is off duty. <find-duty>`

|w_worktime|    :ref:`Return workshift's work time. <obtaining-work-time>`

|rollforward|   |section-rolling-fwd|

`+` (plus)      Shortcut for |rollforward|

|rollback|      |section-rolling-back|

`-` (minus)     Shortcut for |rollback| 
=============== ===============================================================

.. |is_on_duty| replace:: :py:meth:`~timeboard.Workshift.is_on_duty`

.. |is_off_duty| replace:: :py:meth:`~timeboard.Workshift.is_off_duty`

.. |w_worktime| replace:: :py:meth:`~timeboard.Workshift.worktime`

.. |rollforward| replace:: :py:meth:`~timeboard.Workshift.rollforward`

.. |rollback| replace:: :py:meth:`~timeboard.Workshift.rollback`

.. |section-rolling-fwd| replace:: :ref:`Return a workshift by taking the specified number of steps toward the future. <rolling>`

.. |section-rolling-back| replace:: :ref:`Return a workshift by taking the specified number of steps toward the past. <rolling>`


Each of the above methods must use some schedule to identify workshift's duty.
The schedule is selected as follows:

- if a schedule is explicitly given as method's parameter, then use this schedule;

- else use the schedule attached to this workshift when it has been instantiated;

- if no `schedule` parameter was given to the workshift constructor, use the default schedule of the timeboard.

.. _find-duty:

Determining duty
----------------

Examples::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
                                        selector=lambda label: label>1)

::

    >>> ws1 = clnd.get_workshift('01 Oct 2017')
    >>> ws2 = clnd.get_workshift('01 Oct 2017', schedule=my_schedule)

`ws1` and `ws2` are the same workshift but with different schedules attached. `ws1` comes with the default schedule of the timeboard, while `ws2` is given `my_schedule`.

The workshift has label ``1``. Its duty under the default schedule::

    >>> ws1.is_on_duty()
    True
    >>> ws2.is_on_duty(schedule=clnd.default_schedule)
    True

and under `my_schedule`::

    >>> ws1.is_on_duty(schedule=my_schedule)
    False
    >>> ws2.is_on_duty()
    False

.. _obtaining-work-time:

Obtaining work time
-------------------

The source of the information about workshift's work time is determined by :py:class:`.Timeboard`\ .\ :py:attr:`worktime_source` attribute.

:py:meth:`.Workshift.worktime` method returns the work time of the workshift if the duty value passed to the method corresponds to that of the workshift. Otherwise, it returns zero. 

By default, the work time equals to workshift's duration::

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

In the example below, the work time is taken from the labels::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
    ...                     layout=[4, 8, 4, 8],
    ...                     default_selector = lambda label: label>4,
    ...                     worktime_source = 'labels')

::

    >>> ws = tb.Workshift(clnd, 3)
    >>> ws.worktime()
    8.0
    >>> ws.worktime(duty='off')
    0
    >>> ws.worktime(duty='any')
    8.0

::

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

The query with ``duty='off'`` can be interpreted as "What is the work time for a worker who comes in when the main workforce is off duty?"

.. _rolling:


Rolling forward and back
------------------------

The methods :py:meth:`~timeboard.Workshift.rollforward` and :py:meth:`~timeboard.Workshift.rollback` allow to identify the workshift which is located in a specified distance from the current workshift.

Actually, the methods do not roll, they step. The distance is measured in a number of steps with regard to a certain duty. It means that, when taking steps, the methods tread only on the workshifts with this duty, ignoring all others.

`rollforward` and `rollback` operate in the same manner except for the direction of time. You specify the number of steps and the duty to tread on. The default values are ``steps=0, duty='on'``. The algorithm has two stages. 

**Stage 1.** If you call a method omitting the number of steps (same as ``steps=0``) it finds the closest workshift with the required duty. ::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> print(clnd)
    Timeboard of 'D': 2017-09-30 -> 2017-10-11
    <BLANKLINE>
            ws_ref      start  duration        end  label  on_duty
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

::

    >>> clnd('05 Oct 2017').rollforward()
    Workshift(5) of 'D' at 2017-10-05
    >>> clnd('06 Oct 2017').rollforward()
    Workshift(7) of 'D' at 2017-10-07

::

    >>> clnd('05 Oct 2017').rollback()
    Workshift(5) of 'D' at 2017-10-05
    >>> clnd('06 Oct 2017').rollback()
    Workshift(5) of 'D' at 2017-10-05

A method returns the self workshift if its duty is the same as the duty sought. Otherwise it returns the next (`rollforward`) or the previous (`rollback`) workshift with the required duty. The example above illustrates this behavior for ``duty='on'``, the example below - for ``duty='off'``::

    >>> clnd('05 Oct 2017').rollforward(duty='off')
    Workshift(6) of 'D' at 2017-10-06
    >>> clnd('06 Oct 2017').rollforward(duty='off')
    Workshift(6) of 'D' at 2017-10-06

::

    >>> clnd('05 Oct 2017').rollback(duty='off')
    Workshift(4) of 'D' at 2017-10-04
    >>> clnd('06 Oct 2017').rollback(duty='off')
    Workshift(6) of 'D' at 2017-10-06

The result of stage 1 is called the "zero step workshift".

**Stage 2.** If the number of steps is not zero, a method proceeds to stage 2. After the zero step workshift has been found the method takes the required number of steps in the appropriate direction treading only on the workshifts with the specified duty::

    >>> clnd('05 Oct 2017').rollforward(2)
    Workshift(9) of 'D' at 2017-10-09
    >>> clnd('06 Oct 2017').rollforward(2)
    Workshift(11) of 'D' at 2017-10-11

::

    >>> clnd('05 Oct 2017').rollback(2)
    Workshift(1) of 'D' at 2017-10-01
    >>> clnd('06 Oct 2017').rollback(2)
    Workshift(1) of 'D' at 2017-10-01

::

    >>> clnd('05 Oct 2017').rollforward(2, duty='off')
    Workshift(10) of 'D' at 2017-10-10
    >>> clnd('06 Oct 2017').rollforward(2, duty='off')
    Workshift(10) of 'D' at 2017-10-10

::

    >>> clnd('05 Oct 2017').rollback(2, duty='off')
    Workshift(0) of 'D' at 2017-09-30
    >>> clnd('06 Oct 2017').rollback(2, duty='off')
    Workshift(2) of 'D' at 2017-10-02

.. note:: If you don't care about the duty and want to step on all workshifts, use ``duty='any'``. This way the zero step workshift is always self.

As with the other methods, you can override the workshift's schedule in method's parameter. Take note that the returned workshift will have the schedule used by the method::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
    ...                                 selector=lambda label: label>1)
    >>> ws = clnd('05 Oct 2017').rollforward(schedule=my_schedule)
    >>> ws
    Workshift(7, my_schedule) of 'D' at 2017-10-07
    >>> ws.rollforward(1)
    Workshift(11, my_schedule) of 'D' at 2017-10-11


.. _plus-minus:

Using operators `+` and `-`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add or subtract an integer number to/from a workshift. This is the same as calling, accordingly, `rollforward` or `rollback` with ``duty='on'``. ::

    # under default schedule
    >>> clnd('05 Oct 2017') + 1
    Workshift(7) of 'D' at 2017-10-07
    >>> clnd('06 Oct 2017') - 1
    Workshift(3) of 'D' at 2017-10-03

::

    # under my_schedule
    >>> ws = clnd.get_workshift('05 Oct 2017', schedule=my_schedule)
    >>> ws + 1
    Workshift(11, my_schedule) of 'D' at 2017-10-11


Caveats
^^^^^^^

`steps` can take a negative value. A method will step in the opposite direction, however, the algorithm of seeking the zero step workshift does not change. Therefore, the results of `rollforward` with negative `steps` and `rollback` with the same but positive value of `steps` may differ::

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

============================= =================================================
Method                        Result
============================= =================================================
|get-interval|                Create an interval with regard to specific points
                              or periods of time: from two points in time, or
                              from a calendar period, or specify the starting point and the length of the interval.

calling `Timeboard` instance  Shortcut for :py:meth:`.Timeboard.get_interval`

|interval|                    Instantiate an interval from the first and the
                              last workshifts or from their sequence numbers on
                              the timeline.

|overlap|                     Get an interval that is the intersection of two 
                              intervals.

`*` (multiplication)          Shortcut for 
                              :py:meth:`~timeboard.Interval.overlap`
============================= =================================================

.. |get-interval| replace:: :py:meth:`.Timeboard.get_interval`

.. |instance| replace:: calling :py:class:`Timeboard` instance

.. |interval| replace:: :py:meth:`~timeboard.Interval`

.. |overlap| replace:: :py:meth:`.Interval.overlap`

To create an interval with regard to the specific points or periods of time call :py:meth:`.Timeboard.get_interval`. This method takes several combinations of parameters. In most cases, you can also use a shortcut by calling the instance of :py:class:`~.Timeboard` which will invoke :py:meth:`get_interval` for you. 

Obtaining an interval from two points in time::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> clnd.get_interval(('02 Oct 2017', '08 Oct 2017'))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    
    # Shortcut: 
    
    >>> clnd(('02 Oct 2017', '08 Oct 2017'))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

The points in time come as a tuple of two values which are timestamps, or strings convertible to timestamps, or objects which implement `to_timestamp()` method.

Note that the points in time are not the boundaries of the interval but  references to the first and the last workshifts of the interval. The points in time may be located anywhere within these workshifts. The following operation produces the same interval as the one above::

    >>> clnd.get_interval(('02 Oct 2017 15:15', '08 Oct 2017 23:59'))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

You may also pass a null value (such as `None`, `NaN`, or `NaT`) in place of a point in time. If the first element of the tuple is null, then the interval will start on the first workshift of the timeboard. If the second element is null, then the interval will end on the last workshift of the timeboard. ::

    >>> clnd.get_interval((None, '08 Oct 2017 23:59'))
    Interval((0, 8)): 'D' at 2017-09-30 -> 'D' at 2017-10-08 [9]
    >>> clnd(('02 Oct 2017 15:15', None))
    Interval((2, 15)): 'D' at 2017-10-02 -> 'D' at 2017-10-15 [14]

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


Alternatively, you can call :py:meth:`~timeboard.Interval` constructor directly if you have got the first and the last workshifts of the interval or know their sequence numbers on the timeline::

    >>> ws_first = clnd('02 Oct 2017')
    >>> ws_first
    Workshift(2) of 'D' at 2017-10-02
    >>> ws_last = clnd('08 Oct 2017')
    >>> ws_last
    Workshift(8) of 'D' at 2017-10-08

::

    >>> tb.Interval(clnd, (ws_first, ws_last))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

::

    >>> tb.Interval(clnd, (2, 8))
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]

If you have got two intervals you can obtain an interval representing their intersection by calling :py:meth:`~timeboard.Interval.overlap` on any of the two while passing the other as the parameter::

    >>> ivl = tb.Interval(clnd, (2, 8))
    >>> other = tb.Interval(clnd, (6, 10))

::

    >>> ivl.overlap(other)
    Interval((6, 8)): 'D' at 2017-10-06 -> 'D' at 2017-10-08 [3]

As a shortcut, `*` (multiplication) operator can be used::

    >>> ivl * other
    Interval((6, 8)): 'D' at 2017-10-06 -> 'D' at 2017-10-08 [3]


Every interval comes with an attached schedule. This schedule is used in calculations carried out with this interval unless it is overridden by `schedule` parameter of the method called to perform the calculation. 

By default, a new interval receives the default schedule of the timeboard or inherits the schedule from its parent interval (i.e. from the interval on which `overlap()` has been called). 

You may attach a specific schedule to a new interval by passing it in `schedule` parameter of any method you use to instantiate an interval::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
    ...                                 selector=lambda label: label>1)

::

    >>> clnd(('02 Oct 2017', '08 Oct 2017'), schedule=my_schedule)
    Interval((2, 8), my_schedule): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    >>> tb.Interval(clnd, (2,8), schedule=my_schedule)
    Interval((2, 8), my_schedule): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    >>> ivl.overlap(other, schedule=my_schedule)
    Interval((6, 8), my_schedule): 'D' at 2017-10-06 -> 'D' at 2017-10-08 [3]


Caveats
-------

There are a few caveats when you instantiate an interval from a calendar period.

Period extends beyond timeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the calendar period extends beyond the timeline, the interval is created as the intersection of the timeline and the calendar period. ::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> clnd('Oct 2017', period='M')
    Interval(1, 15): 'D' at 2017-10-01 -> 'D' at 2017-10-15 [15]
        
There is a parameter called `clip_period` which determines how this situation is handled. By default ``clip_period=True`` which results in the behavior illustrated above. If it is set to False, `PartialOutOfBoundsError` is raised::

    >>> clnd('Oct 2017', period='M', clip_period=False)
    -----------------------------------------------------------------------
    PartialOutOfBoundsError               Traceback (most recent call last)
      ...
    PartialOutOfBoundsError: The right bound of interval referenced by `Oct
    2017` is outside Timeboard of 'D': 2017-09-30 -> 2017-10-15

.. _workshift-straddling-1:

Workshift straddles period boundary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following timeboard::

    >>> clnd = tb.Timeboard('12H', '01 Oct 2017 21:00', '03 Oct 2017',
    ...                     layout=[1])
    >>> print(clnd)
    <BLANKLINE>
                     ws_ref               start  duration                 end
    loc                                                                      
    0   2017-10-01 21:00:00 2017-10-01 21:00:00         1 2017-10-02 08:59:59
    1   2017-10-02 09:00:00 2017-10-02 09:00:00         1 2017-10-02 20:59:59
    2   2017-10-02 21:00:00 2017-10-02 21:00:00         1 2017-10-03 08:59:59

    # columns "label" and "on_duty" have been omitted to fit the output
    # to the page

Suppose we want to build an interval corresponding to the day of October 2. The workshifts at locations 0 and 2 straddle the boundaries of the day: they partly lay within October 2 and partly - without. 

This ambiguity is solved with :py:class:`.Timeboard`\ .\ :py:attr:`workshift_ref` attribute. The workshift is considered a member of the calendar period where its reference timestamp belongs. By default, workshift's reference timestamp is its start time (``workshift_ref='start'``). This is shown in column 'workshift' in the output above. Hence, workshift's membership in a calendar period is determined by its start time. In our timeboard, consequently, workshift 0 belongs to October 1 while workshift 2 stays with October 2::

    >>> clnd('02 Oct 2017', period='D')
    Interval((1, 2)): '12H' at 2017-10-02 09:00 -> '12H' at 2017-10-02 21:00 [2]

Note the change in 'workshift' column in the output below when ``workshift_ref='end'``::

    >>> clnd = tb.Timeboard('12H', '01 Oct 2017 21:00', '03 Oct 2017',
    ...                     layout=[1], 
    ...                        ws_ref_ref='end')
    >>> print(clnd)
    Timeboard of '12H': 2017-10-01 21:00 -> 2017-10-02 21:00
    <BLANKLINE>
                     ws_ref               start  duration                 end
    loc                                                                      
    0   2017-10-02 08:59:59 2017-10-01 21:00:00         1 2017-10-02 08:59:59
    1   2017-10-02 20:59:59 2017-10-02 09:00:00         1 2017-10-02 20:59:59
    2   2017-10-03 08:59:59 2017-10-02 21:00:00         1 2017-10-03 08:59:59

    # columns "label" and "on_duty" have been omitted to fit the output
    # to the page

In this way, the end time of workshift is used as the indicator of period membership. Workshift 0 becomes a member of October 2 while workshift 2 goes with October 3::

    >>> clnd('02 Oct 2017', period='D')
    Interval((0, 1)): '12H' at 2017-10-01 21:00 -> '12H' at 2017-10-02 09:00 [2]

Due to the skewed workshift alignment, in both cases the boundaries of the produced interval do not coincide with the period given as the interval reference (the day of October 2).

Period too short for workshifts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a corner case, you can try to obtain an interval from a period which is shorter than the workshifts in this area of the timeline. For example, in a timeboard with daily workshifts you seek an interval defined by an hour::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '05 Oct 2017', layout=[1])
    >>> ivl = clnd.get_interval('02 Oct 2017 00:00', period='H')

However meaningless, this operation is handled according to the same logic of attributing a workshift to the period as discussed in the previous section. In this timeboard, the workshift reference time is its start time (the default setting). The hour starting at 02 Oct 2017 00:00 contains the reference time of the daily workshift of October 2. Technically, this one-day workshift is the member of the one-hour period and, therefore, becomes the only element of the sought interval::

    >>> print(ivl)
    Interval((2, 2)): 'D' at 2017-10-02 -> 'D' at 2017-10-02 [1]
    <BLANKLINE>
            ws_ref      start  duration        end  label  on_duty
    loc                                                           
    2   2017-10-02 2017-10-02         1 2017-10-02    1.0     True

On the other hand, if you try to obtain an interval from another hour of the same day, `VoidIntervalError` will be raised as no workshift has its reference time within that hour::

    >>> clnd.get_interval('02 Oct 2017 01:00', period='H')
    ---------------------------------------------------------------------------
    VoidIntervalError                         Traceback (most recent call last)
      ...
    VoidIntervalError: Attempted to create reversed or void interval 
    referenced by `02 Oct 2017 01:00` within Timeboard of 'D': 2017-09-30 -> 
    2017-10-05


Interval-based calculations
===========================

=============== ===============================================================
Method          Result
=============== ===============================================================
|nth|           |section_seek_nth|

|first|         |section_seek_first|

|last|          |section_seek_last|

|workshifts|    |section_iteration|

|count|         |section_seek_count|

|i_worktime|    |section_i_worktime|

|what_portion|  |section_relation_portion|

`/` (division)  Shortcut for :py:meth:`~timeboard.Interval.what_portion_of`

|count_periods| |section_count_periods|
=============== ===============================================================

.. |nth| replace:: :py:meth:`~timeboard.Interval.nth`

.. |section_seek_nth| replace:: :ref:`Find n-th workshift with the specified duty in the interval. <seek-count-ws>`

.. |first| replace:: :py:meth:`~timeboard.Interval.first`

.. |section_seek_first| replace:: :ref:`Find the first workshift with the specified duty in the interval. <seek-count-ws>`

.. |last| replace:: :py:meth:`~timeboard.Interval.last`

.. |section_seek_last| replace:: :ref:`Find the last workshift with the specified duty in the interval. <seek-count-ws>`

.. |count| replace:: :py:meth:`~timeboard.Interval.count`

.. |section_seek_count| replace:: :ref:`Count workshifts with the specified duty in the interval. <seek-count-ws>`

.. |workshifts| replace:: :py:meth:`~timeboard.Interval.workshifts`

.. |section_iteration| replace:: :ref:`Iterate through workshifts with the specified duty. <iterating>`

.. |i_worktime| replace:: :py:meth:`~timeboard.Interval.worktime`

.. |section_i_worktime| replace:: :ref:`The total work time of workshifts with the specified duty. <measuring-worktime>`

.. |what_portion| replace:: :py:meth:`~timeboard.Interval.what_portion_of`

.. |section_relation_portion| replace:: :ref:`What portion of another interval this interval takes up. <relation-with-other>`

.. |count_periods| replace:: :py:meth:`~timeboard.Interval.count_periods`

.. |section_count_periods| replace:: :ref:`How many calendar periods fit into the interval. <counting-periods>`


All methods are duty-aware meaning that they "see" only workshifts with the specified duty ignoring the others.

Each of the above methods must use some schedule to identify workshift's duty. The schedule is selected as follows:

- if a schedule is explicitly given as method's parameter, then use this schedule;

- else use the schedule attached to this interval when it has been instantiated;

- if no `schedule` parameter was given to the interval constructor, use the default schedule of the timeboard.

.. note:: If you don't care about the duty and want to take into account all workshifts in the interval, use ``duty='any'``. 

.. _seek-count-ws:

Seeking and counting workshifts
-------------------------------

Create an interval for the examples::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
    >>> print(ivl)
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    <BLANKLINE>
            ws_ref      start  duration        end  label  on_duty
    loc                                                           
    2   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    3   2017-10-03 2017-10-03         1 2017-10-03    2.0     True
    4   2017-10-04 2017-10-04         1 2017-10-04    0.0    False
    5   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    6   2017-10-06 2017-10-06         1 2017-10-06    0.0    False
    7   2017-10-07 2017-10-07         1 2017-10-07    2.0     True
    8   2017-10-08 2017-10-08         1 2017-10-08    0.0    False

Seeking and counting with ``duty='on'``::

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
    ...                                 selector=lambda label: label>1)
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

.. _iterating:

Itertating over the interval
----------------------------

:py:meth:`~timeboard.Interval.workshifts` returns a generator that iterates over the interval and yields workshifts with the specified duty. By default, the duty is "on".
::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '15 Oct 2017', 
    ...                     layout=[0, 1, 0, 2])
    >>> ivl = clnd(('02 Oct 2017', '08 Oct 2017'))
    >>> print(ivl)
    Interval((2, 8)): 'D' at 2017-10-02 -> 'D' at 2017-10-08 [7]
    <BLANKLINE>
            ws_ref      start  duration        end  label  on_duty
    loc                                                           
    2   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    3   2017-10-03 2017-10-03         1 2017-10-03    2.0     True
    4   2017-10-04 2017-10-04         1 2017-10-04    0.0    False
    5   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    6   2017-10-06 2017-10-06         1 2017-10-06    0.0    False
    7   2017-10-07 2017-10-07         1 2017-10-07    2.0     True
    8   2017-10-08 2017-10-08         1 2017-10-08    0.0    False

::

    >>> for ws in ivl.workshifts():
    ...     print("{}\t{}".format(ws.start_time, ws.label))
    2017-10-03 00:00:00     2
    2017-10-05 00:00:00     1
    2017-10-07 00:00:00     2

::

    >>> list(ivl.workshifts(duty='off'))
    [Workshift(2) of 'D' at 2017-10-02,
     Workshift(4) of 'D' at 2017-10-04,
     Workshift(6) of 'D' at 2017-10-06,
     Workshift(8) of 'D' at 2017-10-08]

You can also use the interval itself as a generator that yields every workshift of the interval. This is the same generator as returned by ``ivl.workshifts(duty='any')``. ::

    >>> for ws in ivl:
    ...     print("{}\t{}".format(ws.start_time, ws.label))
    2017-10-02 00:00:00 0
    2017-10-03 00:00:00 2
    2017-10-04 00:00:00 0
    2017-10-05 00:00:00 1
    2017-10-06 00:00:00 0
    2017-10-07 00:00:00 2
    2017-10-08 00:00:00 0

::

    >>> list(ivl.workshifts(duty='any'))
    [Workshift(2) of 'D' at 2017-10-02,
     Workshift(3) of 'D' at 2017-10-03,
     Workshift(4) of 'D' at 2017-10-04,
     Workshift(5) of 'D' at 2017-10-05,
     Workshift(6) of 'D' at 2017-10-06,
     Workshift(7) of 'D' at 2017-10-07,
     Workshift(8) of 'D' at 2017-10-08]


.. _measuring-worktime:

Measuring work time
-------------------

The source of the information about workshifts' work time is determined by :py:class:`.Timeboard`\ .\ :py:attr:`worktime_source` attribute.

:py:meth:`.Interval.worktime` method returns the sum of the work times of the workshifts with the specified duty. If the interval does not contain workshifts with this duty, the method returns zero. 

By default, workshift's work time equals to workshift's duration::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
    ...                     layout=[4, 8, 4, 8],
    ...                     default_selector = lambda label: label>4)
    >>> ivl = tb.Interval(clnd, (1, 3))
    >>> print (ivl)
    Interval((1, 3)): 'D' at 2017-10-01 -> 'D' at 2017-10-03 [3]
    <BLANKLINE>
            ws_ref      start  duration        end  label  on_duty
    loc                                                           
    1   2017-10-01 2017-10-01         1 2017-10-01    8.0     True
    2   2017-10-02 2017-10-02         1 2017-10-02    4.0    False
    3   2017-10-03 2017-10-03         1 2017-10-03    8.0     True

::

    >>> ivl.worktime()
    2
    >>> ivl.worktime(duty='off')
    1
    >>> ivl.worktime(duty='any')
    3

In the example below, the work time is taken from the labels::

    >>> clnd = tb.Timeboard('D', '30 Sep 2017', '11 Oct 2017', 
    ...                     layout=[4, 8, 4, 8],
    ...                     default_selector = lambda label: label>4,
    ...                     worktime_source = 'labels')
    >>> ivl = tb.Interval(clnd, (1, 3))

::

    >>> ivl.worktime()
    16.0
    >>> ivl.worktime(duty='off')
    4.0
    >>> ivl.worktime(duty='any')
    20.0

.. note:: To count the total duration of the workshifts in the interval (regardless of the work time) call :py:meth:`.Interval.total_duration`.

.. _relation-with-other:

Relation with another interval
------------------------------

:py:meth:`~timeboard.Interval.what_portion_of` builds the intersection of this interval and another and returns the ratio of the workshift count in the intersection to the workshift count in the other interval.  Only workshifts with the specified duty are counted. 
        
If the two intervals do not overlap or their intersection contains no workshifts with the specified duty, zero is returned.

The common use of this method is to answer questions like "what portion of year 2017 has employee X been with the company?". In the examples below, for the purpose of demonstration, the question is scaled down to "what portion of the week?.."::

    >>> clnd = tb.Timeboard('D', '02 Oct 2017', '15 Oct 2017',
    ...                     layout=[1, 1, 1, 1, 1, 0, 0])
    >>> week1 = clnd('02 Oct 2017', period='W')

`week1` contains five working days and two days off. ::

    >>> X_in_staff = clnd(('05 Oct 2017', '07 Oct 2017'))

X was was with the company Thursday through Saturday of `week1` (two
working days and one day off). ::

    >>> .what_portion_of(week1)
    0.4
    >>> 2 / 5 # working days
    0.4

::

    >>> X_in_staff.what_portion_of(week1, duty='off')
    0.5
    >>> 1 / 2 # days off
    0.5

::

    >>> X_in_staff.what_portion_of(week1, duty='any')
    0.42857142857142855
    >>> 3 / 7 # all days
    0.42857142857142855

You can use  `/` (division) operator as a shortcut. It calls `what_portion_of()` with the default parameter values (so, the duty is 'on')::

    >>> X_in_staff / week1
    0.4

X had already left before `week2` started::

    >>> week2 = clnd('09 Oct 2017', period='W')
    >>> X_in_staff.what_portion_of(week2, duty='any')
    0.0

Y has worked the entire `week1` and stayed afterwards::

        >>> Y_in_staff = clnd(('02 Oct 2017', '11 Oct 2017'))
        >>> decade.what_portion_of(week1)
        1.0

A corner case::

    >>> weekend = clnd(('07 Oct 2017', '08 Oct 2017'))

All days of `weekend` are also the days of `week1` but they are not 
working days, so::

    >>> weekend.what_portion_of(week1)
    0.0

However, `weekend` contains all off duty days of `week1`::

    >>> weekend.what_portion_of(week1, duty='off')
    1.0


.. _counting-periods:

Counting periods
----------------

Call :py:meth:`~timeboard.Interval.count_periods` to find out how many calendar periods of the specific frequency fit into the interval. As with the other methods, the duty of workshifts is taken into account. The method returns a float number.

To obtain the result, the interval is sliced into calendar periods of the given frequency and then each slice of the interval is compared to its corresponding period duty-wise. That is to say, the count of workshifts in the interval's slice is divided by the total count of workshifts in the  period containing this slice but only workshifts with the specified duty are counted. The quotients for each period are summed to produce the return value of the method.
        
If some period does not contain workshifts of the required duty, it contributes zero to the returned value.
        
Regardless of the period frequency, the method returns 0.0 if there are no workshifts with the specified duty in the interval.

The common use of this method is to answer questions like "Exactly, how many years has X worked in the company?" In the examples below, for the purpose of demonstration, the question is scaled down to "how many days?.." for a timeboard with hourly shifts.

Examples::

    >>> clnd = tb.Timeboard('H', '01 Oct 2017', '08 Oct 2017 23:59', 
    ...                     layout=[0, 1, 0, 2])
    >>> X_in_staff = clnd(('01 Oct 2017 13:00', '02 Oct 2017 23:59'))

X's tenure spans two days: it contains 11 of 24 workshifts of 
October 1, and all 24 workshifts of October 2::

     >>> X_in_staff.count_periods('D', duty='any')
     1.4583333333333333
     >>> 11.0/24 + 24.0/24
     1.4583333333333333

The timeboard's `layout` defines that all workshifts taking place on even hours are off duty, and those on odd hours are on duty. The first workshift of the interval (01 October 13:00 - 13:59) is on duty. Hence, interval `X_in_staff` contains 6 of 12 on duty workshifts of October 1, and all 12 on duty workshifts of October 2::

    >>> X_in_staff.count_periods('D')
    1.5
    >>> 6.0/12 + 12.0/12
    1.5

The interval contains 5 of 12 off duty workshifts of October 1, and all 12 off duty workshifts of October 2::

    >>> X_in_staff.count_periods('D', duty='off')
    1.4166666666666667
    >>> 5.0/12 + 12.0/12
    1.4166666666666667

If we change the schedule to `my_schedule`, on duty workshifts will start only at 3, 7, 11, 15, 19, and 23 o'clock yielding 6 on duty workshifts per day. Interval `X_in_staff` will contain 3/6 + 6/6 on duty days and 8/18 + 18/18 off duty days::

    >>> my_schedule = clnd.add_schedule(name='my_schedule', 
    ...                                 selector=lambda label: label>1)

::

    >>> X_in_staff.count_periods('D', schedule=my_schedule)
    1.5
    >>> 3.0/6 + 6.0/6
    1.5
    >>> X_in_staff.count_periods('D', duty='off', schedule=my_schedule)
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

::

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
    ...                     layout=[0, 1, 0, 2])
    >>> ivl1 = clnd(('02 Oct 2017 00:00', '02 Oct 2017 23:59'))
    >>> ivl2 = clnd(('01 Oct 2017 13:00', '02 Oct 2017 23:59'))

We can count how many weeks are in interval `ivl1` but not in `ivl2`. 

All workshifts of `ivl1` belong to the week of October 2 - 8 which is situated entirely within the timeboard. On the other hand, in `ivl2` there are the workshifts belonging to the week of September 25 - October 1. This week extends beyond the timeboard. We may not guess what layout *could* be applied to the workshifts of Sep 25 - Sep 30 if the week were included in the timeboard entirely. We are not authorized to extrapolate the existing layout outside the timeboard. Moreover, for some complex layouts, any attempt at extrapolation would be ambiguous. ::

    >>> ivl1.count_periods('W')
    0.14285714285714285
    >>> ivl2.count_periods('W')
    -----------------------------------------------------------------------
    PartialOutOfBoundsError               Traceback (most recent call last)
      ...
    PartialOutOfBoundsError: The left bound of interval or period referenced by `2017-09-25/2017-10-01` is outside Timeboard of 'H': 2017-10-01 00:00 -> 2017-10-08 23:00


Workshift straddles period boundary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This case is analogous to the already reviewed  
:ref:`issue <workshift-straddling-1>` of constructing an interval from a calendar period. :py:class:`.Timeboard`\ .\ :py:attr:`workshift_ref` attribute  is used to identify workshift's membership in a period. 

Period too short for workshifts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you try to count periods which are shorter than (some) of the workshifts in the interval, you are likely to encounter a period which does not contain *any* workshift's reference whatever the duty. This makes any result meaningless and, consequently, `UnacceptablePeriodError` is raised. 

You may accidentally run into this issue in two situations:

- You use compound workshifts and while most of the workshifts (usually those covering the working time) are of one size, there are a few workshifts (usually those covering the closed time) which are much larger. Trying to count periods, you have in mind the smaller workshifts. If a larger one gets into the interval and your period is not long enough, you will find yourself with `UnacceptablePeriodError`.

- You have misinterpreted the purpose of :py:meth:`count_periods` method and try to use it as a general time counter. For example, in a timeboard with workshifts of varying duration measured in hours, you want to find out how many clock hours there are in an interval. In order to do that use `pandas.Timedelta` tools with `start_time` and `end_time` attributes of workshifts and intervals.
