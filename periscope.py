#!/usr/bin/env /usr/bin/python3

import argparse
from termcolor import colored
import yaml
import concurrent.futures

from checks import CheckResult, checks, Ok, Warn, Err

#### globals

quiet = False
parser = None

parser = argparse.ArgumentParser(description='Simple system-context testing tool')

#### config arguments

parser.add_argument("-f","--file",
    nargs='?', 
    type=str, 
    help="provide a yaml file as configuration")

parser.add_argument("--tcp-timeout", 
    nargs='?', 
    type=float, 
    default=2.0, 
    help="sets the tcp timeout in seconds (e.g 10.5)")

parser.add_argument("--http-method", 
    nargs='?', 
    type=str, 
    default='HEAD', 
    help="sets the HTTP method that should be used (e.g GET)")

parser.add_argument("--ping-count", 
    nargs='?', 
    default=1, 
    help="sets the amount of ICMP ping requests sent")

parser.add_argument("--ca-certs", 
    nargs='?', 
    default='/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt', 
    help="sets path to ca-bundle, set to nothing to disable certificate check")

for check in checks:
    parser.add_argument('--%s' % checks[check]['f'].__name__, nargs='*', help=checks[check]['help'])

#### helper functions

def print_results(results: list[CheckResult]):
    if quiet:
        return
    
    for result in results:
        if isinstance(result, Warn):
            print(colored('[WARN]  ', 'yellow'), result.msg) 
        elif isinstance(result, Ok):
            print(colored('[OK]    ', 'green'), result.msg)
        elif isinstance(result, Err):
            print(colored('[ERROR] ', 'red'), result.msg) 

def run(commands):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(cmd[0], **{'x': cmd[1], **cmd[2]}) for cmd in commands]
        for future in futures:
            yield future.result()

def gen_commands_from_cli(args):
    for check in checks:
        arg = checks[check]['f'].__name__
        for param in (getattr(args, arg, []) or []):
            call_args = {}
            for check_arg in checks[check]['args']:
                call_args[check_arg] = getattr(args, check_arg)
            yield (checks[check]['f'], param, call_args)

def gen_commands_from_yaml(filepath, args):
    with open(filepath, 'r') as yaml_file:
        y = yaml.load(yaml_file, Loader=yaml.FullLoader)
        for opt in y['options']:
            setattr(args,opt,y['options'][opt])
        for check in y['checks']:
            arg = next(iter(check))
            g_check = checks[arg]
            call_args = {}
            for check_arg in g_check['args']:
                call_args[check_arg] = getattr(args, check_arg)
            param = check[arg]
            yield (g_check['f'], param, call_args)

if __name__ == '__main__':
    args = parser.parse_args()
    if args.file:
        commands = gen_commands_from_yaml(args.file, args)
    else:
        commands = gen_commands_from_cli(args)      
    ret_code = 0
    results = run(commands)
    print_results(results)
    if any(isinstance(x, Err) for x in results):
        exit(1)
    else:
        exit(0)