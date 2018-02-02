***************
About timeboard
***************

:py:mod:`timeboard` performs calendar calculations over business schedules such as business days or work shifts.

Examples of problems solved by :py:mod:`timeboard`: 

- If we have 20 business days to complete the project, when will be the deadline? 

- If a person was employed from November 15 do December 22, how many month's salaries the company owes them?

- A 24x7 call center operates in shifts of varying length. An operator comes in on every forth shift. How many hours has the operator worked in a specific month?

Based on pandas timeseries library, :py:mod:`timeboard` gives more flexibility than pandas's built-in business calendars limited to a weekly pattern of days. The key features of :py:mod:`timeboard` are:

    - Workshifts of any duration from seconds to years.
    - Tools to build sophisticated schedules which can combine periodical patterns, seasonal variations, stop-and-resume behavior, etc.
    - Built-in standard business day calendars for USA, UK, and Russia.


Developer
---------

:py:mod:`timeboard` is authored and maintained by Maxim Mamaev.


License
-------

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

Attribution
-----------

Logo design by Olga Mamaeva.

Icon 'Worker' made by Freepik from www.flaticon.com is used as an element of the logo.
