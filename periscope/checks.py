import icmplib
import socket
from inspect import signature
from netaddr import IPNetwork, IPAddress
from functools import wraps
import urllib3

checks = {}


def check(help):
    def wrap(f):
        sig = signature(f)
        checks[f.__name__] = {
            'f': f,
            'args': list(sig.parameters.keys()),
            'help': help
        }

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


class Warn(Ok):
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
def http(url, http_method, ca_certs) -> CheckResult:
    method = http_method
    if ca_certs:
        h = urllib3.PoolManager(ca_certs=ca_certs)
    else:
        urllib3.disable_warnings()
        h = urllib3.PoolManager()
    try:
        response = h.request(method, url)
        if 200 <= response.status <= 299:
            return Ok(f"HTTP {method} to '{url}' returned {response.status}")
        elif 300 >= response.status >= 399:
            return Warn(f"HTTP {method} to '{url}' returned {response.status}")
        return Err(f"HTTP {method} to '{url}' returned {response.status}")
    except urllib3.exceptions.MaxRetryError as e:
        if type(e.reason) == urllib3.exceptions.SSLError:
            result = http(url, http_method, None)
            msg = f"{result.msg}. SSL Certificate verification failed on '{url}' ({e.reason})"
            if isinstance(result, Ok):
                return Warn(msg)
            else:
                return Err(msg)
        return Err(f"HTTP {method} to '{url}' failed ({e.reason})")
    finally:
        h.clear()


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


@check("DNS resolution check against given IPv4 (e.g. www.google.com=172.217.23.36) "
       "NOTE: it is possible to use subnets as target using CIDR notation")
def dns(name, ips) -> CheckResult:
    try:
        ip = socket.gethostbyname(name)
    except socket.gaierror as e:
        return Err(f"DNS resolution for '{name}' failed ({e})")

    target = " ".join(ips)
    if '/' in target:
        if any(IPAddress(ip) in IPNetwork(t) for t in ips):
            return Ok(f"DNS resolution for '{name}' returned ip '{ip}' in expected subnet '{target}'")
        return Err(f"DNS resolution for '{name}' did not return ip '{ip}' in expected subnet '{target}'")
    elif target:
        if any(ip == t for t in ips):
            return Ok(f"DNS resolution for '{name}' returned expected ip '{ip}'")
        return Err(f"DNS resolution for '{name}' did not return expected ip '{target}' but '{ip}'")
