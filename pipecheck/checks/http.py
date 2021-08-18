import ssl

import certifi
import urllib3

from pipecheck.checks.check import check
from pipecheck.api import CheckResult, Ok, Warn, Err


@check
def http(
    url,
    http_status=list(range(200, 208)) + list(range(300, 308)),
    http_method="HEAD",
    ca_certs=certifi.where(),
    insecure=False,
) -> CheckResult:
    '''HTTP request checking on response status (not >=400)'''

    if insecure:
        urllib3.disable_warnings()

    def request(cert_reqs):
        h = urllib3.PoolManager(ca_certs=ca_certs, cert_reqs=cert_reqs)
        try:
            response = h.request(http_method, url, retries=False)
            if response.status in http_status:
                return Ok(f"HTTP {http_method} to '{url}' returned {response.status}")
            return Err(f"HTTP {http_method} to '{url}' returned {response.status}")
        finally:
            h.clear()

    try:
        return request(cert_reqs=ssl.CERT_REQUIRED)
    except urllib3.exceptions.SSLError as e:
        if not insecure:
            return Err(f"HTTP {http_method} to '{url}' failed ({e})")
        result = request(cert_reqs=ssl.CERT_NONE)
        msg = f"{result.msg}. SSL Certificate verification failed on '{url}' ({e})"
        if isinstance(result, Ok):
            return Warn(msg)
        else:
            return Err(msg)
    except Exception as e:
        return Err(f"HTTP {http_method} to '{url}' failed ({e.__class__}: {e})")
