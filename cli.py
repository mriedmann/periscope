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

def extend_args_from_dict(y, args):
    for opt in y['options']:
        setattr(args,opt,y['options'][opt])
    for check in y['checks']:
        arg = next(iter(check))
        param = check[arg]
        setattr(args,arg,param)