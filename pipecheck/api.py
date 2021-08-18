from inspect import signature
from typing import Any


class CheckResult:
    msg: str = ""

    def __init__(self, msg) -> None:
        self.msg = msg


class Ok(CheckResult):
    pass


class Warn(CheckResult):
    pass


class Err(CheckResult):
    pass


class Unk(CheckResult):
    pass


class Probe:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_help(self):
        return self.__doc__

    def get_type(self):
        return self.__class__.__name__.replace("Probe", "").lower()

    def get_args(self):
        return signature(self.__call__).parameters.keys()
    
    def get_labels(self):
        return {}

    def __call__(self) -> CheckResult:
        return Unk("No check implemented")
