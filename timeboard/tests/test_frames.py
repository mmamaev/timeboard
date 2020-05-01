#from timeboard.timeboard import Timeboard
from timeboard.core import _Frame, _Span
from timeboard.exceptions import (OutOfBoundsError,
                                  VoidIntervalError,
                                  UnacceptablePeriodError)
import pandas as pd
import datetime
import pytest


class TestFrameConstructor(object) :

    def test_frame_constructor_days(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f)==60
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f[59] == pd.Period('01 Mar 2017', freq='D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('01 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_end_same_as_start(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Jan 2017')
        assert len(f)==1
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('01 Jan 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_same_base_unit(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017 08:00', end='01 Jan 2017 09:00')
        assert len(f)==1
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('01 Jan 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_multiple_days(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='08 Jan 2017')
        assert len(f) == 2
        assert f[0] == pd.Period('01 Jan 2017', freq='4D')
        assert f[1] == pd.Period('05 Jan 2017', freq='4D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('08 Jan 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('09 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_multiple_days_partial(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='10 Jan 2017')
        assert len(f) == 3
        assert f[0] == pd.Period('01 Jan 2017', freq='4D')
        assert f[2] == pd.Period('09 Jan 2017', freq='4D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('12 Jan 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('13 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_weeks(self):
        f = _Frame(base_unit_freq='W', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f)==10
        assert f[0] == pd.Period('26 Dec 2016', freq='W-SUN')
        assert f[9] == pd.Period('27 Feb 2017', freq='W-SUN')
        assert f.start_time == pd.Timestamp('26 Dec 2016 00:00:00')
        assert f.end_time >= pd.Timestamp('05 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('06 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_weeks_shifted(self):
        f = _Frame(base_unit_freq='W-WED', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f)==9
        assert f[0] == pd.Period('29 Dec 2016', freq='W-WED')
        assert f[8] == pd.Period('23 Feb 2017', freq='W-WED')
        assert f.start_time == pd.Timestamp('29 Dec 2016 00:00:00')
        assert f.end_time >= pd.Timestamp('01 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_months(self):
        f = _Frame(base_unit_freq='M', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f) == 3
        assert f[0] == pd.Period('Jan 2017', freq='M')
        assert f[2] == pd.Period('Mar 2017', freq='M')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_with_timestamps(self):
        f = _Frame(base_unit_freq='M',
                   start=pd.Timestamp('01 Jan 2017 08:00:01'),
                   end=pd.Timestamp('01 Mar 2017 12:15:03'))
        assert len(f) == 3
        assert f[0] == pd.Period('Jan 2017', freq='M')
        assert f[2] == pd.Period('Mar 2017', freq='M')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_with_datetime_redundant(self):
        f = _Frame(base_unit_freq='M',
                   start=datetime.datetime(year=2017, month=1, day=1,
                                           hour=8, minute=0, second=1),
                   end=datetime.datetime(year=2017, month=3, day=1,
                                         hour=12, minute=15, second=3))
        assert len(f) == 3
        assert f[0] == pd.Period('Jan 2017', freq='M')
        assert f[2] == pd.Period('Mar 2017', freq='M')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_with_datetime_deficient(self):
        f = _Frame(base_unit_freq='H',
                   start=datetime.date(year=2017,month=1,day=1),
                   end=datetime.date(year=2017,month=1,day=2))
        assert len(f) == 25
        assert f[0] == pd.Period('01 Jan 2017 00:00:00', freq='H')
        assert f[24] == pd.Period('02 Jan 2017 00:00:00', freq='H')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('02 Jan 2017 00:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Jan 2017 01:00:00')
        assert f.is_monotonic

    def test_frame_constructor_days_from_periods(self):
        f = _Frame(base_unit_freq='D',
                   start=pd.Period('01 Jan 2017', freq='D'),
                   end=pd.Period('01 Mar 2017', freq='D'))
        assert len(f)==60
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f[59] == pd.Period('01 Mar 2017', freq='D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('01 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_days_from_subperiods(self):
        f = _Frame(base_unit_freq='D',
                   start=pd.Period('01 Jan 2017 12:00', freq='H'),
                   end=pd.Period('01 Mar 2017 15:00', freq='H'))
        assert len(f)==60
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f[59] == pd.Period('01 Mar 2017', freq='D')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('01 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('02 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_days_from_superperiods(self):
        f = _Frame(base_unit_freq='D',
                   start=pd.Period('01 Jan 2017', freq='M'),
                   end=pd.Period('01 Mar 2017', freq='M'))
        # it takes the END of a period given as argument
        # to define start or end of the frame
        # Therefore of January 2017 only the last day made it into the frame
        assert len(f) == 1 + 28 + 31
        assert f[0] == pd.Period('31 Jan 2017', freq='D')
        assert f[59] == pd.Period('31 Mar 2017', freq='D')
        assert f.start_time == pd.Timestamp('31 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_days_from_nonsubperiods(self):
        f = _Frame(base_unit_freq='M',
                   start=pd.Period('31 Dec 2016', freq='W'),
                   end=pd.Period('01 Mar 2017', freq='W'))
        # it takes the END of a period given as argument
        # to define start or end of the frame
        # therefore December is not in the frame, because the week of
        # 31 Dec 2016 ends on 01 Jan 2017.
        assert len(f) == 3
        assert f[0] == pd.Period('Jan 2017', freq='M')
        assert f[2] == pd.Period('Mar 2017', freq='M')
        assert f.start_time == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_time >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_time <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_end_before_start(self):
        with pytest.raises(VoidIntervalError):
            _Frame(base_unit_freq='D', start='01 Mar 2017', end='01 Jan 2017')

    def test_frame_constructor_bad_timestamp(self):
        with pytest.raises(ValueError):
            _Frame(base_unit_freq='D', start='01 Mar 2017', end='bad timestamp')

    def test_frame_constructor_too_big_range(self):

        try:
            excpt = (RuntimeError,  pd._libs.tslibs.np_datetime.OutOfBoundsDatetime)
        except AttributeError:
            excpt = RuntimeError
        with pytest.raises(excpt):
            _Frame(start='21 Sep 1677', end='2017', base_unit_freq='D')
            # '22 Sep 1677' is the earliest possible day,
            # '21 Sep 1677 00:12:44' is the earliest possible time


def frame_60d():
    return _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Mar 2017')


def split_frame_60d():
    return [(0,8), (9,39), (40,49), (50,59)]


def split_frame_60d_int():
    return [(5,8), (9,39), (40,49), (50,55)]


class TestFrameLocSubframesWhole(object):

    def test_frame_locsubf_basic(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i])

    def test_frame_locsubf_multiplied_freq(self):
        f = _Frame(start='31 Dec 2016', end='09 Jan 2017', base_unit_freq='2D')
        split_points=[pd.Timestamp('02 Jan 2017'),
                      pd.Timestamp('02 Jan 2017 12:12:12'),
                      pd.Timestamp('07 Jan 2017'),
                      pd.Timestamp('07 Jan 2017 11:05')]
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result) == 3
        assert result[0] == (0, 0)
        assert result[1] == (1, 2)
        assert result[2] == (3, 4)

    def test_frame_locsubf_basic_from_dti(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        dti = pd.DatetimeIndex(split_points)
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), dti))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i])

    def test_frame_locsubf_unordered(self):
        split_points = [pd.Timestamp('20 Feb 2017 11:05'),
                        pd.Timestamp('10 Feb 2017 12:12:12'),
                        pd.Timestamp('10 Jan 2017')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result) == 4
        for i in range(len(result)):
            assert (result[i] == split_frame_60d()[i])

    def test_frame_locsubf_multiple_points_per_bu(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('10 Feb 2017 20:20:20'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i])

    def test_frame_locsubf_with_points_outside(self):
        split_points=[pd.Timestamp('30 Dec 2016'),
                      pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05'),
                      pd.Timestamp('20 Feb 2018')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i])

    def test_frame_locsubf_with_point_outside_only(self):
        split_points=[pd.Timestamp('30 Dec 2016'),
                      pd.Timestamp('20 Feb 2018')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==1
        assert (result[0] == (0,59))

    def test_frame_locsubf_with_first_bu(self):
        split_points=[pd.Timestamp('01 Jan 2017'),
                      pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i])

    def test_frame_locsubf_at_first_bu_only(self):
        split_points=[pd.Timestamp('01 Jan 2017')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==1
        assert (result[0] == (0,59))

    def test_frame_locsubf_at_last_bu(self):
        split_points = [pd.Timestamp('01 Mar 2017')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result) == 2
        assert result[0] == (0,58)
        assert result[1] == (59,59)

    def test_frame_split_empty(self):
        split_points=[]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, len(f) - 1), split_points))
        assert len(result)==1
        assert result[0] == (0,59)


class TestFrameLocSubframesSpan(object):

    def test_frame_locsubf_int_basic(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 55), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d_int()[i])

    def test_frame_locsubf_with_points_outside(self):
        split_points=[pd.Timestamp('30 Dec 2016'),
                      pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05'),
                      pd.Timestamp('20 Feb 2018')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 55), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d_int()[i])

    def test_frame_locsubf_with_point_outside_only(self):
        split_points=[pd.Timestamp('30 Dec 2016'),
                      pd.Timestamp('20 Feb 2018')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 55), split_points))
        assert len(result)==1
        assert (result[0] == (5,55))

    def test_frame_locsubf_with_first_bu(self):
        split_points=[pd.Timestamp('06 Jan 2017'),
                      pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 55), split_points))
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d_int()[i])

    def test_frame_locsubf_at_first_bu_only(self):
        split_points=[pd.Timestamp('06 Jan 2017')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 55), split_points))
        assert len(result)==1
        assert (result[0] == (5,55))

    def test_frame_locsubf_span_single(self):
        split_points=[pd.Timestamp('06 Jan 2017')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 5), split_points))
        assert len(result)==1
        assert (result[0] == (5,5))

    def test_frame_locsubf_span_single_points_outside(self):
        split_points=[pd.Timestamp('07 Jan 2017')]
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 5), split_points))
        assert len(result)==1
        assert (result[0] == (5,5))

    def test_frame_locsubf_span_single_no_points(self):
        split_points = []
        f = frame_60d()
        result = list(f._locate_subspans(_Span(5, 5), split_points))
        assert len(result) == 1
        assert (result[0] == (5, 5))

    def test_frame_locsubf_span_single_at_zero(self):
        split_points = []
        f = frame_60d()
        result = list(f._locate_subspans(_Span(0, 0), split_points))
        assert len(result) == 1
        assert (result[0] == (0, 0))

    def test_frame_locsubf_span_negative1(self):
        split_points = [pd.Timestamp('10 Feb 2017 12:12:12')]
        f = frame_60d()
        with pytest.raises(OutOfBoundsError):
            f._locate_subspans(_Span(5 - 60, 55), split_points)

    def test_frame_locsubf_span_negative2(self):
        split_points = [pd.Timestamp('10 Feb 2017 12:12:12')]
        f = frame_60d()
        with pytest.raises(OutOfBoundsError):
            f._locate_subspans(_Span(5, 55 - 60), split_points)

    def test_frame_locsubf_span_outside(self):
        split_points = [pd.Timestamp('10 Feb 2017 12:12:12')]
        f = frame_60d()
        with pytest.raises(OutOfBoundsError):
            f._locate_subspans(_Span(5, 70), split_points)

    def test_frame_locsubf_span_reverse_(self):
        split_points = [pd.Timestamp('10 Feb 2017 12:12:12')]
        f = frame_60d()
        with pytest.raises(VoidIntervalError):
            f._locate_subspans(_Span(55, 5), split_points)

    def test_frame_locsubf_span_ts_injection1(self):
        split_points = [pd.Timestamp('10 Feb 2017 12:12:12')]
        f = frame_60d()
        with pytest.raises(Exception):
             f._locate_subspans(_Span(5, '20 Feb 2017'), split_points)

    def test_frame_locsubf_span_ts_injection2(self):
        split_points = [pd.Timestamp('10 Feb 2017 12:12:12')]
        f = frame_60d()
        with pytest.raises(Exception):
             f._locate_subspans(_Span(5, pd.Timestamp('20 Feb 2017')),
                                split_points)