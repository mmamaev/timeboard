from timeboard.core import _Timeline, _Frame, Organizer, RememberingPattern, _to_iterable
from timeboard.exceptions import OutOfBoundsError
from itertools import cycle
import numpy as np
import pandas as pd
import pytest

class TestOrganizerConstructor(object):

    def test_to_iterable(self):
        assert _to_iterable(None) is None
        assert _to_iterable(1) == [1]
        assert _to_iterable('1') == ['1']
        assert _to_iterable([1]) == [1]
        assert _to_iterable(['1']) == ['1']
        assert _to_iterable(set((1,2,3))) == set((1,2,3))
        assert _to_iterable(1==3) == [False]

    def test_organizer_constructor_marker(self):
        org = Organizer(marker='W', structure=[1, 2, 3])
        assert org.marker.each == 'W'
        assert org.marks is None
        assert org.structure == [1, 2, 3]

    def test_organizer_constructor_marks(self):
        org = Organizer(marks=['01 Jan 2017'], structure=[1, 2, 3])
        assert org.marker is None
        assert org.marks == ['01 Jan 2017']
        assert org.structure == [1, 2, 3]

    def test_organizer_constructor_structures_as_str(self):
        with pytest.raises(TypeError):
            Organizer(marks='01 Jan 2017', structure='123')

    def test_organizer_constructor_no_marker_or_marks(self):
        with pytest.raises(ValueError):
            Organizer(structure=[1, 2, 3])

    def test_organizer_constructor_both_marker_and_marks(self):
        with pytest.raises(ValueError):
            Organizer(marker='W', marks='01 Jan 2017', structure=[1, 2, 3])

    def test_organizer_constructor_no_structures(self):
        with pytest.raises(TypeError):
            Organizer(marker='W')

    def test_organizer_constructor_bad_structures(self):
        with pytest.raises(TypeError):
            Organizer(marker='W', structure=1)


class TestOrganizeSimple(object):

    def test_organize_trivial(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marks=[], structure=[[1, 2, 3]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_organize_trivial_string_are_labels(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marks=[], structure=[['ab', 'cd', 'ef']])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq(['ab', 'cd', 'ef', 'ab', 'cd', 'ef', 'ab', 'cd',
                            'ef', 'ab']).all()

    def test_organize_one_mark(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marks=['05 Jan 2017'],
                        structure=[[1, 2, 3], [11, 12]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 11, 12, 11, 12, 11, 12]).all()

    def test_organize_one_mark_as_single_value(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marks='05 Jan 2017',
                        structure=[[1, 2, 3], [11, 12]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 11, 12, 11, 12, 11, 12]).all()

    def test_organize_one_mark_cycle_structures(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marks=['05 Jan 2017'],
                        structure=[[1, 2, 3]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 1, 2, 3, 1, 2, 3]).all()

    def test_organize_simple_marker(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marker='W', structure=[[1, 2, 3], [11, 12]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 11, 12, 11, 12, 11, 12, 11, 1, 2]).all()

    def test_organize_simple_marker_cycle_structures(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marker='W', structure=[[1, 2, 3]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 1, 2, 3, 1, 2, 3, 1, 1, 2]).all()

    def test_organize_marks_outside(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marks=['20 Jan 2017'], structure=[[1, 2, 3]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_organize_marker_outside(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org = Organizer(marker='M', structure=[[1, 2, 3]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 2, 3, 1, 2, 3, 1]).all()

    def test_organize_pattern_with_memory(self):
        f = _Frame(base_unit_freq='D', start='02 Jan 2017',
                   end='22 Jan 2017')
        p = RememberingPattern([1, 2, 3])
        org = Organizer(marker='W', structure=[p, [9], p])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 3, 1, 2, 3, 1,
                            9, 9, 9, 9, 9, 9, 9,
                            2, 3, 1, 2, 3, 1, 2]).all()


class TestOrganizeRecursive(object):

    def test_organize_recursive_mixed(self):
        f = _Frame(base_unit_freq='D', start='01 Jan 2017', end='10 Jan 2017')
        org_int = Organizer(marker='W', structure=[[1, 2, 3]])
        org_ext = Organizer(marks=['06 Jan 2017'],
                            structure=[org_int, [11, 12]])
        t = _Timeline(frame=f, organizer=org_ext)
        assert t.labels.eq([1, 1, 2, 3, 1, 11, 12, 11, 12, 11]).all()

    def test_organize_recursive_2org(self):
        f = _Frame(base_unit_freq='D', start='27 Dec 2016', end='05 Jan 2017')
        org_int1 = Organizer(marks=['30 Dec 2016'],
                             structure=[['a', 'b'],
                                        ['x']])
        org_int2 = Organizer(marker='W', structure=[[1, 2, 3]])
        org_ext = Organizer(marker='M', structure=[org_int1, org_int2])
        t = _Timeline(frame=f, organizer=org_ext)
        assert t.labels.eq(['a', 'b', 'a', 'x', 'x', 1, 1, 2, 3, 1]).all()

    def test_organize_recursive_cycled_org(self):
        f = _Frame(base_unit_freq='D', start='27 Dec 2016', end='05 Jan 2017')
        org_int = Organizer(marker='W', structure=[[1, 2, 3]])
        org_ext = Organizer(marker='M', structure=[org_int])
        t = _Timeline(frame=f, organizer=org_ext)
        assert t.labels.eq([2, 3, 1, 2, 3, 1, 1, 2, 3, 1]).all()

    def test_organize_recursive_with_memory(self):
        f = _Frame(base_unit_freq='D', start='29 Nov 2017', end='06 Dec 2017')
        p = RememberingPattern(['a', 'b', 'c', 'd'])
        org_int = Organizer(marker='W', structure=[[1, 2], p])
        org_ext = Organizer(marker='M', structure=[p, org_int])
        t = _Timeline(frame=f, organizer=org_ext)
        assert t.labels.eq(['a', 'b', 1, 2, 1, 'c', 'd', 'a']).all()

    def test_organize_recursive_complex(self):
        f = _Frame(base_unit_freq='D', start='27 Dec 2016', end='01 Feb 2017')
        # org0 : 27.12.16 - 31.12.16 <-org4 ; 01.01.17 - 01.02.17 <- org1
        # org4 : 27.12.16 - 31.12.16 <-'dec'
        # If we put 'dec' directly into org0.structure it will be anchored
        #   at the start of the year (01.01.16) because marker='A'.
        #   With org4 we anchor 'dec' at the start of the subframe (27.12.16)
        #
        # org1 : 01.01.17 - 31.01.17 <-org2  ; 01.02.17 <- org3
        # org2 : 01.01.17 - 05.01.17 <-org3  ; 06.01.17 - 31.01.17 <- 'z'
        # org3(1) : 01.01.17(Sun) - 05.01.17(Thu) <-[1,2,3] anchored at W-SUN
        # org3(2) : 01.02.17(Wed) <-[1,2,3] anchored at W-SUN
        org3 = Organizer(marker='W', structure=[[1, 2, 3]])
        org2 = Organizer(marks='06 Jan 2017',
                         structure=[org3, ['z']])
        org1 = Organizer(marker='M', structure=[org2, org3])
        org4 = Organizer(marks=[], structure=[['d', 'e', 'c']])
        org0 = Organizer(marker='A', structure=[org4, org1])
        t = _Timeline(frame=f, organizer=org0)
        #result: Dec 27-31               Jan 1-5       rest of Jan      Feb 1
        result = ['d','e','c','d','e'] + [1,1,2,3,1] + ['z']*(31-6+1) + [3]
        assert t.labels.eq(result).all()


class TestOrganizeVariousTypesOfStructure(object):

    def test_organize_with_empty_structure(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0, 0, 0]).all()

    def test_organize_with_empty_pattern_in_structure(self):
        f = _Frame(base_unit_freq='D',
                   start='01 Oct 2017', end='10 Oct 2017')
        org = Organizer(marker='W', structure=[[1,2],[]])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1] + [0]*7 + [1,2]).all()

    def test_organize_structure_as_rememberingpattern(self):
        f = _Frame(base_unit_freq='H',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='D', structure=RememberingPattern([1,2]))
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1,2,1]).all()

    def test_organize_structure_as_empty_rememberingpattern(self):
        f = _Frame(base_unit_freq='H',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='D', structure=RememberingPattern([]))
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0]*72).all()

    def test_organize_structure_element_as_rememberingpattern(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[RememberingPattern([1, 2])])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1, 2, 1]).all()

    def test_organize_structure_element_as_empty_rememberingpattern(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[RememberingPattern([])])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0, 0, 0]).all()

    def test_organize_structure_as_generator(self):
        f = _Frame(base_unit_freq='H',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='D', structure=cycle([1,2]))
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1,2,1]).all()

    def test_organize_structure_as_empty_generator(self):
        f = _Frame(base_unit_freq='H',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='D', structure=cycle([]))
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0]*72).all()

    def test_organize_structure_element_as_generator(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[cycle([1, 2])])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1, 2, 1]).all()

    def test_organize_structure_element_as_empty_generator(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[cycle([])])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0, 0, 0]).all()

    def test_organize_structure_as_numpy_array(self):
        f = _Frame(base_unit_freq='H',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='D', structure=np.array([1,2]))
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1,2,1]).all()

    def test_organize_structure_as_empty_numpy_array(self):
        f = _Frame(base_unit_freq='H',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='D', structure=np.array([]))
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0]*72).all()

    def test_organize_structure_element_as_numpy_array(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[np.array([1,2])])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([1,2,1]).all()

    def test_organize_structure_element_as_empty_numpy_array(self):
        f = _Frame(base_unit_freq='D',
                   start='02 Oct 2017', end='04 Oct 2017 23:59')
        org = Organizer(marker='W', structure=[np.array([])])
        t = _Timeline(frame=f, organizer=org, data=0)
        assert t.labels.eq([0,0,0]).all()


class TestApplyAmendments(object):

    def test_amendments_basic(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {'02 Jan 2017' : 1, '09 Jan 2017' : 2}
        t.amend(amendments)
        assert t.labels.eq([0, 1, 0, 0, 0, 0, 0, 0, 2, 0]).all()

    def test_amendments_timestamps(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {pd.Timestamp('02 Jan 2017'): 1,
                      pd.Timestamp('09 Jan 2017'): 2}
        t.amend(amendments)
        assert t.labels.eq([0, 1, 0, 0, 0, 0, 0, 0, 2, 0]).all()

    def test_amendments_periods(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {pd.Period('02 Jan 2017', freq='D'): 1,
                      pd.Period('09 Jan 2017', freq='D'): 2}
        t.amend(amendments)
        assert t.labels.eq([0, 1, 0, 0, 0, 0, 0, 0, 2, 0]).all()

    def test_amendments_subperiods(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {pd.Period('02 Jan 2017 12:00', freq='H'): 1,
                      pd.Period('09 Jan 2017 15:00', freq='H'): 2}
        t.amend(amendments)
        assert t.labels.eq([0, 1, 0, 0, 0, 0, 0, 0, 2, 0]).all()

    def test_amendments_outside(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {'02 Jan 2017': 1, '11 Jan 2017': 2}
        t.amend(amendments)
        assert t.labels.eq([0, 1, 0, 0, 0, 0, 0, 0, 0, 0]).all()

    def test_amendments_all_outside(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {'02 Jan 2016': 1, '11 Jan 2017': 2}
        t.amend(amendments)
        assert t.labels.eq([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]).all()

    def test_amendments_outside_raise_and_clean(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {'02 Jan 2017': 1, '11 Jan 2017': 2}
        try:
            t.amend(amendments, not_in_range='raise')
        except OutOfBoundsError:
            assert t.labels.eq([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]).all()
        else:
            pytest.fail(msg="DID NOT RAISE KeyError when not_in_range='raise'")

    def test_amendments_empty(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {}
        t.amend(amendments)
        assert t.labels.eq([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]).all()

    def test_amendments_bad_timestamp_raise_and_clean(self):
        t = _Timeline(frame=_Frame(base_unit_freq='D',
                      start='01 Jan 2017', end='10 Jan 2017'),
                      data=0)
        amendments = {'02 Jan 2017': 1, 'bad timestamp': 2}
        try:
            t.amend(amendments)
        except ValueError:
            assert t.labels.eq([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]).all()
        else:
            pytest.fail(msg='DID NOT RAISE for bad timestamp')


class TestOrganizeCompoundWorkshifts(object):

    def test_organize_compound_all(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='10 Jan 2017')
        org = Organizer(marker='W', structure=[1, 2])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([1, 2, 1]).all()
        assert t._frameband.eq([0,0,2,2,2,2,2,2,2,9,9]).all()
        assert (t._wsband.index == [0, 2, 9]).all()

    def test_organize_compound_alternate(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='10 Jan 2017')
        org = Organizer(marker='W', structure=[100, [1, 2, 3]])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq([100, 1, 2, 3, 1, 2, 3, 1, 100]).all()
        assert t._frameband.eq([0,0,2,3,4,5,6,7,8,9,9]).all()
        assert (t._wsband.index == [0, 2,3,4,5,6,7,8, 9]).all()

    def test_organize_compound_when_strings_are_labels(self):
        f = _Frame(base_unit_freq='D', start='31 Dec 2016', end='10 Jan 2017')
        org = Organizer(marker='W', structure=['abc', 'x'])
        t = _Timeline(frame=f, organizer=org)
        assert t.labels.eq(['abc', 'x', 'abc']).all()
        assert t._frameband.eq([0,0,2,2,2,2,2,2,2,9,9]).all()
        assert (t._wsband.index == [0, 2, 9]).all()