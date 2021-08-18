from functools import wraps
from inspect import signature

from pipecheck.api import Probe

_probes = {}


def make_adhoc_probe(f, args, help=""):
    class AdhocProbe(Probe):
        def __init__(self, **kwargs) -> None:
            self.kwargs = {}
            for check_arg in args:
                if check_arg not in kwargs:
                    continue
                if kwargs[check_arg]:
                    self.kwargs[check_arg] = kwargs[check_arg]

        def __call__(self):
            return f(**self.kwargs)

        def get_labels(self):
            return self.kwargs

        def get_help(self):
            return help

        def get_args(self):
            return args

        def get_type(self):
            return f.__name__
    return AdhocProbe


def check(help):
    def wrap(f):
        sig = signature(f)
        _probes[f.__name__] = make_adhoc_probe(f, list(sig.parameters.keys()), help)

        @wraps(f)
        def wrapped_f(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapped_f

    return wrap

def get_probes():
    return _probes
