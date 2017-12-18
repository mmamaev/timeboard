import pandas as pd
import numpy as np


def simple_offset(pi, normalize_by=None, **kwargs):
    """Calculate point in time specified by offset.
    
    To the start time of each period in the period index `pi` add an offset 
    specified by the supplied keyword arguments. If the resulting timestamp 
    is not within the period, silently omit this result from the returned array.
    
    Parameters
    ----------
    pi : pandas.PeriodIndex
    normalize_by : str (pandas time frequency), optional
        If given, snap results to the start time of the `normalize_by` 
        periods.
    **kwargs 
        keyword arguments for pandas.DateOffset
    
    Returns
    -------
    pandas.DatetimeIndex
    
    """
    offset = pd.DateOffset(**kwargs)
    testtime = pd.Timestamp('01 Jan 2004') #longest month of longest year
    if testtime + offset < testtime:
        # with negative offset all results will fall out of their periods
        return pd.DatetimeIndex([])

    start_times = pi.to_timestamp(how='start')
    end_times = pi.to_timestamp(how='end')

    # workaround for bug in pandas when pi.freq='D
    if end_times[0] == start_times[0]:
        et = np.array([p.end_time for p in pi], dtype='datetime64[ns]')
        end_times = pd.DatetimeIndex(et)

    result = start_times + offset
    if normalize_by is not None:
        result = pd.PeriodIndex(result,
                                freq=normalize_by).to_timestamp(how='start')
    result = result[result <= end_times]
    return result


def nth_weekday_of_month(pi, month, week, weekday, shift=None, **kwargs):
    """Calculate nth weekday of a month.
    
    For each element of the period index `pi` take the month when this 
    element begins. Starting from this point go to the M-th month (number M is 
    given by `month`) and find the N-th `weekday` within that month 
    (number N is given by `week`). If `shift` is specified, 
    shift the result by the corresponding number of days. Return an 
    array of timestamps for the start times of the days found.
    Duplicates are removed. If, for a particular element of `pi`, 
    the requested day does not exist within the month, the result for this 
    element is silently omitted from the returned array.
    
    Parameters
    ----------
    pi : pandas.PeriodIndex
    month : int 1..12 
        1 refers to the month when the current element of `pi` begins, 
        2 refers to the next month, and so on. If the current element of `pi` 
        points to the start of a year, then 1 is January, 12 is December 
        of this year.
    week : int -5..5 
        Use week=1 to find the first weekday in the month, week=-1 to find 
        the last. week=0 is not allowed.
    weekday : int 1..7 
        Monday is 1, Sunday is 7
    shift: int, optional
        Number of days to add to the calculated dates, may be negative.
    **kwargs 
        not used; it is here for parameter compatibility with other functions 
        of this module.

    Returns
    -------
    pandas.DatetimeIndex
 
    """
    assert month in range(1, 13)
    assert weekday in range(1, 8)
    assert week in range(1, 6) or week in range(-5, 0)
    if shift is None:
        shift = 0

    dti = pi.asfreq(freq='M', how='START').drop_duplicates().to_timestamp(
        how='start')
    m_start_times = dti + pd.tseries.offsets.MonthBegin(month - 1,
                                                        normalize=True)
    m_end_times = dti + pd.tseries.offsets.MonthEnd(month, normalize=True)

    if week > 0:
        off_by_one_bug_flag = m_start_times.weekday == weekday - 1
        week_factors = week * np.ones(len(dti),
                                      dtype=np.int8) - off_by_one_bug_flag
        week_offsets = week_factors * pd.tseries.offsets.Week(
            weekday=weekday - 1, normalize=True)
        dtw = pd.DatetimeIndex(
            [m_start_times[i] + week_offsets[i] for i in range(len(dti))])
        dtw = dtw[dtw <= m_end_times]
    else:
        off_by_one_bug_flag = m_end_times.weekday == weekday - 1
        week_factors = week * np.ones(len(dti),
                                      dtype=np.int8) + off_by_one_bug_flag
        week_offsets = week_factors * pd.tseries.offsets.Week(
            weekday=weekday - 1, normalize=True)
        dtw = pd.DatetimeIndex(
            [m_end_times[i] + week_offsets[i] for i in range(len(dti))])
        dtw = dtw[dtw >= m_start_times]

    return dtw + pd.DateOffset(days=shift)