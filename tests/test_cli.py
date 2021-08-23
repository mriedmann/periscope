import unittest

from parameterized import parameterized

from pipecheck.cli import get_commands_and_config_from_args, parse_args


class CliTests(unittest.TestCase):
    def assertSubset(self, collection, subset):
        self.assertTrue(subset.items() <= collection.items(), f"{subset} not in {collection}")

    def assertSubsetList(self, collection, subset):
        for i in range(0, len(subset)):
            self.assertSubset(collection[i], subset[i])

    @parameterized.expand(
        [
            (["--http", "https://httpstat.us/200"], {"http": ["https://httpstat.us/200"]}),
            (["--tcp", "8.8.8.8:53"], {"tcp": ["8.8.8.8:53"]}),
            (["--dns", "one.one.one.one"], {"dns": ["one.one.one.one"]}),
            (["--dns", "one.one.one.one=1.1.1.1"], {"dns": ["one.one.one.one=1.1.1.1"]}),
            (["--ping", "8.8.8.8"], {"ping": ["8.8.8.8"]}),
            (["--ping", "8.8.8.8", "1.1.1.1"], {"ping": ["8.8.8.8", "1.1.1.1"]}),
            (
                ["--http", "https://httpstat.us/200", "--tcp", "8.8.8.8:53", "--dns", "one.one.one.one=1.1.1.1,1.0.0.1"],
                {
                    "http": ["https://httpstat.us/200"],
                    "tcp": ["8.8.8.8:53"],
                    "dns": ["one.one.one.one=1.1.1.1,1.0.0.1"]
                }
            ),
        ]
    )
    def test_cli_parser(self, params, expected_args):
        args = parse_args(params)
        self.assertSubset(args, expected_args)

    @parameterized.expand(
        [
            ({"http": ["https://httpstat.us/200"]}, [{"type": "http", "url": "https://httpstat.us/200"}]),
            ({"tcp": ["8.8.8.8:53"]}, [{"type": "tcp", "host": "8.8.8.8", "port": 53}]),
            (
                {"dns": ["one.one.one.one=1.1.1.1,1.0.0.1"]},
                [{"type": "dns", "name": "one.one.one.one", "ips": ["1.1.1.1", "1.0.0.1"]}],
            ),
            ({"dns": ["one.one.one.one"]}, [{"type": "dns", "name": "one.one.one.one", "ips": []}]),
            ({"dns": ["one.one.one.one=1.1.1.1"]}, [{"type": "dns", "name": "one.one.one.one", "ips": ["1.1.1.1"]}]),
            ({"ping": ["8.8.8.8"]}, [{"type": "ping", "host": "8.8.8.8"}]),
            ({"ping": ["8.8.8.8", "1.1.1.1"]}, [{"type": "ping", "host": "8.8.8.8"}, {"type": "ping", "host": "1.1.1.1"}]),
            (
                {"http": ["https://httpstat.us/200"], "tcp": ["8.8.8.8:53"], "dns": ["one.one.one.one=1.1.1.1,1.0.0.1"]},
                [
                    ({"type": "http", "url": "https://httpstat.us/200"}),
                    ({"type": "dns", "name": "one.one.one.one", "ips": ["1.1.1.1", "1.0.0.1"]}),
                    ({"type": "tcp", "host": "8.8.8.8", "port": 53}),
                ],
            ),
        ]
    )
    def test_cli(self, args, expected_commands):
        (commands, _) = list(get_commands_and_config_from_args(args))
        self.assertSubsetList(commands, expected_commands)

    @parameterized.expand(
        [
            (
                ["--http", "https://self-signed.badssl.com/", "--insecure"],
                [{"type": "http", "url": "https://self-signed.badssl.com/"}],
                {"insecure": True},
            ),
            (
                ["--http", "https://self-signed.badssl.com/", "--http-status", "200"],
                [{"type": "http", "url": "https://self-signed.badssl.com/"}],
                {"http_status": [200]},
            ),
            (
                ["--http", "https://self-signed.badssl.com/", "--http-status", "200", "301"],
                [{"type": "http", "url": "https://self-signed.badssl.com/"}],
                {"http_status": [200, 301]},
            ),
        ]
    )
    def test_cli_and_config(self, params, expected_commands, expected_config):
        args = parse_args(params)
        (commands, config) = list(get_commands_and_config_from_args(args))
        self.assertSubsetList(commands, expected_commands)
        self.assertSubset(config, expected_config)


if __name__ == "__main__":
    unittest.main()
