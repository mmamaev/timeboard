import timeboard as tb
from timeboard.interval import Interval
from timeboard.exceptions import OutOfBoundsError, PartialOutOfBoundsError

import datetime
import pandas as pd
import pytest

@pytest.fixture(scope='module')
def tb_10_8_6_hours(workshift_ref='start'):
    shifts = tb.Marker(each='D', at=[{'hours': 2}, {'hours': 8}, {'hours': 18}])
    daily = tb.Organizer(marker=shifts, structure=[1, 0])
    return tb.Timeboard(base_unit_freq='H',
                        start='01 Oct 2017', end='06 Oct 2017',
                        layout=daily,
                        workshift_ref=workshift_ref)

    #               workshift  day  dur                 end  label  on_duty
    # loc
    # 0   2017-10-01 00:00:00   1 1   2 2017-10-01 01:59:59    1.0     True
    # 1   2017-10-01 02:00:00   1 1   6 2017-10-01 07:59:59    0.0    False
    # 2   2017-10-01 08:00:00   1 1  10 2017-10-01 17:59:59    1.0     True
    # 3   2017-10-01 18:00:00   1x2   8 2017-10-02 01:59:59    0.0    False
    # 4   2017-10-02 02:00:00   2 2   6 2017-10-02 07:59:59    1.0     True
    # 5   2017-10-02 08:00:00   2 2  10 2017-10-02 17:59:59    0.0    False
    # 6   2017-10-02 18:00:00   2x3   8 2017-10-03 01:59:59    1.0     True
    # 7   2017-10-03 02:00:00   3 3   6 2017-10-03 07:59:59    0.0    False
    # 8   2017-10-03 08:00:00   3 3  10 2017-10-03 17:59:59    1.0     True
    # 9   2017-10-03 18:00:00   3x4   8 2017-10-04 01:59:59    0.0    False
    # 10  2017-10-04 02:00:00   4 4   6 2017-10-04 07:59:59    1.0     True
    # 11  2017-10-04 08:00:00   4 4  10 2017-10-04 17:59:59    0.0    False
    # 12  2017-10-04 18:00:00   4x5   8 2017-10-05 01:59:59    1.0     True
    # 13  2017-10-05 02:00:00   5 5   6 2017-10-05 07:59:59    0.0    False
    # 14  2017-10-05 08:00:00   5 5  10 2017-10-05 17:59:59    1.0     True
    # 15  2017-10-05 18:00:00   5x6   7 2017-10-06 00:59:59    0.0    False


class TestIntervalCompoundConstructor:

    def test_interval_constructor_compound_with_two_ts(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval(('01 Oct 2017 10:00', '02 Oct 2017 23:00'))
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 8, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 3, 1, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 3, 2, 0, 0)
        assert ivl._loc == (2,6)
        assert len(ivl) == 5

        ivlx = clnd(('01 Oct 2017 10:00', '02 Oct 2017 23:00'))
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_compound_with_two_ts_open_ended(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval(('01 Oct 2017 10:00', '02 Oct 2017 23:00'),
                                closed='00')
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 18, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 2, 17, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 2, 18, 0, 0)
        assert ivl._loc == (3, 5)
        assert len(ivl) == 3

    def test_interval_constructor_compound_with_two_ts_same_ws(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval(('02 Oct 2017 19:15', '03 Oct 2017 01:10'))
        assert ivl.start_time == datetime.datetime(2017, 10, 2, 18, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 3, 1, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 3, 2, 0, 0)
        assert ivl._loc == (6,6)
        assert len(ivl) == 1

        ivlx = clnd(('02 Oct 2017 19:15', '03 Oct 2017 01:10'))
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_compound_with_length(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval('02 Oct 2017 15:00', length=7)
        assert ivl.start_time == datetime.datetime(2017, 10, 2, 8, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 4, 17, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 4, 18, 0, 0)
        assert ivl._loc == (5,11)
        assert len(ivl) == 7

        ivlx = clnd('02 Oct 2017 15:00', length=7)
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_compound_with_period(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval('01 Oct 2017 19:00', period='D')
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 2, 1, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 2, 2, 0, 0)
        assert ivl._loc == (0, 3)
        assert len(ivl) == 4

        ivlx = clnd('01 Oct 2017 03:00', period='D')
        assert ivlx._loc == ivl._loc

        ivl = clnd.get_interval(pd.Period('01 Oct 2017 19:00', freq='D'))
        assert ivl._loc == (0, 3)


    def test_interval_constructor_compound_with_period2(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval('02 Oct 2017 01:00', period='D')
        # The ws of '02 Oct 2017 01:00' begins on the previous day.
        # With workshift_ref='start', it does not belong to ivl, hence
        # the day is not fully covered by the interval, the ivl reference point
        # is not in the interval
        assert ivl.start_time == datetime.datetime(2017, 10, 2, 2, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 3, 1, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 3, 2, 0, 0)
        assert ivl._loc == (4, 6)
        assert len(ivl) == 3

        ivlx = clnd('02 Oct 2017 01:00', period='D')
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_compound_with_period3(self):
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = clnd.get_interval('01 Oct 2017 19:00', period='D')
        # the ws starting at 18:00 ends next day.
        # With workshift_ref='end' is does not belong to the ivl , hence
        # the day is not fully covered by the interval, the ivl reference point
        # is not in the interval
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 1, 17, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 1, 18, 0, 0)
        assert ivl._loc == (0, 2)
        assert len(ivl) == 3

        ivlx = clnd('01 Oct 2017 19:00', period='D')
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_compound_with_period4(self):
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = clnd.get_interval('02 Oct 2017 01:00', period='D')
        # the ws starting at 18:00 ends next day.
        # With workshift_ref='end' is does not belong to the ivl , hence
        # the day is not fully covered by the interval
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 18, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 2, 17, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 2, 18, 0, 0)
        assert ivl._loc == (3, 5)
        assert len(ivl) == 3

        ivlx = clnd('02 Oct 2017 01:00', period='D')
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_compound_with_period_partial(self):
        clnd = tb_10_8_6_hours()
        # this period is completely outside the tb because the last workshift's
        # ref time is in the previous day Oct 5
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('06 Oct 2017 00:15', period='D')


    def test_interval_constructor_compound_with_period_partial2(self):
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = clnd.get_interval('06 Oct 2017 00:15', period='D')
        assert ivl.start_time == datetime.datetime(2017, 10, 5, 18, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 6, 0, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 6, 1, 0, 0)
        assert ivl._loc == (15, 15)
        assert len(ivl) == 1

        ivl = clnd.get_interval('06 Oct 2017 20:15', period='D')
        assert ivl._loc == (15, 15)
        with pytest.raises(PartialOutOfBoundsError):
            ivl = clnd.get_interval('06 Oct 2017 00:15', period='D',
                                    clip_period=False)

    def test_interval_constructor_compound_with_period_partial3(self):
        clnd = tb_10_8_6_hours()
        ivl = clnd.get_interval('01 Oct 2017 00:15', period='W')
        # 01 Oct 2017 is Sunday, the last day of the week
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 2, 1, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 2, 2, 0, 0)
        assert ivl._loc == (0, 3)
        assert len(ivl) == 4

        ivl = clnd.get_interval('30 Sep 2017 12:00', period='W')
        assert ivl._loc == (0, 3)
        with pytest.raises(PartialOutOfBoundsError):
            ivl = clnd.get_interval('01 Oct 2017 00:15', period='W',
                                    clip_period=False)

    def test_interval_constructor_compound_with_period_partial4(self):
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = clnd.get_interval('01 Oct 2017 00:15', period='W')
        # 01 Oct 2017 is Sunday, the last day of the week
        assert ivl.start_time == datetime.datetime(2017, 10, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 10, 1, 17, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 10, 1, 18, 0, 0)
        assert ivl._loc == (0, 2)
        assert len(ivl) == 3

        ivl = clnd.get_interval('30 Sep 2017 12:00', period='W')
        assert ivl._loc == (0, 2)
        with pytest.raises(PartialOutOfBoundsError):
            ivl = clnd.get_interval('01 Oct 2017 00:15', period='W',
                                    clip_period=False)


class TestIntervalCompoundCountPeriodsWithLocsNotStraddling(object):

    def test_ivl_compound_count_periods_one_float_right_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (4, 5))
        assert ivl.count_periods('D') == 1.0 / 2.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        assert clnd._timeline._workshift_ref == 'end'
        ivl = Interval(clnd, (4, 5))
        assert ivl.count_periods('D') == 1.0

    def test_ivl_compound_count_periods_one_float_right_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (7, 8))
        assert ivl.count_periods('D', duty='off') == 1.0 / 2.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (7, 8))
        assert ivl.count_periods('D', duty='off') == 2.0 / 2.0

    def test_ivl_compound_count_periods_one_float_right_duty_any(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (1, 2))
        assert ivl.count_periods('D', duty='any') == 2.0 / 4.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (1, 2))
        assert ivl.count_periods('D', duty='any') == 2.0 / 3.0

    def test_ivl_compound_count_periods_one_float_left_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (7, 8))
        assert ivl.count_periods('D') == 1.0 / 1.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (7, 8))
        assert ivl.count_periods('D') == 1.0 / 2.0

    def test_ivl_compound_count_periods_one_float_left_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (4, 5))
        assert ivl.count_periods('D', duty='off') == 1.0 / 1.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (4, 5))
        assert ivl.count_periods('D', duty='off') == 1.0 / 2.0

    def test_ivl_compound_count_periods_many_float_right_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (4, 11))
        assert ivl.count_periods('D') == 2.5
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (4, 11))
        assert ivl.count_periods('D') == 3.0

    def test_ivl_compound_count_periods_many_float_left_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (4, 11))
        assert ivl.count_periods('D', duty='off') == 3.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (4, 11))
        assert ivl.count_periods('D', duty='off') == 2.5

    def test_ivl_compound_count_periods_many_float_left_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (7, 14))
        assert ivl.count_periods('D') == 3.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (7, 14))
        assert ivl.count_periods('D') == 2.5

    def test_ivl_compound_count_periods_many_float_right_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (7, 14))
        assert ivl.count_periods('D', duty='off') == 2.5
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (7, 14))
        assert ivl.count_periods('D', duty='off') == 3.0

    def test_ivl_compound_count_periods_many_float_both_duty_any(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (7, 14))
        assert ivl.count_periods('D', duty='any') == 2.0 + 2.0/3.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (7, 14))
        assert ivl.count_periods('D', duty='any') == 2.0 + 2.0/3.0


class TestIntervalCompoundCountPeriodsWithLocsStraddling(object):

    def test_ivl_compound_count_periods_straddle_float_left_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (6, 8))
        assert ivl.count_periods('D') == 1.0 / 2.0 + 1.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (6, 8))
        assert ivl.count_periods('D') == 1.0

    def test_ivl_compound_count_periods_straddle_float_left_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (9, 11))
        assert ivl.count_periods('D', duty='off') == 1.0 / 2.0 + 1.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (9, 11))
        assert ivl.count_periods('D', duty='off') == 1.0

    def test_ivl_compound_count_periods_straddle_float_right_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (4, 6))
        assert ivl.count_periods('D') == 1.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (4, 6))
        assert ivl.count_periods('D') == 1.0 + 1.0 / 2.0

    def test_ivl_compound_count_periods_straddle_float_right_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (7, 9))
        assert ivl.count_periods('D', duty='off') == 1.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (7, 9))
        assert ivl.count_periods('D', duty='off') == 1.0 + 1.0 / 2.0

    def test_ivl_compound_count_periods_many_straddle_both_ends_duty_on(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (3, 12))
        assert ivl.count_periods('D') == 3.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (3, 12))
        assert ivl.count_periods('D') == 3.0 + 1.0 / 2.0

    def test_ivl_compound_count_periods_many_straddle_both_ends_duty_off(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (3, 12))
        assert ivl.count_periods('D', duty='off') == 1.0 / 2.0 + 3.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (3, 12))
        assert ivl.count_periods('D', duty='off') == 3.0

    def test_ivl_compound_count_periods_many_straddle_both_ends_duty_any(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (3, 12))
        assert ivl.count_periods('D', duty='any') == 1.0 / 4.0 + 3.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (3, 12))
        assert ivl.count_periods('D', duty='any') > 3.0 + 0.3332
        assert ivl.count_periods('D', duty='any') < 3.0 + 0.3334


class TestIntervalCompoundCountPeriodsOOB(object):

    def test_ivl_compound_count_periods_OOB(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (0, 2))
        with pytest.raises(PartialOutOfBoundsError):
            ivl.count_periods('W')

    def test_ivl_compound_count_periods_OOB_floating(self):
        clnd = tb_10_8_6_hours()
        ivl = Interval(clnd, (14, 15))
        assert ivl.count_periods('D', duty='off') == 1.0 / 2.0
        clnd = tb_10_8_6_hours(workshift_ref='end')
        ivl = Interval(clnd, (14, 15))
        with pytest.raises(PartialOutOfBoundsError):
            ivl.count_periods('D', duty='off')

