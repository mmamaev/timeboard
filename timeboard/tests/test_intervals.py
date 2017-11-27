import timeboard as tb
from timeboard.interval import Interval
from timeboard.exceptions import OutOfBoundsError, VoidIntervalError

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
        assert clnd._get_interval_locs_from_reference(None) == (0, 12)

    def test_interval_locator_with_two_ts(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
            ('02 Jan 2017 15:00', '08 Jan 2017 15:00')) == (2, 8)
        # reverse is ok; it is taken care later in 'get_interval'
        assert clnd._get_interval_locs_from_reference(
            ('08 Jan 2017 15:00', '02 Jan 2017 15:00')) == (8, 2)

    def test_interval_locator_with_with_excessive_item(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(('02 Jan 2017 15:00',
                                                       '08 Jan 2017 15:00',
                                                       'something')) == (2, 8)

    def test_interval_locator_with_two_pd_ts(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
                                (pd.Timestamp('02 Jan 2017 15:00'),
                                 pd.Timestamp('08 Jan 2017 15:00'))) == (2, 8)

    def test_interval_locator_with_two_datettime_ts(self):
        clnd = tb_12_days()
        assert clnd._get_interval_locs_from_reference(
                (datetime.datetime(2017, 1, 2, 15, 0, 0),
                 datetime.datetime(2017, 1, 8, 15, 0, 0))) == (2, 8)

    def test_interval_locator_with_OOB_ts(self):
        clnd = tb_12_days()
        # only one end of the interval is OOB
        assert clnd._get_interval_locs_from_reference(
            ('02 Jan 2017 15:00', '13 Jan 2017 15:00')) == (2, -1)
        assert clnd._get_interval_locs_from_reference(
            ('30 Dec 2016 15:00', '08 Jan 2017 15:00')) == (-2, 8)
        # the interval spans over the timeboard
        assert clnd._get_interval_locs_from_reference(
            ('30 Dec 2016 15:00', '13 Jan 2017 15:00')) == (-2, -1)
        assert clnd._get_interval_locs_from_reference(
            ('13 Jan 2017 15:00', '30 Dec 2016 15:00')) == (-1, -2)
        # the interval is completely outside the timeboard
        assert clnd._get_interval_locs_from_reference(
            ('25 Dec 2016 15:00', '30 Dec 2016 15:00')) == (-2, -2)
        assert clnd._get_interval_locs_from_reference(
            ('30 Dec 2016 15:00', '25 Dec 2016 15:00')) == (-2, -2)
        assert clnd._get_interval_locs_from_reference(
            ('13 Jan 2017 15:00', '15 Jan 2017 15:00')) == (-1, -1)
        assert clnd._get_interval_locs_from_reference(
            ('15 Jan 2017 15:00', '13 Jan 2017 15:00')) == (-1, -1)

    def test_interval_locator_from_pd_periods(self):
        clnd = tb_12_days()
        # if we could not directly Timestamp() a reference, we try to call its
        # `to_timestamp` method which would return reference's start time

        # First day of Jan is inside clnd
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('02 Jan 2017', freq='M'),
                                 '11 Jan 2017 15:00')) == (1, 11)
        # While 31 Dec is within clnd, the first day of Dec is outside
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('31 Dec 2016', freq='M'),
                                 '11 Jan 2017 15:00')) == (-2, 11)
        # freq=W begins weeks on Mon which is 02 Jan 2017
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('05 Jan 2017', freq='W'),
                                 '11 Jan 2017 15:00')) == (2, 11)
        # freq=W-MON ends weeks on Mondays, and 02 Jan is Monday,
        # but this week begins on Tue 27 Dec 2016 which is outside the timeboard
        assert clnd._get_interval_locs_from_reference(
            (pd.Period('02 Jan 2017', freq='W-MON'),
                                 '11 Jan 2017 15:00')) == (-2, 11)


    def test_interval_locator_with_bad_ts(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd._get_interval_locs_from_reference(
                ('bad_timestamp', '08 Jan 2017 15:00'))
        with pytest.raises(ValueError):
            clnd._get_interval_locs_from_reference(
                ('02 Jan 2017 15:00', 'bad_timestamp'))

    def test_interval_locator_with_singletons(self):
        clnd = tb_12_days()
        with pytest.raises(TypeError):
            clnd._get_interval_locs_from_reference(('08 Jan 2017 15:00',))
        with pytest.raises(ValueError):
            clnd._get_interval_locs_from_reference('08 Jan 2017 15:00')
        with pytest.raises(TypeError):
            clnd._get_interval_locs_from_reference(
                pd.Timestamp('08 Jan 2017 15:00'))

class TestIntervalStripLocs:

    def test_interval_strip_locs(self):
        clnd = tb_12_days()
        assert clnd._strip_interval_locs((2, 8), '11') == (2, 8)
        assert clnd._strip_interval_locs((2, 8), '01') == (3, 8)
        assert clnd._strip_interval_locs((2, 8), '10') == (2, 7)
        assert clnd._strip_interval_locs((2, 8), '00') == (3, 7)
        assert clnd._strip_interval_locs((2, 4), '00') == (3, 3)


    def test_interval_strip_locs_corner_cases(self):
        clnd = tb_12_days()
        assert clnd._strip_interval_locs((2, 2), '11') == (2, 2)
        assert clnd._strip_interval_locs((2, 2), '01') == (3, 2)
        assert clnd._strip_interval_locs((2, 2), '10') == (2, 1)
        assert clnd._strip_interval_locs((2, 2), '00') == (3, 1)
        assert clnd._strip_interval_locs((2, 3), '00') == (3, 2)
        assert clnd._strip_interval_locs((0, 0), '00') == (1, -1)
        assert clnd._strip_interval_locs((-4, -2), '00') == (-3, -3)


    def test_interval_strip_locs_bad_locs(self):
        # in '_strip_interval_locs' we do not care about validity of 'locs'
        # type and value; other parts of 'get_interval' should care about this
        assert True

    def test_interval_strip_locs_bad_closed(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd._strip_interval_locs((2, 8), '010')
        with pytest.raises(ValueError):
            clnd._strip_interval_locs((2, 8), True)


class TestIntervalConstructorWithTS:

    def test_interval_constructor_with_two_ts(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void


    def test_interval_constructor_with_two_ts_open_ended(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='11')
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='01')
        assert ivl._loc == (3,8)
        assert ivl.length == 6
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='10')
        assert ivl._loc == (2,7)
        assert ivl.length == 6
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '08 Jan 2017 15:00'),
                                closed='00')
        assert ivl._loc == (3,7)
        assert ivl.length == 5
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '03 Jan 2017 15:00'),
                                closed='01')
        assert ivl._loc == (3,3)
        assert ivl.length == 1
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '03 Jan 2017 15:00'),
                                closed='10')
        assert ivl._loc == (2,2)
        assert ivl.length == 1

    def test_interval_constructor_with_closed_leads_to_void(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'))
        assert ivl._loc == (2,2)
        assert ivl.length == 1
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 15:00'),
                              closed='01')
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
        # only one enf of the interval is OOB
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('02 Jan 2017 15:00', '13 Jan 2017 15:00'))
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('30 Dec 2016 15:00', '08 Jan 2017 15:00'))
        # the interval spans over the timeboard
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(('30 Dec 2016 15:00', '13 Jan 2017 15:00'))
        # check for OOBError precedes VoidIntervalError;
        # this must be changed when clipping is enabled
        with pytest.raises(OutOfBoundsError):
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
        assert ivl.length == 1
        assert not ivl.is_void

    def test_interval_constructor_reverse_ts_to_same_BU(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(('02 Jan 2017 15:00', '02 Jan 2017 10:00'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 2, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 3, 0, 0, 0)
        assert ivl._loc == (2,2)
        assert ivl.length == 1
        assert not ivl.is_void

    def test_interval_constructor_reverse_ts(self):
        clnd = tb_12_days()
        with pytest.raises(VoidIntervalError):
            clnd.get_interval(('08 Jan 2017 15:00', '02 Jan 2017 15:00'))

class TestIntervalConstructorDefault:

    def test_interval_constructor_default(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval()
        assert ivl.start_time == datetime.datetime(2016, 12, 31, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 12, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 13, 0, 0, 0)
        assert ivl._loc == (0,12)
        assert ivl.length == 13
        assert not ivl.is_void

    def test_interval_constructor_default_open_ended(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(closed='00')
        assert ivl.start_time == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 11, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 12, 0, 0, 0)
        assert ivl._loc == (1,11)
        assert ivl.length == 11
        assert not ivl.is_void

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


class TestIntervalConstructorOtherWays:

    def test_interval_constructor_with_period(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('02 Jan 2017 15:00', period='W')
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_constructor_with_OOB_period(self):
        clnd = tb_12_days()
        # period defined by good ts but extends beyond the left bound of clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('01 Jan 2017 15:00', period='W')
        # period defined by good ts but extends beyond the right bound of clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('10 Jan 2017 15:00', period='W')
        # period completely outside clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('18 Jan 2017 15:00', period='W')

    def test_interval_constructor_with_bad_period(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd.get_interval('02 Jan 2017 15:00', period='bad_period')
        with pytest.raises(ValueError):
            clnd.get_interval('bad_timestamp', period='W')

    def test_interval_constructor_with_length(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('02 Jan 2017 15:00', length=7)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_constructor_with_negative_length(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('08 Jan 2017 15:00', length=-7)
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_constructor_with_length_one(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval('02 Jan 2017 15:00', length=1)
        assert ivl._loc == (2,2)
        assert ivl.length == 1
        ivl = clnd.get_interval('02 Jan 2017 15:00', length=-1)
        assert ivl._loc == (2,2)
        assert ivl.length == 1


    def test_interval_constructor_with_zero_length(self):
        # same treatment as interval with reverse timestamps
        clnd = tb_12_days()
        with pytest.raises(VoidIntervalError):
            clnd.get_interval('08 Jan 2017 15:00', length=0)

    def test_interval_constructor_with_length_OOB(self):
        clnd = tb_12_days()
        # May be build interval from the portion falling inside clnd?
        # NO. You either get an expected result or an exception, not
        # some other interval you did not ask for
        #
        # starts inside clnd, ends OOB
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval('02 Jan 2017 15:00', length=20)
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
            clnd.get_interval('02 Jan 2017 15:00', length='x')
        with pytest.raises(ValueError):
            clnd.get_interval('bad_timestamp', length=5)

    def test_interval_constructor_from_pd_period(self):
        clnd = tb_12_days()
        ivl = clnd.get_interval(pd.Period('05 Jan 2017 15:00', freq='W'))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2, 8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_constructor_from_pd_period_OOB(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                        start='07 Jan 2017', end='18 Jan 2017',
                        layout=[0, 1, 0])
        # period defined by good ts but extends beyond the left bound of clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('08 Jan 2017 15:00', freq='W'))
        # period defined by good ts but extends beyond the right bound of clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('17 Jan 2017 15:00', freq='W'))
        # period overlapping clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('08 Jan 2017 15:00', freq='M'))
        # period completely outside clnd
        with pytest.raises(OutOfBoundsError):
            clnd.get_interval(pd.Period('25 Jan 2017 15:00', freq='W'))

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
        assert ivl.length == 32
        assert not ivl.is_void

    def test_interval_constructor_bad_arg_combinations(self):
        clnd = tb_12_days()
        with pytest.raises(ValueError):
            clnd.get_interval('01 Jan 2017')
        with pytest.raises(TypeError):
            clnd.get_interval(('01 Jan 2017',))
        with pytest.raises(TypeError):
            clnd.get_interval('01 Jan 2017', '05 Jan 2017')
        with pytest.raises(TypeError):
            clnd.get_interval(('01 Jan 2017',), length=1)
        with pytest.raises(TypeError):
            clnd.get_interval(('anyhting', 'anything'), length=1)
        with pytest.raises(ValueError):
            clnd.get_interval(('02 Jan 2017',), period='W')
        with pytest.raises(ValueError):
            clnd.get_interval(('anyhting', 'anything'), period='W')
        with pytest.raises(TypeError):
            clnd.get_interval('anyhting', length=1, period='W')
        with pytest.raises(TypeError):
            clnd.get_interval(('anyhting', 'anything'), length=1, period='W')
        with pytest.raises(TypeError):
            clnd.get_interval(length=1, period='W')



class TestIntervalConstructorDirect:

    def test_interval_direct_with_locs(self):
        clnd = tb_12_days()
        ivl = Interval(clnd, (2, 8))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_direct_with_ws(self):
        clnd = tb_12_days()
        ivl = Interval(clnd,(clnd('02 Jan 2017'), clnd('08 Jan 2017')))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_direct_mixed_args(self):
        clnd = tb_12_days()
        ivl = Interval(clnd, (2, clnd('08 Jan 2017')))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 8, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 9, 0, 0, 0)
        assert ivl._loc == (2,8)
        assert ivl.length == 7
        assert not ivl.is_void

    def test_interval_direct_same_locs(self):
        clnd = tb_12_days()
        ivl = Interval(clnd, (2, 2))
        assert ivl.start_time == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert ivl.end_time > datetime.datetime(2017, 1, 2, 23, 59, 59)
        assert ivl.end_time < datetime.datetime(2017, 1, 3, 0, 0, 0)
        assert ivl._loc == (2,2)
        assert ivl.length == 1
        assert not ivl.is_void

    def test_interval_direct_reverse_locs(self):
        clnd = tb_12_days()
        with pytest.raises(VoidIntervalError):
            Interval(clnd, (8, 2))

    def test_interval_direct_OOB_locs(self):
        clnd = tb_12_days()
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (-1, 2))
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (8, 13))
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (-1, 13))
        with pytest.raises(OutOfBoundsError):
            Interval(clnd, (13, 25))

    def test_interval_direct_bad_args(self):
        clnd = tb_12_days()
        with pytest.raises(AttributeError):
            Interval('not a clnd', (2, 8))
        with pytest.raises(TypeError):
            Interval(clnd, (2, 8.5))
        with pytest.raises(TypeError):
            Interval(clnd, (2, '08 Jan 2017'))
        with pytest.raises(IndexError):
            Interval(clnd, (2,))
        with pytest.raises(TypeError):
            Interval(clnd, 'not a tuple')

