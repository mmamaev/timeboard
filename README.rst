.. image:: https://timeboard.readthedocs.io/en/latest/_static/timeboard_logo.png
   :align: center
   :alt: timeboard logo

.. image:: https://img.shields.io/travis/mmamaev/timeboard.svg
   :align: center
   :alt: travis build status
   :target: https://travis-ci.org/mmamaev/timeboard


*********************************************
timeboard - business calendar calculations
*********************************************

`timeboard` performs calendar calculations over business schedules such as business days or work shifts.

.. pypi-start

Examples of problems solved by `timeboard`: 

    - If we have 20 business days to complete the project, when will be the deadline? 

    - If a person was employed from November 15 to December 22, how many month's salaries the company owes them?

    - A 24x7 call center operates in shifts of varying length starting at 02:00, 08:00, and 18:00. An operator comes in on every fourth shift. How many hours has the operator worked in a specific month?

Based on pandas timeseries library, `timeboard` gives more flexibility than pandas's built-in business calendars. The key features of `timeboard` are:

- Support of any time periods as elements of a calendar such as days, hours, multiple-hour shifts, etc.

- Tools to build sophisticated schedules which can combine periodical patterns, seasonal variations, stop-and-resume behavior, etc.

- Built-in standard business day calendars (in this version: for USA, UK, and Russia).


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


Firstly, you need to build a timeboard (calendar). The simplest way to do it is to use a preconfigured calendar which is shipped with the package. Let's take a regular business day calendar for the United States. 
::

    >>> import timeboard.calendars.US as US
    >>> clnd = US.Weekly8x5()

Now you may perform queries and calculations over your timeboard.


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

It tells us that this calendar's unit (workshift) has the sequence number of 6359 and covers a period of 'D' (day) on 30 May 2017, which, by the way, was the Tuesday after the Memorial Day holiday.


**If we were to finish the project in 22 business days starting on 01 May 2017, when would be our deadline?** 
::

    >>> clnd('01 May 2017') + 22
    Workshift(6361) of 'D' at 2017-06-01


**When was the first business day in 2017?** 
::

    >>> clnd('2017', period='A').first()
    Workshift(6212) of 'D' at 2017-01-03


**How many business days were in a certain month?** 
::

    >>> clnd('May 2017', period='M').count()
    22


**How many days off?** 
::

    >>> clnd('May 2017', period='M').count(duty='off')
    9


**How many working hours?**
::

    >>> clnd('May 2017', period='M').sum()
    176.0


**If an employee was on staff from the 3rd to the 28th of April, 2017, how many business months did this person work in the company?** 
::

    >>> clnd(('03 Apr 2017','28 Apr 2017')).count_periods('M')
    1.0

Indeed, the 1st, the 2nd, as well as the 29th and the 30th of April in 2017 fell on the weekends, therefore, having started on the 3rd and finished on the 28th, the employee checked out all the working days in the month.


**And if it were the same dates in May?** 
::

    >>> clnd(('03 May 2017','28 May 2017')).count_periods('M')
    0.8181818181818182


Links
=====

**Documentation:** https://timeboard.readthedocs.io/

**GitHub:** https://github.com/mmamaev/timeboard

**PyPI:** https://pypi.python.org/pypi/timeboard


.. pypi-end

License
=======

`BSD 3 Clause <LICENSE.txt>`_
