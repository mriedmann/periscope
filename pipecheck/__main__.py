#!/usr/bin/env /usr/bin/python3

import concurrent.futures
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

commands = []
results = []


def print_result(result: CheckResult):
    if isinstance(result, Warn):
        print(colored("[WARN]  ", "yellow"), result.msg)
    elif isinstance(result, Ok):
        print(colored("[OK]    ", "green"), result.msg)
    elif isinstance(result, Err):
        print(colored("[ERROR] ", "red"), result.msg)


def launch_checks(commands):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for cmd in commands:
            yield (cmd, executor.submit(cmd[0]))


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
    launched_checks = ic(list(launch_checks(calls)))
    return_code = 0
    for (cmd, future) in launched_checks:
        result = future.result()
        print_result(result)
        labels = {k: v for k, v in cmd[0].get_labels().items() if k in CHECK_STATE_LABLES}
        CHECK_STATES[cmd[1]].labels(**labels).state(result.__class__.__name__)
        if isinstance(result, Err):
            return_code = 1

    return return_code


if __name__ == "__main__":
    args = parse_args()

    if not ("verbose" in args and args["verbose"]):
        ic.disable()
    ic(args)

    calls = list(gen_calls(args))
    ic(calls)

    if "interval" in args and args["interval"]:
        start_http_server(args["port"])
        while True:
            run(calls)
            time.sleep(float(args["interval"]))
    else:
        exit(run(calls))
