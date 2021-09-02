import ssl

import certifi
import urllib3
from icecream import ic

from pipecheck.api import CheckResult, Err, Ok, Probe, Warn


class HttpProbe(Probe):
    """HTTP request checking on response status (not >=400)"""

    url: str = ""
    http_status: list = list(range(200, 208)) + list(range(300, 308))
    http_method: str = "HEAD"
    http_timeout: int = 5
    ca_certs: str = certifi.where()
    insecure: bool = False

    def __call__(self) -> CheckResult:
        if self.insecure:
            urllib3.disable_warnings()

        def request(cert_reqs):
            h = urllib3.PoolManager(ca_certs=self.ca_certs, cert_reqs=cert_reqs)
            try:
                response = ic(h.request(self.http_method, self.url, retries=False, timeout=self.http_timeout))
                if ic(response.status) in self.http_status:
                    return Ok(f"HTTP {self.http_method} to '{self.url}' returned {response.status}")
                return Err(f"HTTP {self.http_method} to '{self.url}' returned {response.status}")
            finally:
                h.clear()

        try:
            return request(cert_reqs=ssl.CERT_REQUIRED)
        except urllib3.exceptions.SSLError as e:
            if not self.insecure:
                return Err(f"HTTP {self.http_method} to '{self.url}' failed ({e})")
            result = request(cert_reqs=ssl.CERT_NONE)
            msg = f"{result.msg}. SSL Certificate verification failed on '{self.url}' ({e})"
            if isinstance(result, Ok):
                return Warn(msg)
            else:
                return Err(msg)
        except Exception as e:
            return Err(f"HTTP {self.http_method} to '{self.url}' failed ({e.__class__}: {e})")
