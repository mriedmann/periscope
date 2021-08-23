import socket

from pipecheck.api import CheckResult, Err, Ok, Probe


class TcpProbe(Probe):
    """Try simple TCP handshake on given host and port (e.g. 8.8.8.8:53)"""

    host: str = ""
    port: int = 0
    tcp_timeout: int = 5

    def __call__(self) -> CheckResult:
        s = socket.socket()
        s.settimeout(self.tcp_timeout)

        try:
            s.connect((self.host, self.port))
            return Ok(f"TCP connection successfully established to port {self.port} on {self.host}")
        except Exception as e:
            return Err(f"TCP connection failed on port {self.port} for {self.host} ({e})")
        finally:
            s.close()
