***************
Release Notes
***************

timeboard 0.1
=============

**Release date:** February 01, 2018

This is the first release.


timeboard 0.2
=============

**Release date:** March 01, 2018

New features
------------

* :py:meth:`.Interval.overlap` (also ``*``) - return the interval that is the intersection of two intervals.

* :py:meth:`.Interval.what_portion_of` (also ``/``) - calculate what portion of the other interval this interval takes up.

* :py:meth:`.Interval.workshifts` - return a generator that yields workshifts with the specified duty from the interval.

* Work time calculation: :py:meth:`.Workshift.worktime`, :py:meth:`.Interval.worktime`

Miscellaneous
-------------

* Performance: building any practical timeboard should take a fraction of a second.

* Documentation: added :doc:`Common Use Cases <use_cases>` section. It is also available as a :download:`jupyter notebook <use_cases.ipynb>`.
