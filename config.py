"""
MOdule for reading and maintaining the configuration of the web service.

Usage:
    This contains classes and should not be run directly.
"""

import yaml


class PluginConfig:
    '''
    PluginConfig class
    Reads plugin configuration from a YAML file
    Stores the values in instance variables

    Methods:
        __init__(self, file_path):
            Initializes the PluginConfig object by reading the YAML file
            and storing the values in instance variables.
    '''

    def __init__(
        self,
        file_name="config/plugins.yaml",
    ) -> None:
        '''
        Class constructor

        Reads the YAML file and initializes the instance variables.
        A list of dictionaries is created from the YAML file
            and stored in the instance variable `self.config`.

        Args:
            file_path (str): Path to the YAML configuration file.
        '''

        # Read the YAML file - Automatically stored as a list of dictionaries
        with open(file_name, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
