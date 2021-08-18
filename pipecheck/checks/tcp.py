import socket

from pipecheck.checks.check import check
from pipecheck.api import CheckResult, Ok, Err


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
