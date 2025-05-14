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

        update_config(self, new_config):
            Updates the configuration with a new list of dictionaries.
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

        '''
        Config format:

        [
            {
                "name": "<NAME>",
                "description": "<DESC>",
                "webhook": {
                    "url': "<URL>",
                    "secret": <SECRET>,
                    "allowed-ip": [
                        "<IP1>",
                        "<IP2>"
                    ]
                }
            },
            {...}
        ]
        '''

    def update_config(
        self,
        new_config: dict,
    ) -> bool:
        '''
        Updates the configuration with a new list of dictionaries.

        Args:
            new_config (list): New configuration to be set.

        Returns:
            bool: True if the config updated successfully, False otherwise.

        new_config format:
        {
            "plugin_name": <ORIGINAL_NAME>,
            "new_name": "<NEW_NAME>",
            "description": "<DESCRIPTION>",
            "webhook": {
                "url': "<URL>",
                "secret": <SECRET>,
                "allowed-ip": [
                    "<IP1>",
                    "<IP2>"
                ]
        }
        '''

        # Find existing entry in config
        for entry in self.config:
            if (entry['name']) == new_config['plugin_name']:
                # Update the entry with new values
                entry['name'] = new_config['new_name']
                entry['description'] = new_config['description']
                entry['webhook']['url'] = new_config['webhook']['url']
                entry['webhook']['secret'] = new_config['webhook']['secret']
                entry['webhook']['allowed-ip'] = new_config['webhook']['allowed-ip']

                # Save the updated config back to the YAML file
                with open("config/plugins.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(
                        self.config,
                        f,
                        default_flow_style=False,
                        allow_unicode=True
                    )

                return True

        # If no matching entry is found, return False
        print("Entry not found")
        return False


if __name__ == "__main__":
    # This module is not meant to be run directly.
    raise RuntimeError("This module is not meant to be run directly.")
