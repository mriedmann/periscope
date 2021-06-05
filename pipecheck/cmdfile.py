import sys

import yaml


def get_config_from_yamlfile(filepath):
    if filepath == "-":
        return yaml.load(sys.stdin, Loader=yaml.FullLoader)

    with open(filepath, "r") as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.FullLoader)


def get_commands_from_config(c):
    commands = []

    def scan(x):
        if "type" in x.keys():
            final_x = dict(filter(lambda elem: not isinstance(elem[1], dict), x.items()))
            commands.append(final_x)
        else:
            for key in x:
                scan(x[key])

    scan(c)
    return commands
