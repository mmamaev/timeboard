*****************
Quick Start Guide
*****************

Set up a timeboard
------------------

To get started you need to build a timeboard (calendar). The simplest way to do so is to use a preconfigured calendar which is shipped with the package. Let's take a regular business day calendar for the United States. 
::

    >>> import timeboard.calendars.US as US
    >>> clnd = US.Weekly8x5()


.. note:: If you need to build a custom calendar, for example, a schedule of shifts for a 24x7 call center, :doc:`Making a Timeboard <making_a_timeboard>` section of the documentation explains this topic in details. 

Once you have got a timeboard, you may perform queries and calculations over it.


Play with workshifts
--------------------

Calling a timeboard instance `clnd` with a single point in time produces an object representing a unit of the calendar (in this case, a day) that contains this point in time. Object of this type is called *workshift*.

**Is a certain date a business day?** 
::

    >>> ws = clnd('27 May 2017')
    >>> ws.is_on_duty()
    False

Indeed, it was a Saturday. 


**When was the next business day?** 
::

    >>> ws.rollforward()
    Workshift(6359) of 'D' at 2017-05-30

The returned calendar unit (workshift) has the sequence number of 6359 and represents the day of 30 May 2017, which, by the way, was the Tuesday after the Memorial Day holiday.


**If we were to finish the project in 22 business days starting on 01 May 2017, when would be our deadline?** 
::

    >>> clnd('01 May 2017') + 22
    Workshift(6361) of 'D' at 2017-06-01

This is the same as:
::

    >>> clnd('01 May 2017').rollforward(22)
    Workshift(6361) of 'D' at 2017-06-01


Play with intervals
-------------------

Calling ``clnd()`` with a different set of parameters produces an object representing an *interval* on the calendar. The interval below contains all workshifts of the months of May 2017.

**How many business days were there in a certain month?** 
::

    >>> may2017 = clnd('May 2017', period='M')
    >>> may2017.count()
    22


**How many days off?** 
::

    >>> may2017.count(duty='off')
    9


**How many working hours?**
::

    >>> may2017.worktime()
    176.0


An employee was on the staff from April 3, 2017 to May 15, 2017. **What portion of April's salary did the company owe them?** 

Calling ``clnd()`` with a tuple of two points in time produces an interval containing all workshifts between these points, inclusively.
::

    >>> time_in_company = clnd(('03 Apr 2017','15 May 2017'))
    >>> time_in_company.what_portion_of(clnd('Apr 2017', period='M'))
    1.0

Indeed, the 1st and the 2nd of April in 2017 fell on the weekend, therefore, having started on the 3rd, the employee checked out all the working days in the month.

**And what portion of May's?** 
::

    >>> time_in_company.what_portion_of(may2017)
    0.5

**How many days had the employee worked in May?**

The multiplication operator returns the intersection of two intervals.
::

    >>> (time_in_company * may2017).count()
    11

**How many hours?**
::

    >>> (time_in_company * may2017).worktime()
    88


An employee was on the staff from 01 Jan 2016 to 15 Jul 2017. **How many years this person had worked for the company?**
::

    >>> clnd(('01 Jan 2016', '15 Jul 2017')).count_periods('A')
    1.5421686746987953


