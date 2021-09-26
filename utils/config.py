# Std Lib Imports
pass

# 3rd Party Imports
pass

# Local Imports
import yaml
from dotted_dict import DottedDict


def load_config():
    with open("config.yaml") as file:
        config = yaml.safe_load(file)
    return DottedDict(config)

# TODO config schema verifier?