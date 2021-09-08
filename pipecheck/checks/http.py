import certifi
import requests
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
            requests.packages.urllib3.disable_warnings()

        def request(verify):
            response = ic(requests.request(self.http_method, self.url, timeout=self.http_timeout, verify=verify))
            if ic(response.status_code) in self.http_status:
                return Ok(f"HTTP {self.http_method} to '{self.url}' returned {response.status_code}")
            return Err(f"HTTP {self.http_method} to '{self.url}' returned {response.status_code}")

        try:
            return request(verify=True)
        except requests.exceptions.SSLError as e:
            if not self.insecure:
                return Err(f"HTTP {self.http_method} to '{self.url}' failed ({e})")
            result = request(verify=False)
            msg = f"{result.msg}. SSL Certificate verification failed on '{self.url}' ({e})"
            if isinstance(result, Ok):
                return Warn(msg)
            else:
                return Err(msg)
        except Exception as e:
            return Err(f"HTTP {self.http_method} to '{self.url}' failed ({e.__class__}: {e})")
