#!/usr/bin/env /usr/bin/python3

import argparse
from termcolor import colored
import icmplib
import socket
from netaddr import IPNetwork, IPAddress
import urllib3
import yaml
from inspect import signature
import concurrent.futures

urllib3.disable_warnings() #suppress cert warning

#### globals

checks = []
check_args = {}
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

#### helper functions

class CheckResult:
    msg: str = ""

    def __init__(self, msg) -> None:
        self.msg = msg

class Ok(CheckResult):
    pass

class Warn(Ok):
    pass

class Err(CheckResult):
    pass

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

def check(help):
    def wrap(f):
        sig = signature(f)
        check_args[f.__name__] = list(sig.parameters.keys())[1:]
        checks.append(f)
        parser.add_argument('--%s' % f.__name__, nargs='*', help=help)
        def wrapped_f(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_f
    return wrap

#### checks

@check("ICMP ping check")
def ping(x, ping_count) -> CheckResult:
    host = icmplib.ping(x, privileged=False,count=ping_count)
    if host.is_alive:
        if host.packet_loss > 0.0:
            return Warn(f"ICMP '{x}' ({host.address}) unreliable! packet loss {host.packet_loss*100}%")
        return Ok(f"ICMP '{x}' reachable ({host.avg_rtt}ms)")
    return Err(f"ICMP '{x}' unreachable")

@check("HTTP request checking on response status (not >=400)")
def http(x, http_method, ca_certs) -> CheckResult:
    method = http_method
    if ca_certs:
        h = urllib3.PoolManager(ca_certs=ca_certs)
    else:
        h = urllib3.PoolManager()
    try:
        response = h.request(method, x)
        if 200 <= response.status <= 299:
            return Ok(f"HTTP {method} to '{x}' returned {response.status}")
        elif 300 >= response.status >= 399:
            return Warn(f"HTTP {method} to '{x}' returned {response.status}")
        return Err(f"HTTP {method} to '{x}' returned {response.status}")
    except urllib3.exceptions.MaxRetryError as e:
        if type(e.reason) == urllib3.exceptions.SSLError:
            result = http(x, http_method, None)
            msg = f"{result.msg}. SSL Certificate verification failed on '{x}' ({e.reason})"
            if isinstance(result, Ok):
                return Warn(msg)
            else:
                return Err(msg)
        return Err(f"HTTP {method} to '{x}' failed ({e.reason})")
    finally:
        h.clear()

@check("Try simple TCP handshake on given host and port (e.g. 8.8.8.8:53)")
def tcp(x, tcp_timeout) -> CheckResult:
    (address, port_text) = x.split(':')
    s = socket.socket()
    s.settimeout(tcp_timeout)
    port = int(port_text)
    try:
        s.connect((address, port)) 
        return Ok(f"TCP connection successfully established to port {port} on {address}")
    except Exception as e: 
        return Err(f"TCP connection failed on port {port} for {address} ({e})")
    finally:
        s.close()

@check("DNS resolution check against given IPv4 (e.g. www.google.com=172.217.23.36) NOTE: it is possible to use subnets as target using CIDR notation")
def dns(x) -> CheckResult:
    if '=' in x:
        (hostname, target) = x.split('=')
        if ',' in target:
            targets = target.split(',')
        else:
            targets = [target]
    else:
        hostname = x
        target = None

    try:
        ip = socket.gethostbyname(hostname)
    except socket.gaierror as e:
        return Err(f"DNS resolution for '{hostname}' failed ({e})")

    if '/' in target:
        if any(IPAddress(ip) in IPNetwork(t) for t in targets):
            return Ok(f"DNS resolution for '{hostname}' returned ip '{ip}' in expected subnet '{target}'")
        return Err(f"DNS resolution for '{hostname}' did not return ip '{ip}' in expected subnet '{target}'")
    elif target:
        if any(ip == t for t in targets):
            return Ok(f"DNS resolution for '{hostname}' returned expected ip '{ip}'")
        return Err(f"DNS resolution for '{hostname}' did not return expected ip '{target}' but '{ip}'")


def run(commands):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(cmd[0], **{'x': cmd[1], **cmd[2]}) for cmd in commands]
        for future in futures:
            yield future.result()

def gen_commands_from_cli(args):
    for f in checks:
        arg = f.__name__
        for param in (getattr(args, arg, []) or []):
            call_args = {}
            for check_arg in check_args[arg]:
                call_args[check_arg] = getattr(args, check_arg)
            yield (f, param, call_args)

def gen_commands_from_yaml(filepath, args):
    with open(filepath, 'r') as yaml_file:
        y = yaml.load(yaml_file, Loader=yaml.FullLoader)
        for opt in y['options']:
            setattr(args,opt,y['options'][opt])
        for check in y['checks']:
            arg = next(iter(check))
            f = globals()[arg]
            call_args = {}
            for check_arg in check_args[arg]:
                call_args[check_arg] = getattr(args, check_arg)
            param = check[arg]
            yield (f, param, call_args)

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