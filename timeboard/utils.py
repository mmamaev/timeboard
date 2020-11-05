import pandas as pd
import numpy as np
import six


try:
    from collections.abc import Iterable, Mapping
except ImportError:
    from collections import Iterable, Mapping


try:
    _pandas_is_subperiod = pd.tseries.frequencies.is_subperiod
except AttributeError:
    _pandas_is_subperiod = pd._libs.tslibs.frequencies.is_subperiod

try:
    _ = pd.Series.to_numpy
except AttributeError:
    nonzero = np.nonzero
else:
    def _nonzero(a):
        """
        Return the non - zero nonzero.

        Args:
            a: (todo): write your description
        """
        if isinstance(a, pd.Series):
            return np.nonzero(a.to_numpy())
        else:
            return np.nonzero(a)

    nonzero = _nonzero



def is_string(obj):
    """
    Return true if obj is a string.

    Args:
        obj: (todo): write your description
    """
    return isinstance(obj, six.string_types)

def is_iterable(obj):
    """
    Check if an iterable is iterable.

    Args:
        obj: (todo): write your description
    """
    return (isinstance(obj, Iterable) and
            not is_string(obj))


def to_iterable(x):
    """
    Convert an iterable to an iterable.

    Args:
        x: (todo): write your description
    """
    if x is None:
        return x
    if is_iterable(x):
        return x
    else:
        return [x]

def is_dict(obj):
    """
    Return true if obj is a dict.

    Args:
        obj: (todo): write your description
    """
    return isinstance(obj, Mapping)

def is_null(x):
    """
    Return true if x is null.

    Args:
        x: (todo): write your description
    """
    return pd.isnull(x)

def assert_value(x, value_render_function, value_test_function, title='Parameter'):
    """
    Return the value of x is not none.

    Args:
        x: (todo): write your description
        value_render_function: (str): write your description
        value_test_function: (todo): write your description
        title: (str): write your description
    """
    if value_render_function is not None:
        x = value_render_function(x)
    if value_test_function is not None:
        assert value_test_function(x), "Got invalid {} = {!r}".format(title, x)
    return x
