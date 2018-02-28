.. image:: https://timeboard.readthedocs.io/en/latest/_static/timeboard_logo.png
   :align: center
   :alt: timeboard logo

.. image:: https://img.shields.io/travis/mmamaev/timeboard.svg
   :alt: travis build status
   :target: https://travis-ci.org/mmamaev/timeboard

.. image:: https://img.shields.io/readthedocs/timeboard.svg
   :alt: readthedocs build status
   :target: https://timeboard.readthedocs.io/

*********************************************
timeboard - business calendar calculations
*********************************************

`timeboard` creates schedules of work periods and performs calendar calculations over them. You can build standard business day calendars as well as a variety of other schedules, simple or complex.

.. pypi-start

Examples of problems solved by `timeboard`: 

    - If we have 20 business days to complete the project when will be the deadline? 

    - If a person was employed from November 15 to December 22 and salary is paid monthly, how many month's salaries has the employee earned?

    - The above-mentioned person was scheduled to work Mondays, Tuesdays, Saturdays, and Sundays on odd weeks, and Wednesdays, Thursdays, and Fridays on even weeks. The question is the same.

    - A 24x7 call center operates in shifts of varying length starting at 02:00, 08:00, and 18:00. An operator comes in on every fourth shift and is paid per shift. How many shifts has the operator sat in a specific month?

    - With employees entering and leaving a company throughout a year, what was the average annual headcount?

Based on pandas timeseries library, `timeboard` gives more flexibility than pandas's built-in business calendars. The key features of `timeboard` are:

- You can choose any time frequencies (days, hours, multiple-hour shifts, etc.) as work periods.

- You can create sophisticated schedules which can combine periodical patterns, seasonal variations, stop-and-resume behavior, etc.

- There are built-in standard business day calendars (in this version: for USA, UK, and Russia).


Installation
============

::

    pip install timeboard

`timeboard` is tested with Python versions 2.7 and 3.6.

Dependencies:

- pandas >= 0.22
- numpy >= 1.13
- dateutil >= 2.6.1
- six >= 1.11

The import statement to run all the examples:
::

    >>> import timeboard as tb


Quick Start Guide
=================

Set up a timeboard
------------------

To get started you need to build a timeboard (calendar). The simplest way to do so is to use a preconfigured calendar which is shipped with the package. Let's take a regular business day calendar for the United States. 
::

    >>> import timeboard.calendars.US as US
    >>> clnd = US.Weekly8x5()


.. note:: If you need to build a custom calendar, for example, a schedule of shifts for a 24x7 call center, `Making a Timeboard <https://timeboard.readthedocs.io/en/latest/making_a_timeboard.html>`_ section of the documentation explains this topic in details. 

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

**How many business days were in a certain month?** 
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


**If an employee was on the staff from April 3, 2017 to May 15, 2017, what portion of April did they spend with the company?** 

Calling ``clnd()`` with a tuple of two points in time produces an interval containing all workshifts between these points, inclusively.
::

    >>> time_in_company = clnd(('03 Apr 2017','15 May 2017'))
    >>> time_in_company.what_portion_of(clnd('Apr 2017', period='M'))
    1.0

Indeed, the 1st and the 2nd of April in 2017 fell on the weekend, therefore, having started on the 3rd, the employee checked out all the working days in the month.

**And what portion of May?** 
::

    >>> time_in_company.what_portion_of(may2017)
    0.5

**How many days has the employee worked in May?**

The multiplication operator returns the intersection of two intervals.
::

    >>> (time_in_company * may2017).count()
    11

**How many hours?**
::

    >>> (time_in_company * may2017).worktime()
    88


**If an employee was on the staff from 01 Jan 2016 to 15 Jul 2017, how many years this person has worked for the company?**
::

    >>> clnd(('01 Jan 2016', '15 Jul 2017')).count_periods('A')
    1.5421686746987953


Links
=====

**Documentation:** https://timeboard.readthedocs.io/

**GitHub:** https://github.com/mmamaev/timeboard

**PyPI:** https://pypi.python.org/pypi/timeboard


.. pypi-end

License
=======

`BSD 3 Clause <LICENSE.txt>`_
