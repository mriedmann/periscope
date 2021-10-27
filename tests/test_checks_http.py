import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Err, Ok, Warn
from pipecheck.checks.http import HttpProbe


class CheckHttpTests(unittest.TestCase):
    @parameterized.expand(
        [
            ("https://httpstat.us/200", Ok),
            ("https://httpstat.us/301", Ok),
            ("https://httpstat.us/404", Err),
            ("https://httpstat.us/500", Err),
            ("https://self-signed.badssl.com/", Warn),
            ("https://self-signed.badssl.com/notfound", Err),
        ]
    )
    def test_http_nocert(self, target, return_type: Type):
        result = HttpProbe(url=target, insecure=True)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", Ok),
            ("https://httpstat.us/500", Err),
            ("https://self-signed.badssl.com/", Err),
        ]
    )
    def test_http_certcheck(self, target, return_type: Type):
        result = HttpProbe(url=target)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", [200], Ok),
            ("https://httpstat.us/300", [200, 301], Err),
            ("https://httpstat.us/400", [200, 400], Ok),
        ]
    )
    def test_http_status(self, target, status, return_type: Type):
        result = HttpProbe(url=target, http_status=status)()
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("single header", {"X-Test": "testvalue"}),
            ("multiple headers", {"X-Test": "testvalue", "X-Test2": "anothertestvalue"}),
        ]
    )
    def test_http_headers(self, _: str, headers: dict):
        test_url = "https://httpbin.org/headers"
        probe = HttpProbe(url=test_url, http_headers=headers, http_method="GET")
        result = probe()
        self.assertIsInstance(result, Ok, result.msg)
        subset = {k: v for k, v in probe._last_response.json()["headers"].items() if k in headers}
        self.assertDictEqual(subset, headers)

    @parameterized.expand(
        [
            ("regex minimal ok", {"content_regex": ".*"}, Ok),
            ("regex ok", {"content_regex": '{"code": 200.*'}, Ok),
            ("regex fail", {"content_regex": '.*"THIS DOES NOT EXIST".*'}, Err),
            ("exact ok", {"content_exact": '{"code": 200, "description": "OK"}'}, Ok),
            ("exact fail", {"content_exact": "INVALID CONTENT"}, Err),
            ("regex ok exact ok", {"content_regex": ".*", "content_exact": '{"code": 200, "description": "OK"}'}, Ok),
            ("regex fail exact ok", {"content_regex": "[.*", "content_exact": '{"code": 200, "description": "OK"}'}, Err),
            ("regex ok exact fail", {"content_regex": ".*", "content_exact": '{"code": 200, "DDDdescription": "OK"}'}, Err),
            ("regex fail exact fail", {"content_regex": "[.*", "content_exact": '{"code": 200, "DDDdescription": "OK"}'}, Err),
        ]
    )
    def test_http_content_checks(self, _: str, checks: dict, return_type: Type):
        test_url = "https://httpstat.us/200"
        probe = HttpProbe(url=test_url, http_method="GET", http_headers={"Accept": "application/json"}, **checks)
        result = probe()
        print(probe._last_response.text)
        self.assertIsInstance(result, return_type, result.msg)


if __name__ == "__main__":
    unittest.main()
