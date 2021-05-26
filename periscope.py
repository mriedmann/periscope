#!/usr/bin/env /usr/bin/python3

from cli import parse_args, extend_args_from_dict
from termcolor import colored
import yaml
import concurrent.futures

from checks import CheckResult, checks, Ok, Warn, Err

#### globals
commands = []
results = []

#### helper functions

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
        futures = [executor.submit(cmd[0], **{'x': cmd[1], **cmd[2]}) for cmd in commands]
        for future in futures:
            yield future.result()

def gen_commands(args):
    for check in checks:
        arg = checks[check]['f'].__name__
        for param in (getattr(args, arg, []) or []):
            call_args = {}
            for check_arg in checks[check]['args']:
                call_args[check_arg] = getattr(args, check_arg)
            yield (checks[check]['f'], param, call_args)

if __name__ == '__main__':
    args = parse_args()
    if args.file:
        with open(args.file, 'r') as yaml_file:
            y = yaml.load(yaml_file, Loader=yaml.FullLoader)
            extend_args_from_dict(y, args)
    
    commands = gen_commands(args)      
    results = run_checks(commands)
    print_results(results)
    if any(isinstance(x, Err) for x in results):
        exit(1)
    else:
        exit(0)