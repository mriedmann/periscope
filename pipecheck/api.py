from inspect import signature


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

    @classmethod
    def get_help(cls):
        return cls.__doc__

    @classmethod
    def get_type(cls):
        return cls.__name__.replace("Probe", "").lower()

    @classmethod
    def get_args(cls):
        return signature(cls.__call__).parameters.keys()

    def get_labels(self):
        return {}

    def __call__(self) -> CheckResult:
        return Unk("No check implemented")
