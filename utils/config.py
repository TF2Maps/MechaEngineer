# Std Lib Imports
pass

# 3rd Party Imports
pass

# Local Imports
import yaml
from dotted_dict import DottedDict


def load_config():
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=yaml.Loader)
    return DottedDict(config)

