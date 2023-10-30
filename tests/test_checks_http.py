import os
import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Err, Ok, Warn
from pipecheck.checks.http import HttpProbe

httpbin_baseurl = os.getenv("HTTPSTAT_BASEURL") or "https://httpbin.org"
badssl_baseurl = os.getenv("BADSSL_BASEURL") or "https://self-signed.badssl.com"


class CheckHttpTests(unittest.TestCase):
    @parameterized.expand(
        [
            (f"{httpbin_baseurl}/status/200", Ok),
            (f"{httpbin_baseurl}/status/301", Ok),
            (f"{httpbin_baseurl}/status/404", Err),
            (f"{httpbin_baseurl}/status/500", Err),
            (f"{badssl_baseurl}/", Warn),
            (f"{badssl_baseurl}/notfound", Err),
        ]
    )
    def test_http_nocert(self, target, return_type: Type):
        result = HttpProbe(url=target, http_method="GET", insecure=True)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            (f"{httpbin_baseurl}/status/200", Ok),
            (f"{httpbin_baseurl}/status/500", Err),
            (f"{badssl_baseurl}/", Err),
        ]
    )
    def test_http_certcheck(self, target, return_type: Type):
        result = HttpProbe(url=target)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            (f"{httpbin_baseurl}/status/200", [200], Ok),
            (f"{httpbin_baseurl}/status/300", [200, 301], Err),
            (f"{httpbin_baseurl}/status/400", [200, 400], Ok),
        ]
    )
    def test_http_status(self, target, status, return_type: Type):
        result = HttpProbe(url=target, http_status=status)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("single header", {"Test": "testvalue"}),
            ("multiple headers", {"Test": "testvalue", "Test2": "anothertestvalue"}),
        ]
    )
    def test_http_headers(self, _: str, headers: dict):
        test_url = f"{httpbin_baseurl}/headers"
        probe = HttpProbe(url=test_url, http_headers={f"{k}": v for k, v in headers.items()}, http_method="GET")
        result = probe()
        self.assertIsInstance(result, Ok, result.msg)
        subset = {k: v for k, v in probe._last_response.json()["headers"].items() if k in headers}
        print(subset)
        self.assertDictEqual(subset, headers)

    @parameterized.expand(
        [
            ("regex minimal ok", {"content_regex": ".*"}, Ok),
            ("regex ok", {"content_regex": '{"code":200.*'}, Ok),
            ("regex fail", {"content_regex": '.*"THIS DOES NOT EXIST".*'}, Err),
            ("exact ok", {"content_exact": '{"code":200,"description":"OK"}'}, Ok),
            ("exact fail", {"content_exact": "INVALID CONTENT"}, Err),
            ("regex ok exact ok", {"content_regex": ".*", "content_exact": '{"code":200,"description":"OK"}'}, Ok),
            ("regex fail exact ok", {"content_regex": "[.*", "content_exact": '{"code":200,"description":"OK"}'}, Err),
            ("regex ok exact fail", {"content_regex": ".*", "content_exact": '{"code":200,"DDDdescription":"OK"}'}, Err),
            ("regex fail exact fail", {"content_regex": "[.*", "content_exact": '{"code":200,"DDDdescription":"OK"}'}, Err),
        ]
    )
    def test_http_content_checks(self, _: str, checks: dict, return_type: Type):
        test_url = f"{httpbin_baseurl}/base64/eyJjb2RlIjoyMDAsImRlc2NyaXB0aW9uIjoiT0sifQ%3D%3D"
        probe = HttpProbe(url=test_url, http_method="GET", http_headers={"Accept": "text/html"}, **checks)
        result = probe()
        print(probe._last_response.text)
        self.assertIsInstance(result, return_type, result.msg)


if __name__ == "__main__":
    unittest.main()
