from pipecheck.checks.dns import DnsProbe
from pipecheck.checks.http import HttpProbe
from pipecheck.checks.icmp import PingProbe
from pipecheck.checks.tcp import TcpProbe
from pipecheck.checks.mysql import MysqlProbe

probes = {}

for cls in [HttpProbe, DnsProbe, PingProbe, TcpProbe, MysqlProbe]:
    probes[cls.get_type()] = cls
