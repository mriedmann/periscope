from typing import Callable


class Check:
    f: Callable = lambda *args: args
    args: list[str] = []
    help: str = ""

    def __init__(self, f, args=[], help=""):
        self.f = f
        self.args = args
        self.help = help

    def to_dict(self):
        return {"f": self.f, "args": self.args, "help": self.help}

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
