import argparse
from checks import checks

def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Simple system-context testing tool')

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
    
    return parser.parse_args(args=args)

def rewrite_dns(x):
    if '=' in x:
        (hostname, target) = x.split('=')
        if ',' in target:
            targets = target.split(',')
        else:
            targets = [target]
    else:
        hostname = x
        targets = []
    return { 'name':hostname, 'ips': targets }

def rewrite_tcp(x):
    (host, port) = x.split(':')
    return { 'host':host, 'port': int(port) }

def rewrite_http(x):
    return { 'url': x }

def rewrite_ping(x):
    return { 'host': x }

def gen_commands_from_args(args):
    for check in checks:
        f = checks[check]['f']
        arg = f.__name__
        for param in (getattr(args, arg, []) or []):  
            l_args = vars(args)
            if f'rewrite_{arg}' in globals():
                l_args.update(globals()[f'rewrite_{arg}'](param))
            call_args = {}
            for check_arg in checks[check]['args']:
                if check_arg not in l_args:
                    raise Exception(f"{check_arg} not in {l_args}")
                call_args[check_arg] = l_args[check_arg]
            yield (f, call_args)
