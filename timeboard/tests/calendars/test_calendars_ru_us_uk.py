from timeboard.exceptions import OutOfBoundsError
from timeboard.core import get_period
import timeboard.calendars.RU as RU
import timeboard.calendars.US as US
import timeboard.calendars.UK as UK

import datetime
import pytest

class TestCalendarsRU(object):

    def test_calendar_RU_week8x5(self):

        start = RU.Weekly8x5.parameters()['start']
        end = RU.Weekly8x5.parameters()['end']
        freq = RU.Weekly8x5.parameters()['base_unit_freq']
        clnd = RU.Weekly8x5()
        assert clnd.start_time == get_period(start, freq=freq).start_time
        assert clnd.end_time == get_period(end, freq=freq).end_time

        bdays_in_year = {
            2005: 248, 2006: 248, 2007: 249,
            2008: 250, 2009: 249, 2010: 249, 2011: 248, 2012: 249, 2013: 247,
            2014: 247, 2015: 247, 2016: 247, 2017: 247, 2018: 247, 2019: 247,
        }
        for year, bdays in bdays_in_year.items():
            assert clnd.get_interval('01 Jan {}'.format(year),
                                     period='A').count() == bdays

        bhours_in_year =  {
            2015: 1971, 2016: 1974, 2017: 1973, 2018: 1970, 2019: 1970,
        }
        for year, bhours in bhours_in_year.items():
            assert clnd.get_interval('01 Jan {}'.format(year),
                                     period='A').worktime() == bhours

        # a regular week
        for day in range(20, 25):
            ws = clnd("{} Nov 2017".format(day))
            assert ws.is_on_duty()
            assert ws.label == 8
        for day in range(25, 27):
            ws = clnd("{} Nov 2017".format(day))
            assert ws.is_off_duty()
            assert ws.label == 0
        assert clnd(('20 Nov 2017', '26 Nov 2017')).worktime() == 40

        # standard holidays
        assert clnd('01 Jan 2008').is_off_duty()
        assert clnd('23 Feb 2017').is_off_duty()
        # week day made a day off
        assert clnd('24 Feb 2017').is_off_duty()
        # weekend made a working day
        assert clnd('05 May 2012').is_on_duty()
        # by default 31 Dec is a working day if not a weekend
        assert clnd('31 Dec 2015').is_on_duty()
        # by default a holiday eve has shorter hours
        assert clnd('22 Feb 2017').label == 7

    def test_calendar_RU_week8x5_31dec_off(self):
        clnd = RU.Weekly8x5(work_on_dec31=False)
        for y in range(2008,2020):
            assert clnd("31 Dec {}".format(y)).is_off_duty()

    def test_calendar_RU_week8x5_no_short_eves(self):
        clnd = RU.Weekly8x5(short_eves=False)
        assert clnd('22 Feb 2017').label == 8

    def test_calendar_RU_week8x5_custom_amds(self):
        clnd = RU.Weekly8x5(custom_amendments={'22 Feb 2017 00:00': 0,
                                             '23.02.2017': 8})
        assert clnd('21 Feb 2017').is_on_duty()
        assert clnd('22 Feb 2017').is_off_duty()
        assert clnd('23 Feb 2017').is_on_duty()
        assert clnd('24 Feb 2017').is_off_duty()
        assert clnd('01 May 2017').is_off_duty()

    def test_calendar_RU_week8x5_custom_amds_ambiguous(self):
        # We already have timestamps of 22.02.17 00:00:00 and 23.02.17 00:00:00
        # in amendments dict which is to be update by custom amds.
        # Applying the custom amds below would result in ambiguous keys (two
        # keys referring to the same day) but we preprocess custom_amedndments
        # to align them at the start_time of days in the same manner as
        # in amendments dict
        clnd = RU.Weekly8x5(custom_amendments={'22 Feb 2017 13:00': 0,
                                             '23 Feb 2017 15:00': 8})
        assert clnd('21 Feb 2017').is_on_duty()
        assert clnd('22 Feb 2017').is_off_duty()
        assert clnd('23 Feb 2017').is_on_duty()
        assert clnd('24 Feb 2017').is_off_duty()
        assert clnd('01 May 2017').is_off_duty()


    def test_calendar_RU_week8x5_only_custom_amds(self):
        clnd = RU.Weekly8x5(only_custom_amendments=True,
                            custom_amendments={'22 Feb 2017': 0,
                                             '23 Feb 2017': 8})
        assert clnd('21 Feb 2017').is_on_duty()
        assert clnd('22 Feb 2017').is_off_duty()
        assert clnd('23 Feb 2017').is_on_duty()
        assert clnd('24 Feb 2017').is_on_duty()
        assert clnd('01 May 2017').is_on_duty()


    def test_calendar_RU_week8x5_no_amds(self):
        clnd = RU.Weekly8x5(do_not_amend=True,
                            only_custom_amendments=True,
                            custom_amendments={'22 Feb 2017': 0,
                                             '23 Feb 2017': 8}
                            )
        assert clnd('21 Feb 2017').is_on_duty()
        assert clnd('22 Feb 2017').is_on_duty()
        assert clnd('23 Feb 2017').is_on_duty()
        assert clnd('24 Feb 2017').is_on_duty()
        assert clnd('01 May 2017').is_on_duty()

    def test_calendar_RU_week8x5_select_years(self):

        clnd = RU.Weekly8x5('01 Jan 2010', '31 Dec 2015')
        assert clnd.start_time == datetime.datetime(2010, 1, 1, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2015, 12, 31, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2016, 1, 1, 0, 0, 0)
        # if only year is given, the 1st of Jan is implied at the both ends
        clnd = RU.Weekly8x5('2010', '2015')
        assert clnd.start_time == datetime.datetime(2010, 1, 1, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2015, 1, 1, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2015, 1, 2, 0, 0, 0)

    def test_calendar_RU_week8x5_OOB(self):
        with pytest.raises(OutOfBoundsError):
            RU.Weekly8x5('1990')
        with pytest.raises(OutOfBoundsError):
            RU.Weekly8x5('2008', '31 Dec 2020')

class TestCalendarsUS(object):

    def test_calendar_US_week8x5(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
            # Christmas observance moved forward to Monday
        ]
        clnd0 = US.Weekly8x5(do_not_amend=True)
        assert all([clnd0(d).is_on_duty() for d in holidays_2011])

        clnd1 = US.Weekly8x5()
        #regular week
        assert clnd1(('04 Dec 2017', '10 Dec 2017')).worktime() == 40

        assert all([clnd1(d).is_off_duty() for d in holidays_2011])
        assert clnd0.get_interval('2011', period='A').count() == (
               clnd1.get_interval('2011', period='A').count() +
               len(holidays_2011) - 1)

        # Observance moved backward to Friday:
        assert clnd1('31 Dec 2010').is_off_duty()

        # one-off or irregular holidays
        assert clnd1('05 Dec 2018').is_off_duty()
        assert clnd1('24 Dec 2018').is_off_duty()
        assert clnd1('26 Dec 2018').is_off_duty()

    def test_calendar_US_week8x5_exclusions(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd = US.Weekly8x5(do_not_observe=[
            'independence', 'christmas', 'black_friday',
            'one_off', 'xmas_additional_day'
        ])
        assert clnd('04 Jul 2011').is_on_duty()
        assert clnd('25 Nov 2011').is_on_duty()
        assert clnd('25 Dec 2011').is_off_duty()
        assert clnd('26 Dec 2011').is_on_duty()
        assert clnd('24 Dec 2018').is_on_duty()
        assert clnd('26 Dec 2018').is_on_duty()

    def test_calendar_US_week8x5_short_weekends(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd = US.Weekly8x5(long_weekends=False)
        assert clnd('31 Dec 2010').is_on_duty()
        assert clnd('04 Jul 2011').is_off_duty()
        assert clnd('25 Dec 2011').is_off_duty()
        assert clnd('26 Dec 2011').is_on_duty()

    def test_calendar_US_week8x5_shortened(self):
        holidays_2011_shortened = [
                           '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011'
        ]
        clnd0 = US.Weekly8x5('01 Jan 2011', '30 Nov 2011', do_not_amend=True)
        assert all([clnd0(d).is_on_duty() for d in holidays_2011_shortened])
        clnd1 = US.Weekly8x5('01 Jan 2011', '30 Nov 2011')
        assert all([clnd1(d).is_off_duty() for d in holidays_2011_shortened])
        assert clnd0.get_interval().count() == (
               clnd1.get_interval().count() + len(holidays_2011_shortened))


    def test_calendar_US_week8x5_custom_amds(self):
        holidays_2011 = [
            '31 Dec 2010', '17 Jan 2011', '21 Feb 2011', '30 May 2011',
            '04 Jul 2011', '05 Sep 2011', '10 Oct 2011', '11 Nov 2011',
            '24 Nov 2011', '25 Nov 2011', '26 Dec 2011'
        ]
        clnd = US.Weekly8x5(custom_amendments={'18 Jan 2011': 0,
                                             '26 Dec 2011': 8})

        assert clnd('18 Jan 2011').is_off_duty()
        assert clnd('04 Jul 2011').is_off_duty()
        assert clnd('25 Dec 2011').is_off_duty()
        assert clnd('26 Dec 2011').is_on_duty()


class TestCalendarsUK(object):

    def test_calendar_UK_week8x5_nirl(self):
        holidays_nirl_2016 = [
            '01 Jan 2016', '17 Mar 2016', '25 Mar 2016', '28 Mar 2016',
            '02 May 2016', '30 May 2016', '12 Jul 2016', '29 Aug 2016',
            '26 Dec 2016', '27 Dec 2016'
        ]
        clnd0 = UK.Weekly8x5(country='northern_ireland', do_not_amend=True)
        assert all([clnd0(d).is_on_duty() for d in holidays_nirl_2016])

        clnd1 = UK.Weekly8x5(country='northern_ireland')
        #regular week
        assert clnd1(('04 Dec 2017', '10 Dec 2017')).worktime() == 40

        assert all([clnd1(d).is_off_duty() for d in holidays_nirl_2016])
        assert clnd0.get_interval('2016', period='A').count() == (
               clnd1.get_interval('2016', period='A').count() +
               len(holidays_nirl_2016))

    def test_calendar_UK_week8x5_scot(self):
        holidays_scot_2012 = [
            '02 Jan 2012', '03 Jan 2012', '06 Apr 2012',
            '07 May 2012', '04 Jun 2012', '05 Jun 2012', '06 Aug 2012',
            '30 Nov 2012', '25 Dec 2012', '26 Dec 2012'
        ]
        clnd0 = UK.Weekly8x5(country='scotland', do_not_amend=True)
        assert all([clnd0(d).is_on_duty() for d in holidays_scot_2012])
        clnd1 = UK.Weekly8x5(country='scotland')
        assert all([clnd1(d).is_off_duty() for d in holidays_scot_2012])
        assert clnd0.get_interval('2012', period='A').count() == (
               clnd1.get_interval('2012', period='A').count() +
               len(holidays_scot_2012))

    def test_calendar_UK_week8x5_exclusions(self):
        holidays_scot_2012 = [
            '02 Jan 2012', '03 Jan 2012', '06 Apr 2012',
            '07 May 2012', '04 Jun 2012', '05 Jun 2012', '06 Aug 2012',
            '30 Nov 2012', '25 Dec 2012', '26 Dec 2012'
        ]
        clnd = UK.Weekly8x5(country='scotland',
                            do_not_observe=['new_year', 'good_friday',
                                            'royal', 'summer'])
        assert clnd('01 Jan 2012').is_off_duty()
        assert clnd('03 Jan 2012').is_on_duty()
        assert clnd('06 Apr 2012').is_on_duty()
        assert clnd('07 May 2012').is_off_duty()
        assert clnd('28 May 2012').is_on_duty()
        assert clnd('04 Jun 2012').is_on_duty()
        assert clnd('05 Jun 2012').is_on_duty()
        assert clnd('06 Aug 2012').is_on_duty()
        assert clnd('30 Nov 2012').is_off_duty()

    def test_calendar_UK_week8x5_short_weekends(self):
        clnd = UK.Weekly8x5(country='northern_ireland', long_weekends=False)
        assert clnd('28 Dec 2015').is_on_duty()
        assert clnd('13 Jul 2015').is_on_duty()
        assert clnd('27 Dec 2016').is_on_duty()
        clnd = UK.Weekly8x5(country='scotland', long_weekends=False)
        assert clnd('03 Jan 2012').is_on_duty()

    def test_calendar_UK_week8x5_shortened(self):

        holidays_nirl_2016_shortened = [
            '01 Jan 2016', '17 Mar 2016', '25 Mar 2016', '28 Mar 2016',
            '02 May 2016', '30 May 2016', '12 Jul 2016', '29 Aug 2016',
        ]
        clnd0 = UK.Weekly8x5('01 Jan 2016', '30 Nov 2016',
                             country='northern_ireland', do_not_amend=True)
        assert all([clnd0(d).is_on_duty() for d in holidays_nirl_2016_shortened])
        clnd1 = UK.Weekly8x5('01 Jan 2016', '30 Nov 2016',
                             country='northern_ireland')
        assert all([clnd1(d).is_off_duty() for d in holidays_nirl_2016_shortened])
        assert clnd0.get_interval().count() == (
               clnd1.get_interval().count() +
               len(holidays_nirl_2016_shortened))

    def test_calendar_UK_week8x5_custom_amds(self):
        holidays_scot_2012 = [
            '02 Jan 2012', '03 Jan 2012', '06 Apr 2012',
            '07 May 2012', '04 Jun 2012', '05 Jun 2012', '06 Aug 2012',
            '30 Nov 2012', '25 Dec 2012', '26 Dec 2012'
        ]
        clnd = UK.Weekly8x5(country='scotland',
                            custom_amendments={'18 Jan 2012': 0,
                                             '26 Dec 2012': 8})

        assert clnd('18 Jan 2012').is_off_duty()
        assert clnd('04 Jun 2012').is_off_duty()
        assert clnd('25 Dec 2012').is_off_duty()
        assert clnd('26 Dec 2012').is_on_duty()
