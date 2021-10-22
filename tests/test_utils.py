import unittest

from parameterized import parameterized

from pipecheck.utils import mergedicts


class UtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    @parameterized.expand(
        [
            (
                "L0 merge",
                {"a1": {"b1": {"c1": "a1b1c1"}}},
                {"a2": {"b2": {"c2": "a2b2c2"}}},
                {"a1": {"b1": {"c1": "a1b1c1"}}, "a2": {"b2": {"c2": "a2b2c2"}}},
            ),
            (
                "L0 merge same sub-key",
                {"a1": {"b1": {"c1": "a1b1c1"}}},
                {"a2": {"b2": {"c1": "a2b2c1"}}},
                {"a1": {"b1": {"c1": "a1b1c1"}}, "a2": {"b2": {"c1": "a2b2c1"}}},
            ),
            (
                "L1 merge",
                {"a1": {"b1": {"c1": "a1b1c1"}}},
                {"a1": {"b2": {"c2": "a1b2c2"}}},
                {"a1": {"b1": {"c1": "a1b1c1"}, "b2": {"c2": "a1b2c2"}}},
            ),
            (
                "L2 merge",
                {"a1": {"b1": {"c1": "a1b1c1"}}},
                {"a1": {"b1": {"c2": "a1b1c2"}}},
                {
                    "a1": {
                        "b1": {"c1": "a1b1c1", "c2": "a1b1c2"},
                    }
                },
            ),
            (
                "L2 merge conflicting",
                {"a1": {"b1": {"c1": "a1b1c1_1"}}},
                {"a1": {"b1": {"c1": "a1b1c1_2"}}},
                {"a1": {"b1": {"c1": "a1b1c1_2"}}},
            ),
        ]
    )
    def test_mergedicts(self, msg, dict1, dict2, expected_merged_dict):
        merges_dict = dict(mergedicts(dict1, dict2))
        self.assertDictEqual(expected_merged_dict, merges_dict, msg=msg)
