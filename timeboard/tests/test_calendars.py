import timeboard.calendars.RU as RU
from timeboard.exceptions import OutOfBoundsError
import datetime
import pytest

class TestCalendarsRU:

    def test_calendar_RU_week8x5(self):

        clnd = RU.Week8x5()
        assert clnd.start_time == datetime.datetime(2005, 01, 01, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2018, 12, 31, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2019, 01, 01, 0, 0, 0)

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

    def test_calendar_RU_week8x5_custome_amds(self):
        clnd = RU.Week8x5(custom_amendments={'22 Feb 2017':0,
                                             '23 Feb 2017':8})
        assert clnd('21 Feb 2017').is_on_duty
        assert clnd('22 Feb 2017').is_off_duty
        assert clnd('23 Feb 2017').is_on_duty
        assert clnd('24 Feb 2017').is_off_duty

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









