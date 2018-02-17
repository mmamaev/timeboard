*****************
Quick Start Guide
*****************

To get started you need to build a timeboard (calendar). The simplest way to do so is to use a preconfigured calendar which is shipped with the package. Let's take a regular business day calendar for the United States. 
::

    >>> import timeboard.calendars.US as US
    >>> clnd = US.Weekly8x5()


.. note:: If you need to build a custom calendar, for example, a schedule of shifts for a 24x7 call center, :doc:`Making a Timeboard <making_a_timeboard>` section of the documentation explains this topic in details. 

Once you have got a timeboard, you may perform queries and calculations over it.


**Is a certain date a business day?** 

Calling `clnd()` with a single point in time produces an object representing a unit of the calendar (in this case, a day) that contains this point in time. Object of this type is called *workshift*.
::

    >>> ws = clnd('27 May 2017')
    >>> ws.is_on_duty()
    False

Indeed, it was a Saturday. 


**When was the next business day?** 
::

    >>> ws.rollforward()
    Workshift(6359) of 'D' at 2017-05-30

This calendar unit (workshift) has the sequence number of 6359 and takes a day of 30 May 2017, which, by the way, was the Tuesday after the Memorial Day holiday.


**If we were to finish the project in 22 business days starting on 01 May 2017, when would be our deadline?** 
::

    >>> clnd('01 May 2017') + 22
    Workshift(6361) of 'D' at 2017-06-01


**How many business days were in a certain month?** 

Calling `clnd()` with two arguments produces an object representing an *interval* on the calendar.
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


**If an employee was on the staff from the 3rd to the 28th of April, 2017, how many business months did this person work in the company?** 

Calling `clnd()` with a tuple of two points in time also produces an *interval*.
::

    >>> clnd(('03 Apr 2017','28 Apr 2017')).count_periods('M')
    1.0

Indeed, the 1st, the 2nd, as well as the 29th and the 30th of April in 2017 fell on the weekends, therefore, having started on the 3rd and finished on the 28th, the employee checked out all the working days in the month.


**And if it were the same dates in May?** 
::

    >>> clnd(('03 May 2017','28 May 2017')).count_periods('M')
    0.8181818181818182

**If an employee was on the staff from 01 Jan 2016 to 15 Jul 2017, what portion of the year 2017 this person has spent in the company?**
::

    >>> tenure = clnd(('01 Jan 2016', '15 Jul 2017'))
    >>> y2017 = clnd('2017', period='A')
    >>> tenure.what_portion_of(y2017)
    0.5421686746987951

**And what portion of 2016?**
::

    >>> y2016 = clnd('2016', period='A')
    >>> tenure.what_portion_of(y2016)
    1.0

**In total, how many years this person has worked for the company?**
::

    >>> tenure.count_periods('A')
    1.5421686746987953


