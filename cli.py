import argparse
from checks import checks
import certifi

def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Simple system-context testing tool')

    parser.add_argument("-v", "--verbose",
                        action=argparse.BooleanOptionalAction,
                        help="enabled detailed output (might be hard to parse)")

    parser.add_argument("-f", "--file",
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
                        default=certifi.where(),
                        help="sets path to ca-bundle, set to nothing to disable certificate check")

    for check in checks:
        parser.add_argument('--%s' % checks[check]['f'].__name__, nargs='*', help=checks[check]['help'])

    return vars(parser.parse_args(args=args))

def parse_dns(x):
    if '=' in x:
        (hostname, target) = x.split('=')
        if ',' in target:
            targets = target.split(',')
        else:
            targets = [target]
    else:
        hostname = x
        targets = []
    return {'type': 'dns', 'name': hostname, 'ips': targets}

def parse_tcp(x):
    (host, port) = x.split(':')
    return {'type': 'tcp', 'host': host, 'port': int(port)}

def parse_http(x):
    return {'type': 'http', 'url': x}

def parse_ping(x):
    return {'type': 'ping', 'host': x}

def get_commands_and_config_from_args(args: dict):
    l_checks = {}
    for check in checks:
        l_check = args.pop(check)
        if l_check:
            l_checks[check] = l_check

    commands = []
    for check in l_checks:
        for param in l_checks[check]:
            commands.append(globals()[f'parse_{check}'](param))
    return (commands, args)
