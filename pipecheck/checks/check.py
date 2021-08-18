from functools import wraps
from inspect import signature

from pipecheck.api import Probe
from pipecheck.checks import probes


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

        @classmethod
        def get_help(cls):
            return help

        @classmethod
        def get_args(cls):
            return args

        @classmethod
        def get_type(cls):
            return f.__name__
    return AdhocProbe


def check(f):
    sig = signature(f)
    probes[f.__name__] = make_adhoc_probe(f, list(sig.parameters.keys()), f.__doc__)

    @wraps(f)
    def wrapped_f(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapped_f
