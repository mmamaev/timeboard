from timeboard.calendars.calendarbase import CalendarBase
from timeboard.exceptions import OutOfBoundsError
from timeboard.core import get_period
from pandas import Timedelta
import timeboard.calendars.RU as RU

import datetime
import pytest

class TestCalendarBase(object):
    def test_calendar_base(self):
        assert CalendarBase.amendments() == {}
        start = CalendarBase.parameters()['start']
        end = CalendarBase.parameters()['end']
        freq = CalendarBase.parameters()['base_unit_freq']
        clnd = CalendarBase()
        assert clnd.start_time == get_period(start, freq=freq).start_time
        assert clnd.end_time == get_period(end, freq=freq).end_time
        delta = end - start
        assert clnd.get_interval().count() == delta.components.days + 1

    def test_calendar_base_custom_limits(self):
        clnd = CalendarBase(custom_start='01 Jan 2017',
                            custom_end='31 Dec 2018')
        assert clnd.get_interval().count() == 365*2

    def test_calendar_base_custom_amds(self):
        clnd = CalendarBase(custom_start='01 Jan 2017',
                            custom_end='31 Dec 2018',
                            custom_amendments={
                                '01 Mar 2017': 0,
                                '01 Mar 2019': 0}
                            )
        assert clnd.get_interval().count() == 365 * 2 - 1

    def test_calendat_base_OOB(self):
        start = CalendarBase.parameters()['start']
        end = CalendarBase.parameters()['end']
        with pytest.raises(OutOfBoundsError):
            CalendarBase(start-Timedelta(days=1))
        with pytest.raises(OutOfBoundsError):
            CalendarBase(custom_end=end+Timedelta(days=1))


class TestCalendarsRU(object):

    def test_calendar_RU_week8x5(self):

        start = RU.Week8x5.parameters()['start']
        end = RU.Week8x5.parameters()['end']
        freq = RU.Week8x5.parameters()['base_unit_freq']
        clnd = RU.Week8x5()
        assert clnd.start_time == get_period(start, freq=freq).start_time
        assert clnd.end_time == get_period(end, freq=freq).end_time

        bdays_in_year = {
            2005: 248, 2006: 248, 2007: 249,
            2008: 250, 2009: 249, 2010: 249, 2011: 248, 2012: 249, 2013: 247,
            2014: 247, 2015: 247, 2016: 247, 2017: 247, 2018: 247
        }
        for year, bdays in bdays_in_year.iteritems():
            assert clnd.get_interval('01 Jan {}'.format(year),
                                     period='A').count() == bdays

        # a regular week
        for day in range(21, 25):
            ws = clnd("{} Nov 2017".format(day))
            assert ws.is_on_duty
            assert ws.label == 8
        for day in range(25, 27):
            ws = clnd("{} Nov 2017".format(day))
            assert ws.is_off_duty
            assert ws.label == 0

        # standard holidays
        assert clnd('01 Jan 2008').is_off_duty
        assert clnd('23 Feb 2017').is_off_duty
        # week day made a day off
        assert clnd('24 Feb 2017').is_off_duty
        # weekend made a working day
        assert clnd('05 May 2012').is_on_duty
        # by default 31 Dec is a working day if not a weekend
        assert clnd('31 Dec 2015').is_on_duty
        # by default a holiday eve has shorter hours
        assert clnd('22 Feb 2017').label == 7

    def test_calendar_RU_week8x5_31dec_off(self):
        clnd = RU.Week8x5(work_on_dec31=False)
        for y in range(2008,2019):
            assert clnd("31 Dec {}".format(y)).is_off_duty

    def test_calendar_RU_week8x5_no_short_eves(self):
        clnd = RU.Week8x5(short_eves=False)
        assert clnd('22 Feb 2017').label == 8

    def test_calendar_RU_week8x5_custom_amds(self):
        clnd = RU.Week8x5(custom_amendments={'22 Feb 2017 00:00': 0,
                                             '23.02.2017': 8})
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_off_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_off_duty
        assert clnd('01 May 2017').is_off_duty

    def test_calendar_RU_week8x5_custom_amds_ambiguous(self):
        # custom_amendments keys should stick to the same timestamp reference as
        # pre-configured amendments. We cannot match the duplicates
        # because we do not know whether different keys
        # refer to the same base unit until the timeline is created.
        with pytest.raises(KeyError):
            RU.Week8x5(custom_amendments={'22 Feb 2017 13:00': 0,
                                          '23 Feb 2017 15:00': 8})


    def test_calendar_RU_week8x5_only_custom_amds(self):
        clnd = RU.Week8x5(only_custom_amendments=True,
                          custom_amendments={'22 Feb 2017': 0,
                                             '23 Feb 2017': 8})
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_off_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_on_duty
        assert clnd('01 May 2017').is_on_duty


    def test_calendar_RU_week8x5_no_amds(self):
        clnd = RU.Week8x5(do_not_amend=True,
                          only_custom_amendments=True,
                          custom_amendments={'22 Feb 2017': 0,
                                             '23 Feb 2017': 8}
                          )
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_on_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_on_duty
        assert clnd('01 May 2017').is_on_duty

    def test_calendar_RU_week8x5_select_years(self):

        clnd = RU.Week8x5('01 Jan 2010','31 Dec 2015')
        assert clnd.start_time == datetime.datetime(2010, 01, 01, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2015, 12, 31, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2016, 01, 01, 0, 0, 0)
        # if only year is given, the 1st of Jan is implied at the both ends
        clnd = RU.Week8x5('2010','2015')
        assert clnd.start_time == datetime.datetime(2010, 01, 01, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2015, 01, 01, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2015, 01, 02, 0, 0, 0)

    def test_calendar_RU_week8x5_OOB(self):
        with pytest.raises(OutOfBoundsError):
            RU.Week8x5('1990')
        with pytest.raises(OutOfBoundsError):
            RU.Week8x5('2008', '31 Dec 2019')









