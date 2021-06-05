import socket
import ssl
from functools import wraps
from inspect import signature

import certifi
import icmplib
import urllib3
from netaddr import IPAddress, IPNetwork

checks = {}


def check(help):
    def wrap(f):
        sig = signature(f)
        checks[f.__name__] = {"f": f, "args": list(sig.parameters.keys()), "help": help}

        @wraps(f)
        def wrapped_f(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapped_f

    return wrap


class CheckResult:
    msg: str = ""

    def __init__(self, msg) -> None:
        self.msg = msg


class Ok(CheckResult):
    pass


class Warn(CheckResult):
    pass


class Err(CheckResult):
    pass


@check("ICMP ping check")
def ping(host, ping_count) -> CheckResult:
    h = icmplib.ping(host, privileged=False, count=ping_count)
    if h.is_alive:
        if h.packet_loss > 0.0:
            return Warn(f"ICMP '{host}' ({h.address}) unreliable! packet loss {h.packet_loss*100}%")
        return Ok(f"ICMP '{host}' reachable ({h.avg_rtt}ms)")
    return Err(f"ICMP '{host}' unreachable")


@check("HTTP request checking on response status (not >=400)")
def http(
    url,
    http_status=list(range(200, 208)) + list(range(300, 308)),
    http_method="HEAD",
    ca_certs=certifi.where(),
    insecure=False,
) -> CheckResult:

    if insecure:
        urllib3.disable_warnings()

    def request(cert_reqs):
        h = urllib3.PoolManager(ca_certs=ca_certs, cert_reqs=cert_reqs)
        try:
            response = h.request(http_method, url, retries=False)
            if response.status in http_status:
                return Ok(f"HTTP {http_method} to '{url}' returned {response.status}")
            return Err(f"HTTP {http_method} to '{url}' returned {response.status}")
        finally:
            h.clear()

    try:
        return request(cert_reqs=ssl.CERT_REQUIRED)
    except urllib3.exceptions.SSLError as e:
        if not insecure:
            return Err(f"HTTP {http_method} to '{url}' failed ({e})")
        result = request(cert_reqs=ssl.CERT_NONE)
        msg = f"{result.msg}. SSL Certificate verification failed on '{url}' ({e})"
        if isinstance(result, Ok):
            return Warn(msg)
        else:
            return Err(msg)
    except Exception as e:
        return Err(f"HTTP {http_method} to '{url}' failed ({e.__class__}: {e})")


@check("Try simple TCP handshake on given host and port (e.g. 8.8.8.8:53)")
def tcp(host, port, tcp_timeout) -> CheckResult:
    s = socket.socket()
    s.settimeout(tcp_timeout)

    try:
        s.connect((host, port))
        return Ok(f"TCP connection successfully established to port {port} on {host}")
    except Exception as e:
        return Err(f"TCP connection failed on port {port} for {host} ({e})")
    finally:
        s.close()


@check(
    "DNS resolution check against given IPv4 (e.g. www.google.com=172.217.23.36) "
    "NOTE: it is possible to use subnets as target using CIDR notation"
)
def dns(name, ips) -> CheckResult:
    try:
        ip = socket.gethostbyname(name)
    except socket.gaierror as e:
        return Err(f"DNS resolution for '{name}' failed ({e})")

    target = " ".join(ips)
    if "/" in target:
        if any(IPAddress(ip) in IPNetwork(t) for t in ips):
            return Ok(f"DNS resolution for '{name}' returned ip '{ip}' in expected subnet '{target}'")
        return Err(f"DNS resolution for '{name}' did not return ip '{ip}' in expected subnet '{target}'")
    elif target:
        if any(ip == t for t in ips):
            return Ok(f"DNS resolution for '{name}' returned expected ip '{ip}'")
        return Err(f"DNS resolution for '{name}' did not return expected ip '{target}' but '{ip}'")
