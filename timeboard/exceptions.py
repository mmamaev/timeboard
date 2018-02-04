class OutOfBoundsError(LookupError):
    """Raise on attempt to create or access an object which is outside 
    timeboard's bounds."""
    pass


class PartialOutOfBoundsError(ValueError):
    """Raise on attempt to construct an object which partially lays within 
    the timeboard but extends beyond the timeboard's bounds."""
    pass

class VoidIntervalError(ValueError):
    """Raise on attempt to create an empty interval. This includes the case
    when the would-be interval is too short to contain a workshift."""
    pass


class UnacceptablePeriodError(ValueError):
    """Raise on attempt to pass an unsupported or unacceptable calendar 
    frequency."""
    pass

