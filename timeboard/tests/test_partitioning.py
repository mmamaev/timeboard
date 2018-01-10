from timeboard.core import _Frame, _Subframe, Marker, get_timestamp
from timeboard.exceptions import UnsupportedPeriodError
import pytest
from pandas import Period


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
        result = f.partition_with_marker(0, len(f) - 1, Marker('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_dangling(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='18 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W'))
        assert len(result) == 4
        assert assert_subframe(result[0], 0, 0, 6, 0)
        assert assert_subframe(result[1], 1, 7, 0, 0)
        assert assert_subframe(result[2], 8, 14, 0, 0)
        assert assert_subframe(result[3], 15, 17, 0, 4)

    def test_days_splitby_weekly_short(self):
        f = _Frame(base_unit_freq='D', start='03 Jan 2017', end='06 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W'))
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 3, 1, 2)

    def test_days_splitby_weekly_dangling_span(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='18 Jan 2017')
        result = f.partition_with_marker(4, 15, Marker('W'))
        assert len(result) == 3
        assert assert_subframe(result[0], 4, 7, 3, 0)
        assert assert_subframe(result[1], 8, 14, 0, 0)
        assert assert_subframe(result[2], 15, 15, 0, 6)

    def test_days_splitby_weekly_dangling_span_aligned(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='18 Jan 2017')
        result = f.partition_with_marker(1, 14, Marker('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 1, 7, 0, 0)
        assert assert_subframe(result[1], 8, 14, 0, 0)

    def test_days_splitby_weekly_shifted(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(1, 12, Marker('W-MON'))
        assert len(result) == 3
        assert assert_subframe(result[0], 1, 1, 6, 0)
        assert assert_subframe(result[1], 2, 8, 0, 0)
        assert assert_subframe(result[2], 9, 12, 0, 3)


class TestDaysSplitByWeeklyAtPoints(object):

    def test_days_splitby_weekly_atpoints_empty(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W', at=[]))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_withzerobound(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 0}, {'days': 2},
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
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 2}, {'days': 5}]))
        # Frame starts on Mon, ends on Sun
        # Subframes will be Wed to Fri, Sat to Tue
        # Here would be no dangle with simple marker 'W'
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
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 2}, {'days': 5}]))
        # Frame starts on Sat, ends on Tue
        # Subframes will be Wed to Fri, Sat to Tue -> No dangle
        # Here would be dangles with simple marker 'W'
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 3, 0, 0) # Sat 31 to Tue 3
        assert assert_subframe(result[1], 4, 6, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 7, 10, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 11, 13, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 14, 17, 0, 0) # Sat 14 to Tue 17

    def test_days_splitby_weekly_atpoints_3(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='16 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 2}, {'days': 5}]))
        # Frame starts on Sun, ends on Mon
        # Subframes will be Wed to Fri, Sat to Tue
        # With simple marker 'W' here would be dangles but with other values
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
        result = f.partition_with_marker(10, 23,
                                         Marker('W', at=[{'days': 2}, {'days': 5}]))
        assert len(result) == 5
        assert assert_subframe(result[0], 10, 11, 2, 0) # Mon 2 to Tue 3
                                                      # dangle from Sat 31 Dec
        assert assert_subframe(result[1], 12, 14, 0, 0) # Wed 4 to Fri 6
        assert assert_subframe(result[2], 15, 18, 0, 0) # Sat 7 to Tue 10
        assert assert_subframe(result[3], 19, 21, 0, 0) # Wed 11 to Fri 13
        assert assert_subframe(result[4], 22, 23, 0, 2) # Sat 14 to Sun 15
                                                        # dangle to Tue 17


class TestDaysSplitByAtPointsCornerCases(object):

    def test_days_splitby_weekly_atpoints_excessive1(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 2, 'hours': 10},
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
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 2, 'hours': 24},
                                               {'days': 5, 'hours': 25}]))
        # However adding to many hours does move the mark to the next day
        # this is same as days:3 and days:6
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
        result = f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'days': 7}]))
        # Points which dall outside the period of marker freq
        # will be ignored
        # Here `how` returns empty list, hence no partitioning is done and
        # dangles are undefined
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 13, -1, -1)

    def test_days_splitby_weekly_atpoints_excessive4(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': 5}, {'days': 16}]))
        # Points which fall outside the period of marker freq
        # will be ignored
        # Here only 'days':5 will be taken into account
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 4, 2, 0)
        assert assert_subframe(result[1], 5, 11, 0, 0)
        assert assert_subframe(result[2], 12, 13, 0, 5)

    def test_days_splitby_weekly_atpoints_duplicates(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'days': 2},
                                                                        {'days': 2,
                                                               'hours': 4},
                                                                        {'days': 5},
                                                                        {'days': 4,
                                                               'hours': 25}]))
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
        result = f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'days': 0}]))
        # Here result will be the same as with at=None
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 6, 0, 0)
        assert assert_subframe(result[1], 7, 13, 0, 0)

    def test_days_splitby_weekly_atpoints_negative(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'days': -1}]))
        # Negative offset falls out of a period.
        # Here `how` returns empty list and no partitioning is done,
        # dangles are undefined
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 13, -1, -1)

    def test_days_splitby_weekly_atpoints_negative_compensated(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('W', at=[{'days': -1, 'hours': 72}]))
        # Negative day offset is compendates by positive hours
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 5, 0)
        assert assert_subframe(result[1], 2, 8, 0, 0)
        assert assert_subframe(result[2], 9, 13, 0, 2)

    @pytest.mark.xfail(reason='Pandas does not implement '
                      'PeriodIndex + float offset.'
                      ' However, it does implement Timestamp + float offset')
    def test_days_splitby_weekly_atpoints_float(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'weeks': 0.29}]))
        # 0.29 of a week is 2+ days, so the result is the same as with 'days':2
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 5, 0)
        assert assert_subframe(result[1], 2, 8, 0, 0)
        assert assert_subframe(result[2], 9, 13, 0, 2)

    def test_days_splitby_weekly_atpoints_badkeyword(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        with pytest.raises(TypeError):
            f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'nonsense': 1}]))

    def test_days_splitby_weekly_atpoints_badvalue(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        with pytest.raises(TypeError):
            f.partition_with_marker(0, len(f) - 1, Marker('W', at=[{'days': 'nonsense'}]))

    def test_days_splitby_weekly_atpoints_missedlist(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017', end='15 Jan 2017')
        with pytest.raises(TypeError):
            f.partition_with_marker(0, len(f) - 1, Marker('W', at={'days': 2}))


class TestDaysSplitByMonthly(object):

    def test_days_splitby_monthly_dangling(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Feb 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('M'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 0, 30, 0)
        assert assert_subframe(result[1], 1, 31, 0, 0)
        assert assert_subframe(result[2], 32, 32, 0, 27)

    def test_days_splitby_monthly_atpoints(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        # set mark at 10th (=1+9) and 20th (=1+19) day of each month
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('M', at=[{'days': 9}, {'days': 19}]))
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 9, 11, 0)
        assert assert_subframe(result[1], 10, 19, 0, 0)
        assert assert_subframe(result[2], 20, 40, 0, 0)
        assert assert_subframe(result[3], 41, 50, 0, 0)
        assert assert_subframe(result[4], 51, 60, 0, 8)

    def test_days_splitby_monthly_at_day30(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        # set marks at 30th (=1+29) day of each month
        # no mark in February, there is just Jan 30
        result = f.partition_with_marker(0, len(f) - 1, Marker('M', at=[{'days': 29}]))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 29, 1, 0)
        assert assert_subframe(result[1], 30, 60, 0, 28)

    def test_days_splitby_monthly_at_weekdays(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        # set mark on second Monday and last Thursday
        # 09.01.17, 26.01.17, 13.02.17, 23.02.17
        # left dangle from 29.12  == 2; right dangle thru 12.03 == 11
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='M',
                                                               at=[{'month': 1, 'week': 2,
                                                          'weekday': 1},
                                                         {'month': 1,
                                                          'week': -1,
                                                          'weekday': 4}],
                                                               how='nth_weekday_of_month'))
        assert len(result) == 5
        assert assert_subframe(result[0], 0, 8, 2, 0)
        assert assert_subframe(result[1], 9, 25, 0, 0)
        assert assert_subframe(result[2], 26, 43, 0, 0)
        assert assert_subframe(result[3], 44, 53, 0, 0)
        assert assert_subframe(result[4], 54, 60, 0, 11)


class TestDaysSplitByAnnually(object):

    def test_days_splitby_annually_dangling(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('A'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 365, 0)  # 2016 was a leap year
        assert assert_subframe(result[1], 1, 1, 0, 364)

    def test_days_splitby_annually_at_specific_date(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2015', end='31 Dec 2017')
        # set mark on Apr 11
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('A', at=[{'months': 3, 'days': 10}]))
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

    def test_days_splitby_annually_at_month_weekdays(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2015', end='31 Dec 2017')
        # mark last Monday in May and first Monday in September
        # 25.05.15, 07.09.15, 30.05.16, 05.09.16, 29.05.17, 04.09.17
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'month': 5,
                                                          'week': -1,
                                                          'weekday': 1},
                                                         {'month': 9, 'week': 1,
                                                          'weekday': 1}],
                                                               how='nth_weekday_of_month'))
        assert len(result) == 7
        assert assert_subframe(result[0], 0, 143, 122, 0)
        assert assert_subframe(result[1], 144, 248, 0, 0)
        assert assert_subframe(result[2], 249, 514, 0, 0)
        assert assert_subframe(result[3], 515, 612, 0, 0)
        assert assert_subframe(result[4], 613, 878, 0, 0)
        assert assert_subframe(result[5], 879, 976, 0, 0)
        assert assert_subframe(result[6], 977, 1095, 0, 147)

    def test_days_splitby_annually_at_month_weekdays_shift(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2015', end='31 Dec 2017')
        # mark Wednesday after last Monday in May and Thursday before
        # first Monday in September
        # 25.05.15+2, 07.09.15-4, 30.05.16+2, 05.09.16-4, 29.05.17+2, 04.09.17-4
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'month': 5,
                                                          'week': -1,
                                                          'weekday': 1,
                                                          'shift': 2},
                                                         {'month': 9, 'week': 1,
                                                          'weekday': 1,
                                                          'shift': -4}],
                                                               how='nth_weekday_of_month'))
        assert len(result) == 7
        assert assert_subframe(result[0], 0, 145, 126, 0)
        assert assert_subframe(result[1], 146, 244, 0, 0)
        assert assert_subframe(result[2], 245, 516, 0, 0)
        assert assert_subframe(result[3], 517, 608, 0, 0)
        assert assert_subframe(result[4], 609, 880, 0, 0)
        assert assert_subframe(result[5], 881, 972, 0, 0)
        assert assert_subframe(result[6], 973, 1095, 0, 149)

    def test_days_splitby_annually_at_easter_western(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2013', end='01 Jan 2017')
        # mark Good Friday, Easter and Easter Monday in 2014, 2015, 2016
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'days': -2},
                                                         {'days': 0},
                                                         {'days': 1}],
                                                               how='from_easter_western'
                                                               ))
        result_dates = map(lambda x: (f[x.first], f[x.last]), result)
        assert len(result) == 10
        assert result_dates[1][0] == Period('2014-04-18', 'D')
        assert result_dates[2][0] == Period('2014-04-20', 'D') #easter
        assert result_dates[3][0] == Period('2014-04-21', 'D')
        assert result_dates[4][0] == Period('2015-04-03', 'D')
        assert result_dates[5][0] == Period('2015-04-05', 'D') #easter
        assert result_dates[6][0] == Period('2015-04-06', 'D')
        assert result_dates[7][0] == Period('2016-03-25', 'D')
        assert result_dates[8][0] == Period('2016-03-27', 'D') #easter
        assert result_dates[9][0] == Period('2016-03-28', 'D')

    def test_days_splitby_annually_at_easter_orthodox(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2013', end='01 Jan 2017')
        # mark Good Friday, Easter and Easter Monday in 2014, 2015, 2016
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'days': -2},
                                                         {'days': 0},
                                                         {'days': 1}],
                                                               how='from_easter_orthodox'
                                                               ))
        result_dates = map(lambda x: (f[x.first], f[x.last]), result)
        assert len(result) == 10
        assert result_dates[1][0] == Period('2014-04-18', 'D')
        assert result_dates[2][0] == Period('2014-04-20', 'D') #easter
        assert result_dates[3][0] == Period('2014-04-21', 'D')
        assert result_dates[4][0] == Period('2015-04-10', 'D')
        assert result_dates[5][0] == Period('2015-04-12', 'D') #easter
        assert result_dates[6][0] == Period('2015-04-13', 'D')
        assert result_dates[7][0] == Period('2016-04-29', 'D')
        assert result_dates[8][0] == Period('2016-05-01', 'D') #easter
        assert result_dates[9][0] == Period('2016-05-02', 'D')

class TestDaysSplitByAtWeekdaysCornerCases(object):

    def test_days_splitby_monthly_at_weekdays_outside(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='M',
                                                               at=[{'month': 2, 'week': 2,
                                                          'weekday': 1}],
                                                               how='nth_weekday_of_month'))
        # month=2 is outside the single month which is a period of `each`
        # therefore `how` returns empty list and no partitioning is done,
        # dangles are undefined
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 60, -1, -1)

    def test_days_splitby_monthly_at_weekdays_gaps(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='M',
                                                               at=[{'month': 1, 'week': 5,
                                                          'weekday': 2}],
                                                               how='nth_weekday_of_month'))
        # 5th Tuesday is only in January (31 Jan)
        # Previous 5th Tuesday was in November 2016 and next will be
        # only in May 2017 - both fell outside the envelope
        # So we cannot provide correct calculations of skip_left and skip_right
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 29, -1, 0)
        assert assert_subframe(result[1], 30, 59, 0, -1)

    def test_days_splitby_monthly_at_weekdays_gaps2(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='M',
                                                               at=[{'month': 1, 'week': 5,
                                                          'weekday': 2}],
                                                               how='nth_weekday_of_month'))
        # 5th Tuesday is only in January (31 Jan)
        # Previous 5th Tuesday was in November 2016 and next will be
        # So we can provide skip_left but cannot calculate skip_right
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 30, 32, 0)
        assert assert_subframe(result[1], 31, 60, 0, -1)

    def test_days_splitby_monthly_at_weekdays_gaps3(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'month': 1, 'week': 5,
                                                          'weekday': 2}],
                                                               how='nth_weekday_of_month'))
        # Here we look for 5th Tue in each January. There is only one January
        # in the frame which by the way has 5th Tuesday on Jan 31.
        # But what about dangles? Envelope is 2015-2018
        # There was no 5th Tues in Jan of 2015 and 2016, so we do not have
        # left dangle. There is 5th Tues in Jan 2018, so we have the right
        # dangle.
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 30, -1, 0)
        assert assert_subframe(result[1], 31, 60, 0, 334)

    def test_days_splitby_monthly_at_weekdays_gaps3n(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'month': 1,
                                                          'week': -5,
                                                          'weekday': 2}],
                                                               how='nth_weekday_of_month'))
        # Here we look for minus 5th Tue in each January. There is only one
        # January in the frame which by the way such Tuesday on Jan 3.
        # But what about dangles? Envelope is 2015-2018
        # There was no -5th Tues in Jan of 2015 and 2016, so we do not have
        # left dangle. There is -5th Tues in Jan 2018, so we have the right
        # dangle.
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 2, -1, 0)
        assert assert_subframe(result[1], 3, 60, 0, 306)


    def test_days_splitby_monthly_at_weekdays_gaps4(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'month': 1, 'week': 5,
                                                          'weekday': 7}],
                                                               how='nth_weekday_of_month'))
        # Here we look for 5th Sun in each January. There is only one January
        # in the frame which by the way has 5th Sunday on Jan 29.
        # But what about dangles? Envelope is 2015-2018
        # There was 5th Sunday in 2016, so we haveleft dangle.
        # There is no 5th Sunday in Jan 2018, so we do not have the right
        # dangle.
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 28, 335, 0)
        assert assert_subframe(result[1], 29, 60, 0, -1)

    def test_days_splitby_monthly_at_weekdays_gaps4n(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                               at=[{'month': 1,
                                                          'week': -5,
                                                          'weekday': 7}],
                                                               how='nth_weekday_of_month'))
        # Here we look for -5th Sun in each January. There is only one January
        # in the frame which by the way has such Sunday on Jan 1.
        # But what about dangles? Envelope is 2015-2018
        # There was -5th Sunday in 2016, so we have left dangle.
        # There is no -5th Sunday in Jan 2018, so we do not have the right
        # dangle.
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 363, 0)
        assert assert_subframe(result[1], 1, 60, 0, -1)

    def test_days_splitby_monthly_at_weekdays_bad_args(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Mar 2017')
        for badmnth in [-1,0,13, 6.5, 'Jan']:
            with pytest.raises(AssertionError):
                f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                              at=[{'month': badmnth,
                                                         'week': 1,
                                                         'weekday': 7}],
                                                              how='nth_weekday_of_month'))
        for badweek in [-6, 0, 6, 3.5]:
            with pytest.raises(AssertionError):
                f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                              at=[{'month': 1,
                                                         'week': badweek,
                                                         'weekday': 7}],
                                                              how='nth_weekday_of_month'))
        for badwday in [-1, 0, 8, 2.5, 'Mon']:
            with pytest.raises(AssertionError):
                f.partition_with_marker(0, len(f) - 1, Marker(each='A',
                                                              at=[{'month': 1, 'week': 1,
                                                         'weekday': badwday}],
                                                              how='nth_weekday_of_month'))


class TestHoursSplitBy(object):

    def test_hours_splitby_weekly_aligned(self):
        f = _Frame(base_unit_freq='H', start='02 Jan 2017 00:00',
                   end='15 Jan 2017 23:30')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 7*24-1, 0, 0)
        assert assert_subframe(result[1], 7*24, 14*24-1, 0, 0)

    def test_hours_splitby_weekly_dangling(self):
        f = _Frame(base_unit_freq='H', start='03 Jan 2017 01:00',
                   end='15 Jan 2017 22:30')
        result = f.partition_with_marker(0, len(f) - 1, Marker('W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 7 * 24 - 25 - 1, 25, 0)
        assert assert_subframe(result[1], 7*24 - 25, 14 * 24 - 25 - 1 - 1, 0, 1)

    def test_hours_splitby_weekly_dangling_span_short(self):
        f = _Frame(base_unit_freq='H', start='03 Jan 2017 01:00',
                   end='15 Jan 2017 22:30')
        result = f.partition_with_marker(7 * 24 - 25 + 2, len(f) - 3, Marker('W'))
        assert len(result) == 1
        assert assert_subframe(result[0], 7 * 24 - 25 + 2, len(f) - 3, 2, 3)

    def test_hours_splitby_daily_at_specific_hours(self):
        f = _Frame(base_unit_freq='H', start='01 Jan 2017 00:00',
                   end='02 Jan 2017 23:59')
        result = f.partition_with_marker(0, len(f) - 1,
                                         Marker('D', at=[{'hours': 8}, {'hours': 18}]))
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
            f.partition_with_marker(0, len(f) - 1, Marker('M'))

    def test_weeks_splitby_years(self):
        f = _Frame(base_unit_freq='W', start='31 Dec 2016', end='01 Mar 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('A'))


class TestMonthSplitBy(object):

    def test_months_splitby_years(self):
        f = _Frame(base_unit_freq='M', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('A'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 11, 0)
        assert assert_subframe(result[1], 1, 3, 0, 9)

    def test_months_splitby_years_short(self):
        f = _Frame(base_unit_freq='M', start='01 Feb 2017', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('A'))
        assert len(result) == 1
        assert assert_subframe(result[0], 0, 1, 1, 9)

    def test_months_splitby_years_shifted(self):
        f = _Frame(base_unit_freq='M', start='31 Dec 2016', end='01 Mar 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('A-JAN'))
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
            f.partition_with_marker(0, len(f) - 1, Marker('W'))

    def test_4D_splitby_months(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('M'))

    def test_4D_splitby_8D(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('8D'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 3, 0, 0)
        assert assert_subframe(result[2], 4, 4, 0, 1)

    def test_4D_splitby_8D_span_aligned(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        result = f.partition_with_marker(1, 4, Marker('8D'))
        assert len(result) == 2
        assert assert_subframe(result[0], 1, 2, 0, 0)
        assert assert_subframe(result[1], 3, 4, 0, 0)

    def test_4D_splitby_8D_span_dangling(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='19 Jan 2017')
        result = f.partition_with_marker(1, 3, Marker('8D'))
        assert len(result) == 2
        assert assert_subframe(result[0], 1, 2, 0, 0)
        assert assert_subframe(result[1], 3, 3, 0, 1)

    def test_weeks_splitby_multiple_weeks(self):
        f = _Frame(base_unit_freq='W', start='02 Jan 2017', end='29 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('2W'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 3, 0, 0)

    def test_weeks_splitby_multiple_weeks_dangling(self):
        f = _Frame(base_unit_freq='W', start='02 Jan 2017', end='30 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('2W'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 1, 0, 0)
        assert assert_subframe(result[1], 2, 3, 0, 0)
        assert assert_subframe(result[2], 4, 4, 0, 1)

    def test_splitby_different_multiple_freqs1(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='30 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('2W'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 8, 5, 0)
        assert assert_subframe(result[1], 9, 22, 0, 0)
        assert assert_subframe(result[2], 23, 30, 0, 6)

    @pytest.mark.xfail(reason='Case not covered by _check_groupby_freq')
    def test_splitby_different_multiple_freqs2(self):
        f = _Frame(base_unit_freq='12H', start='02 Jan 2017 12:05',
                   end='04 Jan 2017 10:00')
        result = f.partition_with_marker(0, len(f) - 1, Marker('D'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 0, 1, 0)
        assert assert_subframe(result[1], 1, 2, 0, 0)
        assert assert_subframe(result[2], 3, 3, 0, 1)

    def test_splitby_different_multiple_freqs2b(self):
        f = _Frame(base_unit_freq='12H', start='02 Jan 2017 13:05',
                   end='04 Jan 2017 10:00')
        # these 12H periods are not aligned with boundaries of days
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('D'))

    @pytest.mark.xfail(reason='Case not covered by _check_groupby_freq')
    def test_splitby_different_multiple_freqs3(self):
        f = _Frame(base_unit_freq='12H', start='02 Jan 2017',
                   end='30 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('2W'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 27, 0, 0)
        assert assert_subframe(result[1], 28, 55, 0, 0)
        assert assert_subframe(result[2], 56, 57, 0, 26)

    def test_splitby_different_multiple_freqs3b(self):
        f = _Frame(base_unit_freq='12H', start='02 Jan 2017 01:00',
                   end='30 Jan 2017')
        # these 12H periods are not aligned with boundaries of days, and,
        # consequently. of weeks
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('2W'))

    def test_splitby_different_multiple_freqs4(self):
        f = _Frame(base_unit_freq='9H', start='02 Jan 2017',
                   end='30 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('D'))
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('2W'))

    def test_splitby_different_multiple_freqs5(self):
        f = _Frame(base_unit_freq='48H', start='02 Jan 2017',
                   end='30 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('D'))

    @pytest.mark.xfail(reason='Case not covered by _check_groupby_freq')
    def test_splitby_different_multiple_freqs6(self):
        f = _Frame(base_unit_freq='48H', start='02 Jan 2017',
                   end='30 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('4D'))

    def test_splitby_different_multiple_freqs6b(self):
        f = _Frame(base_unit_freq='48H', start='02 Jan 2017 01:00',
                   end='30 Jan 2017')
        # these 48H periods are not aligned with boundaries of days
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('4D'))

    @pytest.mark.xfail(reason='Case not covered by _check_groupby_freq')
    def test_splitby_different_multiple_freqs7(self):
        f = _Frame(base_unit_freq='7H', start='02 Jan 2017',
                   end='30 Jan 2017')
        # These 7H periods are not aligned with days, but aligned with weeks
        result = f.partition_with_marker(0, len(f) - 1, Marker('W'))

    def test_splitby_different_multiple_freqs7b(self):
        f = _Frame(base_unit_freq='7H', start='03 Jan 2017 00:00',
                   end='30 Jan 2017')
        # these 7H periods are not aligned with boundaries of weeks
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('W'))

    # CORNER CASES

class TestSplitByWeird(object):

    def test_splitby_same_freq(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='03 Jan 2017')
        result = f.partition_with_marker(0, len(f) - 1, Marker('D'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 0, 0, 0)
        assert assert_subframe(result[1], 1, 1, 0, 0)
        assert assert_subframe(result[2], 2, 2, 0, 0)

    def test_splitby_higher_freq_aligned(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='03 Jan 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('H'))

    def test_splitby_higher_freq_not_aligned(self):
        f = _Frame(base_unit_freq='M', start='01 Jan 2017', end='01 Feb 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.partition_with_marker(0, len(f) - 1, Marker('W'))

    # TODO: test other pandas freqs injected as offset methods  \
    # TODO: (i.e. MonthBegin(), also in _Frame constructor
