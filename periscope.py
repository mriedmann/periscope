#!/usr/bin/env /usr/bin/python3

import argparse
import inspect
from logging import fatal
import re
from termcolor import colored
import icmplib
import socket
from netaddr import IPNetwork, IPAddress
import urllib3
from multiprocessing import Process
import yaml
from inspect import signature

urllib3.disable_warnings() #suppress cert warning

#### globals

ret_code=0
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

def ok(msg):
    if not quiet:
        print(colored('[OK]    ', 'green'), msg)

def warn(msg):
    if not quiet:
        print(colored('[WARN]  ', 'yellow'), msg) 

def err(msg):
    global ret_code
    ret_code = 1
    if not quiet:
        print(colored('[ERROR] ', 'red'), msg) 

def check(help):
    def wrap(f):
        sig = signature(f)
        check_args[f.__name__] = list(sig.parameters.keys())[1:]
        checks.append(f)
        parser.add_argument('--%s' % f.__name__, nargs='*', help=help)
        def wrapped_f(*args, **kwargs):
            f(*args, **kwargs)
        return wrapped_f
    return wrap

#### checks

@check("ICMP ping check")
def ping(x, ping_count):
    host = icmplib.ping(x, privileged=False,count=ping_count)
    if host.is_alive:
        if host.packet_loss > 0.0:
            return warn(f"ICMP '{x}' ({host.address}) unreliable! packet loss {host.packet_loss*100}%")
        return ok(f"ICMP '{x}' reachable ({host.avg_rtt}ms)")
    return err(f"ICMP '{x}' unreachable")

@check("HTTP request checking on response status (not >=400)")
def http(x, http_method, ca_certs):
    method = http_method
    if ca_certs:
        h = urllib3.PoolManager(ca_certs=ca_certs)
    else:
        h = urllib3.PoolManager()
    try:
        response = h.request(method, x)
        if 200 <= response.status <= 299:
            ok(f"HTTP {method} to '{x}' returned {response.status}")
        elif 300 >= response.status >= 399:
            warn(f"HTTP {method} to '{x}' returned {response.status}")
        else:
            err(f"HTTP {method} to '{x}' returned {response.status}")
    except urllib3.exceptions.MaxRetryError as e:
        if type(e.reason) == urllib3.exceptions.SSLError:
            warn(f"SSL Certificate verification failed on '{x}' ({e.reason})")
            http(x, http_method, None)
        else:
            err(f"HTTP {method} to '{x}' failed ({e.reason})")
    finally:
        h.clear()

@check("Try simple TCP handshake on given host and port (e.g. 8.8.8.8:53)")
def tcp(x, tcp_timeout):
    (address, port_text) = x.split(':')
    s = socket.socket()
    s.settimeout(tcp_timeout)
    port = int(port_text)
    try:
        s.connect((address, port)) 
        ok(f"TCP connection successfully established to port {port} on {address}")
    except Exception as e: 
        err(f"TCP connection failed on port {port} for {address} ({e})")
    finally:
        s.close()

@check("DNS resolution check against given IPv4 (e.g. www.google.com=172.217.23.36) NOTE: it is possible to use subnets as target using CIDR notation")
def dns(x):
    if '=' in x:
        (hostname, target) = x.split('=')
        if ',' in target:
            targets = target.split(',')
        else:
            targets = [target]
    else:
        hostname = x
        target = None

    ip = socket.gethostbyname(hostname)
    if not ip:
        return err(f"DNS resolution for '{hostname}' failed")
    ok(f"DNS resolution for '{hostname}' successfull ({ip})")

    if '/' in target:
        if any(IPAddress(ip) in IPNetwork(t) for t in targets):
            ok(f"DNS resolution for '{hostname}' returned ip '{ip}' in expected subnet '{target}'")
        else:
            err(f"DNS resolution for '{hostname}' did not return ip '{ip}' in expected subnet '{target}'")
    elif target:
        if any(ip == t for t in targets):
            ok(f"DNS resolution for '{hostname}' returned expected ip '{ip}'")
        else:
            err(f"DNS resolution for '{hostname}' did not return expected ip '{target}' but '{ip}'")


def run(commands):
    processes = []
    for cmd in commands:
        p = Process(target=cmd[0], kwargs={'x': cmd[1], **cmd[2]})
        processes.append(p)
        p.start()
    for p in processes:
        p.join()

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
    run(commands)
    exit(ret_code)