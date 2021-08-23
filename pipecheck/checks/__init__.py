from pipecheck.checks.icmp import PingProbe
from pipecheck.checks.http import HttpProbe
from pipecheck.checks.tcp import TcpProbe
from pipecheck.checks.dns import DnsProbe

probes = {}

for cls in [HttpProbe, DnsProbe, PingProbe, TcpProbe]:
    probes[cls.get_type()] = cls
