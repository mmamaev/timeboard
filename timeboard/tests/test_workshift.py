import timeboard as tb
from timeboard.workshift import Workshift
from timeboard.exceptions import OutOfBoundsError
from timeboard.timeboard import _Location, LOC_WITHIN, OOB_LEFT, OOB_RIGHT
from timeboard.core import get_timestamp

import datetime
import pytest
import pandas as pd

@pytest.fixture(scope='module')
def tb_12_days():
    return tb.Timeboard(base_unit_freq='D',
                        start='31 Dec 2016', end='12 Jan 2017',
                        layout=[0, 1, 0])
    # 31  01  02  03  04  05  06  07  08  09  10  11  12
    #  0   1   0   0   1   0   0   1   0   0   1   0   0

class TestWorkshiftConstructor(object):

    def test_locate(self):
        clnd = tb_12_days()
        loc = clnd._locate('04 Jan 2017')
        assert loc == _Location(4, LOC_WITHIN)

    def test_locate_outside(self):
        clnd = tb_12_days()
        loc = clnd._locate('13 Jan 2017')
        assert loc == _Location(None, OOB_RIGHT)
        loc = clnd._locate('30 Dec 2016')
        assert loc == _Location(None, OOB_LEFT)

    def test_locate_bad_ts(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd._locate('33 Dec 2016')
        with pytest.raises(ValueError):
            clnd._locate('bad timestamp')


    def test_workshift_constructor(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift('04 Jan 2017')
        assert ws._loc == 4
        assert ws.start_time == datetime.datetime(2017, 1, 4, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 4, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 5, 0, 0, 0)
        assert ws.label == 1
        assert ws.is_on_duty
        assert not ws.is_off_duty
        assert not ws.is_void
        assert ws.duration == 1

        wsx = clnd('04 Jan 2017')
        assert wsx._loc == ws._loc

    def test_workshift_constructor_from_ts(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift(pd.Timestamp('04 Jan 2017 15:00'))
        assert ws._loc == 4
        assert ws.start_time == datetime.datetime(2017, 1, 4, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 4, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 5, 0, 0, 0)
        assert ws.label == 1
        assert ws.is_on_duty
        assert not ws.is_off_duty
        assert not ws.is_void
        assert ws.duration == 1

        wsx = clnd(pd.Timestamp('04 Jan 2017 15:00'))
        assert wsx._loc == ws._loc

    def test_workshift_constructor_from_datetime(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift(datetime.datetime(2017,1,4,15,0,0))
        assert ws._loc == 4
        assert ws.start_time == datetime.datetime(2017, 1, 4, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 4, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 5, 0, 0, 0)
        assert ws.label == 1
        assert ws.is_on_duty
        assert not ws.is_off_duty
        assert not ws.is_void
        assert ws.duration == 1

        wsx = clnd(datetime.datetime(2017,1,4,15,0,0))
        assert wsx._loc == ws._loc

    def test_workshift_constructor_from_pd_period(self):
        clnd = tb_12_days()
        # freq='W' begins in Mon, which is 02 Jan
        ws = clnd.get_workshift(pd.Period('05 Jan 2017', freq='W'))
        assert ws._loc == 2
        assert ws.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 2, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 3, 0, 0, 0)
        assert ws.label == 0
        assert not ws.is_on_duty
        assert ws.is_off_duty
        assert not ws.is_void
        assert ws.duration == 1

        wsx = clnd(pd.Period('05 Jan 2017', freq='W'))
        assert wsx._loc == ws._loc

    def test_workshift_constructor_date_outside(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('14 Jan 2017')

    def test_direct_workshift_constructor_with_bad_loc(self):
        clnd = tb_12_days()
        #with pytest.raises(KeyError):
        get_timestamp(Workshift(clnd, -1, clnd.schedules['_default'])
                             ) ==  datetime.datetime(2017, 1, 12, 0, 0, 0)
        with pytest.raises(OutOfBoundsError):
            Workshift(clnd, 500000000, clnd.schedules['_default'])
        with pytest.raises(TypeError):
            Workshift(clnd, 10.5, clnd.schedules['_default'])
        with pytest.raises(TypeError):
            Workshift(clnd, '05 Jan 2017', clnd.schedules['_default'])

class TestRollForward(object):

    def test_rollforward_trivial_0_to_self(self):
        clnd = tb_12_days()
        ws = clnd('04 Jan 2017')
        new_ws = ws.rollforward()
        assert new_ws._loc == 4


    def test_rollforward_trivial_0_to_next(self):
        clnd = tb_12_days()
        ws = clnd('31 Dec 2016')
        new_ws = ws.rollforward()
        assert new_ws._loc == 1

    def test_rollforward_on_0(self):
        clnd = tb_12_days()
        ws = clnd('01 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollforward(duty=duty)._loc)
        assert new_ws_list == [1, 2, 1, 2, 1, 1]

    def test_rollforward_off_0(self):
        clnd = tb_12_days()
        ws = clnd('02 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollforward(duty=duty)._loc)
        assert new_ws_list == [4, 2, 2, 4, 2, 4]

    def test_rollforward_on_n(self):
        clnd = tb_12_days()
        ws = clnd('04 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollforward(steps=2, duty=duty)._loc)
        assert new_ws_list == [10, 8, 10, 8, 6, 10]

    def test_rollforward_off_n(self):
        clnd = tb_12_days()
        ws = clnd('03 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollforward(steps=2, duty=duty)._loc)
        assert new_ws_list == [10, 6, 6, 10, 5, 10]

    def test_rollforward_on_n_negative(self):
        clnd = tb_12_days()
        ws = clnd('10 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollforward(steps=-2, duty=duty)._loc)
        assert new_ws_list == [4, 8, 4, 8, 8, 4]

    def test_rollforward_off_n_negative(self):
        clnd = tb_12_days()
        ws = clnd('08 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollforward(steps=-2, duty=duty)._loc)
        assert new_ws_list == [4, 5, 5, 4, 6, 4]

    def test_rollforward_n_off_limits(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('10 Jan 2017').rollforward(1)

    def test_rollforward_alt_off_limits(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('11 Jan 2017').rollforward(duty='alt')

    def test_rollforward_n_negative_off_limits(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('01 Jan 2017').rollforward(-1)

    def test_rollforward_no_such_duty(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='31 Dec 2016', end='12 Jan 2017',
                            layout=[0])
        with pytest.raises(OutOfBoundsError):
            clnd('31 Dec 2016').rollforward()

class TestRollBack(object):

    def test_rollback_trivial_0_to_self(self):
        clnd = tb_12_days()
        ws = clnd('04 Jan 2017')
        new_ws = ws.rollback()
        assert new_ws._loc == 4


    def test_rollback_trivial_0_to_next(self):
        clnd = tb_12_days()
        ws = clnd('02 Jan 2017')
        new_ws = ws.rollback()
        assert new_ws._loc == 1

    def test_rollback_on_0(self):
        clnd = tb_12_days()
        ws = clnd('01 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollback(duty=duty)._loc)
        assert new_ws_list == [1, 0, 1, 0, 1, 1]

    def test_rollback_off_0(self):
        clnd = tb_12_days()
        ws = clnd('12 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollback(duty=duty)._loc)
        assert new_ws_list == [10, 12, 12, 10, 12, 10]

    def test_rollback_on_n(self):
        clnd = tb_12_days()
        ws = clnd('10 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollback(steps=2, duty=duty)._loc)
        assert new_ws_list == [4, 6, 4, 6, 8, 4]

    def test_rollback_off_n(self):
        clnd = tb_12_days()
        ws = clnd('11 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollback(steps=2, duty=duty)._loc)
        assert new_ws_list == [4, 8, 8, 4, 9, 4]

    def test_rollback_on_n_negative(self):
        clnd = tb_12_days()
        ws = clnd('04 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollback(steps=-2, duty=duty)._loc)
        assert new_ws_list == [10, 6, 10, 6, 6, 10]

    def test_rollback_off_n_negative(self):
        clnd = tb_12_days()
        ws = clnd('05 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any', 'bad_value'):
            new_ws_list.append(ws.rollback(steps=-2, duty=duty)._loc)
        assert new_ws_list == [10, 8, 8, 10, 7, 10]

    def test_rollback_alt_off_limits(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('31 Dec 2016').rollback(duty='alt')

    def test_rollback_n_off_limits(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('01 Jan 2017').rollback(1)

    def test_rollback_n_negative_off_limits(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            clnd('10 Jan 2017').rollback(-1)

    def test_rollback_only_alt(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='31 Dec 2016', end='12 Jan 2017',
                            layout=[0])
        with pytest.raises(OutOfBoundsError):
            clnd('10 Jan 2017').rollback()

class TestWorkshiftAddSubNumber(object):

    def test_workshift_add_positive_n(self):
        clnd = tb_12_days()
        ws = clnd('02 Jan 2017') + 2
        assert ws._loc == 10

    def test_workshift_add_zero(self):
        clnd = tb_12_days()
        ws0 = clnd('02 Jan 2017')
        addition = 0
        ws = ws0 + addition
        assert ws._loc == 4

    def test_workshift_add_negative_n(self):
        clnd = tb_12_days()
        ws0 = clnd('09 Jan 2017')
        addition = -2
        ws = ws0 + addition
        assert ws._loc == 4

    def test_workshift_sub_positive_n(self):
        clnd = tb_12_days()
        ws = clnd('09 Jan 2017') - 2
        assert ws._loc == 1

    def test_workshift_sub_zero(self):
        clnd = tb_12_days()
        ws0 = clnd('02 Jan 2017')
        addition = 0
        ws = ws0 - addition
        assert ws._loc == 1

    def test_workshift_sub_negative_n(self):
        clnd = tb_12_days()
        ws0 = clnd('02 Jan 2017')
        addition = -2
        ws = ws0 - addition
        assert ws._loc == 7


class TestWorkshiftSubAnotherWS:

    def test_workshift_sub_non_ws(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd('07 Jan 2017') - clnd('01 Jan 2017')

    # def test_workshift_sub_earlier_ws_both_off(self):
    #     clnd = tb_12_days()
    #     result = clnd('09 Jan 2017') - clnd('31 Dec 2016')
    #     assert result == 3
    #
    # def test_workshift_sub_earlier_ws_1st_off(self):
    #     clnd = tb_12_days()
    #     result = clnd('09 Jan 2017') - clnd('01 Jan 2017')
    #     assert result == 2
    #
    # def test_workshift_sub_earlier_ws_both_on(self):
    #     clnd = tb_12_days()
    #     result = clnd('07 Jan 2017') - clnd('01 Jan 2017')
    #     assert result == 2
    #
    # def test_workshift_sub_earlier_ws_2nd_off(self):
    #     clnd = tb_12_days()
    #     result = clnd('07 Jan 2017') - clnd('31 Dec 2016')
    #     assert result == 3
    #
    # def test_workshift_sub_earlier_ws_both_off_zero(self):
    #     clnd = tb_12_days()
    #     result = clnd('06 Jan 2017') - clnd('05 Jan 2017')
    #     assert result == 0
    #
    # def test_workshift_sub_earlier_ws_1st_off_zero(self):
    #     clnd = tb_12_days()
    #     result = clnd('06 Jan 2017') - clnd('04 Jan 2017')
    #     assert result == 0
    #
    # def test_workshift_sub_self_on(self):
    #     clnd = tb_12_days()
    #     result = clnd('07 Jan 2017') - clnd('07 Jan 2017')
    #     assert result == 0
    #
    # def test_workshift_sub_self_off(self):
    #     clnd = tb_12_days()
    #     result = clnd('08 Jan 2017') - clnd('08 Jan 2017')
    #     assert result == 0
    #
    # def test_workshift_sub_later_ws_both_off(self):
    #     clnd = tb_12_days()
    #     result = clnd('08 Jan 2017') - clnd('11 Jan 2017')
    #     #assert result == 0
    #     #TODO: maybe, __sub__ will return abs(difference)?
    #     assert False
    #
    # def test_workshift_sub_later_ws_1st_on(self):
    #     clnd = tb_12_days()
    #     result = clnd('07 Jan 2017') - clnd('11 Jan 2017')
    #     #assert result == 0
    #     #TODO: maybe, __sub__ will return abs(difference)?
    #     assert False

    def test_workshift_sub_non_ws(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd('07 Jan 2017') - datetime.datetime(2017,1,1,0,0,0)


