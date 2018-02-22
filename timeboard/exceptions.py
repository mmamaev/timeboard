class OutOfBoundsError(LookupError):
    """Raise on an attempt to create or access an object which is outside 
    the bounds of the timeboard or the interval."""
    pass


class PartialOutOfBoundsError(ValueError):
    """Raise on an attempt to construct an object which partially lays within 
    the timeboard but extends beyond the timeboard's bounds."""
    pass


class VoidIntervalError(ValueError):
    """Raise on an attempt to create an empty interval. This includes the case
    creating an interval from a calendar period that is too short to contain 
    a workshift."""
    pass


class UnacceptablePeriodError(ValueError):
    """Raise on an attempt to pass an unsupported or unacceptable calendar 
    frequency."""
    pass

