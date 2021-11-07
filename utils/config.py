# Std Lib Imports
pass

# 3rd Party Imports
pass

# Local Imports
import yaml
from dotted_dict import DottedDict


def load_config():
    with open("config.yaml") as file:
<<<<<<< HEAD
        config = yaml.safe_load(file)
=======
        config = yaml.load(file)
>>>>>>> 0af49079da6c7edef51ab4e65fe47928bde3a227
    return DottedDict(config)

# TODO config schema verifier?