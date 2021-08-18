from functools import wraps
from inspect import signature

from pipecheck.api import Check

_checks = {}

def check(help):
    def wrap(f):
        sig = signature(f)
        _checks[f.__name__] = Check(f, list(sig.parameters.keys()), help)

        @wraps(f)
        def wrapped_f(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapped_f

    return wrap

def get_checks():
    return _checks
