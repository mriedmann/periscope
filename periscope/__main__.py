#!/usr/bin/env /usr/bin/python3

from periscope.cli import get_commands_and_config_from_args, parse_args
from termcolor import colored
import concurrent.futures
from periscope.cmdfile import get_config_from_yamlfile, get_commands_from_config
from periscope.checks import Ok, Warn, Err, CheckResult, checks
import pprint

commands = []
results = []

def print_results(results: list[CheckResult]):
    for result in results:
        if isinstance(result, Warn):
            print(colored('[WARN]  ', 'yellow'), result.msg)
        elif isinstance(result, Ok):
            print(colored('[OK]    ', 'green'), result.msg)
        elif isinstance(result, Err):
            print(colored('[ERROR] ', 'red'), result.msg)

def print_calls(calls):
    for call in calls:
        f_name = call[0].__name__
        print(f"{f_name:<8}", ': ', call[1])

def run_checks(commands):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(cmd[0], **cmd[1]) for cmd in commands]
        for future in futures:
            yield future.result()

def gen_calls(commands, config):
    for command in commands:
        f_name = command.pop('type')
        if f_name not in checks:
            raise Exception(f"can't find check of type '{f_name}'")
        f = checks[f_name]['f']
        call_args = {}
        l_config = {**config, **command}
        for check_arg in checks[f_name]['args']:
            if check_arg not in l_config:
                raise Exception(f"{check_arg} not in {l_config}")
            call_args[check_arg] = l_config[check_arg]
        yield (f, call_args)


if __name__ == '__main__':
    args = parse_args()
    if 'verbose' in args and args['verbose']:
        pp = pprint.PrettyPrinter()
        print("ARGS")
        pp.pprint(args)
        print()

    (commands, config) = get_commands_and_config_from_args(args)
    if 'file' in args and args['file']:
        c = get_config_from_yamlfile(args['file'])
        commands.extend(get_commands_from_config(c))

    calls = list(gen_calls(commands, config))
    if 'verbose' in args and args['verbose']:
        print("CALLS")
        print_calls(calls)
        print()

    results = run_checks(calls)
    print_results(results)

    if any(isinstance(x, Err) for x in results):
        exit(1)
    else:
        exit(0)
