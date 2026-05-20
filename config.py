"""
class Config : myqobuz settings

    Create Config instance to import
"""

import os
import json
from pathlib import Path

# config file in current directory
CONFIG_FILE = "config.json"


def dict_merge(dict1, dict2):
    for key in dict2:
        if (
            key in dict1
            and isinstance(dict1[key], dict)
            and isinstance(dict2[key], dict)
        ):
            dict_merge(dict1[key], dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1


class Config(dict):
    """
    configuration class
    """

    DEFAULT_CONFIG = {
        "login": {
            "user_id": "",
            "app_id": "",
            "secrets": "",
            "auth_token": "",
            "private_key": "",
        },
        "album": {
            "cover_size": "large",
            "cover_dir": str(Path.home()),
        },
        "qobuz_module": "",
    }

    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.read(self.config_file)

    def read(self, config_file):
        """
        return settings from config file
        """
        self.config_file = config_file
        # read config file for login and preferences
        try:
            with open(config_file, encoding="utf8") as fconf:
                config = json.load(fconf)
            return dict_merge(self.DEFAULT_CONFIG, config)
        except FileNotFoundError:
            print(
                f'FAILED to load "{config_file}" file from current path "{os.getcwd()}" : use a default config'
            )
            return self.DEFAULT_CONFIG

    def write(self):
        """write config file"""
        with open(self.config_file, "w", encoding="utf8") as f:
            f.write(json.dumps(self.config, indent=4))

    def get_config(self):
        """return config dict"""
        return self.config


# create config instance
qobuz_config = Config(CONFIG_FILE)
