import sys

import yaml


def get_config_from_yamlfile(filepath):
    if filepath == "-":
        return yaml.load(sys.stdin, Loader=yaml.FullLoader)

    with open(filepath, "r") as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.FullLoader)
