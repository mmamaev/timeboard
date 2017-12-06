from timeboard.core import _Frame, _Subframe, Splitter
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


class TestSplitBy(object):
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

    def test_days_splitby_monthly_dangling(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Feb 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('M'))
        assert len(result) == 3
        assert assert_subframe(result[0], 0, 0, 30, 0)
        assert assert_subframe(result[1], 1, 31, 0, 0)
        assert assert_subframe(result[2], 32, 32, 0, 27)

    def test_days_splitby_annually_dangling(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='01 Jan 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('A'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 365, 0)  # 2016 was a leap year
        assert assert_subframe(result[1], 1, 1, 0, 364)

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

    def test_weeks_splitby_months(self):
        f = _Frame(base_unit_freq='W', start='01 Jan 2017', end='01 Mar 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('M'))

    def test_weeks_splitby_years(self):
        f = _Frame(base_unit_freq='W', start='31 Dec 2016', end='01 Mar 2017')
        with pytest.raises(UnsupportedPeriodError):
            f.do_split_by(0, len(f) - 1, Splitter('A'))

    def test_months_splitby_years(self):
        f = _Frame(base_unit_freq='M', start='31 Dec 2016', end='01 Mar 2017')
        result = f.do_split_by(0, len(f) - 1, Splitter('A'))
        assert len(result) == 2
        assert assert_subframe(result[0], 0, 0, 11, 0)
        assert assert_subframe(result[1], 1, 3, 0, 9)

    def test_month_splitby_years_short(self):
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
