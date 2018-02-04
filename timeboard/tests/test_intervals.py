import timeboard as tb
from timeboard.interval import Interval
from timeboard.workshift import Workshift
from timeboard.exceptions import OutOfBoundsError, VoidIntervalError
from timeboard.timeboard import _Location, OOB_LEFT, OOB_RIGHT, LOC_WITHIN

import datetime
import pandas as pd
import pytest

@pytest.fixture(scope='module')
def tb_12_days():
    return tb.Timeboard(base_unit_freq='D',
                        start='31 Dec 2016', end='12 Jan 2017',
                        layout=[0, 1, 0])
    # 31  01  02  03  04  05  06  07  08  09  10  11  12
    #  0   1   0   0   1   0   0   1   0   0   1   0   0


class TestIntervalLocatorFromReference:

    def test_interval_locator_default(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
            None, False, False) == [_Location(0, LOC_WITHIN),
                                    _Location(12, LOC_WITHIN)]

    def test_interval_locator_with_two_ts(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
            ('02 Jan 2017 15:00', '08 Jan 2017 15:00'), False, False) == [
            _Location(2, LOC_WITHIN), _Location(8, LOC_WITHIN)]
        # reverse is ok; it is taken care later in 'get_interval'
        assert clnd._get_interval_locs_from_reference(
            ('08 Jan 2017 15:00', '02 Jan 2017 15:00'), False, False) == [
            _Location(8, LOC_WITHIN), _Location(2, LOC_WITHIN)]

    def test_interval_locator_with_with_excessive_item(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
            ('02 Jan 2017 15:00','08 Jan 2017 15:00','something'), False,
            False) == [_Location(2, LOC_WITHIN), _Location(8, LOC_WITHIN)]

    def test_interval_locator_with_two_pd_ts(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
                                (pd.Timestamp('02 Jan 2017 15:00'),
                                 pd.Timestamp('08 Jan 2017 15:00')),
                                False, False) == [
                            _Location(2, LOC_WITHIN), _Location(8, LOC_WITHIN)]

    def test_interval_locator_with_two_datettime_ts(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
                (datetime.datetime(2017, 1, 2, 15, 0, 0),
                 datetime.datetime(2017, 1, 8, 15, 0, 0)),
                False, False) == [
            _Location(2, LOC_WITHIN), _Location(8, LOC_WITHIN)]

    def test_interval_locator_with_OOB_ts(self):
        clnd = tb_12_days()
        # only one end of the interval is OOB
        assert clnd._get_interval_locs_from_reference(
            ('02 Jan 2017 15:00', '13 Jan 2017 15:00'), False, False) == [
            _Location(2, LOC_WITHIN), _Location(None, OOB_RIGHT)]
        assert clnd._get_interval_locs_from_reference(
            ('30 Dec 2016 15:00', '08 Jan 2017 15:00'), False, False) == [
            _Location(None, OOB_LEFT), _Location(8, LOC_WITHIN)]
        # the interval spans over the timeboard
        assert clnd._get_interval_locs_from_reference(
            ('30 Dec 2016 15:00', '13 Jan 2017 15:00'), False, False) == [
            _Location(None, OOB_LEFT), _Location(None, OOB_RIGHT)]
        assert clnd._get_interval_locs_from_reference(
            ('13 Jan 2017 15:00', '30 Dec 2016 15:00'), False, False) == [
            _Location(None, OOB_RIGHT), _Location(None, OOB_LEFT)]
        # the interval is completely outside the timeboard
        assert clnd._get_interval_locs_from_reference(
            ('25 Dec 2016 15:00', '30 Dec 2016 15:00'), False, False) == [
            _Location(None, OOB_LEFT), _Location(None, OOB_LEFT)]
        assert clnd._get_interval_locs_from_reference(
            ('30 Dec 2016 15:00', '25 Dec 2016 15:00'), False, False) == [
            _Location(None, OOB_LEFT), _Location(None, OOB_LEFT)]
        assert clnd._get_interval_locs_from_reference(
            ('13 Jan 2017 15:00', '15 Jan 2017 15:00'), False, False) == [
            _Location(None, OOB_RIGHT), _Location(None, OOB_RIGHT)]
        assert clnd._get_interval_locs_from_reference(
            ('15 Jan 2017 15:00', '13 Jan 2017 15:00'), False, False) == [
            _Location(None, OOB_RIGHT), _Location(None, OOB_RIGHT)]

    def test_interval_locator_from_pd_periods(self):
        clnd = tb_12_days()
        # if we could not directly Timestamp() a reference, we try to call its
        # `to_timestamp` method which would return reference's start time

        # First day of Jan is inside clnd
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('02 Jan 2017', freq='M'), '11 Jan 2017 15:00'),
            False, False) == [
            _Location(1, LOC_WITHIN), _Location(11, LOC_WITHIN)]
        # While 31 Dec is within clnd, the first day of Dec is outside
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('31 Dec 2016', freq='M'), '11 Jan 2017 15:00'),
            False, False) == [
            _Location(None, OOB_LEFT), _Location(11, LOC_WITHIN)]
        # freq=W begins weeks on Mon which is 02 Jan 2017
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('05 Jan 2017', freq='W'), '11 Jan 2017 15:00'),
            False, False) == [
            _Location(2, LOC_WITHIN), _Location(11, LOC_WITHIN)]
        # freq=W-MON ends weeks on Mondays, and 02 Jan is Monday,
        # but this week begins on Tue 27 Dec 2016 which is outside the timeboard
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('02 Jan 2017', freq='W-MON'), '11 Jan 2017 15:00'),
            False, False) == [
            _Location(None, OOB_LEFT), _Location(11, LOC_WITHIN)]


    def test_interval_locator_with_bad_ts(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd._get_interval_locs_from_reference(
                ('bad_timestamp', '08 Jan 2017 15:00'), False, False)
        with pytest.raises(ValueError):
            clnd._get_interval_locs_from_reference(
                ('02 Jan 2017 15:00', 'bad_timestamp'), False, False)

    def test_interval_locator_with_singletons(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd._get_interval_locs_from_reference(('08 Jan 2017 15:00',),
                                                   False, False)
        with pytest.raises(TypeError):
            clnd._get_interval_locs_from_reference('08 Jan 2017 15:00',
                                                   False, False)
        with pytest.raises(TypeError):
            clnd._get_interval_locs_from_reference(
                pd.Timestamp('08 Jan 2017 15:00'), False, False)


class TestIntervalStripLocs:

    def test_interval_strip_locs(self):
        clnd = tb_12_days()
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(8, 'whatever')], False, False) \
            == [_Location(2,'anything'),_Location(8, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(8, 'whatever')], True, False) \
            == [_Location(3,'anything'),_Location(8, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(8, 'whatever')], False, True) \
            == [_Location(2,'anything'),_Location(7, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(8, 'whatever')], True, True) \
            == [_Location(3,'anything'),_Location(7, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(4, 'whatever')], True, True) \
            == [_Location(3,'anything'),_Location(3, 'whatever')]


    def test_interval_strip_locs_single_unit(self):
        clnd = tb_12_days()
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(2, 'whatever')], False, False) \
            == [_Location(2,'anything'),_Location(2, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(2, 'whatever')], True, False) \
            == [_Location(3,'anything'),_Location(2, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(2, 'whatever')], False, True) \
            == [_Location(2,'anything'),_Location(1, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(2, 'whatever')], True, True) \
            == [_Location(3,'anything'),_Location(1, 'whatever')]

    def test_interval_strip_locs_corner_cases(self):
        clnd = tb_12_days()
        assert clnd._strip_interval_locs(
            [_Location(0, 'anything'), _Location(0, 'whatever')], True, True) \
            == [_Location(1, 'anything'), _Location(-1, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(-4, 'anything'), _Location(-2, 'whatever')], True, True) \
            == [_Location(-3, 'anything'), _Location(-3, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(None,'anything'),_Location(2, 'whatever')], False, False) \
            == [_Location(None,'anything'),_Location(2, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(None,'anything'),_Location(2, 'whatever')], True, False) \
            == [_Location(None,'anything'),_Location(2, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(None,'anything'),_Location(2, 'whatever')], False, True) \
            == [_Location(None,'anything'),_Location(1, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(2,'anything'),_Location(None, 'whatever')], True, True) \
            == [_Location(3,'anything'),_Location(None, 'whatever')]
        assert clnd._strip_interval_locs(
            [_Location(None,'anything'),_Location(None, 'whatever')], True, True) \
            == [_Location(None,'anything'),_Location(None, 'whatever')]


    def test_interval_strip_locs_bad_locs(self):
        # in '_strip_interval_locs' we do not care about validity of 'locs'
        # type and value; other parts of 'get_interval' should care about this
        assert True

    def test_get_interval_with_bad_closed(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd.get_interval(closed='010')
        with pytest.raises(ValueError):
            clnd.get_interval(closed=True)


class TestIntervalConstructorWithTS:

    def test_interval_constructor_with_two_ts(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7
        assert ivl.labels == [0, 0, 1, 0, 0, 1, 0]

        ivlx = clnd(('02 Jan 2017 15:00', '08 Jan 2017 15:00'))
        assert ivlx._loc == ivl._loc

    def test_interval_iterator(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'))
        wslist1 = []
        for ws in ivl:
            wslist1.append(ws)
        wslist2 = list(ivl)
        assert len(wslist1) == 7
        assert len(wslist2) == 7
        for i in range(7):
            assert isinstance(wslist1[i], Workshift)
            assert isinstance(wslist2[i], Workshift)
            assert wslist1[i]._loc == i+2
            assert wslist1[i]._loc == i+2

    def test_interval_constructor_with_two_ts_open_ended(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='11')
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

        ivlx = clnd(('02 Jan 2017 15:00', '08 Jan 2017 15:00'), closed='11')
        assert ivlx._loc == ivl._loc

        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='01')
        assert ivl._loc == (3,8)
        assert len(ivl) == 6
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='10')
        assert ivl._loc == (2,7)
        assert len(ivl) == 6
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='00')
        assert ivl._loc == (3,7)
        assert len(ivl) == 5
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '03 Jan 2017 15:00'),
                                closed='01')
        assert ivl._loc == (3,3)
        assert len(ivl) == 1
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '03 Jan 2017 15:00'),
                                closed='10')
        assert ivl._loc == (2,2)
        assert len(ivl) == 1

    def test_interval_constructor_with_closed_leads_to_void(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'))
        assert ivl._loc == (2,2)
        assert len(ivl) == 1
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'),
                              closed='01')
        with pytest.raises(VoidIntervalError):
            clnd(('02 Jan 2017 15:00', '02 Jan 2017 15:00'), closed='01')
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'),
                              closed='10')
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'),
                              closed='00')
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('02 Jan 2017 15:00', '03 Jan 2017 15:00'),
                              closed='00')

    def test_interval_constructor_with_OOB_ts(self):
        clnd = tb_12_days()
        # only one end of the interval is OOB
        with pytest.raises(OutOfBoundsError):
            ivl = clnd.get_interval(('02 Jan 2017 15:00', '13 Jan 2017 15:00'))
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('02 Jan 2017 15:00', '13 Jan 2017 15:00'),
                              clip_period=False)
        with pytest.raises(OutOfBoundsError):
            clnd(('02 Jan 2017 15:00', '13 Jan 2017 15:00'),
                              clip_period=False)
        with pytest.raises(OutOfBoundsError):
            ivl = clnd.get_interval(('30 Dec 2016 15:00', '08 Jan 2017 15:00'))
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('30 Dec 2016 15:00', '08 Jan 2017 15:00'),
                              clip_period=False)
        # the interval spans over the timeboard
        with pytest.raises(OutOfBoundsError):
            ivl = clnd.get_interval(('30 Dec 2016 15:00', '13 Jan 2017 15:00'))
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('30 Dec 2016 15:00', '13 Jan 2017 15:00'),
                              clip_period=False)
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('13 Jan 2017 15:00', '30 Dec 2016 15:00'))
        # the interval is completely outside the timeboard
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('25 Dec 2016 15:00', '30 Dec 2016 15:00'))
        # OOBError is ok, since we cannot clip a complete outsider anyway
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('30 Dec 2016 15:00', '25 Dec 2016 15:00'))
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('13 Jan 2017 15:00', '15 Jan 2017 15:00'))
        # OOBError is ok, since we cannot clip a complete outsider anyway
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('15 Jan 2017 15:00', '13 Jan 2017 15:00'))

    def test_interval_constructor_with_same_ts(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 2, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 3, 0, 0, 0)
        assert ivl._loc == (2,2)
        assert len(ivl) == 1

    def test_interval_constructor_reverse_ts_to_same_BU(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 10:00'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 2, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 3, 0, 0, 0)
        assert ivl._loc == (2,2)
        assert len(ivl) == 1

    def test_interval_constructor_reverse_ts(self):
        clnd = tb_12_days()
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('08 Jan 2017 15:00', '02 Jan 2017 15:00'))
        with pytest.raises(VoidIntervalError):
            clnd(('08 Jan 2017 15:00', '02 Jan 2017 15:00'))

    def test_interval_constructor_two_pd_periods_as_ts(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                        start='31 Dec 2016', end='31 Mar 2017',
                        layout=[0, 1, 0])
        ivl = clnd.get_interval((pd.Period('05 Jan 2017 15:00', freq='M'),
                                 pd.Period('19 Feb 2017 15:00', freq='M')))
        assert ivl.start_time == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 2, 1, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 2, 2, 0, 0, 0)
        assert ivl._loc == (1,32)
        assert len(ivl) == 32

        ivlx = clnd((pd.Period('05 Jan 2017 15:00', freq='M'),
                     pd.Period('19 Feb 2017 15:00', freq='M')))
        assert ivlx._loc == ivl._loc


class TestIntervalConstructorDefault:

    def test_interval_constructor_default(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval()
        assert ivl.start_time == datetime.datetime(2016, 12, 31, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 12, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 13, 0, 0, 0)
        assert ivl._loc == (0,12)
        assert len(ivl) == 13
        assert ivl.labels == [0] + [1, 0, 0] * 4

    def test_interval_constructor_default_open_ended(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(closed='00')
        assert ivl.start_time == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 11, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 12, 0, 0, 0)
        assert ivl._loc == (1,11)
        assert len(ivl) == 11

    def test_interval_constructor_default_closed_leads_to_void(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='01 Jan 2017', end='01 Jan 2017',
                            layout=[1])
        with pytest.raises(VoidIntervalError):
            ivl = clnd.get_interval(closed='01')
        with pytest.raises(VoidIntervalError):
            ivl = clnd.get_interval(closed='10')
        with pytest.raises(VoidIntervalError):
            ivl = clnd.get_interval(closed='00')


class TestIntervalConstructorFromPeriod:

    def test_interval_constructor_with_period(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('02 Jan 2017 15:00', period='W')
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

        ivlx = clnd('02 Jan 2017 15:00', period='W')
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_with_OOB_period(self):
        clnd = tb_12_days()
        #period is defined by good ts but extends beyond the left bound of clnd
        ivl = clnd.get_interval('01 Jan 2017 15:00', period='W')
        assert ivl._loc == (0, 1)
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('01 Jan 2017 15:00', period='W',
                              clip_period=False)
        with pytest.raises(OutOfBoundsError):
            clnd('01 Jan 2017 15:00', period='W',
                              clip_period=False)
        #same period defined by outside ts
        ivl = clnd.get_interval('26 Dec 2016 15:00', period='W')
        assert ivl._loc == (0, 1)
        #period is defined by good ts but extends beyond the right bound of clnd
        ivl = clnd.get_interval('10 Jan 2017 15:00', period='W')
        assert ivl._loc == (9, 12)
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('10 Jan 2017 15:00', period='W',
                              clip_period=False)
        #same period defined by outside ts
        ivl = clnd.get_interval('14 Jan 2017 15:00', period='W')
        assert ivl._loc == (9, 12)
        #period spans over clnd (a year ending on 31 March)
        ivl = clnd.get_interval('10 Mar 2017 15:00', period='A-MAR')
        assert ivl._loc == (0, 12)
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('10 Mar 2017 15:00', period='A-MAR',
                              clip_period=False)
        #period is completely outside clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('18 Jan 2017 15:00', period='W')

    def test_interval_constructor_with_bad_period(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd.get_interval('02 Jan 2017 15:00', period='bad_period')
        with pytest.raises(ValueError):
            clnd('02 Jan 2017 15:00', period='bad_period')
        with pytest.raises(ValueError):
            clnd.get_interval('bad_timestamp', period='W')

    def test_interval_constructor_from_pd_period(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(pd.Period('05 Jan 2017 15:00', freq='W'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2, 8)
        assert len(ivl) == 7

        # if we call timeboard instance directly, it cannot figure that we
        # want a period, as only one argument is given and it can be converted
        # to a timestamp
        ws = clnd(pd.Period('05 Jan 2017 15:00', freq='W'))
        assert ws._loc == 2

    def test_interval_constructor_from_pd_period_OOB(self):
        clnd = tb_12_days()
        # period defined by good ts but extends beyond the reight bound of clnd
        ivl = clnd.get_interval(pd.Period('10 Jan 2017 15:00', freq='W'))
        assert ivl._loc == (9, 12)
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('10 Jan 2017 15:00', freq='W'),
                              clip_period=False)
        # period defined by good ts but extends beyond the left bound of clnd
        ivl = clnd.get_interval(pd.Period('01 Jan 2017 15:00', freq='W'))
        assert ivl._loc == (0, 1)
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('01 Jan 2017 15:00', freq='W'),
                              clip_period=False)
        # period overlapping clnd
        ivl = clnd.get_interval(pd.Period('08 Mar 2017 15:00', freq='A-MAR'))
        assert ivl._loc == (0, 12)
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('08 Mar 2017 15:00', freq='A-MAR'),
                              clip_period=False)
        # period completely outside clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('25 Jan 2017 15:00', freq='W'))

    def test_interval_constructor_period_smaller_than_bu(self):
        clnd = tb.Timeboard(base_unit_freq='H',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=[0, 1],
                         )
        clnd2 = tb.Timeboard(base_unit_freq='H',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=[0, 1],
                         workshift_ref='end'
                         )
        # no ws reference time falls within this period:
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('04 Oct 2017 01:15', period='T')
        with pytest.raises(VoidIntervalError):
            clnd2.get_interval('04 Oct 2017 01:15', period='T')

        # reference time of clnd.ws 1 (01:00) falls within this period:
        ivl = clnd.get_interval('04 Oct 2017 01:00', period='T')
        assert ivl._loc == (1, 1)
        # but not within this
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('04 Oct 2017 01:59', period='T')

        # vice versa for clnd 2
        with pytest.raises(VoidIntervalError):
            clnd2.get_interval('04 Oct 2017 01:00', period='T')
        ivl = clnd2.get_interval('04 Oct 2017 01:59', period='T')
        assert ivl._loc == (1, 1)


    def test_interval_constructor_period_straddles_2_ws(self):
        shifts = tb.Organizer(marker='90T', structure=[0, 1, 0, 2])
        clnd = tb.Timeboard(base_unit_freq='T',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=shifts,
                         )
        # period straddles ws 0 and 1
        # but only ref time of ws 1 falls into the period
        ivl = clnd.get_interval('04 Oct 2017 01:00', period='H')
        assert ivl._loc == (1, 1)

    def test_interval_constructor_period_start_aligned_end_inside_ws(self):
        shifts = tb.Organizer(marker='90T', structure=[0, 1, 0, 2])
        clnd = tb.Timeboard(base_unit_freq='T',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=shifts,
                         )
        # period (00:00 - 00:59) is inside ws 0 (00:00 - 01:29)
        # ref time of ws 0 falls into the period
        ivl = clnd.get_interval('04 Oct 2017 00:00', period='H')
        assert ivl._loc == (0, 0)

        # now ref time is end time and ws 0 ref time is outside the period
        clnd = tb.Timeboard(base_unit_freq='T',
                            start='04 Oct 2017', end='04 Oct 2017 23:59',
                            layout=shifts,
                            workshift_ref='end'
                            )
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('04 Oct 2017 00:00', period='H')


    def test_interval_constructor_period_begin_inside_ws_end_aligned(self):
        shifts = tb.Organizer(marker='90T', structure=[0, 1, 0, 2])
        clnd = tb.Timeboard(base_unit_freq='T',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=shifts,
                         )
        # period (02:00 - 02:59) is inside ws 1 (01:30 - 02:59)
        # ref time of ws 1 is outside the period
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('04 Oct 2017 02:00', period='H')

        # now ref time is end time and ws 1 ref time is within the period
        clnd = tb.Timeboard(base_unit_freq='T',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=shifts,
                         workshift_ref='end'
                         )

        ivl = clnd.get_interval('04 Oct 2017 02:00', period='H')
        assert ivl._loc == (1, 1)

    def test_interval_constructor_period_entirely_inside_ws(self):
        shifts = tb.Organizer(marker='3H', structure=[0, 1, 0, 2])
        clnd = tb.Timeboard(base_unit_freq='T',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=shifts,
                         )
        # period (04:00 - 04:59) is inside workshift  (03:00 - 05:59)
        # and does not includes workshift's start or end times.
        # No matter if the ref time is 'start' or 'end',
        # it is outside the period
        with pytest.raises(VoidIntervalError):
           clnd.get_interval('04 Oct 2017 04:00', period='H')

        clnd = tb.Timeboard(base_unit_freq='T',
                         start='04 Oct 2017', end='04 Oct 2017 23:59',
                         layout=shifts,
                         workshift_ref='end'
                         )
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('04 Oct 2017 04:00', period='H')

        # if we supported workshift_ref being somewhere in the middle of
        # workshift, an interval could be constructed


class TestIntervalConstructorWithLength:

    def test_interval_constructor_with_length(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('02 Jan 2017 15:00', length=7)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

        ivlx = clnd('02 Jan 2017 15:00', length=7)
        assert ivlx._loc == ivl._loc

    def test_interval_constructor_with_negative_length(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('08 Jan 2017 15:00', length=-7)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

    def test_interval_constructor_with_length_one(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('02 Jan 2017 15:00', length=1)
        assert ivl._loc == (2,2)
        assert len(ivl) == 1
        ivl = clnd.get_interval('02 Jan 2017 15:00', length=-1)
        assert ivl._loc == (2,2)
        assert len(ivl) == 1

    def test_interval_constructor_with_zero_length(self):
        # same treatment as interval with reverse timestamps
        clnd = tb_12_days()
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('08 Jan 2017 15:00', length=0)
        with pytest.raises(VoidIntervalError):
            clnd('08 Jan 2017 15:00', length=0)

    def test_interval_constructor_with_length_OOB(self):
        clnd = tb_12_days()
        # May be build interval from the portion falling inside clnd?
        # NO. You either get an expected result or an exception, not
        # some other interval you did not ask for
        #
        # starts inside clnd, ends OOB
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('02 Jan 2017 15:00', length=20)
        with pytest.raises(OutOfBoundsError):
            clnd('02 Jan 2017 15:00', length=20)
        # starts OOB, ends inside clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('30 Dec 2016 15:00', length=10)
        # starts and ends OOB, spans over clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('30 Dec 2016 15:00', length=20)
        # completely outside clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('20 Jan 2017 15:00', length=10)

    def test_interval_constructor_with_bad_length(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd.get_interval('02 Jan 2017 15:00', length=5.5)
        with pytest.raises(TypeError):
            clnd('02 Jan 2017 15:00', length=5.5)
        with pytest.raises(TypeError):
            clnd.get_interval('02 Jan 2017 15:00', length='x')
        with pytest.raises(ValueError):
            clnd.get_interval('bad_timestamp', length=5)


class TestIntervalConstructorBadArgs:

    def test_interval_constructor_bad_arg_combinations(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd.get_interval('01 Jan 2017')
        with pytest.raises(TypeError):
            clnd.get_interval(('01 Jan 2017',))
        with pytest.raises(TypeError):
            clnd.get_interval('01 Jan 2017', '05 Jan 2017')
        with pytest.raises(TypeError):
            clnd.get_interval(('01 Jan 2017',), length=1)
        with pytest.raises(TypeError):
            clnd.get_interval(('anyhting', 'anything'), length=1)
        with pytest.raises(TypeError):
            clnd.get_interval(('02 Jan 2017',), period='W')
        with pytest.raises(TypeError):
            clnd.get_interval(('anyhting', 'anything'), period='W')
        with pytest.raises(TypeError):
            clnd.get_interval('anyhting', length=1, period='W')
        with pytest.raises(TypeError):
            clnd.get_interval(('anyhting', 'anything'), length=1, period='W')
        with pytest.raises(TypeError):
            clnd.get_interval(length=1, period='W')

    def test_interval_constructor_bad_arg_combinations_2(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd(('01 Jan 2017',))
        with pytest.raises(TypeError):
            clnd('01 Jan 2017', '05 Jan 2017')
        with pytest.raises(TypeError):
            clnd(('01 Jan 2017',), length=1)
        with pytest.raises(TypeError):
            clnd(('anyhting', 'anything'), length=1)
        with pytest.raises(TypeError):
            clnd(('02 Jan 2017',), period='W')
        with pytest.raises(TypeError):
            clnd(('anyhting', 'anything'), period='W')
        with pytest.raises(TypeError):
            clnd('anyhting', length=1, period='W')
        with pytest.raises(TypeError):
            clnd(('anyhting', 'anything'), length=1, period='W')
        with pytest.raises(TypeError):
            clnd(length=1, period='W')

class TestIntervalConstructorDirect:

    def test_interval_direct_with_locs(self):
        clnd = tb_12_days()
        ivl = Interval(clnd, (2, 8), clnd.default_schedule)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

    def test_interval_direct_with_ws(self):
        clnd = tb_12_days()
        ivl = Interval(clnd,
                       (clnd('02 Jan 2017'), clnd('08 Jan 2017')),
                        clnd.default_schedule)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

    def test_interval_direct_mixed_args(self):
        clnd = tb_12_days()
        ivl = Interval(clnd, (2, clnd('08 Jan 2017')),
                       clnd.default_schedule)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert len(ivl) == 7

    def test_interval_direct_same_locs(self):
        clnd = tb_12_days()
        ivl = Interval(clnd, (2, 2), clnd.default_schedule)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 2, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 3, 0, 0, 0)
        assert ivl._loc == (2,2)
        assert len(ivl) == 1

    def test_interval_direct_reverse_locs(self):
        clnd = tb_12_days()
        with pytest.raises(VoidIntervalError):
            Interval(clnd, (8, 2), clnd.default_schedule)

    def test_interval_direct_OOB_locs(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (-1, 2), clnd.default_schedule)
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (8, 13), clnd.default_schedule)
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (-1, 13), clnd.default_schedule)
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (13, 25), clnd.default_schedule)

    def test_interval_direct_bad_args(self):
        clnd = tb_12_days()
        with pytest.raises(AttributeError):
            Interval('not a clnd', (2, 8), clnd.default_schedule)
        with pytest.raises(TypeError):
            Interval(clnd, (2, 8.5), clnd.default_schedule)
        with pytest.raises(TypeError):
            Interval(clnd, (2, '08 Jan 2017'), clnd.default_schedule)
        with pytest.raises(IndexError):
            Interval(clnd, (2,), clnd.default_schedule)
        with pytest.raises(TypeError):
            Interval(clnd, 'not a tuple', clnd.default_schedule)

