import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Err, Ok, Warn
from pipecheck.checks import http


class CheckHttpTests(unittest.TestCase):

    @parameterized.expand(
        [
            ("https://httpstat.us/200", Ok),
            ("https://httpstat.us/301", Ok),
            ("https://httpstat.us/404", Err),
            ("https://httpstat.us/500", Err),
            ("https://self-signed.badssl.com/", Warn),
        ]
    )
    def test_http_nocert(self, target, return_type: Type):
        result = http(target, insecure=True)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", Ok),
            ("https://httpstat.us/500", Err),
            ("https://self-signed.badssl.com/", Err),
        ]
    )
    def test_http_certcheck(self, target, return_type: Type):
        result = http(target)
        self.assertIsInstance(result, return_type, result.msg)

    @parameterized.expand(
        [
            ("https://httpstat.us/200", [200], Ok),
            ("https://httpstat.us/300", [200, 301], Err),
            ("https://httpstat.us/400", [200, 400], Ok),
        ]
    )
    def test_http_status(self, target, status, return_type: Type):
        result = http(target, status)
        self.assertIsInstance(result, return_type, result.msg)


if __name__ == "__main__":
    unittest.main()
