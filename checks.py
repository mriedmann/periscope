import icmplib
import socket
from inspect import signature
from netaddr import IPNetwork, IPAddress
from functools import wraps
import urllib3

urllib3.disable_warnings() #suppress cert warning

checks = {}

def check(help):
    def wrap(f):
        sig = signature(f)
        checks[f.__name__] = {'f':f, 'args': list(sig.parameters.keys())[1:], 'help': help}
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