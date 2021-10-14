#!/usr/bin/env /usr/bin/python3

import concurrent.futures
import os
import signal
import sys
import time

from icecream import ic
from prometheus_client import Enum, Summary, start_http_server
from termcolor import colored

from pipecheck.api import CheckResult, Err, Ok, Warn
from pipecheck.checks import probes
from pipecheck.cli import get_commands_and_config_from_args, parse_args
from pipecheck.cmdfile import get_commands_from_config, get_config_from_yamlfile

REQUEST_TIME = Summary("checks_processing_seconds", "Time spent processing all checks")

CHECK_STATE_LABLES = ["url", "host", "port", "name"]
CHECK_STATES = {}

for check in probes:
    labels = [x for x in probes[check].get_args() if x in CHECK_STATE_LABLES]
    CHECK_STATES[check] = Enum(f"{check}_check_state", f"State of check {check}", labels, states=["Ok", "Warn", "Err"])

no_color = False

commands = []
results = []


def supports_color():
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (plat != "win32" or "ANSICON" in os.environ)
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return supported_platform and is_a_tty


def print_result(result: CheckResult):
    if not no_color:
        c = colored
    else:
        c = lambda msg, _: msg

    if isinstance(result, Warn):
        print(c("[WARN]  ", "yellow"), result.msg, flush=True)
    elif isinstance(result, Ok):
        print(c("[OK]    ", "green"), result.msg, flush=True)
    elif isinstance(result, Err):
        print(c("[ERROR] ", "red"), result.msg, flush=True)


def print_error(msg: str):
    print(msg, file=sys.stderr, flush=True)


def gen_calls(args):
    (commands, config) = get_commands_and_config_from_args(args)
    if "file" in args and args["file"]:
        c = ic(get_config_from_yamlfile(args["file"]))
        commands.extend(ic(get_commands_from_config(c)))

    for command in commands:
        yield gen_call(command, config)


def gen_call(command, config):
    f_name = command.pop("type")
    if f_name not in probes:
        raise Exception(f"can't find check of type '{f_name}'")
    l_config = {**config, **command}
    f = probes[f_name](**l_config)
    return (f, f_name)


@REQUEST_TIME.time()
def run(calls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        launched_checks = ic({executor.submit(cmd[0]): cmd for cmd in calls})
        return_code = 0
        for future in concurrent.futures.as_completed(launched_checks):
            cmd = launched_checks[future]
            result = future.result()
            print_result(result)
            labels = {k: v for k, v in cmd[0].get_labels().items() if k in CHECK_STATE_LABLES}
            CHECK_STATES[cmd[1]].labels(**labels).state(result.__class__.__name__)
            if isinstance(result, Err):
                return_code = 1

    return return_code


def signal_handler(signal, frame):
    print_error(f"signal {signal} received. exited.")
    sys.exit(0)


if __name__ == "__main__":
    args = parse_args()

    if not ("verbose" in args and args["verbose"]):
        ic.disable()
    if not supports_color() or ("no_color" in args and args["no_color"]):
        no_color = True
    ic(args)

    calls = list(gen_calls(args))
    ic(calls)
    if len(calls) <= 0:
        print_error("No probes specified")
        sys.exit(0)

    last_status = 0
    if "interval" in args and args["interval"]:
        start_http_server(args["port"])

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while True:
            last_status = run(calls)
            time.sleep(float(args["interval"]))
    else:
        last_status = run(calls)
    exit(last_status)
