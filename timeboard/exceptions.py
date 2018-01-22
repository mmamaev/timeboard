class OutOfBoundsError(LookupError):
    """Raise on attempt to create or pass ab object which is outside 
    timeboard's bounds"""
    pass


class VoidIntervalError(ValueError):
    """Raise on attempt to create an empty interval"""
    pass


class UnsupportedPeriodError(ValueError):
    """Raise on attempt to pass an unsupported or unacceptable calendar 
    frequency"""
    pass

