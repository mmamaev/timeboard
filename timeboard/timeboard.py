from .core import _Frame, _Timeline, Organizer


class Timeboard:

    def __init__(self, base_unit_freq, start, end, structure, disruptions=[],
                 selector=None, counter=None, aggregator=None):
        self._base_unit_freq = base_unit_freq
        self._start = start
        self._end = end
        if not isinstance(structure, Organizer):
            if not isinstance(structure, list) :
                raise TypeError("structure value must be either a list "
                                "representing a pattern "
                                "or an instance of Organizer")
            structure = Organizer(split_at=[], pattern=structure)
        frame = _Frame(self._base_unit_freq, self._start, self._end)
        self._timeline = frame.organize(structure).apply_disruptions(disruptions)


