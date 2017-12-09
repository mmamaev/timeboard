timeboard - business calendar calculations
==========================================

timeboard package builds business calendars / workshift schedules and performs calculations over them.

This package allows you to answer questions like: if we have 20 working days to complete the project, when will be the deadline? Or a bit more complex one: if a mechanic's workshifts were Mon, Tue, Sat, Sun on odd weeks, Wed, Thu, Fri on even weeks and this person worked from November 15 do December 22, how many month's salaries the dealership must pay them? 

Based on pandas timeseries library, timeboard gives more flexibility than pandas's built-in business calendars:
- you can build sophisticated timeboards by slicing and dicing your calendar's span in various ways not limiting yourself to a weekly pattern of days; the base unit of your calendar may be anything from seconds to years.
- a regular calendar pattern can be amended not only by turning a business day into a day off (a holiday) but also vice versa - turning a would-be day off
into a business day (by the way, a common practice in Russia).

Quick Examples
--------------

>>> import timeboard as tb

Firstly, you need to construct a timeboard (calendar). 

Kind of a teaser, before we look at the actual quick examples, remember the mechanic in the dealership from the question above? His workshift schedule for 2017 (assuming he does not take vacations) will be:

>>> biweekly = tb.Organizer(split_by='W', structure=[[1, 1, 0, 0, 0, 1, 1],
                                                     [0, 0, 1, 1, 1, 0, 0]])
>>> clnd = tb.Timeboard(base_unit_freq='D', 
                        start='01 Jan 2017', end='31 Dec 2017', 
                        layout=biweekly)

And the answer to the question is:

>>> clnd(('15 Nov 2017','22 Dec 2017')).count_periods('M')
1.25

Yet the simplest way to obtain a calendar is to use a pre-built one which is shipped with the package. Let's take a regular business day calendar for the United States. 

>>> import timeboard.calendars.US as US
>>> clnd = US.Weekly8x5()

Having got the calendar, you may perform queries and calculations over it.

Is a certain date a business day?

>>> ws = clnd('27 May 2017')
>>> ws.is_on_duty
False

Indeed, it was a Saturday. When was the next business day?

>>> print(ws.rollforward())
Workshift 'D' at 2017-05-30

It tells us that our calendar's unit (workshift) is 'D' (day) and the next 'on duty' workshift is 30 May 2017, which, by the way, was the Tuesday after the Memorial Day holiday.

How many business days were in a certain month?

>>> clnd('May 2017', period='M').count()
22

How many days off?
>>> clnd('May 2017', period='M').count(duty='off')
9

If we were to finish the project in 22 business days starting on 01 May 2017, when would be our deadline?

>>> print (clnd('01 May 2017') + 22)
Workshift 'D' at 2017-06-01

What was the first business day in 2017?

>>> print(clnd('2017', period='A').first())
Workshift 'D' at 2017-01-03

If an employee was on staff from the 3rd to the 28th of April, 2017, how many business months did this person work in the company?

>>> clnd(('03 Apr 2017','28 Apr 2017')).count_periods('M')
1.0

Indeed, the 1st, the 2nd, as well as the 29th and the 30th of April in 2017 fell on the weekends, therefore, having started on the 3rd and finished on the 28th, the employee checked out all the working days in the month.

And if it were the same dates in May?

>>> clnd(('03 May 2017','28 May 2017')).count_periods('M')
0.8181818181818182






