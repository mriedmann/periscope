
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
    def get_result(self, *args, **kwargs) -> CheckResult:
        return Unk("No check implemented")
    
    def get_help(self):
        return self.__doc__
    
    def get_args(self):
        return []
    
    def get_name(self):
        return self.__class__.__name__
