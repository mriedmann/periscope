import icmplib

from pipecheck.checks.check import check
from pipecheck.api import CheckResult, Ok, Warn, Err


@check
def ping(host, ping_count) -> CheckResult:
    '''ICMP ping check'''

    h = icmplib.ping(host, privileged=False, count=ping_count)
    if h.is_alive:
        if h.packet_loss > 0.0:
            return Warn(f"ICMP '{host}' ({h.address}) unreliable! packet loss {h.packet_loss*100}%")
        return Ok(f"ICMP '{host}' reachable ({h.avg_rtt}ms)")
    return Err(f"ICMP '{host}' unreachable")
