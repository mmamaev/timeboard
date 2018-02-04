******************
Making a Timeboard
******************

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: none


A timeboard is constructed by calling :py:meth:`~timeboard.Timeboard` constructor with parameters that define the desired configuration of the calendar. In the simplest case this can be done by an one-liner but most likely you will use auxiliary tools such as :py:class:`.Organizer`, :py:class:`.Marker`, and :py:class:`.RememberingPattern`.

The import statement to run the examples::

    >>> import timeboard as tb

It is assumed that you are familiar with :doc:`Data Model <data_model>`.

Basic case
==========

:py:class:`.Timeboard` class requires four mandatory parameters for instantiating a timeboard::

 >>> clnd = tb.Timeboard(base_unit_freq='D', 
                         start='01 Oct 2017', end='10 Oct 2017', 
                         layout=[1, 0, 0])


The first three parameters define the frame:

base_unit_freq : str
    A pandas-compatible calendar frequency (i.e. 'D' for calendar day  or '8H' for 8 consecutive hours regarded as one period) which defines timeboard's base unit. Pandas-native business  periods (i.e. 'BM') are not supported. 
start : `Timestamp`-like
    A point in time referring to the first base unit of the timeboard. 
    The point in time can be located anywhere within this base unit.
    The value may be a pandas Timestamp, or a string convertible 
    to Timestamp (i.e. "01 Oct 2017 18:00"), or a datetime object. 
end : `Timestamp`-like
    Same as `start` but for the last base unit of the timeboard.

The forth parameter, `layout`, describes the timeline of workshifts. 

In the basic case `layout` is simply an iterable of workshift labels. In the above example ``layout=[1, 0, 0]`` means that each workshift occupies one base unit; the workshift at the first base unit receives label 1, the second workshift recevies label 0, the third - again label 0. Further on, label assignment repeats in cycles: the forth workshift will get label 1, the fifth - 0, the sixth - 0, the seventh - 1, and so on. This way the timeline is created.

Under the hood the timeboard builds default schedule using default selector which returns ``bool(label)``. Therefore, under this schedule the first and then every forth workshift are on duty, and the rest are off duty. ::

    >>> print(clnd)
    Timeboard of 'D': 2017-10-01 -> 2017-10-10

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2017-10-01 2017-10-01         1 2017-10-01    1.0     True
    1   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    2   2017-10-03 2017-10-03         1 2017-10-03    0.0    False
    3   2017-10-04 2017-10-04         1 2017-10-04    1.0     True
    4   2017-10-05 2017-10-05         1 2017-10-05    0.0    False
    5   2017-10-06 2017-10-06         1 2017-10-06    0.0    False
    6   2017-10-07 2017-10-07         1 2017-10-07    1.0     True
    7   2017-10-08 2017-10-08         1 2017-10-08    0.0    False
    8   2017-10-09 2017-10-09         1 2017-10-09    0.0    False
    9   2017-10-10 2017-10-10         1 2017-10-10    1.0     True


Amendments
----------

You use the optional parameter `amendments` to account for any disruptions of the regular pattern of the calendar (such as holidays, etc.). 

The `amendments` is a dictionary. The keys are `Timestamp`-like points in time used to identify workshifts (the point in time may be located anywhere within the workshift, i.e. at noon of a day as in the example below). The values of `amendments` are labels for the corresponding workshifts overriding the labels which have been set by `layout`.  ::

    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Oct 2017', end='10 Oct 2017', 
                            layout=[1, 0, 0], 
                            amendments={'07 Oct 2017 12:00': 0})
    >>> print(clnd)
    Timeboard of 'D': 2017-10-01 -> 2017-10-10

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2017-10-01 2017-10-01         1 2017-10-01      1     True
    1   2017-10-02 2017-10-02         1 2017-10-02      0    False
    2   2017-10-03 2017-10-03         1 2017-10-03      0    False
    3   2017-10-04 2017-10-04         1 2017-10-04      1     True
    4   2017-10-05 2017-10-05         1 2017-10-05      0    False
    5   2017-10-06 2017-10-06         1 2017-10-06      0    False
    6   2017-10-07 2017-10-07         1 2017-10-07      0    False
    7   2017-10-08 2017-10-08         1 2017-10-08      0    False
    8   2017-10-09 2017-10-09         1 2017-10-09      0    False
    9   2017-10-10 2017-10-10         1 2017-10-10      1     True


Note, that if there are several keys in `amendments` which refer to the same 
workshift, the final label of this workshift would be unpredictable, therefore a `KeyError` is raised::

    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Oct 2017', end='10 Oct 2017', 
                            layout=[1, 0, 0], 
                            amendments={'07 Oct 2017 12:00': 0,
                                        '07 Oct 2017 15:00': 1})
    ---------------------------------------------------------------------------
    KeyError                                  Traceback (most recent call last)
    ...
    KeyError: "Amendments key '07 Oct 2017 15:00' is a duplicate reference to workshift 6"


Other `Timeboard` parameters
----------------------------

workshift_ref : {``"start"`` | ``"end"``}, optional (default ``"start"``)
    Define what point in time will be used to represent a workshift. 
    The respective point in time will be returned by :py:meth:`.Workshift.to_timestamp`. Available  options: ``"start"`` to use the start time of the workshift, ``"end"`` to use the end time. 

    When printing a timeboard, the workshift reference time is shown in "workshift" column.

    Workshift reference time is used to determine to which calendar period the workshift belongs if the workshift straddles a boundary of the calendar period. This is used by :py:meth:`.Interval.count_periods`.

default_name : str, optional
    The name for the default schedule. If not supplied, "on_duty" 
    is used.

    When printing a timeboard, the rightmost column(s) are titled with the names of the schedules and show the workshift duty statuses under the corresponding schedules: True if the workshift is on duty, False otherwise. There is at least one column, showing the default schedule.

default_selector : function, optional
    The selector function for the default schedule. This is 
    the function which takes one argument - label of a workshift, and 
    returns True if this is an on duty workshift, False otherwise. 
    If not supplied, the function that returns ``bool(label)`` is used.


Example: Call Center Shifts With Equal Duration
-----------------------------------------------

Operators in a 24x7 call center work in three 8-hour shifts starting at 10:00, 18:00, and 02:00. For each operator one on duty shift is followed by three off duty shifts. The working schedule for operators at shift 'A'::

    >>> clnd = tb.Timeboard(base_unit_freq='8H', 
                            start='01 Oct 2017 02:00', end='05 Oct 2017 01:59',
                            layout=['A', 'B', 'C', 'D'],
                            default_selector=lambda label: label=='A',
                            default_name='shift_A')
    >>> print(clnd)
    Timeboard of '8H': 2017-10-01 02:00 -> 2017-10-04 18:00

                  workshift ...                  end  label  shift_A
    loc                     ...                                     
    0   2017-10-01 02:00:00 ...  2017-10-01 09:59:59      A     True
    1   2017-10-01 10:00:00 ...  2017-10-01 17:59:59      B    False
    2   2017-10-01 18:00:00 ...  2017-10-02 01:59:59      C    False
    3   2017-10-02 02:00:00 ...  2017-10-02 09:59:59      D    False
    4   2017-10-02 10:00:00 ...  2017-10-02 17:59:59      A     True
    5   2017-10-02 18:00:00 ...  2017-10-03 01:59:59      B    False
    6   2017-10-03 02:00:00 ...  2017-10-03 09:59:59      C    False
    7   2017-10-03 10:00:00 ...  2017-10-03 17:59:59      D    False
    8   2017-10-03 18:00:00 ...  2017-10-04 01:59:59      A     True
    9   2017-10-04 02:00:00 ...  2017-10-04 09:59:59      B    False
    10  2017-10-04 10:00:00 ...  2017-10-04 17:59:59      C    False
    11  2017-10-04 18:00:00 ...  2017-10-05 01:59:59      D    False

    # The "start" and "duration" columns have been omitted to fit the output 
    # to the page

There are two things in this example to point out. 

First, to avoid the compound workshifts we use the 8 hour base unit but we need to align the base units with the workshifts, hence the frame starts at 02:00 o'clock. Note that duration of each workshift equals to one (base unit).

Second, we have overriden the selector function for the default schedule which now sets on duty status for workshifts labeled as 'A'. The name for the default schedule has been changed accordingly to 'shift_A'.

Should you need to know which workshifts are on duty for the shift labeled with another symbol, you may add another schedule to the timeboard and supply the appropriate selector function::

    >>> clnd.add_schedule(name='shift_B', selector=lambda label: label=='B')
    >>> print(clnd)
    Timeboard of '8H': 2017-10-01 02:00 -> 2017-10-04 18:00

                  workshift ...                 end  label  shift_A  shift_B  
    loc                     ...                                             
    0   2017-10-01 02:00:00 ... 2017-10-01 09:59:59      A     True    False
    1   2017-10-01 10:00:00 ... 2017-10-01 17:59:59      B    False     True
    2   2017-10-01 18:00:00 ... 2017-10-02 01:59:59      C    False    False
    3   2017-10-02 02:00:00 ... 2017-10-02 09:59:59      D    False    False
    4   2017-10-02 10:00:00 ... 2017-10-02 17:59:59      A     True    False
    5   2017-10-02 18:00:00 ... 2017-10-03 01:59:59      B    False     True
    6   2017-10-03 02:00:00 ... 2017-10-03 09:59:59      C    False    False
    7   2017-10-03 10:00:00 ... 2017-10-03 17:59:59      D    False    False
    8   2017-10-03 18:00:00 ... 2017-10-04 01:59:59      A     True    False
    9   2017-10-04 02:00:00 ... 2017-10-04 09:59:59      B    False     True
    10  2017-10-04 10:00:00 ... 2017-10-04 17:59:59      C    False    False
    11  2017-10-04 18:00:00 ... 2017-10-05 01:59:59      D    False    False

    # The "start" and "duration" columns have been omitted to fit the output 
    # to the page

The "shift_A" schedule still holds a special role of the default schedule which is used in calculations when no schedule is explicitly given. ::

    >>> clnd.default_schedule.name
    'shift_A'


Using `Organizer`
=================

For most real-world scenarios a simple pattern of labels uniformly recurring across the whole timeboard is not sufficient for building a usable timeline. This is where :py:class:`.Organizer` comes into play.

:py:class:`.Organizer` tells how to partition the frame into chunks and how to structure each span into workshifts. 

There are two mandatory parameters for an organizer. The first one is either `marks` or `marker` (but not both), it defines spans' boundaries. The second one is `structure`, it defines the structure of each span.

Below is an example of the organizer used to build a regular business calendar::

>>> weekly = tb.Organizer(marker='W', structure=[[1,1,1,1,1,0,0]])

An organizer is supplied to :py:meth:`~timeboard.Timeboard` constructor in `layout` parameter instead of a pattern of labels which has been discussed in the previous section::

    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Oct 2017', end='12 Oct 2017', 
                            layout=weekly)

Parameters of `Organizer`
-------------------------

The first parameter of :py:meth:`~timeboard.Organizer` - `marks` or `marker`, whichever is given, - tells where on the frame there will be marks designating the boundaries of spans. A mark is a point in time; the base unit containing this point in time will be the first base unit of a span. 

If, for example, an organizer defines two marks, there will be three spans. The first span will begin on the first base unit of the frame and end on the base unit immediately preceding the unit containing the first mark. The second span will begin on the base unit containing the first mark and end on the base unit immediately preceding the unit containing the second mark. The third span will begin on the base unit containing the second mark and end on the last base unit of the frame.

marks : Iterable
    This is a list of explicit points in time which refer to the first base units of the spans.  

    A point in time is a `Timestamp`-like value (a `pandas.Timestamp`, or a string convertible to `Timestamp` (i.e. "10 Oct 2017 18:00"), or a `datetime` object). A point in time can be located anywhere within the base unit it refers to.

    An empty `marks` list means that no partitioning is done, and the only span is the entire frame. 

marker : str or Marker
    You use `marker` to define the rule how to calculate the locations of marks rather than specify the explicit points in time as with `marks` parameter.

    In simpler cases the value of `marker` is a string representing a `pandas`-compatible calendar frequency (accepts same kind of values as :py:attr:`~.timeboard.Timeboard.base_unit_freq` of `Timeboard`; for example, ``'W'`` for weeks). The marks are set at the start times of the calendar periods, and as the result, the frame is partitioned into spans representing periods of the specified frequency. 

    Note that the first or the last span, or both may end up containing incomplete calendar periods. For example, the daily frame from 1 Oct 2017 through 12 Oct 2017 when partitioned with ``marker='W'`` produces three spans. The first span contains only 1 Oct 2017 as it was Sunday. The second span contains the full week from the Monday 2nd through the Sunday 8th of October. The last span consists of four days 9-12 of October which obviously do not form a complete week.

    The parts of the "marker" calendar periods which fall outside the first and the last spans are called dangles. In the example above the left dangle is the period from Monday 25 through Saturday 30 of September, and the right dangle is Friday 13 through Sunday 15 of October::

                     Mo  Tu  We  Th  Fr  Sa  Su
      left dangle  : 25  26  27  28  29  30       
      span 0       :                          1   frame start='01 Oct 2017'
      span 1       :  2   3   4   5   6   7   8
      span 2       :  9  10  11  12               frame end='12 Oct 2017'
      right dangle :                 13  14  15

structure : Iterable
    Each element of `structure` matches a span produced by partitioning: the first element of `structure` is applied to the first span, the second - to the second span, and so on. If the `structure` gets exhausted, it starts over and iterates in cycles until the last span has been treated.

    An element of `structure` can be one of the following: 

        - a pattern of labels : make each base unit a separate workshift, assign labels from the pattern;
        - another :py:class:`.Organizer` : recusrively organize the span into sub-spans;
        - a single label : combine all base units of the span into a single compound workshift with the given label.

    The following sections will provide examples of all these options.

.. note:: Under the hood, ``layout=[1, 0, 0]`` passed to :py:meth:`~.timeboard.Timeboard` is converted  into ``layout=Organizer(marks=[], structure=[[1, 0, 0]])``.

Example: Business Day Calendar
------------------------------

.. note::

  1. For the demonstration purposes the timeboard is deliberately made short .

  2. For the real-world usage the holidays must be accounted for in the form of `amendments`. Here they are omitted for simplicity.

::

    >>> weekly = tb.Organizer(marker='W', structure=[[1,1,1,1,1,0,0]])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Oct 2017', end='12 Oct 2017',
                            layout=weekly)  


In this example the frame is partitioned into calendar weeks. This process produces three spans as shown in the previous section. The first span contains only Sunday 1 Oct 2017. The second span contains the full week from the Monday 2nd through the Sunday 8th of October. The last span consists of four days 9-12 of October.

The first element of `structure` is a list of values - a pattern. Therefore in the first span workshifts coincide with base units and receive labels from the pattern. 

However, unlike the use of pattern directly in `layout` parameter of :py:class:`.Timeboard`, the first workshift of the span does not nesessarily receive the first label of the pattern. If the span has a left dangle, the pattern starts with a shadow run through the length of the dangle. Only after that it begins yielding labels for workshifts of the span. This approach can be viewed as if the dangle was attached to the first span to form the complete calendar period (in this example, a complete week) and then the pattern was applied to the whole period but only those results (assigned labels) are retained that fall within the span. In this way, the workshift of October 1 receives the seventh label from the pattern, which is 0, after the first six labels have been shadow-assigned to the base units of the dangle. 

The second span, a full week of October 2-8, should be treated with the second element of `structure`. However, there is no second element and `structure` is consequently reenacted in cycles meaning that each span is treated with the first, and the only, element of the structure. 

An interior span, such as the second span of this example, cannot have dangles. Therefore, the seven labels of the pattern are assigned in order to the seven workshifts of the second span.

The last, third span is again an incomplete week, but this time there is a right dangle. As patterns are currently applied only left to right, the presence of the right dangle does not produce any effect upon workshift labeling. The four workshifts of the third span receive the first four labels from the pattern.

The resulting calendar is printed below. ::

    >>> print(clnd)
    Timeboard of 'D': 2017-10-01 -> 2017-10-12

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2017-10-01 2017-10-01         1 2017-10-01    0.0    False
    1   2017-10-02 2017-10-02         1 2017-10-02    1.0     True
    2   2017-10-03 2017-10-03         1 2017-10-03    1.0     True
    3   2017-10-04 2017-10-04         1 2017-10-04    1.0     True
    4   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    5   2017-10-06 2017-10-06         1 2017-10-06    1.0     True
    6   2017-10-07 2017-10-07         1 2017-10-07    0.0    False
    7   2017-10-08 2017-10-08         1 2017-10-08    0.0    False
    8   2017-10-09 2017-10-09         1 2017-10-09    1.0     True
    9   2017-10-10 2017-10-10         1 2017-10-10    1.0     True
    10  2017-10-11 2017-10-11         1 2017-10-11    1.0     True
    11  2017-10-12 2017-10-12         1 2017-10-12    1.0     True


Example: Alternating periods
----------------------------

Consider a schedule of workshifts in a car dealership. A mechanic works on Monday, Tuesday, Saturday, and Sunday this week, and on Wednesday, Thursday, and Friday next week; then the bi-weekly cycle repeats. ::

    >>> biweekly = tb.Organizer(marker='W',
                                structure=[[1,1,0,0,0,1,1],[0,0,1,1,1,0,0]])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Oct 2017', end='22 Oct 2017', 
                            layout=biweekly)
    >>> print(clnd)
    Timeboard of 'D': 2017-10-01 -> 2017-10-22

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2017-10-01 2017-10-01         1 2017-10-01    1.0     True
    1   2017-10-02 2017-10-02         1 2017-10-02    0.0    False
    2   2017-10-03 2017-10-03         1 2017-10-03    0.0    False
    3   2017-10-04 2017-10-04         1 2017-10-04    1.0     True
    4   2017-10-05 2017-10-05         1 2017-10-05    1.0     True
    5   2017-10-06 2017-10-06         1 2017-10-06    1.0     True
    6   2017-10-07 2017-10-07         1 2017-10-07    0.0    False
    7   2017-10-08 2017-10-08         1 2017-10-08    0.0    False
    8   2017-10-09 2017-10-09         1 2017-10-09    1.0     True
    9   2017-10-10 2017-10-10         1 2017-10-10    1.0     True
    10  2017-10-11 2017-10-11         1 2017-10-11    0.0    False
    11  2017-10-12 2017-10-12         1 2017-10-12    0.0    False
    12  2017-10-13 2017-10-13         1 2017-10-13    0.0    False
    13  2017-10-14 2017-10-14         1 2017-10-14    1.0     True
    14  2017-10-15 2017-10-15         1 2017-10-15    1.0     True
    15  2017-10-16 2017-10-16         1 2017-10-16    0.0    False
    16  2017-10-17 2017-10-17         1 2017-10-17    0.0    False
    17  2017-10-18 2017-10-18         1 2017-10-18    1.0     True
    18  2017-10-19 2017-10-19         1 2017-10-19    1.0     True
    19  2017-10-20 2017-10-20         1 2017-10-20    1.0     True
    20  2017-10-21 2017-10-21         1 2017-10-21    0.0    False
    21  2017-10-22 2017-10-22         1 2017-10-22    0.0    False


Undersized and oversized patterns
---------------------------------

A pattern supplied as an element of `structure` can be found undersized. It means that the pattern is shorter than the length of the span it is to be applied to. In this case the pattern will be reenacted in cycles until the full length of the span has been covered.

If, at the same time, the span has a left dangle associated with it, then the aproach is consistent with the one described in the previous section. The dangle is attached to the beginning of the span. Then the pattern is run in cycles over the combined dangle-and-span retaining only those labels that belong to the span.

The example below illustrates the behavior of undersized patterns. It shows the calendar of activities happening on odd days of week. ::

    >>> weekly = tb.Organizer(marker='W', structure=[[1,0]])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Oct 2017', end='12 Oct 2017', 
                            layout=weekly)
    >>> print(clnd)
    Timeboard of 'D': 2017-10-01 -> 2017-10-12

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2017-10-01 2017-10-01         1 2017-10-01    1.0     True
    1   2017-10-02 2017-10-02         1 2017-10-02    1.0     True
    2   2017-10-03 2017-10-03         1 2017-10-03    0.0    False
    3   2017-10-04 2017-10-04         1 2017-10-04    1.0     True
    4   2017-10-05 2017-10-05         1 2017-10-05    0.0    False
    5   2017-10-06 2017-10-06         1 2017-10-06    1.0     True
    6   2017-10-07 2017-10-07         1 2017-10-07    0.0    False
    7   2017-10-08 2017-10-08         1 2017-10-08    1.0     True
    8   2017-10-09 2017-10-09         1 2017-10-09    1.0     True
    9   2017-10-10 2017-10-10         1 2017-10-10    0.0    False
    10  2017-10-11 2017-10-11         1 2017-10-11    1.0     True
    11  2017-10-12 2017-10-12         1 2017-10-12    0.0    False

Note that the first of October receives label ``1`` after the pattern ``[1, 0]`` has completed three shadow cycles over the six-day dangle.

If the pattern is oversized, meaning it is longer than the span, the excess labels are ignored. Should the same pattern be applied to another span in the next cycle through `structure`, the labeling restarts from the beginning of the pattern.

Recursive organizing
====================

A small museum's schedule is seasonal. In winter (November through April) the museum is open only on Wednesdays and Thursdays, but in summer (May through October) the museum works every day except Monday. ::

    >>> winter = tb.Organizer(marker='W', structure=[[0,0,1,1,0,0,0]])
    >>> summer = tb.Organizer(marker='W', structure=[[0,1,1,1,1,1,1]])
    >>> seasonal = tb.Organizer(marker='6M', structure=[winter, summer])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Nov 2015', end='31 Oct 2017', 
                            layout=seasonal)

In this example there are two levels of organizers. 

On the outer level `seasonal` organizer partitions the frame into spans of 6 months each. The spans  represent, alternatively, winter and summer seasons. The `structure` of this organizer, instead of containing patterns of labels, refers to other organizers. These inner level organizers, named `winter` and `summer`, are applied, in turns, to the spans produced by `seasonal` organizer as if they were whole frames. 

On the inner level each season is partitioned into weeks by `winter` or `summer` organizer correspondingly. As the result, workshifts within the weeks of each season receive labels from the patterns specific for the seasons. ::

    >>> print(clnd)
    Timeboard of 'D': 2015-11-01 -> 2017-10-31

         workshift      start  duration        end  label  on_duty
    loc                                                           
    0   2015-11-01 2015-11-01         1 2015-11-01    0.0    False
    1   2015-11-02 2015-11-02         1 2015-11-02    0.0    False
    2   2015-11-03 2015-11-03         1 2015-11-03    0.0    False
    3   2015-11-04 2015-11-04         1 2015-11-04    1.0     True
    4   2015-11-05 2015-11-05         1 2015-11-05    1.0     True
    5   2015-11-06 2015-11-06         1 2015-11-06    0.0    False
    6   2015-11-07 2015-11-07         1 2015-11-07    0.0    False
    7   2015-11-08 2015-11-08         1 2015-11-08    0.0    False
    8   2015-11-09 2015-11-09         1 2015-11-09    0.0    False
    9   2015-11-10 2015-11-10         1 2015-11-10    0.0    False
    10  2015-11-11 2015-11-11         1 2015-11-11    1.0     True
    11  2015-11-12 2015-11-12         1 2015-11-12    1.0     True
    12  2015-11-13 2015-11-13         1 2015-11-13    0.0    False
    13  2015-11-14 2015-11-14         1 2015-11-14    0.0    False
    14  2015-11-15 2015-11-15         1 2015-11-15    0.0    False
    ..         ...        ...       ...        ...    ...      ...
    715 2017-10-16 2017-10-16         1 2017-10-16    0.0    False
    716 2017-10-17 2017-10-17         1 2017-10-17    1.0     True
    717 2017-10-18 2017-10-18         1 2017-10-18    1.0     True
    718 2017-10-19 2017-10-19         1 2017-10-19    1.0     True
    719 2017-10-20 2017-10-20         1 2017-10-20    1.0     True
    720 2017-10-21 2017-10-21         1 2017-10-21    1.0     True
    721 2017-10-22 2017-10-22         1 2017-10-22    1.0     True
    722 2017-10-23 2017-10-23         1 2017-10-23    0.0    False
    723 2017-10-24 2017-10-24         1 2017-10-24    1.0     True
    724 2017-10-25 2017-10-25         1 2017-10-25    1.0     True
    725 2017-10-26 2017-10-26         1 2017-10-26    1.0     True
    726 2017-10-27 2017-10-27         1 2017-10-27    1.0     True
    727 2017-10-28 2017-10-28         1 2017-10-28    1.0     True
    728 2017-10-29 2017-10-29         1 2017-10-29    1.0     True
    729 2017-10-30 2017-10-30         1 2017-10-30    0.0    False
    730 2017-10-31 2017-10-31         1 2017-10-31    1.0     True

    [731 rows x 6 columns]

There may be any number of recursion levels for organizers. 


Using `Marker`
==============

The museum's schedule discussed in the previous section is contrived in that  each season is exactly 6 months long. If, for example, the summer season began on the 1st of May and ended on the 15th of September, we could not construct the timeline by merely partittioning the frame with calendar periods.

More sophisticated partitioning is achieved with the tool called :py:class:`.Marker`. For example, the marks for seasons starting annually on May 1 and Sep 16 are set by::

    tb.Marker(each='A', at=[{'months':4}, {'months':8, 'days':15}])

:py:meth:`~.timeboard.Marker` constructor takes one mandatory parameter, `each`, but the real power comes with the use of parameter `at`.

    each : str
        `pandas`-compatible calendar frequency (accepts same kind of values as 
        :py:attr:`~.timeboard.Timeboard.base_unit_freq` of `Timeboard`). 
    at : list of dict, optional
        This is an iterable of dictionaries. Each dictionary specifies a time offset using such keywords as ``'months'``, ``'days'``, ``'hours'``, etc. 

For each calendar period of frequency `each` we obtain candidate marks by adding offsets from `at` list to the start time of the period.  After that we retain only those candidates that fall within the period (and, obviously, within the frame) - these points become the marks.

The expression in the above example::

    tb.Marker(each='A', at=[{'months':4}, {'months':8, 'days':15}])

means::

 there are two marks per year; 
 to get the first mark add 4 month to the start of each year; 
 to get the second mark add 8 month and 15 days to the start of the same year. 

Therefore, the frame is partitioned into spans starting on the 1st of May and on the 16th of September of each year provided that these dates are within the frame bounds.

An instance of :py:class:`.Marker` is passed to :py:meth:`~timeboard.Organizer` constructor as the value of `marker` parameter instead of a simple calendar frequency.

Example: Seasonal schedule
--------------------------

A small museum's schedule is seasonal. In winter (September 16 through April 30) the museum is open only on Wednesdays and Thursdays, but in summer (May 1 through September 15) the museum works every day except Monday. ::

    >>> winter = tb.Organizer(marker='W', structure=[[0,0,1,1,0,0,0]])
    >>> summer = tb.Organizer(marker='W', structure=[[0,1,1,1,1,1,1]])
    >>> seasons =  tb.Marker(each='A', 
                             at=[{'months':4}, {'months':8, 'days':15}])
    >>> seasonal = tb.Organizer(marker=seasons, 
                                structure=[winter, summer])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Jan 2015', end='31 Dec 2017',
                            layout=seasonal)

As the timeboard is too long to print it wholly, we will print only intervals around the marks. ::

    >>> print(clnd(('20 Apr 2017','10 May 2017')))
    Interval((840, 860)): 'D' at 2017-04-20 -> 'D' at 2017-05-10 [21]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    840 2017-04-20 2017-04-20         1 2017-04-20    1.0     True
    841 2017-04-21 2017-04-21         1 2017-04-21    0.0    False
    842 2017-04-22 2017-04-22         1 2017-04-22    0.0    False
    843 2017-04-23 2017-04-23         1 2017-04-23    0.0    False
    844 2017-04-24 2017-04-24         1 2017-04-24    0.0    False
    845 2017-04-25 2017-04-25         1 2017-04-25    0.0    False
    846 2017-04-26 2017-04-26         1 2017-04-26    1.0     True
    847 2017-04-27 2017-04-27         1 2017-04-27    1.0     True
    848 2017-04-28 2017-04-28         1 2017-04-28    0.0    False
    849 2017-04-29 2017-04-29         1 2017-04-29    0.0    False
    850 2017-04-30 2017-04-30         1 2017-04-30    0.0    False
    851 2017-05-01 2017-05-01         1 2017-05-01    0.0    False
    852 2017-05-02 2017-05-02         1 2017-05-02    1.0     True
    853 2017-05-03 2017-05-03         1 2017-05-03    1.0     True
    854 2017-05-04 2017-05-04         1 2017-05-04    1.0     True
    855 2017-05-05 2017-05-05         1 2017-05-05    1.0     True
    856 2017-05-06 2017-05-06         1 2017-05-06    1.0     True
    857 2017-05-07 2017-05-07         1 2017-05-07    1.0     True
    858 2017-05-08 2017-05-08         1 2017-05-08    0.0    False
    859 2017-05-09 2017-05-09         1 2017-05-09    1.0     True
    860 2017-05-10 2017-05-10         1 2017-05-10    1.0     True

    >>> print(clnd(('04 Sep 2017','24 Sep 2017')))
    Interval((977, 997)): 'D' at 2017-09-04 -> 'D' at 2017-09-24 [21]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    977 2017-09-04 2017-09-04         1 2017-09-04    0.0    False
    978 2017-09-05 2017-09-05         1 2017-09-05    1.0     True
    979 2017-09-06 2017-09-06         1 2017-09-06    1.0     True
    980 2017-09-07 2017-09-07         1 2017-09-07    1.0     True
    981 2017-09-08 2017-09-08         1 2017-09-08    1.0     True
    982 2017-09-09 2017-09-09         1 2017-09-09    1.0     True
    983 2017-09-10 2017-09-10         1 2017-09-10    1.0     True
    984 2017-09-11 2017-09-11         1 2017-09-11    0.0    False
    985 2017-09-12 2017-09-12         1 2017-09-12    1.0     True
    986 2017-09-13 2017-09-13         1 2017-09-13    1.0     True
    987 2017-09-14 2017-09-14         1 2017-09-14    1.0     True
    988 2017-09-15 2017-09-15         1 2017-09-15    1.0     True
    989 2017-09-16 2017-09-16         1 2017-09-16    0.0    False
    990 2017-09-17 2017-09-17         1 2017-09-17    0.0    False
    991 2017-09-18 2017-09-18         1 2017-09-18    0.0    False
    992 2017-09-19 2017-09-19         1 2017-09-19    0.0    False
    993 2017-09-20 2017-09-20         1 2017-09-20    1.0     True
    994 2017-09-21 2017-09-21         1 2017-09-21    1.0     True
    995 2017-09-22 2017-09-22         1 2017-09-22    0.0    False
    996 2017-09-23 2017-09-23         1 2017-09-23    0.0    False
    997 2017-09-24 2017-09-24         1 2017-09-24    0.0    False

If `at` parameter is not given or is an empty list, the marks are placed at the start times of the calendar periods specified by `each`.  

.. note:: Under the hood, ``marker='x'`` passed to :py:meth:`~.timeboard.Organizer` is converted into ``marker=Marker(each='x')``.

It should be emphasized that in the presence of non-empty `at` list the frame is partitioned on the `each` period boundary only if it is explicitly defined in `at` in the form of the zero offset (i.e. ``at=[{'days':0}, ... ]``).

If `at` list is non-empty but its processing has not produced any valid marks, no partitioning occurs.

Note that now we do not have to align the start of the frame with the start of a season. However, we must make sure that, if the frame starts in winter, then the first element in the structure of `seasonal` organizer is the organizer that is responsible for winter, and vice versa.


Using parameter `how`
---------------------

:py:meth:`~timeboard.Marker` constructor has the third parameter `how` which defines the interpretation of keyword arguments provided in `at` list: 

====================== ====================================================
Value of `how`         Interpretation of keyword arguments in `at`
====================== ====================================================
'from_start_of_each'   Keyword arguments define an offset from the beginning 
                       of `each` period. Acceptable keyword arguments
                       are ``'seconds'``, ``'minutes'``, ``'hours'``, 
                       ``'days'``, ``'weeks'``, ``'months'``, ``'years'``. 
                       Offsets nominated in different time units are added 
                       up.
                       
                       Example: ``at=[{'days':0}, {'days':1, 'hours':2}]``
                       (the first mark is at the start of the period, 
                       the second is in 1 day and 2 hours from the start of
                       the period).
                       
'from_easter_western'  Keyword arguments define an offset from the day of 
                       Western Easter. Acceptable arguments are the same 
                       as above.
                       
'from_easter_orthodox' Keyword arguments define an offset from the day of 
                       Orthodox Easter. Acceptable arguments are the same 
                       as above.

'nth_weekday_of_month' Keywords arguments refer to N-th weekday of 
                       M-th month from the start of `each` period. 
                       Acceptable keywords are: 
                       
                       - ``'month'`` : 1..12 
                          1 is for the first month (such as January 
                          for annual periods). 
                          
                       - ``'weekday'`` : 1..7 
                          1 is for Monday, 7 is for Sunday.
                       
                       - ``'week'`` : -5..-1,1..5 
                          -1 is for the last and 1 is for the first 
                          occurence of the weekday in the month. Zero is not
                          allowed.
                          
                       - ``'shift'`` : int, optional, default 0 
                          An offset in days from the weekday found.

                       Example: ``at=[{'month':5, 'weekday':7, 'week':-1}]``
                       (the last Sunday of the 5th month)
====================== ====================================================


The options ``'from_easter_western'`` and ``'from_easter_orthodox'`` assume the same format of `at` keywords as with the default option ``'from_start_of_each'`` which has been explored in the previous section. The difference is that the offset now may be negative. For example, ::

    tb.Marker(each='A', at=[{'days': -2}], how='from_easter_western')

sets marks at 00:00 on Good Fridays.


Example: Seasons turning on N-th weekday of month
-------------------------------------------------
        
The museum's summer season starts on a Tuesday after the first Monday in May and ends on the last Sunday in September. During summer the museum is open every day except Monday; during winter it is open on Wednesdays and Thursdays only. ::

    >>> winter = tb.Organizer(marker='W', structure=[[0,0,1,1,0,0,0]])
    >>> summer = tb.Organizer(marker='W', structure=[[0,1,1,1,1,1,1]])
    >>> seasons =  tb.Marker(each='A', 
                             at=[{'month':5, 'weekday':1, 'week':1, 'shift':1},
                                 {'month':9, 'weekday':7, 'week':-1}],
                             how='nth_weekday_of_month')
    >>> seasonal = tb.Organizer(marker=seasons, 
                                structure=[winter, summer])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Jan 2012', end='31 Dec 2015',
                            layout=seasonal)

    >>> print(clnd(('30 Apr 2012','15 May 2012')))
    Interval((120, 135)): 'D' at 2012-04-30 -> 'D' at 2012-05-15 [16]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    120 2012-04-30 2012-04-30         1 2012-04-30    0.0    False
    121 2012-05-01 2012-05-01         1 2012-05-01    0.0    False
    122 2012-05-02 2012-05-02         1 2012-05-02    1.0     True
    123 2012-05-03 2012-05-03         1 2012-05-03    1.0     True
    124 2012-05-04 2012-05-04         1 2012-05-04    0.0    False
    125 2012-05-05 2012-05-05         1 2012-05-05    0.0    False
    126 2012-05-06 2012-05-06         1 2012-05-06    0.0    False
    127 2012-05-07 2012-05-07         1 2012-05-07    0.0    False
    128 2012-05-08 2012-05-08         1 2012-05-08    1.0     True
    129 2012-05-09 2012-05-09         1 2012-05-09    1.0     True
    130 2012-05-10 2012-05-10         1 2012-05-10    1.0     True
    131 2012-05-11 2012-05-11         1 2012-05-11    1.0     True
    132 2012-05-12 2012-05-12         1 2012-05-12    1.0     True
    133 2012-05-13 2012-05-13         1 2012-05-13    1.0     True
    134 2012-05-14 2012-05-14         1 2012-05-14    0.0    False
    135 2012-05-15 2012-05-15         1 2012-05-15    1.0     True


Note that 1 May 2012 was Tuesday, so the Tuesday after the first Monday was 8 May 2012. The last Sunday in Septermber 2012 was the 30th. ::

    >>> print(clnd(('23 Sep 2012','07 Oct 2012')))
    Interval((266, 280)): 'D' at 2012-09-23 -> 'D' at 2012-10-07 [15]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    266 2012-09-23 2012-09-23         1 2012-09-23    1.0     True
    267 2012-09-24 2012-09-24         1 2012-09-24    0.0    False
    268 2012-09-25 2012-09-25         1 2012-09-25    1.0     True
    269 2012-09-26 2012-09-26         1 2012-09-26    1.0     True
    270 2012-09-27 2012-09-27         1 2012-09-27    1.0     True
    271 2012-09-28 2012-09-28         1 2012-09-28    1.0     True
    272 2012-09-29 2012-09-29         1 2012-09-29    1.0     True
    273 2012-09-30 2012-09-30         1 2012-09-30    0.0    False
    274 2012-10-01 2012-10-01         1 2012-10-01    0.0    False
    275 2012-10-02 2012-10-02         1 2012-10-02    0.0    False
    276 2012-10-03 2012-10-03         1 2012-10-03    1.0     True
    277 2012-10-04 2012-10-04         1 2012-10-04    1.0     True
    278 2012-10-05 2012-10-05         1 2012-10-05    0.0    False
    279 2012-10-06 2012-10-06         1 2012-10-06    0.0    False
    280 2012-10-07 2012-10-07         1 2012-10-07    0.0    False


Using Pattern with Memory
=========================

A school administrator's work schedule is 2 days on followed by 3 days off, with a recess from 14 Jul to 31 Aug every year::

    >>> year = tb.Marker(each='A', 
                         at=[{'months':6, 'days':13}, {'months':8}])
    >>> annually = tb.Organizer(marker=year, 
                                structure=[[1,1,1,0,0],[-1]])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Jan 2016', end='31 Dec 2017',
                            layout=annually, 
                            default_selector=lambda label: label>0)

The days of the recess are labeled with ``-1`` to differentiate them from the regular days off. The schedule selector has been adjusted accordingly.
::

    >>> print(clnd(('07 Jul 2016','17 Jul 2016')))
    Interval((188, 198)): 'D' at 2016-07-07 -> 'D' at 2016-07-17 [11]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    188 2016-07-07 2016-07-07         1 2016-07-07    1.0     True
    189 2016-07-08 2016-07-08         1 2016-07-08    1.0     True
    190 2016-07-09 2016-07-09         1 2016-07-09    1.0     True
    191 2016-07-10 2016-07-10         1 2016-07-10    0.0    False
    192 2016-07-11 2016-07-11         1 2016-07-11    0.0    False
    193 2016-07-12 2016-07-12         1 2016-07-12    1.0     True
    194 2016-07-13 2016-07-13         1 2016-07-13    1.0     True
    195 2016-07-14 2016-07-14         1 2016-07-14   -1.0    False
    196 2016-07-15 2016-07-15         1 2016-07-15   -1.0    False
    197 2016-07-16 2016-07-16         1 2016-07-16   -1.0    False
    198 2016-07-17 2016-07-17         1 2016-07-17   -1.0    False

    >>> print(clnd(('27 Aug 2016','06 Sep 2016')))
    Interval((239, 249)): 'D' at 2016-08-27 -> 'D' at 2016-09-06 [11]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    239 2016-08-27 2016-08-27         1 2016-08-27   -1.0    False
    240 2016-08-28 2016-08-28         1 2016-08-28   -1.0    False
    241 2016-08-29 2016-08-29         1 2016-08-29   -1.0    False
    242 2016-08-30 2016-08-30         1 2016-08-30   -1.0    False
    243 2016-08-31 2016-08-31         1 2016-08-31   -1.0    False
    244 2016-09-01 2016-09-01         1 2016-09-01    1.0     True
    245 2016-09-02 2016-09-02         1 2016-09-02    1.0     True
    246 2016-09-03 2016-09-03         1 2016-09-03    1.0     True
    247 2016-09-04 2016-09-04         1 2016-09-04    0.0    False
    248 2016-09-05 2016-09-05         1 2016-09-05    0.0    False
    249 2016-09-06 2016-09-06         1 2016-09-06    1.0     True

Note that the working period before the recess has ended mid-cycle: the administrator has checked out only two (Jul 12 and Jul 13) of five days forming a complete cycle. The period after the recess started afresh with three working days followed by two days off. This is the expected behavior as `Organizer` applies a next element of `structure` to the next span without knowledge of any previous invocations of this element.

However, if you wish to retain the flow of administator's schedule as if it was uninterrupted by the recess, you may employ :py:class:`.RememberingPattern`. This class creates a pattern which memorizes its state from previous invocations accross all organizers. It takes only one parameter - an iterable of labels.
::

    >>> work_cycle = tb.RememberingPattern([1,1,1,0,0])
    >>> year = tb.Marker(each='A', 
                         at=[{'months':6, 'days':13}, {'months':8}])
    >>> annually = tb.Organizer(marker=year, 
                                structure=[work_cycle,[-1]])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Jan 2016', end='31 Dec 2017',
                            layout=annually, 
                            default_selector=lambda x: x>0)

    >>> print(clnd(('07 Jul 2016','17 Jul 2016')))
    Interval((188, 198)): 'D' at 2016-07-07 -> 'D' at 2016-07-17 [11]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    188 2016-07-07 2016-07-07         1 2016-07-07    1.0     True
    189 2016-07-08 2016-07-08         1 2016-07-08    1.0     True
    190 2016-07-09 2016-07-09         1 2016-07-09    1.0     True
    191 2016-07-10 2016-07-10         1 2016-07-10    0.0    False
    192 2016-07-11 2016-07-11         1 2016-07-11    0.0    False
    193 2016-07-12 2016-07-12         1 2016-07-12    1.0     True
    194 2016-07-13 2016-07-13         1 2016-07-13    1.0     True
    195 2016-07-14 2016-07-14         1 2016-07-14   -1.0    False
    196 2016-07-15 2016-07-15         1 2016-07-15   -1.0    False
    197 2016-07-16 2016-07-16         1 2016-07-16   -1.0    False
    198 2016-07-17 2016-07-17         1 2016-07-17   -1.0    False

    >>> print(clnd(('27 Aug 2016','08 Sep 2016')))
    Interval((239, 251)): 'D' at 2016-08-27 -> 'D' at 2016-09-08 [13]

         workshift      start  duration        end  label  on_duty
    loc                                                           
    239 2016-08-27 2016-08-27         1 2016-08-27   -1.0    False
    240 2016-08-28 2016-08-28         1 2016-08-28   -1.0    False
    241 2016-08-29 2016-08-29         1 2016-08-29   -1.0    False
    242 2016-08-30 2016-08-30         1 2016-08-30   -1.0    False
    243 2016-08-31 2016-08-31         1 2016-08-31   -1.0    False
    244 2016-09-01 2016-09-01         1 2016-09-01    1.0     True
    245 2016-09-02 2016-09-02         1 2016-09-02    0.0    False
    246 2016-09-03 2016-09-03         1 2016-09-03    0.0    False
    247 2016-09-04 2016-09-04         1 2016-09-04    1.0     True
    248 2016-09-05 2016-09-05         1 2016-09-05    1.0     True
    249 2016-09-06 2016-09-06         1 2016-09-06    1.0     True
    250 2016-09-07 2016-09-07         1 2016-09-07    0.0    False
    251 2016-09-08 2016-09-08         1 2016-09-08    0.0    False

The period after the recess started with a shortened cycle consisting of one working day (Sep 1) followed by two days off (Sep 2 and 3). These days were "carried over" from the period before recess to complete the cycle started on the 12th of July. 


Compound Workshifts
===================

Call center's staff operate in shifts of variable length: 08:00 to 18:00 (10 hours), 18:00 to 02:00 (8 hours), and 02:00 to 08:00 (6 hours). An operator's schedule consists of one on duty shift followed by three off duty shifts.

.. note:: See :ref:`Compound Workshifts <compound-workshifts-section>` section in "Data Model" for the discussion about why and when you need compound workshifts.

Compound workshift is created from a span when a corresponding element of `structure` is neither a pattern nor an organizer. The value of such element is considered the label for the compound workshift. The workshift will cover all base units of the corresponding span. ::

    >>> day_parts = tb.Marker(each='D', 
                           at=[{'hours':2}, {'hours':8}, {'hours':18}])
    >>> shifts = tb.Organizer(marker=day_parts, structure=['A', 'B', 'C', 'D'])
    >>> clnd = tb.Timeboard(base_unit_freq='H', 
                            start='02 Oct 2017 08:00', end='07 Oct 2017 01:59',
                            layout=shifts, 
                            default_selector=lambda label: label=='A')

    >>>print(clnd)
    Timeboard of 'H': 2017-10-02 08:00 -> 2017-10-07 01:00

                  workshift ...  duration                 end  label  on_duty
    loc                     ...                                              
    0   2017-10-02 08:00:00 ...        10 2017-10-02 17:59:59      A     True
    1   2017-10-02 18:00:00 ...         8 2017-10-03 01:59:59      B    False
    2   2017-10-03 02:00:00 ...         6 2017-10-03 07:59:59      C    False
    3   2017-10-03 08:00:00 ...        10 2017-10-03 17:59:59      D    False
    4   2017-10-03 18:00:00 ...         8 2017-10-04 01:59:59      A     True
    5   2017-10-04 02:00:00 ...         6 2017-10-04 07:59:59      B    False
    6   2017-10-04 08:00:00 ...        10 2017-10-04 17:59:59      C    False
    7   2017-10-04 18:00:00 ...         8 2017-10-05 01:59:59      D    False
    8   2017-10-05 02:00:00 ...         6 2017-10-05 07:59:59      A     True
    9   2017-10-05 08:00:00 ...        10 2017-10-05 17:59:59      B    False
    10  2017-10-05 18:00:00 ...         8 2017-10-06 01:59:59      C    False
    11  2017-10-06 02:00:00 ...         6 2017-10-06 07:59:59      D    False
    12  2017-10-06 08:00:00 ...        10 2017-10-06 17:59:59      A     True
    13  2017-10-06 18:00:00 ...         8 2017-10-07 01:59:59      B    False

    # The "start" column has been omitted to fit the output to the page 


Caveats
=======

Not all `Marker` frequencies are valid
--------------------------------------

Currently `UnacceptablePeriodError` is raised for some combinations of base unit frequency and `Marker` frequency which may result in one base unit belonging to differen adjacent calendar periods marked by the `Marker`.

Base unit is not a subperiod
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Organizing fails when base unit is not a natural subperiod of the period used by `Marker`, for example::

    >>> org = tb.Organizer(marker='M', structure=[[1]])
    >>> clnd = tb.Timeboard(base_unit_freq='W',
                            start='01 Oct 2017', end='31 Dec 2017',
                            layout=org)
    ---------------------------------------------------------------------------
    UnacceptablePeriodError                    Traceback (most recent call last)
    ...
    UnacceptablePeriodError: Ambiguous organizing: W is not a subperiod of M

Indeed, a week may start in one month, and end in another, therefore it is not obvious to which span such a base unit should belong.

Actually, week is the only such irregular calendar frequency which is not a subperiod of anything. However it is unlikely that week-sized base units will be a common occurence in practice. 

Base unit of multiplied frequency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Organizinf fails when base unit has a multiplied frequency (i.e. ``'2H'``) **and** the period used by Marker is based on a **different** frequency.

This problem is less obvious and may manifest itself in some practical cases.

Consider first the legitimate code::

    >>> org = tb.Organizer(marker='W', structure=[[1]])
    >>> clnd = tb.Timeboard(base_unit_freq='D',
                            start='02 Oct 2017', end='15 Oct 2017',
                            layout=org)
    >>> print(clnd)
    Timeboard of 'D': 2017-10-02 -> 2017-10-15
    ...

Now change base unit frequency from ``'D'`` to ``'24H'``::

    >>> org = tb.Organizer(marker='W', structure=[[1]])
    >>> clnd = tb.Timeboard(base_unit_freq='24H',
                            start='02 Oct 2017', end='15 Oct 2017',
                            layout=org)
    ---------------------------------------------------------------------------
    UnacceptablePeriodError                    Traceback (most recent call last)
    ...
    UnacceptablePeriodError: Ambiguous organizing: 24H is not a subperiod of W

It failed for the following reason. A period of frequency ``'D'`` always starts at 00:00 of a calendar day and thus is guaranteed to be entirely within some week. A period of frequency ``'24H'`` is guaranteed to start at the beginning of some hour but this hour is not necessarily a midnight. For example, a ``'24H'`` period *may* start at 20:00 of a Sunday, therefore its first four hours will fall into one week, and the rest - into another.

Example of a real-life case impacted by this issue: workshifts beginning or ending at half past hour. As shown above, you cannot use ``'30T'`` (30 minutes) as a period for base units. You will have to work around by selecting ``'T'`` as the base unit frequency. The side-effects will be slower performance and consuming 30 times more memory.

While you may ensure that the base units start at midnights, timeboard  is not yet able to identify valid base unit alignments. This is a TODO.


Alignment of frame may be critical
----------------------------------

Let's go back to the example of the call center's timeboard with compound workshifts. This is it::

    >>> day_parts = tb.Marker(each='D', 
                              at=[{'hours':2}, {'hours':8}, {'hours':18}])
    >>> shifts = tb.Organizer(marker=day_parts, structure=['A', 'B', 'C', 'D'])
    >>> clnd = tb.Timeboard(base_unit_freq='H', 
                            start='02 Oct 2017 00:00', end='10 Oct 2017 01:59',
                            layout=shifts, 
                            default_selector=lambda label: label=='A')

Now suppose that this is a call center in Europe which supports traders doing business on stock exchanges around the world. Since markets are closed on Saturdays and Sundays, there is no need to staff the call center from 2:00 on Saturday (New York closes) to 2:00 on Monday (Tokyo opens). 

To adjust the timeboard to this specific schedule, we need to modify the timeline in such a way that it takes into acount the days of week. This job is carried out by marker `week` and organizer `weekly`. Moreover, we will need a :py:class:`.RememberingPattern` to ensure that the order of shifts is uninterrupted by weekends. ::


    >>> shifts_order = tb.RememberingPattern(['A', 'B', 'C', 'D'])
    >>> day_parts = tb.Marker(each='D', 
                              at=[{'hours':2}, {'hours':8}, {'hours':18}])
    >>> shifts = tb.Organizer(marker=day_parts, structure=shifts_order)
    >>> week = tb.Marker(each='W',
                         at=[{'days':0, 'hours':2}, {'days':5, 'hours':2}])
    >>> weekly = tb.Organizer(marker=week, structure=[0, shifts])
    >>> clnd = tb.Timeboard(base_unit_freq='H', 
                            start='02 Oct 2017 00:00', end='10 Oct 2017 01:59',
                            layout=weekly)
    >>> clnd.add_schedule(name='shift_A', selector=lambda label: label=='A')

    >>> print(clnd)
                  workshift ... dur.                 end label  on_duty shift_A
    loc                     ...                                                
    0   2017-10-02 00:00:00 ...    2 2017-10-02 01:59:59     0    False   False
    1   2017-10-02 02:00:00 ...    6 2017-10-02 07:59:59     A     True    True
    2   2017-10-02 08:00:00 ...   10 2017-10-02 17:59:59     B     True   False
    3   2017-10-02 18:00:00 ...    8 2017-10-03 01:59:59     C     True   False
    4   2017-10-03 02:00:00 ...    6 2017-10-03 07:59:59     D     True   False
    5   2017-10-03 08:00:00 ...   10 2017-10-03 17:59:59     A     True    True
    6   2017-10-03 18:00:00 ...    8 2017-10-04 01:59:59     B     True   False
    7   2017-10-04 02:00:00 ...    6 2017-10-04 07:59:59     C     True   False
    8   2017-10-04 08:00:00 ...   10 2017-10-04 17:59:59     D     True   False
    9   2017-10-04 18:00:00 ...    8 2017-10-05 01:59:59     A     True    True
    10  2017-10-05 02:00:00 ...    6 2017-10-05 07:59:59     B     True   False
    11  2017-10-05 08:00:00 ...   10 2017-10-05 17:59:59     C     True   False
    12  2017-10-05 18:00:00 ...    8 2017-10-06 01:59:59     D     True   False
    13  2017-10-06 02:00:00 ...    6 2017-10-06 07:59:59     A     True    True
    14  2017-10-06 08:00:00 ...   10 2017-10-06 17:59:59     B     True   False
    15  2017-10-06 18:00:00 ...    8 2017-10-07 01:59:59     C     True   False
    16  2017-10-07 02:00:00 ...   48 2017-10-09 01:59:59     0    False   False
    17  2017-10-09 02:00:00 ...    6 2017-10-09 07:59:59     D     True   False
    18  2017-10-09 08:00:00 ...   10 2017-10-09 17:59:59     A     True    True
    19  2017-10-09 18:00:00 ...    8 2017-10-10 01:59:59     B     True   False

    # The "start" column has been omitted and "duration" squeezed to fit 
    # the output to the page

Label ``0`` denotes the periods of time when the call center is closed: during first two hours of Monday 2 October, and from 02:00 on Saturday 7 October through 01:59 on Monday 9 October. We left the default schedule's selector and name unchanged. In this way, the default schedule shows the schedule of the call center as a whole. We also added a schedule for shift `A`. For the practical use you will want to add schedules for the other shifts but this is not the point of this example.

The first week ends on shift 'C', and the next week starts with shift 'D', so the order of shifts is preserved which is an essential requirement for this timeboard.

However, if the start of the timeboard is moved to 02:00 of Monday or any time afterwards, the result will be totally incorrect::

    >>> clnd = tb.Timeboard(base_unit_freq='H', 
                            start='02 Oct 2017 02:00', end='10 Oct 2017 01:59',
                            layout=weekly)
    >>> print(clnd)
                  workshift ... duration                 end label  on_duty
    loc                     ...                                            
    0   2017-10-02 20:00:00 ...      102 2017-10-07 01:59:59     0    False
    1   2017-10-07 02:00:00 ...        6 2017-10-07 07:59:59     C     True
    2   2017-10-07 08:00:00 ...       10 2017-10-07 17:59:59     D     True
    3   2017-10-07 18:00:00 ...        8 2017-10-08 01:59:59     A     True
    4   2017-10-08 02:00:00 ...        6 2017-10-08 07:59:59     B     True
    5   2017-10-08 08:00:00 ...       10 2017-10-08 17:59:59     C     True
    6   2017-10-08 18:00:00 ...        8 2017-10-09 01:59:59     D     True
    7   2017-10-09 02:00:00 ...       24 2017-10-10 01:59:59     0    False

What happened is the organizer having produced one span less than we expected when putting together the value of `structure`. We counted on the frame being aligned with a week. Thus the first element of structure, ``0``, should have been applied to the span covering the period up to 01:59 of Monday. However, when the start of the frame moved to 02:00, the sequence of spans produced by the organizer was displaced in relation to the sequence of elements in `structure`. Therefore, the elements of `structure` are now applied to inappropriate spans.

Workarounds:

- The most obvious solution is to swap elements of `structure`: ``structure=[shifts, 0]``. However this approach may render timeboard's configuration less comprehensible and more error-prone especialy when elements of structure are related to specific days of week or of months.

- The better approach is to align the start of the timeboard with boundaries of all calendar frequencies used in the timeboard's configuration. 

  For example, if the base unit is hour and ``'W'`` and ``'D'`` frequencies are used in organizers, start the timeboard at 00:00 Monday. If, instead ``'M'`` frequency is used, start the timeboard at 00:00 of the first day of a month. 

There is also another side effect to note. When we rebuilt the timeboard from 02:00 of Monday, you might have noticed that the pattern of labels in this *new* timeboard started on 'C', not on 'A'. This is because we continued to use the same layout that eventually references `RememberingPattern shifts_order` which has remembered where it stopped in the previous timeboard.

Specific days of month
----------------------

A recurrent meeting gathers on 10th, 20th and 30th day of month. 

The full-blown Marker-based approach is somewhat cumbersome and may produce unobvious errors, like this one which breaks after April 30::

    >>> days_of_month = tb.Marker(each='M', 
                                  at=[{'days':9}, {'days':10}, {'days':19},
                                      {'days':20}, {'days':29}, {'days':30} ])
    >>> monthly = tb.Organizer(marker=days_of_month, 
                               structure=[[0],[1],[0],[1],[0],[1]])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Jan 2017', end='31 Dec 2017',
                            layout=monthly)

A straightforward technique facilitated by use of numpy's `zeros` is the best::

    >>> import numpy as np
    >>> days = np.zeros(31)
    >>> days[[9,19,29]]=1
    >>> monthly = tb.Organizer(marker='M', 
                               structure=[days])
    >>> clnd = tb.Timeboard(base_unit_freq='D', 
                            start='01 Jan 2017', end='31 Dec 2017',
                            layout=monthly)
