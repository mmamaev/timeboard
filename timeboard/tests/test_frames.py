from timeboard.timeboard import Timeboard
from timeboard.core import _Frame, _Timeline
import pandas as pd
import datetime
import pytest


class TestFrameConstructor(object) :

    def test_frame_constructor_days(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f)==60
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f[59] == pd.Period('01 Mar 2017', freq='D')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('01 Mar 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('02 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_end_same_as_start(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Jan 2017')
        assert len(f)==1
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('01 Jan 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('02 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_same_base_unit(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017 08:00', end='01 Jan 2017 09:00')
        assert len(f)==1
        assert f[0] == pd.Period('01 Jan 2017', freq='D')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('01 Jan 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('02 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_multiple_days(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='08 Jan 2017')
        assert len(f) == 2
        assert f[0] == pd.Period('01 Jan 2017', freq='4D')
        assert f[1] == pd.Period('05 Jan 2017', freq='4D')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('08 Jan 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('09 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_multiple_days_partial(self):
        f = _Frame(base_unit_freq='4D', start='01 Jan 2017', end='10 Jan 2017')
        assert len(f) == 3
        assert f[0] == pd.Period('01 Jan 2017', freq='4D')
        assert f[2] == pd.Period('09 Jan 2017', freq='4D')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('12 Jan 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('13 Jan 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_weeks(self):
        f = _Frame(base_unit_freq='W', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f)==10
        assert f[0] == pd.Period('26 Dec 2016', freq='W-SUN')
        assert f[9] == pd.Period('27 Feb 2017', freq='W-SUN')
        assert f.start_ts == pd.Timestamp('26 Dec 2016 00:00:00')
        assert f.end_ts >= pd.Timestamp('05 Mar 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('06 Mar 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_months(self):
        f = _Frame(base_unit_freq='M', start='01 Jan 2017', end='01 Mar 2017')
        assert len(f) == 3
        assert f[0] == pd.Period('Jan 2017', freq='M')
        assert f[2] == pd.Period('Mar 2017', freq='M')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_with_timestamps(self):
        f = _Frame(base_unit_freq='M',
                   start=pd.Timestamp('01 Jan 2017 08:00:01'),
                   end=pd.Timestamp('01 Mar 2017 12:15:03'))
        assert len(f) == 3
        assert f[0] == pd.Period('Jan 2017', freq='M')
        assert f[2] == pd.Period('Mar 2017', freq='M')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('01 Apr 2017 00:00:00')
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
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('31 Mar 2017 23:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('01 Apr 2017 00:00:00')
        assert f.is_monotonic

    def test_frame_constructor_with_datetime_deficient(self):
        f = _Frame(base_unit_freq='H',
                   start=datetime.date(year=2017,month=1,day=1),
                   end=datetime.date(year=2017,month=1,day=2))
        assert len(f) == 25
        assert f[0] == pd.Period('01 Jan 2017 00:00:00', freq='H')
        assert f[24] == pd.Period('02 Jan 2017 00:00:00', freq='H')
        assert f.start_ts == pd.Timestamp('01 Jan 2017 00:00:00')
        assert f.end_ts >= pd.Timestamp('02 Jan 2017 00:59:59.999999999')
        assert f.end_ts <= pd.Timestamp('02 Jan 2017 01:00:00')
        assert f.is_monotonic

    def test_frame_constructor_end_before_start(self):
        with pytest.raises(ValueError) :
            f = _Frame(base_unit_freq='D', start='01 Mar 2017', end='01 Jan 2017')


@pytest.fixture(scope='module')
def frame_60d():
    return _Frame(base_unit_freq='D', start='01 Jan 2017', end='01 Mar 2017')


@pytest.fixture(scope='module')
def split_frame_60d():
    return [_Frame(base_unit_freq='D', start='01 Jan 2017', end='09 Jan 2017'),
            _Frame(base_unit_freq='D', start='10 Jan 2017', end='09 Feb 2017'),
            _Frame(base_unit_freq='D', start='10 Feb 2017', end='19 Feb 2017'),
            _Frame(base_unit_freq='D', start='20 Feb 2017', end='01 Mar 2017')]


class TestFrameSplit(object):

    def test_frame_split_ordinary(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        result = frame_60d().split(split_points)
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i]).all()

    def test_frame_split_ordinary_from_dti(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        dti = pd.DatetimeIndex(split_points)
        result = frame_60d().split(dti)
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i]).all()

    def test_frame_split_unordered(self):
        split_points = [pd.Timestamp('20 Feb 2017 11:05'),
                        pd.Timestamp('10 Feb 2017 12:12:12'),
                        pd.Timestamp('10 Jan 2017')]
        result = frame_60d().split(split_points)
        assert len(result) == 4
        for i in range(len(result)):
            assert (result[i] == split_frame_60d()[i]).all()

    def test_frame_split_multiple_points_per_bu(self):
        split_points=[pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('10 Feb 2017 20:20:20'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        result = frame_60d().split(split_points)
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i]).all()

    def test_frame_split_with_points_outside(self):
        split_points=[pd.Timestamp('30 Dec 2016'),
                      pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05'),
                      pd.Timestamp('20 Feb 2018')]
        result = frame_60d().split(split_points)
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i]).all()

    def test_frame_split_with_point_outside_only(self):
        split_points=[pd.Timestamp('30 Dec 2016'),
                      pd.Timestamp('20 Feb 2018')]
        result = frame_60d().split(split_points)
        assert len(result)==1
        assert (result[0] == frame_60d()).all()

    def test_frame_split_with_first_bu(self):
        split_points=[pd.Timestamp('01 Jan 2017'),
                      pd.Timestamp('10 Jan 2017'),
                      pd.Timestamp('10 Feb 2017 12:12:12'),
                      pd.Timestamp('20 Feb 2017 11:05')]
        result = frame_60d().split(split_points)
        assert len(result)==4
        for i in range(len(result)) :
            assert (result[i] == split_frame_60d()[i]).all()

    def test_frame_split_at_first_bu_only(self):
        split_points=[pd.Timestamp('01 Jan 2017')]
        result = frame_60d().split(split_points)
        assert len(result)==1
        assert (result[0] == frame_60d()).all()

    def test_frame_split_at_last_bu(self):
        split_points = [pd.Timestamp('01 Mar 2017')]
        result = frame_60d().split(split_points)
        assert len(result) == 2
        assert (result[0] == _Frame(base_unit_freq='D',
                                    start='01 Jan 2017',
                                    end='28 Feb 2017')).all()
        assert (result[1] == _Frame(base_unit_freq='D',
                                    start='01 Mar 2017',
                                    end='01 Mar 2017')).all()

    def test_frame_split_empty(self):
        split_points=[]
        result = frame_60d().split(split_points)
        assert len(result)==1
        assert (result[0] == frame_60d()).all()


class TestTimelineConstructor(object):

    def test_time_line_constructor(self):
        t = _Timeline(frame_60d())
        assert len(t)==60
        assert (t.index == frame_60d()).all()
        assert t.isnull().all()