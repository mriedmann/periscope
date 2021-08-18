import socket

from netaddr import IPAddress, IPNetwork

from pipecheck.checks.check import check
from pipecheck.api import CheckResult, Ok, Err


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
