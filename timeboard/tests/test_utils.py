from timeboard.utils import to_iterable

class TestToIterable(object):

    def test_to_iterable(self):
        assert to_iterable(None) is None
        assert to_iterable(1) == [1]
        assert to_iterable('123') == ['123']
        assert to_iterable([1]) == [1]
        assert to_iterable(['112']) == ['112']
        assert to_iterable(['112', '345']) == ['112', '345']
        assert to_iterable({1, 2, 3}) == {1, 2, 3}
        assert to_iterable(1 == 3) == [False]
