from functools import wraps
from inspect import signature
from typing import Callable

from pipecheck.api import Probe

_probes = {}

class AdhocProbe(Probe):
    _f: Callable = lambda *args: args
    _args: list[str] = []
    _help: str = ""

    def __init__(self, f, args=[], help=""):
        self._f = f
        self._args = args
        self._help = help

    def get_result(self, *args, **kwargs):
        return self._f(*args, **kwargs)
    
    def get_help(self):
        return self._help
    
    def get_args(self):
        return self._args
    
    def get_name(self):
        return self._f.__name__

    def to_dict(self):
        return {"f": self._f, "args": self._args, "help": self._help}

def check(help):
    def wrap(f):
        sig = signature(f)
        _probes[f.__name__] = AdhocProbe(f, list(sig.parameters.keys()), help)

        @wraps(f)
        def wrapped_f(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapped_f

    return wrap

def get_probes():
    return _probes
