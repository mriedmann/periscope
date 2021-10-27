import re

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
    http_headers: dict = {}
    content_regex: str = None
    content_exact: str = None
    ca_certs: str = certifi.where()
    insecure: bool = False
    _last_response = None

    def _get_content_checks(self):
        checks = []
        if self.content_regex is not None:
            checks.append((f"regex: {self.content_regex}", lambda x: bool(re.match(self.content_regex, x))))
        if self.content_exact is not None:
            checks.append((f"exact: {self.content_exact}", lambda x: self.content_exact == str(x).strip()))
        return checks

    def _request(self, verify):
        response = ic(
            requests.request(self.http_method, self.url, timeout=self.http_timeout, headers=self.http_headers, verify=verify)
        )
        self._last_response = response
        if ic(response.status_code) in self.http_status:
            checks = self._get_content_checks()
            if len(checks) > 0:
                for check in checks:
                    if not check[1](response.text):
                        return Err(f"HTTP {self.http_method} to '{self.url}' failed content-check '{check[0]}'")
                return Ok(
                    f"HTTP {self.http_method} to '{self.url}' returned {response.status_code}"
                    + " and passed all content checks"
                )
            else:
                return Ok(f"HTTP {self.http_method} to '{self.url}' returned {response.status_code}")
        return Err(f"HTTP {self.http_method} to '{self.url}' returned {response.status_code}")

    def __call__(self) -> CheckResult:
        if self.insecure:
            requests.packages.urllib3.disable_warnings()

        try:
            return self._request(verify=True)
        except requests.exceptions.SSLError as e:
            if not self.insecure:
                return Err(f"HTTP {self.http_method} to '{self.url}' failed ({e})")
            result = self._request(verify=False)
            msg = f"{result.msg}. SSL Certificate verification failed on '{self.url}' ({e})"
            if isinstance(result, Ok):
                return Warn(msg)
            else:
                return Err(msg)
        except Exception as e:
            return Err(f"HTTP {self.http_method} to '{self.url}' failed ({e.__class__}: {e})")
