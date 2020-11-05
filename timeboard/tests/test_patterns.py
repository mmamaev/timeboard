from timeboard.core import (
    _Timeline, _skiperator, _Frame, _Span, RememberingPattern,
    TIMELINE_DEL_TEMP_OBJECTS
)
import pytest


class TestSkiperator(object):

    def test_skiperator_basic(self):
        """
        Perform test test test.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([1, 2, 3])
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]

    def test_skiperator_skip(self):
        """
        Test if the test for test.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([1, 2, 3], skip=2)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [3, 1, 2, 3, 1, 2, 3, 1, 2, 3]

    def test_skiperator_skip_more(self):
        """
        The test test test test test test for test.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([1, 2, 3], skip=4)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [2, 3, 1, 2, 3, 1, 2, 3, 1, 2]

    def test_skiperator_one_value(self):
        """
        Perform one test test.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([1])
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    def test_skiperator_short(self):
        """
        Perform test test test.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([1, 2, 3])
        result = []
        for i in range(2):
            result.append(next(g))
        assert result == [1, 2]

    def test_skiperator_short_skip(self):
        """
        The test testperperator.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([1, 2, 3], skip=2)
        result = []
        for i in range(2):
            result.append(next(g))
        assert result == [3, 1]

    def test_skiperator_skip_negative(self):
        """
        The test test test test. skip_ski.

        Args:
            self: (todo): write your description
        """
        # negative value of skip is the same as skip=0
        g = _skiperator([1, 2, 3], skip=-1)
        result = []
        for i in range(10):
            result.append(next(g))
        assert result == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]

    def test_skiperator_empty(self):
        """
        Determine the test is empty.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([])
        with pytest.raises(StopIteration):
            next(g)

    def test_skiperator_empty_skip(self):
        """
        Test if the test to skip.

        Args:
            self: (todo): write your description
        """
        g = _skiperator([], skip=2)
        with pytest.raises(StopIteration):
            next(g)


class TestTimelineConstructor(object):

    def test_time_line_constructor(self):
        """
        Construct a time series

        Args:
            self: (todo): write your description
        """

        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        t = _Timeline(f)
        assert len(t)==10
        assert t.start_time == f.start_time
        assert t.end_time == f.end_time
        assert t.labels.isnull().all()

def timeline_10d(data=None):
    """
    Generate timestamps object.

    Args:
        data: (array): write your description
    """
    return _Timeline(_Frame(base_unit_freq='D',
                            start='01 Jan 2017', end='10 Jan 2017'),
                     data=data)


@pytest.mark.skipif(TIMELINE_DEL_TEMP_OBJECTS,
                    reason="__apply_pattern uses object that is deleted "
                           "after the timeline has been __init__'ed")
class TestApplyPattern(object):

    def test_apply_pattern_basic(self):
        """
        Apply test test to make a test.

        Args:
            self: (todo): write your description
        """
        p = [1,2,3]
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_apply_pattern_skip(self):
        """
        Apply test test to test.

        Args:
            self: (todo): write your description
        """
        p = [1,2,3]
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=2))
        assert (t._ws_labels == [3, 1, 2, 3, 1, 2, 3, 1, 2, 3]).all()

    def test_apply_pattern_as_string_skip(self):
        """
        Apply string pattern for pattern.

        Args:
            self: (todo): write your description
        """
        # this won't happen in real life as Organizer does not allow
        # pattern as a string
        p = '123'
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=2))
        assert (t._ws_labels == ['3', '1', '2', '3', '1', '2', '3', '1', '2', '3']).all()

    def test_apply_pattern_span_skip(self):
        """
        Apply the number of span of the span.

        Args:
            self: (todo): write your description
        """
        p = [1,2,3]
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(1, 6, skip_left=2))
        assert (t._ws_labels[1:7] == [3, 1, 2, 3, 1, 2]).all()

    def test_apply_pattern_double(self):
        """
        Apply double double double precision.

        Args:
            self: (todo): write your description
        """
        p1 = [11, 12]
        p2 = [1, 2, 3]
        t = timeline_10d()
        t._Timeline__apply_pattern(p1, _Span(0, len(t.frame) - 1))
        t._Timeline__apply_pattern(p2, _Span(1, 6, skip_left=2))
        assert (t._ws_labels == [11, 3, 1, 2, 3, 1, 2, 12, 11, 12]).all()

    def test_apply_pattern_short(self):
        """
        Test if the pattern in the best matching pattern.

        Args:
            self: (todo): write your description
        """
        p = [1]
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]).all()

    def test_apply_pattern_toolong(self):
        """
        Apply pattern to pattern.

        Args:
            self: (todo): write your description
        """
        p = range(15)
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == range(10)).all()

    def test_apply_pattern_toolong_skip(self):
        """
        Apply pattern to pattern.

        Args:
            self: (todo): write your description
        """
        p = range(15)
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=3))
        assert (t._ws_labels == range(3, 13)).all()

    def test_apply_pattern_toolong_skip_more(self):
        """
        Apply test test test to make sure that pattern.

        Args:
            self: (todo): write your description
        """
        p = range(15)
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=10))
        assert (t._ws_labels == [10, 11, 12, 13, 14, 0, 1, 2, 3, 4]).all()

    def test_apply_pattern_empty(self):
        """
        Applies empty empty empty pattern.

        Args:
            self: (todo): write your description
        """
        p = []
        t = timeline_10d(data=100)
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == [100]*10).all()


@pytest.mark.skipif(TIMELINE_DEL_TEMP_OBJECTS,
                    reason="__apply_pattern uses object that is deleted "
                           "after the timeline has been __init__'ed")
class TestApplyRememberingPattern(object):

    def test_apply_pattern_basic(self):
        """
        Apply test test test to test.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([1, 2, 3])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_apply_pattern_skip(self):
        """
        Apply test to see if the test.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([1, 2, 3])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=2))
        assert (t._ws_labels == [3, 1, 2, 3, 1, 2, 3, 1, 2, 3]).all()

    def test_apply_pattern_span_skip(self):
        """
        Apply the number of span.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([1, 2, 3])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(1, 6, skip_left=2))
        assert (t._ws_labels[1:7] == [3, 1, 2, 3, 1, 2]).all()

    def test_apply_pattern_short(self):
        """
        Apply the pattern to make it.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([1])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]).all()

    def test_apply_pattern_toolong(self):
        """
        Apply the pattern to pattern.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern(range(15))
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == range(10)).all()

    def test_apply_pattern_toolong_skip(self):
        """
        Apply the pattern to pattern

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern(range(15))
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=3))
        assert (t._ws_labels == range(3, 13)).all()

    def test_apply_pattern_toolong_skip_more(self):
        """
        Test for pattern for the pattern.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern(range(15))
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1, skip_left=10))
        assert (t._ws_labels == [10, 11, 12, 13, 14, 0, 1, 2, 3, 4]).all()

    def test_apply_pattern_empty(self):
        """
        Apply empty empty empty empty empty pattern.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([])
        t = timeline_10d(data=100)
        t._Timeline__apply_pattern(p, _Span(0, len(t.frame) - 1))
        assert (t._ws_labels == [100]*10).all()

    def test_apply_pattern_with_memory(self):
        """
        Applies the given pattern.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([0, 1])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, 4))
        t._Timeline__apply_pattern([9], _Span(5, 6))
        t._Timeline__apply_pattern(p, _Span(7, 9))
        assert (t._ws_labels == [0, 1, 0, 1, 0, 9, 9, 1, 0, 1]).all()

    def test_apply_pattern_with_memory_long(self):
        """
        Apply a pattern in - place.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([0, 1, 2, 3, 4, 5])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, 4))
        t._Timeline__apply_pattern([9], _Span(5, 6))
        t._Timeline__apply_pattern(p, _Span(7, 9))
        assert (t._ws_labels == [0, 1, 2, 3, 4, 9, 9, 5, 0, 1]).all()

    def test_apply_pattern_with_memory_skip(self):
        """
        Applies the test to test.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([0, 1])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, 4, skip_left=3))
        t._Timeline__apply_pattern([9], _Span(5, 6))
        t._Timeline__apply_pattern(p, _Span(7, 9))
        assert (t._ws_labels == [1, 0, 1, 0, 1, 9, 9, 0, 1, 0]).all()

    def test_apply_pattern_with_memory_skip_long(self):
        """
        Apply pattern to pattern.

        Args:
            self: (todo): write your description
        """
        p = RememberingPattern([0, 1, 2, 3, 4, 5])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, 4, skip_left=3))
        t._Timeline__apply_pattern([9], _Span(5, 6))
        t._Timeline__apply_pattern([9], _Span(5, 6))
        t._Timeline__apply_pattern(p, _Span(7, 9))
        assert (t._ws_labels == [3, 4, 5, 0, 1, 9, 9, 2, 3, 4]).all()

    def test_apply_pattern_with_memory_skip_2(self):
        """
        Apply test test to the test.

        Args:
            self: (todo): write your description
        """
        # this situation is not natural as dangles do not appear in interior
        # subframes
        p = RememberingPattern([0, 1, 2, 3, 4, 5])
        t = timeline_10d()
        t._Timeline__apply_pattern(p, _Span(0, 4, skip_left=3))
        t._Timeline__apply_pattern([9], _Span(5, 6))
        t._Timeline__apply_pattern(p, _Span(7, 9, skip_left=2))
        assert (t._ws_labels == [3, 4, 5, 0, 1, 9, 9, 4, 5, 0]).all()
