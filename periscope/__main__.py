#!/usr/bin/env /usr/bin/python3

import concurrent.futures
import time
from icecream import ic
from termcolor import colored
from periscope.cli import get_commands_and_config_from_args, parse_args
from periscope.cmdfile import get_config_from_yamlfile, get_commands_from_config
from periscope.checks import Ok, Warn, Err, CheckResult, checks

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
                continue
            if l_config[check_arg]:
                call_args[check_arg] = l_config[check_arg]
        yield (f, call_args)

def run(args):
    (commands, config) = get_commands_and_config_from_args(args)
    if 'file' in args and args['file']:
        c = ic(get_config_from_yamlfile(args['file']))
        commands.extend(ic(get_commands_from_config(c)))

    calls = list(gen_calls(commands, config))
    ic(calls)

    if 'interval' in args and args['interval']:
        while(True):
            results = ic(list(run_checks(calls)))
            print_results(results)
            time.sleep(float(args['interval']))
    else:
        results = ic(list(run_checks(calls)))
        print_results(results)

    if any([isinstance(x, Err) for x in results]):
        return 1
    else:
        return 0


if __name__ == '__main__':
    args = parse_args()

    if not ('verbose' in args and args['verbose']):
        ic.disable()
    ic(args)

    exit(run(args))
