import argparse

from icecream import ic

from pipecheck import __version__
from pipecheck.checks import probes
from pipecheck.cli_backport import BooleanOptionalAction


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Simple system-context testing tool")

    parser.add_argument(
        "-v", "--verbose", action=BooleanOptionalAction, help="enabled detailed output (might be hard to parse)"
    )

    parser.add_argument("--version", action="version", version="pipecheck {version}".format(version=__version__))

    parser.add_argument("-f", "--file", nargs="?", type=str, help="provide a yaml file as configuration")

    parser.add_argument("--tcp-timeout", nargs="?", type=float, default=2.0, help="sets the tcp timeout in seconds (e.g 10.5)")

    parser.add_argument("--http-status", nargs="*", type=int, help="sets acceptable HTTP status-codes (e.g 200 301 405)")

    parser.add_argument(
        "--http-method", nargs="?", type=str, default="HEAD", help="sets the HTTP method that should be used (e.g GET)"
    )

    parser.add_argument("--http-timeout", nargs="?", type=int, help="sets the tcp timeout in seconds (e.g 2)")

    parser.add_argument("--ping-count", nargs="?", default=1, help="sets the amount of ICMP ping requests sent")

    parser.add_argument("--ca-certs", nargs="?", help="sets path to custom ca-bundle. If not set bundled Root-CAs are used.")

    parser.add_argument(
        "-k", "--insecure", action=BooleanOptionalAction, help="don't fail on tls certificate validation errors"
    )

    parser.add_argument(
        "-i",
        "--interval",
        nargs="?",
        const=5,
        type=int,
        help="don't exit but repeat checks in given interval. Also activates prometheus exporter",
    )

    parser.add_argument("-p", "--port", nargs="?", default=9000, type=int, help="promtheus exporter port")

    for probe in probes:
        parser.add_argument("--%s" % probes[probe].get_type(), nargs="*", help=probes[probe].get_help())

    return vars(parser.parse_args(args=args))


def parse_dns(x):
    if "=" in x:
        (hostname, target) = x.split("=")
        if "," in target:
            targets = target.split(",")
        else:
            targets = [target]
    else:
        hostname = x
        targets = []
    return {"type": "dns", "name": hostname, "ips": targets}


def parse_tcp(x):
    (host, port) = x.split(":")
    return {"type": "tcp", "host": host, "port": int(port)}


def parse_http(x):
    return {"type": "http", "url": x}


def parse_ping(x):
    return {"type": "ping", "host": x}


def get_commands_and_config_from_args(args: dict):
    commands = []
    for k, v in ic(args.items()):
        if v is None or k not in probes:
            continue
        for param in v:
            commands.append(ic(globals()[f"parse_{k}"](param)))
    return (commands, args)
