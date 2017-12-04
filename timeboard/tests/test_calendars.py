from timeboard.calendars.calendarbase import (
    CalendarBase, nth_weekday_of_month, extend_weekends)
from timeboard.exceptions import OutOfBoundsError
from timeboard.core import get_period, get_timestamp
from pandas import Timedelta
import timeboard.calendars.RU as RU
import timeboard.calendars.US as US

import datetime
import pytest

class TestCalendarBase(object):
    def test_calendar_base(self):
        assert CalendarBase.amendments() == {}
        start = CalendarBase.parameters()['start']
        end = CalendarBase.parameters()['end']
        freq = CalendarBase.parameters()['base_unit_freq']
        clnd = CalendarBase()
        assert clnd.start_time == get_period(start, freq=freq).start_time
        assert clnd.end_time == get_period(end, freq=freq).end_time
        delta = end - start
        assert clnd.get_interval().count() == delta.components.days + 1

    def test_calendar_base_custom_limits(self):
        clnd = CalendarBase(custom_start='01 Jan 2017',
                            custom_end='31 Dec 2018')
        assert clnd.get_interval().count() == 365*2

    def test_calendar_base_custom_amds(self):
        clnd = CalendarBase(custom_start='01 Jan 2017',
                            custom_end='31 Dec 2018',
                            custom_amendments={
                                '01 Mar 2017': 0,
                                '01 Mar 2019': 0}
                            )
        assert clnd.get_interval().count() == 365 * 2 - 1

    def test_calendat_base_OOB(self):
        start = CalendarBase.parameters()['start']
        end = CalendarBase.parameters()['end']
        with pytest.raises(OutOfBoundsError):
            CalendarBase(start-Timedelta(days=1))
        with pytest.raises(OutOfBoundsError):
            CalendarBase(custom_end=end+Timedelta(days=1))

class TestCalendarUtils(object):

    def test_nth_weekday_positive(self):
        date_tuples_2017={
            (12, 5, 1): get_timestamp('01 Dec 2017'),
            (12, 7, 1): get_timestamp('03 Dec 2017'),
            (12, 3, 1): get_timestamp('06 Dec 2017'),
            (12, 3, 4): get_timestamp('27 Dec 2017'),
            (12, 3, 5): None,
            (12, 5, 5): get_timestamp('29 Dec 2017'),
            (12, 7, 5): get_timestamp('31 Dec 2017'),
            (5, 1, 1):  get_timestamp('01 May 2017'),
            (5, 1, 5):  get_timestamp('29 May 2017'),
        }
        result = nth_weekday_of_month(2017, date_tuples_2017.keys(), label=5)
        valid_dates = filter(lambda x: x is not None, date_tuples_2017.values())
        assert sorted(result.keys()) == sorted(valid_dates)
        assert result.values().count(5) == len(result)

    def test_nth_weekday_negative(self):

        date_tuples_2017 = {
            (12, 3, -1): get_timestamp('27 Dec 2017'),
            (12, 3, -4): get_timestamp('06 Dec 2017'),
            (12, 3, -5): None,
            (12, 5, -1): get_timestamp('29 Dec 2017'),
            (12, 7, -1): get_timestamp('31 Dec 2017'),
            (5, 1, -1):  get_timestamp('29 May 2017'),
            (5, 1, -5):  get_timestamp('01 May 2017'),
        }
        result = nth_weekday_of_month(2017, date_tuples_2017.keys(), label=5)
        valid_dates = filter(lambda x: x is not None, date_tuples_2017.values())
        assert sorted(result.keys()) == sorted(valid_dates)
        assert result.values().count(5) == len(result)

    def test_nth_weekday_shift(self):
        date_tuples_2017={
            (12, 5, 1, 0): get_timestamp('01 Dec 2017'),
            (12, 5, 1, 2): get_timestamp('03 Dec 2017'),
            (12, 5, 1, -2): get_timestamp('29 Nov 2017')
        }
        result = nth_weekday_of_month(2017, date_tuples_2017.keys())
        valid_dates = filter(lambda x: x is not None, date_tuples_2017.values())
        assert sorted(result.keys()) == sorted(valid_dates)
        assert result.values().count(0) == len(result)

    def test_nth_weekday_bad_n(self):
        with pytest.raises(OutOfBoundsError):
            nth_weekday_of_month(2017, [(12, 3, 5)], errors='raise')
        with pytest.raises(OutOfBoundsError):
            nth_weekday_of_month(2017, [(12, 3, -5)], errors='raise')
        with pytest.raises(AssertionError):
            nth_weekday_of_month(2017, [(5, 1, -6)])
        with pytest.raises(AssertionError):
            nth_weekday_of_month(2017, [(5, 1, 6)])
        with pytest.raises(AssertionError):
            nth_weekday_of_month(2017, [(5, 1, 0)])

    def test_extend_weekend_saturday(self):
        amds = {'16 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5}
        result = extend_weekends(amds, add='previous')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5}
        result = extend_weekends(amds, add='next')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}

    def test_extend_weekend_sunday(self):
        amds = {'17 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}
        result = extend_weekends(amds, add='previous')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5}
        result = extend_weekends(amds, add='next')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}

    def test_extend_weekend_new_label(self):
        amds = {'17 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest', label='a')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 'a'}

    def test_extend_weekend_weekday(self):
        amds = {'15 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest')
        assert result == {get_timestamp('15 Dec 2017'): 5}

    def test_extend_weekend_two_holidays_same_labels(self):
        amds = {'16 Dec 2017': 5, '17 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest')
        assert result == {get_timestamp('15 Dec 2017'): 5,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}
        result = extend_weekends(amds, add='previous')
        assert result == {get_timestamp('15 Dec 2017'): 5,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          }
        result = extend_weekends(amds, add='next')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}

    def test_extend_weekend_two_holidays_new_label(self):
        amds = {'16 Dec 2017': 5, '17 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest', label=0)
        assert result == {get_timestamp('15 Dec 2017'): 0,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 0}
        result = extend_weekends(amds, add='previous', label=0)
        assert result == {get_timestamp('15 Dec 2017'): 0,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          }
        result = extend_weekends(amds, add='next', label=0)
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 0}

    def test_extend_weekend_two_holidays_diff_labels(self):
        amds = {'16 Dec 2017': 3, '17 Dec 2017': 5}
        result = extend_weekends(amds, add='nearest')
        assert result == {get_timestamp('15 Dec 2017'): 3,
                          get_timestamp('16 Dec 2017'): 3,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}
        with pytest.raises(ValueError):
            result = extend_weekends(amds, add='previous')
        with pytest.raises(ValueError):
            result = extend_weekends(amds, add='next')


class TestCalendarsRU(object):

    def test_calendar_RU_week8x5(self):

        start = RU.Week8x5.parameters()['start']
        end = RU.Week8x5.parameters()['end']
        freq = RU.Week8x5.parameters()['base_unit_freq']
        clnd = RU.Week8x5()
        assert clnd.start_time == get_period(start, freq=freq).start_time
        assert clnd.end_time == get_period(end, freq=freq).end_time

        bdays_in_year = {
            2005: 248, 2006: 248, 2007: 249,
            2008: 250, 2009: 249, 2010: 249, 2011: 248, 2012: 249, 2013: 247,
            2014: 247, 2015: 247, 2016: 247, 2017: 247, 2018: 247
        }
        for year, bdays in bdays_in_year.iteritems():
            assert clnd.get_interval('01 Jan {}'.format(year),
                                     period='A').count() == bdays

        # a regular week
        for day in range(21, 25):
            ws = clnd("{} Nov 2017".format(day))
            assert ws.is_on_duty
            assert ws.label == 8
        for day in range(25, 27):
            ws = clnd("{} Nov 2017".format(day))
            assert ws.is_off_duty
            assert ws.label == 0

        # standard holidays
        assert clnd('01 Jan 2008').is_off_duty
        assert clnd('23 Feb 2017').is_off_duty
        # week day made a day off
        assert clnd('24 Feb 2017').is_off_duty
        # weekend made a working day
        assert clnd('05 May 2012').is_on_duty
        # by default 31 Dec is a working day if not a weekend
        assert clnd('31 Dec 2015').is_on_duty
        # by default a holiday eve has shorter hours
        assert clnd('22 Feb 2017').label == 7

    def test_calendar_RU_week8x5_31dec_off(self):
        clnd = RU.Week8x5(work_on_dec31=False)
        for y in range(2008,2019):
            assert clnd("31 Dec {}".format(y)).is_off_duty

    def test_calendar_RU_week8x5_no_short_eves(self):
        clnd = RU.Week8x5(short_eves=False)
        assert clnd('22 Feb 2017').label == 8

    def test_calendar_RU_week8x5_custom_amds(self):
        clnd = RU.Week8x5(custom_amendments={'22 Feb 2017 00:00': 0,
                                             '23.02.2017': 8})
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_off_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_off_duty
        assert clnd('01 May 2017').is_off_duty

    def test_calendar_RU_week8x5_custom_amds_ambiguous(self):
        # We already have timestamps of 22.02.17 00:00:00 and 23.02.17 00:00:00
        # in amendments dict which is to be update by custom amds.
        # Applying the custom amds below would result in ambiguous keys (two
        # keys referring to the same day) but we preprocess custom_amedndments
        # to align them at the start_time of days in the same manner as
        # in amendments dict
        clnd = RU.Week8x5(custom_amendments={'22 Feb 2017 13:00': 0,
                                             '23 Feb 2017 15:00': 8})
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_off_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_off_duty
        assert clnd('01 May 2017').is_off_duty


    def test_calendar_RU_week8x5_only_custom_amds(self):
        clnd = RU.Week8x5(only_custom_amendments=True,
                          custom_amendments={'22 Feb 2017': 0,
                                             '23 Feb 2017': 8})
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_off_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_on_duty
        assert clnd('01 May 2017').is_on_duty


    def test_calendar_RU_week8x5_no_amds(self):
        clnd = RU.Week8x5(do_not_amend=True,
                          only_custom_amendments=True,
                          custom_amendments={'22 Feb 2017': 0,
                                             '23 Feb 2017': 8}
                          )
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_on_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_on_duty
        assert clnd('01 May 2017').is_on_duty

    def test_calendar_RU_week8x5_select_years(self):

        clnd = RU.Week8x5('01 Jan 2010','31 Dec 2015')
        assert clnd.start_time == datetime.datetime(2010, 01, 01, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2015, 12, 31, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2016, 01, 01, 0, 0, 0)
        # if only year is given, the 1st of Jan is implied at the both ends
        clnd = RU.Week8x5('2010','2015')
        assert clnd.start_time == datetime.datetime(2010, 01, 01, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2015, 01, 01, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2015, 01, 02, 0, 0, 0)

    def test_calendar_RU_week8x5_OOB(self):
        with pytest.raises(OutOfBoundsError):
            RU.Week8x5('1990')
        with pytest.raises(OutOfBoundsError):
            RU.Week8x5('2008', '31 Dec 2019')

class TestCalendarsUS(object):

    def test_calendar_US_week8x5(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd0 = US.Week8x5(do_not_amend=True)
        assert all([clnd0(d).is_on_duty for d in holidays_2011])
        clnd1 = US.Week8x5()
        assert all([clnd1(d).is_off_duty for d in holidays_2011])
        assert clnd0.get_interval('2011', period='A').count() == (
               clnd1.get_interval('2011', period='A').count() +
               len(holidays_2011) - 1)

    def test_calendar_US_week8x5_exclusions(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd = US.Week8x5(exclusions=['independence','christmas',
                                      'black_friday'])
        assert clnd('04 Jul 2011').is_on_duty
        assert clnd('25 Nov 2011').is_on_duty
        assert clnd('25 Dec 2011').is_off_duty
        assert clnd('26 Dec 2011').is_on_duty

    def test_calendar_US_week8x5_short_weekends(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd = US.Week8x5(long_weekends=False)
        assert clnd('30 Dec 2010').is_on_duty
        assert clnd('04 Jul 2011').is_off_duty
        assert clnd('25 Dec 2011').is_off_duty
        assert clnd('26 Dec 2011').is_on_duty

    def test_calendar_US_week8x5_shortened(self):
        holidays_2011_shortened = [
                           '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011'
        ]
        clnd0 = US.Week8x5('01 Jan 2011', '30 Nov 2011', do_not_amend=True)
        assert all([clnd0(d).is_on_duty for d in holidays_2011_shortened])
        clnd1 = US.Week8x5('01 Jan 2011', '30 Nov 2011')
        assert all([clnd1(d).is_off_duty for d in holidays_2011_shortened])
        assert clnd0.get_interval().count() == (
               clnd1.get_interval().count() + len(holidays_2011_shortened))


    def test_calendar_US_week8x5_custom_amds(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd = US.Week8x5(custom_amendments={'18 Jan 2011': 0,
                                             '26 Dec 2011': 8})

        assert clnd('18 Jan 2011').is_off_duty
        assert clnd('04 Jul 2011').is_off_duty
        assert clnd('25 Dec 2011').is_off_duty
        assert clnd('26 Dec 2011').is_on_duty






