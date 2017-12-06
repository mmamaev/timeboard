from timeboard.calendars.calendarbase import (
    CalendarBase, nth_weekday_of_month, extend_weekends, from_easter)
from timeboard.exceptions import OutOfBoundsError
from timeboard.core import get_period, get_timestamp
from pandas import Timedelta
import pytest


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
        result = extend_weekends(amds, how='nearest')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5}
        result = extend_weekends(amds, how='previous')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5}
        result = extend_weekends(amds, how='next')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}

    def test_extend_weekend_sunday(self):
        amds = {'17 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}
        result = extend_weekends(amds, how='previous')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5}
        result = extend_weekends(amds, how='next')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}

    def test_extend_weekend_new_label(self):
        amds = {'17 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest', label='a')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 'a'}

    def test_extend_weekend_weekday(self):
        amds = {'15 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest')
        assert result == {get_timestamp('15 Dec 2017'): 5}

    def test_extend_weekend_weekday_already_off1(self):
        amds = {'17 Dec 2017': 5, '18 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest')
        assert result == {get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5,
                          get_timestamp('19 Dec 2017'): 5
                          }

    def test_extend_weekend_weekday_already_off2(self):
        amds = {'17 Dec 2017': 5, '15 Dec 2017': 5}
        result = extend_weekends(amds, how='previous')
        assert result == {get_timestamp('14 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5
                          }

    def test_extend_weekend_two_holidays_same_labels(self):
        amds = {'16 Dec 2017': 5, '17 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest')
        assert result == {get_timestamp('15 Dec 2017'): 5,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5
                          }
        result = extend_weekends(amds, how='previous')
        assert result == {get_timestamp('14 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 5,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          }
        result = extend_weekends(amds, how='next')
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5,
                          get_timestamp('19 Dec 2017'): 5
                          }

    def test_extend_weekend_two_holidays_new_label(self):
        amds = {'16 Dec 2017': 5, '17 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest', label=0)
        assert result == {get_timestamp('15 Dec 2017'): 0,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 0}
        result = extend_weekends(amds, how='previous', label=0)
        assert result == {get_timestamp('14 Dec 2017'): 0,
                          get_timestamp('15 Dec 2017'): 0,
                          get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          }
        result = extend_weekends(amds, how='next', label=0)
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 0,
                          get_timestamp('19 Dec 2017'): 0}

    def test_extend_weekend_two_holidays_diff_labels(self):
        amds = {'16 Dec 2017': 3, '17 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest')
        assert result == {get_timestamp('15 Dec 2017'): 3,
                          get_timestamp('16 Dec 2017'): 3,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 5}
        result = extend_weekends(amds, how='previous')
        assert result == {get_timestamp('14 Dec 2017'): 5,
                          get_timestamp('15 Dec 2017'): 3,
                          get_timestamp('16 Dec 2017'): 3,
                          get_timestamp('17 Dec 2017'): 5,
                          }
        result = extend_weekends(amds, how='next')
        assert result == {get_timestamp('16 Dec 2017'): 3,
                          get_timestamp('17 Dec 2017'): 5,
                          get_timestamp('18 Dec 2017'): 3,
                          get_timestamp('19 Dec 2017'): 5}

    def test_extend_weekend_strange_weekend(self):
        amds = {'16 Dec 2017': 5}
        result = extend_weekends(amds, how='nearest', weekend=[5])
        # if there is a tie, 'nearest' == 'next'
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('17 Dec 2017'): 5}
        result = extend_weekends(amds, how='next', weekend=[5, 6, 0])
        assert result == {get_timestamp('16 Dec 2017'): 5,
                          get_timestamp('19 Dec 2017'): 5}
        result = extend_weekends(amds, how='previous', weekend=[3, 4, 5])
        assert result == {get_timestamp('13 Dec 2017'): 5,
                          get_timestamp('16 Dec 2017'): 5}
        result = extend_weekends(amds, weekend=[])
        assert result == {get_timestamp('16 Dec 2017'): 5}

    def test_from_easter(self):
        assert from_easter(2017, [0, 1, -2]) == {
                                            get_timestamp('16 Apr 2017'): 0,
                                            get_timestamp('17 Apr 2017'): 0,
                                            get_timestamp('14 Apr 2017'): 0}

        assert from_easter(2017, [1], easter_type='orthodox', label=5) == {
            get_timestamp('17 Apr 2017'): 5}
        assert from_easter(2000, [0]) == {get_timestamp('23 Apr 2000'): 0}
        assert from_easter(2000, [0],
                   easter_type='orthodox') == {get_timestamp('30 Apr 2000'): 0}
        assert from_easter(2000, []) == {}


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
