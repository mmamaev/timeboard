import timeboard as tb
from timeboard.exceptions import OutOfBoundsError
from timeboard.timeboard import _Location, LOC_WITHIN, OOB_LEFT, OOB_RIGHT
from timeboard.core import get_timestamp, Organizer

import datetime
import pytest
import pandas as pd

def tb_12_days():
    org = Organizer(marker='W', structure=[100, [0, 0, 1, 1]])
    return tb.Timeboard(base_unit_freq='D',
                        start='31 Dec 2016', end='12 Jan 2017',
                        layout=org)
    # Dates  31  01  02  03  04  05  06  07  08  09  10  11  12
    # Labels 100 -   0   0   1   1   0   0   1   100 -   -   -
    # WS No. 0       1   2   3   4   5   6   7   8
    # WS Idx 0       2   3   4   5   6   7   8   9

class TestWorkshiftCompoundConstructor(object):

    def test_locate(self):
        clnd = tb_12_days()
        loc = clnd._locate('31 Dec 2016')
        assert loc == _Location(0, LOC_WITHIN)
        loc = clnd._locate('01 Jan 2017')
        assert loc == _Location(0, LOC_WITHIN)
        loc = clnd._locate('04 Jan 2017')
        assert loc == _Location(3, LOC_WITHIN)
        loc = clnd._locate('11 Jan 2017')
        assert loc == _Location(8, LOC_WITHIN)
        loc = clnd._locate('12 Jan 2017')
        assert loc == _Location(8, LOC_WITHIN)

    def test_locate_outside(self):
        clnd = tb_12_days()
        loc = clnd._locate('13 Jan 2017')
        assert loc == _Location(None, OOB_RIGHT)
        loc = clnd._locate('30 Dec 2016')
        assert loc == _Location(None, OOB_LEFT)

    def test_workshift_ordinary_constructor(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift('04 Jan 2017')
        assert ws._loc == 3
        assert ws.start_time == datetime.datetime(2017, 1, 4, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 4, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 5, 0, 0, 0)
        assert ws.label == 1
        assert ws.is_on_duty
        assert ws.duration == 1

        wsx = clnd('04 Jan 2017')
        assert wsx._loc == ws._loc

    def test_workshift_compound_constructor(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift('11 Jan 2017')
        assert ws._loc == 8
        assert ws.start_time == datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 12, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 13, 0, 0, 0)
        assert ws.label == 100
        assert ws.is_on_duty
        assert ws.duration == 4

        wsx = clnd('11 Jan 2017')
        assert wsx._loc == ws._loc
        assert wsx._label == ws._label

    def test_workshift_constructor_compound_at_start(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift('31 Dec 2016')
        assert ws._loc == 0
        assert ws.start_time == datetime.datetime(2016, 12, 31, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 1, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ws.label == 100
        assert ws.is_on_duty
        assert ws.duration == 2

        wsx = clnd('31 Dec 2016')
        assert wsx._loc == ws._loc
        assert wsx._label == ws._label

    def test_workshift_constructor_compound_at_end(self):
        clnd = tb_12_days()
        ws = clnd.get_workshift('12 Jan 2017')
        assert ws._loc == 8
        assert ws.start_time == datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ws.end_time > datetime.datetime(2017, 1, 12, 23, 59, 59)
        assert ws.end_time < datetime.datetime(2017, 1, 13, 0, 0, 0)
        assert ws.label == 100
        assert ws.is_on_duty
        assert ws.duration == 4

        wsx = clnd('12 Jan 2017')
        assert wsx._loc == ws._loc
        assert wsx._label == ws._label


class TestRollForwardCompound(object):

    def test_rollforward_trivial_0_to_self(self):
        clnd = tb_12_days()
        ws = clnd('31 Dec 2016')
        new_ws = ws.rollforward()
        assert new_ws._loc == 0
        ws = clnd('04 Jan 2017')
        new_ws = ws.rollforward()
        assert new_ws._loc == 3
        ws = clnd('11 Jan 2017')
        new_ws = ws.rollforward()
        assert new_ws._loc == 8
        ws = clnd('12 Jan 2017')
        new_ws = ws.rollforward()
        assert new_ws._loc == 8

    def test_rollforward_trivial_0_to_next(self):
        org = Organizer(marker='W', structure=[False, [0, 0, 1, 1]])
        clnd =  tb.Timeboard(base_unit_freq='D',
                            start='31 Dec 2016', end='12 Jan 2017',
                            layout=org)
        ws = clnd('31 Dec 2016')
        new_ws = ws.rollforward()
        assert new_ws._loc == 3
        ws = clnd('03 Jan 2017')
        new_ws = ws.rollforward()
        assert new_ws._loc == 3

    def test_rollforward_on_0(self):
        clnd = tb_12_days()
        ws = clnd('31 Dec 2016')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollforward(duty=duty)._loc)
        assert new_ws_list == [0, 1, 0, 1, 0]
        assert ws.rollforward(duty='off').start_time == get_timestamp('02 Jan '
                                                                   '2017')
        ws1 = clnd('01 Jan 2017')
        assert ws1.rollforward(duty='off').start_time == get_timestamp('02 Jan '
                                                                      '2017')

    def test_rollforward_off_0(self):
        org = Organizer(marker='W', structure=[False, [0, 0, 1, 1]])
        clnd =  tb.Timeboard(base_unit_freq='D',
                            start='31 Dec 2016', end='12 Jan 2017',
                            layout=org)
        ws = clnd('31 Dec 2016')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollforward(duty=duty)._loc)
        assert new_ws_list == [3, 0, 0, 3, 0]

    def test_rollforward_on_n(self):
        clnd = tb_12_days()
        ws = clnd('31 Dec 2016')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollforward(steps=2, duty=duty)._loc)
        assert new_ws_list == [4, 5, 4, 5, 2]

    def test_rollforward_off_n(self):
        org = Organizer(marker='W', structure=[False, [0, 0, 1, 1]])
        clnd =  tb.Timeboard(base_unit_freq='D',
                            start='31 Dec 2016', end='12 Jan 2017',
                            layout=org)
        ws = clnd('31 Dec 2016')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollforward(steps=2, duty=duty)._loc)
        assert new_ws_list == [7, 2, 2, 7, 2]

    def test_rollforward_on_n_negative_from_last_element(self):
        clnd = tb_12_days()
        ws = clnd('11 Jan 2017')
        assert ws.rollforward(steps=-2, duty='on')._loc == 4
        assert ws.rollforward(steps=-2, duty='any')._loc == 6
        with pytest.raises(OutOfBoundsError):
            ws.rollforward(steps=-2, duty='off')


class TestRollBackCompound(object):

    def test_rollback_trivial_0_to_self(self):
        clnd = tb_12_days()
        ws = clnd('11 Jan 2017')
        new_ws = ws.rollback()
        assert new_ws._loc == 8
        ws = clnd('12 Jan 2017')
        new_ws = ws.rollback()
        assert new_ws._loc == 8


    def test_rollback_trivial_0_to_next(self):
        clnd = tb_12_days()
        ws = clnd('02 Jan 2017')
        new_ws = ws.rollback()
        assert new_ws._loc == 0
        assert new_ws.start_time == get_timestamp('31 Dec 2016')

    def test_rollback_on_0(self):
        clnd = tb_12_days()
        ws = clnd('10 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollback(duty=duty)._loc)
        assert new_ws_list == [8, 6, 8, 6, 8]

    def test_rollback_off_0(self):
        org = Organizer(marker='W', structure=[False, [0, 0, 1, 1]])
        clnd =  tb.Timeboard(base_unit_freq='D',
                            start='31 Dec 2016', end='12 Jan 2017',
                            layout=org)
        ws = clnd('12 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollback(duty=duty)._loc)
        assert new_ws_list == [7, 8, 8, 7, 8]

    def test_rollback_on_n(self):
        clnd = tb_12_days()
        ws = clnd('11 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollback(steps=2, duty=duty)._loc)
        assert new_ws_list == [4, 2, 4, 2, 6]

    def test_rollback_off_n(self):
        clnd = tb_12_days()
        ws = clnd('07 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollback(steps=2, duty=duty)._loc)
        assert new_ws_list == [0, 2, 2, 0, 4]

    def test_rollback_on_n_negative(self):
        clnd = tb_12_days()
        ws = clnd('05 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollback(steps=-2, duty=duty)._loc)
        assert new_ws_list == [8, 6, 8, 6, 6]

    def test_rollback_off_n_negative(self):
        clnd = tb_12_days()
        ws = clnd('03 Jan 2017')
        new_ws_list = []
        for duty in ('on', 'off', 'same', 'alt', 'any'):
            new_ws_list.append(ws.rollback(steps=-2, duty=duty)._loc)
        assert new_ws_list == [4, 6, 6, 4, 4]





