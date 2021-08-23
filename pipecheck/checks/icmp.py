import icmplib

from pipecheck.api import CheckResult, Err, Ok, Probe, Warn


class PingProbe(Probe):
    """ICMP ping check"""

    host: str = ""
    ping_count: int = 1

    def __call__(self) -> CheckResult:
        h = icmplib.ping(self.host, privileged=False, count=self.ping_count)
        if h.is_alive:
            if h.packet_loss > 0.0:
                return Warn(f"ICMP '{self.host}' ({h.address}) unreliable! packet loss {h.packet_loss*100}%")
            return Ok(f"ICMP '{self.host}' reachable ({h.avg_rtt}ms)")
        return Err(f"ICMP '{self.host}' unreachable")
