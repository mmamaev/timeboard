import pandas as pd
import numpy as np
from dateutil.easter import easter

# import timeit
# timers1 = []
# timers2 = []
# timers3 = []

def from_start_of_each(pi, normalize_by=None, **kwargs):
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
    testtime = pd.Timestamp('01 Jan 2004')  # longest month of longest year
    if testtime + offset < testtime:
        # with negative offset all results will fall out of their periods
        return pd.DatetimeIndex([])

    start_times = pi.to_timestamp(how='start', freq='S')
    end_times = pi.to_timestamp(how='end', freq='S')


    # result = start_times + offset
    # The above raises VallueError in pandas > 0.22.
    # https://github.com/pandas-dev/pandas/issues/26258
    # Workaround:
    result = pd.DatetimeIndex([t + offset for t in start_times])

    if normalize_by is not None:
        result = pd.PeriodIndex(result,
                                freq=normalize_by).to_timestamp(how='start')
    result = result[result <= end_times]
    # Generally we should also filter result with [result >= start_times]
    # since normalize_by frequency can be anything, incl. having period larger
    # than pi frequency (i.e. pi freq='D', normalize_by='M'). In this case.
    # despite of positive (future-directed) offset, normalization can throw a
    # point in result in the past beyond start_times.
    # However this does not make sense (at least, in the context of this
    # package), and this function is always called from within this package
    # with  normalize_by=_Frame.base_unit_freq.
    # Therefore, we'd rather save time on filtering.
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
        Use ``week=1`` to find the first weekday in the month, ``week=-1`` 
        to find the last. ``week=0`` is not allowed.
    weekday : int 1..7 
        Monday is 1, Sunday is 7.
    shift : int, optional
        Number of days to add to the calculated dates, may be negative.
    **kwargs 
        not used; it is here for parameter compatibility with other functions 
        of this module.

    Returns
    -------
    pandas.DatetimeIndex
 
    """
    # TODO: (Prio: LOW) Optimize performance
    # Creating model timeline '3-DoW-per-M' (compound workshifts on daily frame
    # with marks on 3 weekdays per month) takes ~1 sec for 100 years,
    # ~1,8 sec for 278 years.
    # Counting per workshift it is more than 100 times slower than 'CC-2-8-18'
    # model which uses `from_start_of_each`. However, in practice
    # weekday-of-month marks occur with a frequency that is ~100 times lower
    # than that of 'CC-2-8-18', so in a practical case these markers will
    # be on par with each other.
    # Speed profile of this function:
    #    @timer1 : 24%
    #    @timer2 : 8%
    #    @timer3 : 68%

    # timer0 = timeit.default_timer()
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

    # timer1 = timeit.default_timer()
    # make sure we are inside put periods pi - this check makes sense when
    # pi.freq is based on 'M'
    pi_end_times = pi.to_timestamp(how='end')
    m_start_times = m_start_times[m_start_times <= pi_end_times]
    m_end_times = m_end_times[m_end_times <= pi_end_times]

    # timer2 = timeit.default_timer()
    if week > 0:
        off_by_one_bug_flag = m_start_times.weekday == weekday - 1
        week_factors = week * np.ones(len(m_start_times),
                                      dtype=np.int8) - off_by_one_bug_flag
        week_offsets = week_factors * pd.tseries.offsets.Week(
            weekday=weekday - 1, normalize=True)
        dtw = pd.DatetimeIndex(
            [m_start_times[i] + week_offsets[i]
             for i in range(len(m_start_times))])

        dtw = dtw[dtw <= m_end_times]

    else:
        off_by_one_bug_flag = m_end_times.weekday == weekday - 1
        week_factors = week * np.ones(len(m_end_times),
                                      dtype=np.int8) + off_by_one_bug_flag
        week_offsets = week_factors * pd.tseries.offsets.Week(
            weekday=weekday - 1, normalize=True)
        dtw = pd.DatetimeIndex(
            [m_end_times[i] + week_offsets[i]
             for i in range(len(m_end_times))])
        dtw = dtw[dtw >= m_start_times]

    # timer3 = timeit.default_timer()
    # timers1.append(timer1 - timer0)
    # timers2.append(timer2 - timer1)
    # timers3.append(timer3 - timer2)

    return dtw + pd.DateOffset(days=shift)


def from_easter(pi, easter_type='western', normalize_by=None, shift=None,
                **kwargs):
    """Calculate point in time related to Easter.

    In each period in the period index `pi` find the start time of the day of 
    Easter and add an offset specified by the supplied keyword arguments. 
    If the resulting timestamp is not within the period, silently omit this 
    result from the returned array.

    Parameters
    ----------
    pi : pandas.PeriodIndex
    easter_type : {``'western'``, ``'orthodox'``}, optional (default ``'western'``)
    normalize_by : str (pandas time frequency), optional
        If given, snap results to the start time of the `normalize_by` 
        periods.
    kwargs :
        keyword arguments for pandas.DateOffset

    Returns
    -------
    pandas.DatetimeIndex
    """
    assert easter_type in ['western', 'orthodox']
    if easter_type == 'western':
        _easter_type = 3
    elif easter_type == 'orthodox':
        _easter_type = 2

    if shift is not None:
        kwargs['days']=shift
    offset = pd.DateOffset(**kwargs)
    testtime = pd.Timestamp('01 Jan 2004')
    shift_to_future = testtime + offset >= testtime

    pi_start_times = pi.to_timestamp(how='start', freq='S')
    pi_end_times = pi.to_timestamp(how='end', freq='S')

    easter_dates = pd.DatetimeIndex([easter(y, _easter_type) for y in pi.year])
    easter_dates = easter_dates[(easter_dates >= pi_start_times) &
                                (easter_dates <= pi_end_times)]

    result = easter_dates + offset
    if normalize_by is not None:
        result = pd.PeriodIndex(result,
                                freq=normalize_by).to_timestamp(how='start')
    if shift_to_future:
        result = result[result <= pi_end_times]
    else:
        result = result[result >= pi_start_times]
    # See comment about filtering for the other end of periods in
    # from_start_of_each function
    return result


def from_easter_orthodox(pi, normalize_by=None, **kwargs):
    """
    Initialize easter from easter

    Args:
        pi: (todo): write your description
        normalize_by: (bool): write your description
    """
    return from_easter(pi, easter_type='orthodox', normalize_by=normalize_by,
                       **kwargs)

from_easter_western = from_easter
