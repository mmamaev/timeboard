********************************************
`timeboard` - business calendar calculations
********************************************

:py:mod:`timeboard` is is a library that builds calendars of business days and schedules of work shifts and performs calculations over them.

:py:mod:`timeboard` facilitates answering calendar-related questions. For example: 

- If we have 20 business days to complete the project, when will be the deadline? 

- If a person was employed from November 15 do December 22, how many month's salaries the company owes them?

- A 24x7 call center operates in shifts of varying length. An operator comes in on every forth shift. How many hours has the operator worked in a specific month?

Based on pandas timeseries library, :py:mod:`timeboard` gives more flexibility than pandas's built-in business calendars limited to a weekly pattern of days. The key features of :py:mod:`timeboard` are:

    - Workshifts of any duration from seconds to years.
    - Tools to build sophisticated schedules which can combine periodical patterns, seasonal variations, stop-and-resume behavior, etc.
    - Built-in standard business day calendars for USA, UK, and Russia.


Installation
============
::

    pip install timeboard

:py:mod:`timeboard` is tested with Python versions 2.7 and 3.6.

The import statement to run all the examples is::
    
    >>> import timeboard as tb


Documentation
=============

http://timeboard.readthedocs.io/


Quick Start Guide
=================


Firstly, you need to construct a timeboard (calendar). The simplest way to do it is to use a preconfigured calendar which is shipped with the package. Let's take a regular business day calendar for the United States. ::

    >>> import timeboard.calendars.US as US
    >>> clnd = US.Weekly8x5()

Now you may perform queries and calculations over your timeboard.

**Is a certain date a business day?** ::

    >>> ws = clnd('27 May 2017')
    >>> ws.is_on_duty()
    False

Indeed, it was a Saturday. 

**When was the next business day?** ::

    >>> ws.rollforward()
    Workshift(6359) of 'D' at 2017-05-30

It tells us that this calendar's unit (workshift) has the sequence number of 6359 and covers a period of 'D' (day) on 30 May 2017, which, by the way, was the Tuesday after the Memorial Day holiday.

**How many business days were in a certain month?** ::

    >>> clnd('May 2017', period='M').count()
    22

**How many days off?** ::

    >>> clnd('May 2017', period='M').count(duty='off')
    9

**If we were to finish the project in 22 business days starting on 01 May 2017, when would be our deadline?** ::

    >>> clnd('01 May 2017') + 22
    Workshift(6361) of 'D' at 2017-06-01

**When was the first business day in 2017?** ::

    >>> clnd('2017', period='A').first()
    Workshift(6212) of 'D' at 2017-01-03

**If an employee was on staff from the 3rd to the 28th of April, 2017, how many business months did this person work in the company?** ::

    >>> clnd(('03 Apr 2017','28 Apr 2017')).count_periods('M')
    1.0

Indeed, the 1st, the 2nd, as well as the 29th and the 30th of April in 2017 fell on the weekends, therefore, having started on the 3rd and finished on the 28th, the employee checked out all the working days in the month.

**And if it were the same dates in May?** ::

    >>> clnd(('03 May 2017','28 May 2017')).count_periods('M')
    0.8181818181818182



License
=======

::

    3-Clause BSD License

    Copyright (c) 2018, Maxim Mamaev
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from this
    software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
    IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
    THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
    PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.








