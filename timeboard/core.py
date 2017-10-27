import pandas as pd
from itertools import dropwhile, count, cycle


def _skiperator(values, direction='forward', skip=0):

    def make_counter():
        nonlocal_vars = {'iters': 0}

        def counter(_):
            flag = nonlocal_vars['iters'] < skip
            nonlocal_vars['iters'] += 1
            return flag

        return counter

    pattern = values
    if direction == 'reverse': pattern = values[::-1]
    counter = make_counter()
    return dropwhile(counter, cycle(pattern))


class _Frame(pd.PeriodIndex) :
    """
    Frame is an ordered time-sequence of Base Units (BU).
    Parameters of constructor:
        base_unit_freq: string - defines duration and anchoring of base units;
                                  notation is as in pandas frequency ('D', 'W', 'H', etc.), 
                                  multipliers are ok (i.e. '4D').
        start: pandas Timestamp, datetime object, or a string convertible to Timestamp  - 
               Base Unit containing this timestamp will be the first BU of the frame.
        end:   same as start but for the last BU of the frame.
        
    If time of start == time of end, or both of them fall into the same BU, 
    then the frame will contain only one BU.
    Frame must contain at least one BU. Empty frames are not allowed. 
    Time of start must precede time of end, otherwise ValueError is raised .
    """
    def __new__ (cls, base_unit_freq, start, end) :
        frame = super(_Frame, cls).__new__(cls, start=start, end=end,
                                           freq=base_unit_freq)
        if len(frame) == 0:
            raise(ValueError,
                  'Empty frame not allowed (make sure the start time precedes the end time')
        frame._base_unit_freq=base_unit_freq
        return frame

    @property
    def start_ts(self):
        return self[0].start_time

    @property
    def end_ts(self):
        return self[-1].end_time

    def apply_pattern(self, pattern, skip_left=0, skip_right=0):
        """
        Promotes frame to timeline by applying pattern to base units.
        Status values are taken from pattern which is iterated in cycles until
        the end of the frame is reached. 
        
        :param pattern: list of status values. By default the pattern application
                        starts at the beginning of the frame; that is, the first 
                        value from pattern is used for the first data unit in 
                        the timeline. This behavior can be changed by supplying
                        non-zero skip_left parameter value.
        :param skip_left: int>=0 - number of idle iterations through pattern before
                          a value is set for the first base unit of the timeline.
        :param skip_right: int - not used; reserved for future support of pattern
                                 application done in reverse.
        :return: instance of _Timeline
        """
        timeline = _Timeline(self)
        pattern_iterator = _skiperator(pattern, direction='forward', skip=skip_left)
        # TODO: support both directions (set direction in Organizer?)
        for i in timeline.index:
            try:
                timeline[i] = next(pattern_iterator)
            except StopIteration:
                raise IndexError('Timeline pattern exhausted since {}'.format(i))
        return timeline

    def split(self, points_in_time):
        """
        Splits frame into subframes at specified points in time.
         
        points_in_time parameter supplies a list of timestamps used to identify
        base units which will become the first base units of split subframes.
        Any elements of points_in_time that cannot define a split are ignored.
        These are:
          - points referring to a base unit already referred to by another point,
          - point referring to the first base unit of the frame,
          - points outside the frame.
        
        If no valid split points are found or points_in_time is empty,
        [self] is returned. 
        
        :param points_in_time: iterable of timestamp-like values
        :return: list of _Frames
        """

        split_positions = map(self._get_loc_wrapper, points_in_time)
        split_positions = set(split_positions)
        split_positions.discard(0)
        split_positions = sorted(list(split_positions))

        start_positions = split_positions[:]
        start_positions.insert(0,0)
        end_positions = map(lambda x:x-1, split_positions)
        end_positions.append(len(self)-1)

        result = []
        for (subf_start, subf_end) in zip(start_positions, end_positions):
            result.append(_Frame(base_unit_freq = self._base_unit_freq,
                                 start = self[subf_start],
                                 end = self[subf_end]))
        return result

    def _get_loc_wrapper(self, x):
        try:
            return self.get_loc(x)
        except KeyError:
            return 0

    def organize(self, organizer):
        """
        Promotes frame to timeline by imposing a structure defined by
        organizer.
        
        :param organizer: instance of Organizer 
        :return: instance of _Timeline
        """
        split_points, skip_units_before_start, skip_units_after_end = [], 0, 0
        if organizer.split_by is not None :
            (split_points,
             skip_units_before_start,
             skip_units_after_end) = self._preprocess_split_by(organizer.split_by)
        if organizer.split_at is not None :
            (split_points,
             skip_units_before_start,
             skip_units_after_end) = self._preprocess_split_at(organizer.split_at)

        timeline = _Timeline(self)
        subframe_seq = self.split(split_points)
        for subframe, application, n in zip(subframe_seq,
                                            cycle(organizer.pattern),
                                            count()):
            if isinstance(application, Organizer):
                subtimeline = subframe.organize(application)
                timeline.loc[subtimeline.index] = subtimeline
            elif isinstance(application, list):
                skip_left = 0
                if n == 0:
                    skip_left = skip_units_before_start
                skip_right = 0
                if n == len(subframe_seq) - 1:
                    skip_right = skip_units_after_end
                subtimeline = subframe.apply_pattern(application,
                                                     skip_left,
                                                     skip_right)
                timeline.loc[subtimeline.index] = subtimeline
            else:
                raise TypeError('Pattern may contain either Splitters ' 
                                'or lists of values')
        return timeline

    def _preprocess_split_by(self, split_by):
        """
        Processes split_by parameter of an Organizer to produce data
        required for structuring the frame. 
        
        The frame is to be split into structural periods (i.e. frame of days
        may be structured by weeks). First or last structural periods may
        be misaligned with frame's boundaries.
        
        :param split_by: str, accepts same values as base_unit_freq 
        :return: tuple of :
                 - list of timestamps defining the split points of the frame
                 - number of base units in the first structural period which 
                   fall outside the frame
                 - number of base units in the last structural period which 
                   fall outside the frame
        """
        stencil = _Frame(base_unit_freq=split_by,
                         start=self.start_ts, end=self.end_ts)
        if stencil.start_ts < self.start_ts:
            left_dangle = _Frame(base_unit_freq=self._base_unit_freq,
                                 start=stencil.start_ts, end=self.start_ts)
            skip_units_before_start = len(left_dangle.difference(self))
        else:
            skip_units_before_start = 0

        if stencil.end_ts > self.end_ts:
            right_dangle = _Frame(base_unit_freq=self._base_unit_freq,
                                  start=self.end_ts, end=stencil.end_ts)
            skip_units_after_end = len(right_dangle.difference(self))
        else:
            skip_units_after_end = 0

        split_points = map(lambda x: x.start_time, stencil)
        return split_points, skip_units_before_start, skip_units_after_end

    def _preprocess_split_at(self, split_at):
        """
        Processes split_by parameter of an Organizer to produce data
        required for structuring the frame. 

        :param split_at: definition of points in time to split the frame at
        :return: tuple of :
                 - list of timestamps defining the split points of the frame
                 - number of base units in the first structural period which 
                   fall outside the frame (always 0 by definition of "split_at")
                 - number of base units in the last structural period which 
                   fall outside the frame (always 0 by definition of "split_at")
        """
        return split_at, 0, 0


class _Timeline(pd.Series):

    def __init__(self, frame, data=None):
        return super(_Timeline, self).__init__(index=frame, data=data)

    def apply_disruptions(self,disruptions):
        return self


class Organizer:

    def __init__(self, split_by=None, split_at=None, pattern=[]):
        if (split_by is None) == (split_at is None) :
            raise ValueError("One and only one of 'split_by' or 'split_at'"
                             "must be specified ")
        if not pattern :
            raise ValueError("Pattern must be non-empty")
        self._split_by = split_by
        self._split_at = split_at
        self._pattern = pattern

    @property
    def split_by(self):
        return self._split_by

    @property
    def split_at(self):
        return self._split_at

    @property
    def pattern(self):
        return self._pattern

