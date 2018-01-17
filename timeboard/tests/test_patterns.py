from timeboard.core import _Timeline, _skiperator, _Frame, _Span, RememberingPattern
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

    def test_skiperator_empty_skip(self):
        g = _skiperator([], skip=2)
        with pytest.raises(StopIteration):
            next(g)


class TestTimelineConstructor(object):

    def test_time_line_constructor(self):

        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        t = _Timeline(f)
        assert len(t)==10
        assert t.start_time == f.start_time
        assert t.end_time == f.end_time
        assert t.labels.isnull().all()

@pytest.fixture(scope='module')
def timeline_10d():
    return _Timeline(_Frame(base_unit_freq='D', start='01 Jan 2017', end='10 '
                                                                        'Jan 2017'))

class TestApplyPattern(object):

    def test_apply_pattern_basic(self):
        p = [1,2,3]
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert t.labels.eq([1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_apply_pattern_skip(self):
        p = [1,2,3]
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=2))
        assert t.labels.eq([3, 1, 2, 3, 1, 2, 3, 1, 2, 3]).all()

    def test_apply_pattern_as_string_skip(self):
        # this won't happen in real life as Organizer does not allow
        # pattern as a string
        p = '123'
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=2))
        assert t.labels.eq(['3', '1', '2', '3', '1', '2', '3', '1', '2', '3']).all()

    def test_apply_pattern_span_skip(self):
        p = [1,2,3]
        t = timeline_10d()
        t._apply_pattern(p, _Span(1, 6, skip_left=2))
        assert t[1:7].eq([3, 1, 2, 3, 1, 2]).all()

    def test_apply_pattern_double(self):
        p1 = [11, 12]
        p2 = [1, 2, 3]
        t = timeline_10d()
        t._apply_pattern(p1, _Span(0, len(t.frame) - 1))
        t._apply_pattern(p2, _Span(1, 6, skip_left=2))
        assert t.labels.eq([11, 3, 1, 2, 3, 1, 2, 12, 11, 12]).all()

    def test_apply_pattern_short(self):
        p = [1]
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert t.labels.eq([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]).all()

    def test_apply_pattern_toolong(self):
        p = range(15)
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert t.labels.eq(range(10)).all()

    def test_apply_pattern_toolong_skip(self):
        p = range(15)
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=3))
        assert t.labels.eq(range(3, 13)).all()

    def test_apply_pattern_toolong_skip_more(self):
        p = range(15)
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=10))
        assert t.labels.eq([10, 11, 12, 13, 14, 0, 1, 2, 3, 4]).all()

    def test_apply_pattern_empty(self):
        p = []
        t = timeline_10d()
        with pytest.raises(IndexError):
           t._apply_pattern(p, _Span(0, len(t.frame) - 1))


class TestApplyPatternObject(object):

    def test_apply_pattern_basic(self):
        p = RememberingPattern([1, 2, 3])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert t.labels.eq([1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_apply_pattern_skip(self):
        p = RememberingPattern([1, 2, 3])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=2))
        assert t.labels.eq([3, 1, 2, 3, 1, 2, 3, 1, 2, 3]).all()

    def test_apply_pattern_span_skip(self):
        p = RememberingPattern([1, 2, 3])
        t = timeline_10d()
        t._apply_pattern(p, _Span(1, 6, skip_left=2))
        assert t[1:7].eq([3, 1, 2, 3, 1, 2]).all()

    def test_apply_pattern_short(self):
        p = RememberingPattern([1])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert t.labels.eq([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]).all()

    def test_apply_pattern_toolong(self):
        p = RememberingPattern(range(15))
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert t.labels.eq(range(10)).all()

    def test_apply_pattern_toolong_skip(self):
        p = RememberingPattern(range(15))
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=3))
        assert t.labels.eq(range(3, 13)).all()

    def test_apply_pattern_toolong_skip_more(self):
        p = RememberingPattern(range(15))
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=10))
        assert t.labels.eq([10, 11, 12, 13, 14, 0, 1, 2, 3, 4]).all()

    def test_apply_pattern_empty(self):
        p = RememberingPattern([])
        t = timeline_10d()
        with pytest.raises(IndexError):
           t._apply_pattern(p, _Span(0, len(t.frame) - 1))

    def test_apply_pattern_with_memory(self):
        p = RememberingPattern([0, 1])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, 4))
        t._apply_pattern([9], _Span(5, 6))
        t._apply_pattern(p, _Span(7, 9))
        assert t.labels.eq([0, 1, 0, 1, 0, 9, 9, 1, 0, 1]).all()

    def test_apply_pattern_with_memory_long(self):
        p = RememberingPattern([0, 1, 2, 3, 4, 5])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, 4))
        t._apply_pattern([9], _Span(5, 6))
        t._apply_pattern(p, _Span(7, 9))
        assert t.labels.eq([0, 1, 2, 3, 4, 9, 9, 5, 0, 1]).all()

    def test_apply_pattern_with_memory_skip(self):
        p = RememberingPattern([0, 1])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, 4, skip_left=3))
        t._apply_pattern([9], _Span(5, 6))
        t._apply_pattern(p, _Span(7, 9))
        assert t.labels.eq([1, 0, 1, 0, 1, 9, 9, 0, 1, 0]).all()

    def test_apply_pattern_with_memory_skip_long(self):
        p = RememberingPattern([0, 1, 2, 3, 4, 5])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, 4, skip_left=3))
        t._apply_pattern([9], _Span(5, 6))
        t._apply_pattern([9], _Span(5, 6))
        t._apply_pattern(p, _Span(7, 9))
        assert t.labels.eq([3, 4, 5, 0, 1, 9, 9, 2, 3, 4]).all()

    def test_apply_pattern_with_memory_skip_2(self):
        # this situation is not natural as dangles do not appear in interior
        # subframes
        p = RememberingPattern([0, 1, 2, 3, 4, 5])
        t = timeline_10d()
        t._apply_pattern(p, _Span(0, 4, skip_left=3))
        t._apply_pattern([9], _Span(5, 6))
        t._apply_pattern(p, _Span(7, 9, skip_left=2))
        assert t.labels.eq([3, 4, 5, 0, 1, 9, 9, 4, 5, 0]).all()
