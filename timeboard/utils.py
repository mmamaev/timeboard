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
        if isinstance(a, pd.Series):
            return np.nonzero(a.to_numpy())
        else:
            return np.nonzero(a)

    nonzero = _nonzero



def is_string(obj):
    return isinstance(obj, six.string_types)

def is_iterable(obj):
    return (isinstance(obj, Iterable) and
            not is_string(obj))


def to_iterable(x):
    if x is None:
        return x
    if is_iterable(x):
        return x
    else:
        return [x]

def is_dict(obj):
    return isinstance(obj, Mapping)

def is_null(x):
    return pd.isnull(x)

def assert_value(x, value_render_function, value_test_function, title='Parameter'):
    if value_render_function is not None:
        x = value_render_function(x)
    if value_test_function is not None:
        assert value_test_function(x), "Got invalid {} = {!r}".format(title, x)
    return x
