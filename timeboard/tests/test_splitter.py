from timeboard.core import _Frame, _Timeline, Organizer, _skiperator
import pandas as pd
import pytest


class TestSkiperator(object):

    def test_skiperator_basic(self):
        g = _skiperator([1, 2, 3])
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]

    def test_skiperator_skip(self):
        g = _skiperator([1, 2, 3], skip=2)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [3, 1, 2, 3, 1, 2, 3, 1, 2, 3]

    def test_skiperator_skip_more(self):
        g = _skiperator([1, 2, 3], skip=4)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [2, 3, 1, 2, 3, 1, 2, 3, 1, 2]

    def test_skiperator_reverse(self):
        g = _skiperator([1, 2, 3], direction='reverse')
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [3, 2, 1, 3, 2, 1, 3, 2, 1, 3]

    def test_skiperator_reverse_skip(self):
        g = _skiperator([1, 2, 3], direction='reverse', skip=2)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 3, 2, 1, 3, 2, 1, 3, 2, 1]

    def test_skiperator_one_value(self):
        g = _skiperator([1])
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    def test_skiperator_short(self):
        g = _skiperator([1, 2, 3])
        result = []
        for i in range(2):
            result.append(next(g))
        assert result == [1, 2]

    def test_skiperator_short_skip(self):
        g = _skiperator([1, 2, 3], skip=2)
        result = []
        for i in range(2):
            result.append(next(g))
        assert result == [3, 1]

    def test_skiperator_skip_negative(self):
        # negative value of skip is the same as skip=0
        g = _skiperator([1, 2, 3], skip=-1)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]

    def test_skiperator_empty(self):
        g = _skiperator([])
        with pytest.raises(StopIteration):
            next(g)

    def test_skiperator_empty_reverse(self):
        g = _skiperator([], direction='reverse')
        with pytest.raises(StopIteration):
            next(g)

    def test_skiperator_empty_skip(self):
        g = _skiperator([], skip=2)
        with pytest.raises(StopIteration):
            next(g)

@pytest.fixture(scope='module')
def frame_10d():
    return _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')

class TestApplyPattern(object):

    def test_apply_pattern_basic(self):
        p = [1,2,3]
        f = frame_10d()
        t = f.apply_pattern(p)
        assert t.eq(_Timeline(f, data=[1, 2, 3, 1, 2, 3, 1, 2, 3, 1])).all()

    def test_apply_pattern_skip(self):
        p = [1,2,3]
        f = frame_10d()
        t = f.apply_pattern(p, skip_left=2)
        assert t.eq(_Timeline(f, data=[3, 1, 2, 3, 1, 2, 3, 1, 2, 3])).all()

    def test_apply_pattern_empty(self):
        p = []
        f = frame_10d()
        with pytest.raises(IndexError):
           f.apply_pattern(p)

class TestPrepSplitBy(object):

    def test_prep_splitby_weekly_aligned(self):
        assert True