:orphan:

*****************
`Timeboard` class
*****************

.. autoclass:: timeboard.Timeboard
   :members: 


.. index::
   single: _Schedule (class in timeboard.core)

.. class:: timeboard.core_Schedule
    :noindex:

    Duty schedule of workshifts. 

    :py:meth:`._Schedule` constructor is not supposed to be called directly.

    Default schedule for a timeboard is generated automatically. To add another schedule call :py:meth:`.Timeboard.add_schedule`. To remove a schedule from the timeboard call :py:meth:`.Timeboard.drop_schedule`.

    Users identify schedules by name. To find out the name of a schedule inspect attribute :py:attr:`._Schedule.name`. To obtain a schedule by name look it up in :py:attr:`Timeboard.schedules` dictionary.