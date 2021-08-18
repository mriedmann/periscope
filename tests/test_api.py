import unittest
from typing import Type

from parameterized import parameterized

from pipecheck.api import Probe


class ApiCheckTests(unittest.TestCase):
    def test_help(self):
        probe = Probe()
        self.assertEqual(probe.get_help(), probe.__doc__)


if __name__ == "__main__":
    unittest.main()
