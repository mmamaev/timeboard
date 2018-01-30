*****************************
Using Preconfigured Calendars
*****************************

There are a few preconfigured Timeboards that come with the package. They implement common business day calendars of different countries.

To access calendars of a country you have to import the country module from  :py:mod:`timeboard.calendars`, for example::

    >>> import timeboard.calendars.US as US

Then, to obtain a Timeboard implementing a required calendar, call the class for this calendar from the chosen module. Usually the class takes some country-specific parameters that allow to tune the calendar. For example::

    >>> clnd = US.Weekly8x5(do_not_observe = {'black_friday'})

:py:meth:`parameters` class method returns the dictionary of the parameters used to instantiate the Timeboard. Of these, the most usable are probably parameters `start` and `end` which limit the maximum supported span of the calendar::

    >>> params = US.Weekly8x5.parameters()
    >>> params['start']
    Timestamp('2000-01-01 00:00:00')
    >>> params['end']
    Timestamp('2020-12-31 23:59:59')

The currently available calendars are listed below. Consult the reference page of the calendar class to review its parameters and examples.

=============== ====== =========== ===========================================
Country         Module Calendar    Description
=============== ====== =========== ===========================================
Russia          RU     |RU-W8x5|   Official calendar for 5 days x 8 hours
                                   working week with holiday observations

United Kingdom  UK     |UK-W8x5|   Business calendar for 5 days x 8 hours
                                   working week with bank holidays

United States   US     |US-W8x5|   Business calendar for 5 days x 8 hours
                                   working week with federal holidays
=============== ====== =========== ===========================================

.. |RU-W8x5| replace:: :py:class:`~timeboard.calendars.RU.Weekly8x5`

.. |UK-W8x5| replace:: :py:class:`~timeboard.calendars.UK.Weekly8x5`

.. |US-W8x5| replace:: :py:class:`~timeboard.calendars.US.Weekly8x5`
