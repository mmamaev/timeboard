from timeboard.core import _Frame, _Subframe, Splitter, get_timestamp
from timeboard.exceptions import UnsupportedPeriodError
import pytest


@pytest.fixture(scope='module')
def frame_60d():
    return _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Mar 2017')


@pytest.fixture(scope='module')
def frame_10d():
    return _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')


def assert_subframe(sf, first, last, skip_left, skip_right):
    return (
        sf.first == first and
        sf.last == last and
        sf.skip_left == skip_left and
        sf.skip_right == skip_right
    )


class TestSubframeConstructor(object):
    def test_subframe_constructor(self):
        sf = _Subframe(1, 2)
        assert sf.first == 1
        assert sf.last == 2
        assert sf.skip_left == 0
        assert sf.skip_right == 0

    def test_subframe_modify(self):
        sf = _Subframe(1, 2)
        sf.first = 10
        sf.last = 20
        sf.skip_left = 30
        sf.skip_right = 40
        assert assert_subframe(sf, 10, 20, 30, 40)


class TestDaysSplitByWeekly(object):
    def test_days_splitby_weekly_aligned(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_dangling(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='18 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('W'))
        assert len(result) == 4
        assert assert_subframe(result[0], 0, 0, 6, 0)
        assert assert_subframe(result[1], 1, 7, 0, 0)
        assert assert_subframe(result[2], 8, 14, 0, 0)
        assert assert_subframe(result[3], 15, 17, 0, 4)

    def test_days_splitby_weekly_short(self):
        f = _Frame(base_unit_freq='D', start='03 Jan 2017', end='06 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('W'))
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 3, 1, 2)

    def test_days_splitby_weekly_dangling_span(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='18 Jan 2017')
        result = f.do_split_by(4, 15, Splitter('W'))
        assert len(result) == 3
        assert assert_subframe(result[0], 4, 7, 3, 0)
        assert assert_subframe(result[1], 8, 14, 0, 0)
        assert assert_subframe(result[2], 15, 15, 0, 6)

    def test_days_splitby_weekly_dangling_span_aligned(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='18 Jan 2017')
        result = f.do_split_by(1, 14, Splitter('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 1, 7, 0, 0)
        assert assert_subframe(result[1], 8, 14, 0, 0)

    def test_days_splitby_weekly_shifted(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(1, 12, Splitter('W-MON'))
        assert len(result) == 3
        assert assert_subframe(result[0], 1, 1, 6, 0)
        assert assert_subframe(result[1], 2, 8, 0, 0)
        assert assert_subframe(result[2], 9, 12, 0, 3)

class TestDaysSplitByWeeklyAtPoints(object):

    def test_days_splitby_weekly_atpoints_empty(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('W', at=[]))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_withzerobound(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 0}, {'days': 2},
                                                 {'days': 5}]))
        # Subframes will be Mon to Tue, Wed to Fri, Sat to Sun - > no dangle
        assert len(result) == 6
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 4, 0, 0)
        assert assert_subframe(result[2], 5, 6, 0, 0)
        assert assert_subframe(result[3], 7, 8, 0, 0)
        assert assert_subframe(result[4], 9, 11, 0, 0)
        assert assert_subframe(result[5], 12, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_1(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 2}, {'days': 5}]))
        # Frame starts on Mon, ends on Sun
        # Subframes will be Wed to Fri, Sat to Tue
        # Here would be no dangle with simple split_by 'W'
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 1, 2, 0) # Mon 2 to Tue 3
                                                      # dangle from Sat 31 Dec
        assert assert_subframe(result[1], 2, 4, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 5, 8, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 9, 11, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 12, 13, 0, 2) # Sat 14 to Sun 15
                                                        # dangle to Tue 17


    def test_days_splitby_weekly_atpoints_2(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='17 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 2}, {'days': 5}]))
        # Frame starts on Sat, ends on Tue
        # Subframes will be Wed to Fri, Sat to Tue -> No dangle
        # Here would be dangles with simple split_by 'W'
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 3, 0, 0) # Sat 31 to Tue 3
        assert assert_subframe(result[1], 4, 6, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 7, 10, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 11, 13, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 14, 17, 0, 0) # Sat 14 to Tue 17

    def test_days_splitby_weekly_atpoints_3(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='16 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 2}, {'days': 5}]))
        # Frame starts on Sun, ends on Mon
        # Subframes will be Wed to Fri, Sat to Tue
        # With simple split_by 'W' here would be dangles but with other values
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 2, 1, 0) # Sun 1 to Tue 3
                                                      # dangle from Sat Dec 31
        assert assert_subframe(result[1], 3, 5, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 6, 9, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 10, 12, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 13, 15, 0, 1) # Sat 14 to Mon 16
                                                        # dangle to Jan 16 Tue

    def test_days_splitby_weekly_atpoints_partframe(self):
        f = _Frame(base_unit_freq='D', start='23 Dec 2016', end='25 Jan 2017')
        result = f.do_split_by(10, 23,
                               Splitter('W', at=[{'days': 2}, {'days': 5}]))
        assert len(result) == 5
        assert assert_subframe(result[0], 10, 11, 2, 0) # Mon 2 to Tue 3
                                                      # dangle from Sat 31 Dec
        assert assert_subframe(result[1], 12, 14, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 15, 18, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 19, 21, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 22, 23, 0, 2) # Sat 14 to Sun 15
                                                        # dangle to Tue 17

class TestDaysSplitByWeeklyAtPointsCornerCases(object):

    def test_days_splitby_weekly_atpoints_excessive1(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 2, 'hours': 10},
                                                 {'days': 5, 'hours': 15}]))
        # Adding hours does not change the result
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 1, 2, 0) # Mon 2 to Tue 3
                                                      # dangle from Sat 31 Dec
        assert assert_subframe(result[1], 2, 4, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 5, 8, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 9, 11, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 12, 13, 0, 2) # Sat 14 to Sun 15
                                                        # dangle to Tue 17

    def test_days_splitby_weekly_atpoints_excessive2(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 2, 'hours': 24},
                                                 {'days': 5, 'hours': 25}]))
        # However adding to many hours does move the split to the next day
        # Subframes will be Thu to Sat, Sun to Wed
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 2, 1, 0) # Mon 2 to Wed 4
                                                      # dangle from Sun 1
        assert assert_subframe(result[1], 3, 5, 0, 0) # Thu 5 to Sat 7
        assert assert_subframe(result[2], 6, 9, 0, 0) # Sun 8 to Wed 11
        assert assert_subframe(result[3], 10, 12, 0, 0) # Thu 12 to Sat 14
        assert assert_subframe(result[4], 13, 13, 0, 3) # Sun 15
                                                        # dangle to Wed 18

    def test_days_splitby_weekly_atpoints_excessive3(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 12}, {'days': 16}]))
        # Split points which go outside the period of splitter freq
        # will be ignored
        # Here result will be the same as with at=None
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_excessive4(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 5}, {'days': 16}]))
        # Split points which go outside the period of splitter freq
        # will be ignored
        # Here only 'days':5 will be taken into account
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 4, 2, 0)
        assert assert_subframe(result[1], 5, 11, 0, 0)
        assert assert_subframe(result[2], 12, 13, 0, 5)

    def test_days_splitby_weekly_atpoints_duplicates(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 2},
                                                 {'days': 2, 'hours': 4},
                                                 {'days': 5},
                                                 {'days': 4, 'hours': 25}]))
        # 'at' contains points referring to the same days
        # The result will be the same as with at=[{'days': 2}, {'days': 5}]
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 1, 2, 0)  # Mon 2 to Tue 3
        # dangle from Sat 31 Dec
        assert assert_subframe(result[1], 2, 4, 0, 0)  # Wed 4 to Fri 6
        assert assert_subframe(result[2], 5, 8, 0, 0)  # Sat 7 to Tue 10
        assert assert_subframe(result[3], 9, 11, 0, 0)  # Wed 11 to Fri 13
        assert assert_subframe(result[4], 12, 13, 0, 2)  # Sat 14 to Sun 15
        # dangle to Tue 17

    def test_days_splitby_weekly_atpoints_onlyzero(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': 0}]))
        # Here result will be the same as with at=None
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_negative(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': -1}]))
        # Here result will be the same as with at=None because negative
        # offset falls out of a period
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_negative_compensated(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'days': -1, 'hours': 72}]))
        # Negative day offset is compendates by positive hours
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 5, 0)
        assert assert_subframe(result[1], 2, 8, 0, 0)
        assert assert_subframe(result[2], 9, 13, 0, 2)

    def test_days_splitby_weekly_atpoints_float(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('W', at=[{'weeks': 0.29}]))
        # 0.29 of a week is 2+ days, so the result is the same as with 'days':2
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 5, 0)
        assert assert_subframe(result[1], 2, 8, 0, 0)
        assert assert_subframe(result[2], 9, 13, 0, 2)

    def test_days_splitby_weekly_atpoints_badkeyword(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        with pytest.raises(TypeError):
            f.do_split_by(0, len(f) - 1,
                          Splitter('W', at=[{'nonsense': 1}]))

    def test_days_splitby_weekly_atpoints_badvalue(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        with pytest.raises(TypeError):
            f.do_split_by(0, len(f) - 1,
                          Splitter('W', at=[{'days': 'nonsense'}]))

    def test_days_splitby_weekly_atpoints_missedlist(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        with pytest.raises(TypeError):
            f.do_split_by(0, len(f) - 1,
                          Splitter('W', at={'days': 2}))


class TestDaysSplitByMonthly(object):

    def test_days_splitby_monthly_dangling(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Feb 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('M'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 0, 30, 0)
        assert assert_subframe(result[1], 1, 31, 0, 0)
        assert assert_subframe(result[2], 32, 32, 0, 27)

    def test_days_splitby_monthly_atpoints(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        # split at 10th (=1+9) and 20th (=1+19) day of each month
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('M', at=[{'days':9}, {'days':19}]))
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 9, 11, 0)
        assert assert_subframe(result[1], 10, 19, 0, 0)
        assert assert_subframe(result[2], 20, 40, 0, 0)
        assert assert_subframe(result[3], 41, 50, 0, 0)
        assert assert_subframe(result[4], 51, 60, 0, 8)

    def test_days_splitby_monthly_atday30(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        # split at 30th (=1+29) day of each month
        # no split point in February, there is just Jan 30
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('M', at=[{'days':29}]))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 29, 1, 0)
        assert assert_subframe(result[1], 30, 60, 0, 28)


class TestDaysSplitByAnnually(object):

    def test_days_splitby_annually_dangling(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('A'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 365, 0)  # 2016 was a leap year
        assert assert_subframe(result[1], 1, 1, 0, 364)

    def test_days_splitby_annually_at_specific_date(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2015', end='31 Dec 2017')
        # split at Apr 11
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('A', at=[{'months': 3, 'days': 10}]))
        assert len(result) == 4
        assert assert_subframe(result[0], 0, 99, 365-100, 0)  #01.01.15 -
        # 10.04.15
        assert assert_subframe(result[1], 100, 100+365, 0, 0) #11.04.15-10.04.16
                                                             # 2016 leap year
        assert assert_subframe(result[2], 466, 466+364, 0,
                               0) #11.04.16=10.04.17
        assert assert_subframe(result[3], 831, 365+366+365-1, 0,
                               100)  # 11.04.17=31.12.17
        assert f[result[0].last].start_time == get_timestamp('10 Apr 2015')
        assert f[result[1].last].start_time == get_timestamp('10 Apr 2016')
        assert f[result[2].last].start_time == get_timestamp('10 Apr 2017')


class TestHoursSplitBy(object):

    def test_hours_splitby_weekly_aligned(self):
        f = _Frame(base_unit_freq='H', start='02 Jan 2017 00:00',
                   end='15 Jan 2017 23:30')
        result = f.do_split_by(0, len(f) - 1, Splitter('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 7*24-1, 0, 0)
        assert assert_subframe(result[1], 7*24, 14*24-1, 0, 0)

    def test_hours_splitby_weekly_dangling(self):
        f = _Frame(base_unit_freq='H', start='03 Jan 2017 01:00',
                   end='15 Jan 2017 22:30')
        result = f.do_split_by(0, len(f) - 1, Splitter('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 7 * 24 - 25 - 1, 25, 0)
        assert assert_subframe(result[1], 7*24 - 25, 14 * 24 - 25 - 1 - 1, 0, 1)

    def test_hours_splitby_weekly_dangling_span_short(self):
        f = _Frame(base_unit_freq='H', start='03 Jan 2017 01:00',
                   end='15 Jan 2017 22:30')
        result = f.do_split_by(7 * 24 - 25 + 2, len(f) - 3, Splitter('W'))
        assert len(result) == 1
        assert assert_subframe(result[0], 7 * 24 - 25 + 2, len(f) - 3, 2, 3)

    def test_hours_splitby_daily_at_specific_hours(self):
        f = _Frame(base_unit_freq='H', start='01 Jan 2017 00:00',
                   end='02 Jan 2017 23:59')
        result = f.do_split_by(0, len(f) - 1,
                               Splitter('D', at=[{'hours': 8}, {'hours': 18}]))
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 7, 6, 0)
        assert assert_subframe(result[1], 8, 17, 0, 0)
        assert assert_subframe(result[2], 18, 31, 0, 0)
        assert assert_subframe(result[3], 32, 41, 0, 0)
        assert assert_subframe(result[4], 42, 47, 0, 8)


class TestWeeksSplitBy(object):

    def test_weeks_splitby_months(self):
        f = _Frame(base_unit_freq='W', start='01 Jan 2017', end='01 Mar 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('M'))

    def test_weeks_splitby_years(self):
        f = _Frame(base_unit_freq='W', start='31 Dec 2016', end='01 Mar 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('A'))

class TestMonthSplitBy(object):

    def test_months_splitby_years(self):
        f = _Frame(base_unit_freq='M', start='31 Dec 2016', end='01 Mar 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('A'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 11, 0)
        assert assert_subframe(result[1], 1, 3, 0, 9)

    def test_months_splitby_years_short(self):
        f = _Frame(base_unit_freq='M', start='01 Feb 2017', end='01 Mar 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('A'))
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 1, 1, 9)

    def test_months_splitby_years_shifted(self):
        f = _Frame(base_unit_freq='M', start='31 Dec 2016', end='01 Mar 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('A-JAN'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 1, 10, 0)
        assert assert_subframe(result[1], 2, 3, 0, 10)

class TestMultipliedFreqSplitBy(object):

    # BASE UNIT AS MULTIPLIED FREQ
    """
    4D  8D                          
    00  00  01.01 02.01 03.01  04.01  
    01      05.01 06.01 07.01  08.01
    02  01  09.01 10.01 11.01  12.01  
    03      13.01 14.01 15.01  16.01
    04  02  17.01 18.01 19.01 +20.01
        skip_right 1
    """

    def test_4D_splitby_weeks(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('W'))

    def test_4D_splitby_months(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('M'))

    @pytest.mark.xfail(reason='Probably bug in '
                              'pd.tseries.frequencies.is_subperiod'
                              ' (X is not a subperiod of NX)')
    def test_4D_splitby_8D(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('8D'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 3, 0, 0)
        assert assert_subframe(result[2], 4, 4, 0, 1)

    @pytest.mark.xfail(reason='Probably bug in '
                              'pd.tseries.frequencies.is_subperiod'
                              ' (X is not a subperiod of NX)')
    def test_4D_splitby_8D_span_aligned(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        result = f.do_split_by(1, 4, Splitter('8D'))
        assert len(result) == 2
        assert assert_subframe(result[0], 1, 2, 0, 0)
        assert assert_subframe(result[1], 3, 4, 0, 0)

    @pytest.mark.xfail(reason='Probably bug in '
                              'pd.tseries.frequencies.is_subperiod'
                              ' (X is not a subperiod of NX)')
    def test_4D_splitby_8D_span_dangling(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        result = f.do_split_by(1, 3, Splitter('8D'))
        assert len(result) == 2
        assert assert_subframe(result[0], 1, 2, 0, 0)
        assert assert_subframe(result[1], 3, 3, 0, 1)

    @pytest.mark.xfail(reason='Probably bug in '
                              'pd.tseries.frequencies.is_subperiod'
                              ' (X is not a subperiod of NX)')
    def test_weeks_splitby_multiple_weeks(self):
        f = _Frame(base_unit_freq='W', start='02 Jan 2017', end='29 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('2W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 3, 0, 0)

    @pytest.mark.xfail(reason='Probably bug in '
                              'pd.tseries.frequencies.is_subperiod'
                              ' (X is not a subperiod of NX)')
    def test_weeks_splitby_multiple_weeks_dangling(self):
        f = _Frame(base_unit_freq='W', start='02 Jan 2017', end='30 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('2W'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 3, 0, 0)
        assert assert_subframe(result[2], 4, 4, 0, 1)

    # CORNER CASES

class TestSplitByWeird(object):

    def test_splitby_same_freq(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='03 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('D'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 0, 0, 0)
        assert assert_subframe(result[1], 1, 1, 0, 0)
        assert assert_subframe(result[2], 2, 2, 0, 0)

    def test_splitby_higher_freq_aligned(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='03 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('H'))

    def test_splitby_higher_freq_not_aligned(self):
        f = _Frame(base_unit_freq='M', start='01 Jan 2017', end='01 Feb 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('W'))

    # TODO: test other pandas freqs injected as offset methods  \
    # TODO: (i.e. MonthBegin(), also in _Frame constructor
