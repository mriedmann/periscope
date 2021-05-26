#!/usr/bin/env /usr/bin/python3

from cli import parse_args, gen_commands_from_args
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
        futures = [executor.submit(cmd[0], **cmd[1]) for cmd in commands]
        for future in futures:
            yield future.result()

if __name__ == '__main__':
    args = parse_args()
    if args.file:
        raise NotImplementedError("not implemented in this version")
    
    commands = gen_commands_from_args(args)      
    results = run_checks(commands)
    print_results(results)
    if any(isinstance(x, Err) for x in results):
        exit(1)
    else:
        exit(0)