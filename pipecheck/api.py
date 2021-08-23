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
        for k, v in kwargs.items():
            if v is not None and k in self.__class__.__dict__:
                setattr(self, k, v)

    @classmethod
    def get_help(cls):
        return cls.__doc__

    @classmethod
    def get_type(cls):
        return cls.__name__.replace("Probe", "").lower()

    @classmethod
    def get_args(cls):
        return [i for i in cls.__dict__.keys() if i[:1] != "_"]

    def get_labels(self):
        return {k: getattr(self, k) for k in self.__class__.__dict__ if k[:1] != "_"}

    def __call__(self) -> CheckResult:
        return Unk("No check implemented")

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.get_labels()}>"
