import timeboard as tb
import datetime
import pytest
import pandas as pd


class TestTBConstructor(object):

    def test_tb_constructor_trivial(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='01 Jan 2017', end='12 Jan 2017',
                            layout=[1])
        assert clnd._timeline.labels.eq([1]*12).all()
        assert clnd.start_time == datetime.datetime(2017, 01, 01, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2017, 01, 12, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2017, 01, 13, 0, 0, 0)
        assert clnd.base_unit_freq == 'D'

    def test_tb_constructor_trivial_with_amendments(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='01 Jan 2017', end='12 Jan 2017',
                            layout=[1],
                            amendments={'11 Jan 2017': 2,
                                        '12 Jan 2017': 3})
        assert clnd._timeline.labels.eq([1]*10 + [2,3]).all()
        assert clnd.start_time == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2017, 1, 12, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2017, 1, 13, 0, 0, 0)
        assert clnd.base_unit_freq == 'D'

    def test_tb_constructor_amendments_outside(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='01 Jan 2017', end='12 Jan 2017',
                            layout=[1],
                            amendments={'31 Dec 2016': 2,
                                        '12 Jan 2017': 3})
        assert clnd._timeline.labels.eq([1]*11 + [3]).all()
        assert clnd.start_time == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2017, 1, 12, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2017, 1, 13, 0, 0, 0)
        assert clnd.base_unit_freq == 'D'

    def test_tb_constructor_bad_layout(self):
        with pytest.raises(TypeError):
            tb.Timeboard(base_unit_freq='D',
                         start='01 Jan 2017', end='12 Jan 2017',
                         layout=1)


    def test_tb_constructor_duplicate_amendments(self):
        with pytest.raises(KeyError):
            tb.Timeboard(base_unit_freq='D',
                         start='01 Jan 2017', end='12 Jan 2017',
                         layout=[1],
                         amendments={'02 Jan 2017 12:00': 2,
                                     '02 Jan 2017 15:15': 3})

    def test_tb_constructor_bad_amendments(self):
        with pytest.raises(TypeError):
            tb.Timeboard(base_unit_freq='D',
                         start='01 Jan 2017', end='12 Jan 2017',
                         layout=[1],
                         amendments=[0])

    def test_tb_constructor_trivial_selector(self):
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='01 Jan 2017', end='12 Jan 2017',
                            layout=[0, 1, 0, 2])
        sdl = clnd.schedules['_default']
        selector = clnd.default_selector
        assert selector(clnd._timeline[1])
        assert map(selector, clnd._timeline.labels) == [False, True] * 6
        assert (sdl.on_duty_index == [1, 3, 5, 7, 9, 11]).all()
        assert (sdl.off_duty_index == [0, 2, 4, 6, 8, 10]).all()

    def test_tb_constructor_trivial_custom_selector(self):

        def custom_selector(x):
            return x>1

        clnd = tb.Timeboard(base_unit_freq='D',
                            start='01 Jan 2017', end='12 Jan 2017',
                            layout=[0, 1, 0, 2],
                            default_selector=custom_selector)
        sdl = clnd.schedules['_default']
        selector = clnd.default_selector
        assert not selector(clnd._timeline[1])
        assert map(selector, clnd._timeline.labels) == [False, False, False,
                                                   True] * 3
        assert (sdl.on_duty_index == [3, 7, 11]).all()
        assert (sdl.off_duty_index == [0, 1, 2, 4, 5, 6, 8, 9, 10]).all()


class TestTBConstructorWithOrgs:

    def test_tb_constructor_week5x8(self):
        week5x8 = tb.Organizer(split_by='W', structure=[[1, 1, 1, 1, 1, 0, 0]])
        amendments = pd.Series(index=pd.date_range(start='01 Jan 2017',
                                                end='10 Jan 2017',
                                                freq='D'),
                               data=0).to_dict()
        clnd = tb.Timeboard(base_unit_freq='D',
                            start='28 Dec 2016', end='02 Apr 2017',
                            layout=week5x8,
                            amendments=amendments)

        assert clnd.start_time == datetime.datetime(2016, 12, 28, 0, 0, 0)
        assert clnd.end_time > datetime.datetime(2017, 04, 02, 23, 59, 59)
        assert clnd.end_time < datetime.datetime(2017, 04, 03, 0, 0, 0)
        assert clnd.base_unit_freq == 'D'
        assert clnd('28 Dec 2016').is_on_duty
        assert clnd('30 Dec 2016').is_on_duty
        assert clnd('31 Dec 2016').is_off_duty
        assert clnd('01 Jan 2017').is_off_duty
        assert clnd('10 Jan 2017').is_off_duty
        assert clnd('11 Jan 2017').is_on_duty
        assert clnd('27 Mar 2017').is_on_duty
        assert clnd('31 Mar 2017').is_on_duty
        assert clnd('01 Apr 2017').is_off_duty
        assert clnd('02 Apr 2017').is_off_duty








#TODO: test timeboards with multiplied freqs

