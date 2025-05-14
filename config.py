"""
Module for reading and maintaining the configuration of the web service.

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

        register(self, config):
            Registers a new plugin by adding it to the configuration.
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

    def __len__(
        self
    ) -> int:
        '''
        Magic method to get the length of the config list.

        Returns:
            int: The number of plugins in the config list.
        '''
        return len(self.config)

    def __getitem__(
        self,
        index
    ) -> dict:
        '''
        Magic method to get an item from the config list by index.

        Args:
            index (int): Index of the item to be retrieved.

        Returns:
            dict: The plugin configuration at the specified index.
        '''
        return self.config[index]

    def __iter__(
        self
    ) -> iter:
        '''
        Magic method to iterate over the config list.

        Returns:
            iter: An iterator over the config list.
        '''
        return iter(self.config)

    def __contains__(
        self,
        name
    ) -> bool:
        '''
        Magic method to check if a plugin name exists in the config list.

        Args:
            name (str): Name of the plugin to be checked.

        Returns:
            bool: True if the plugin name exists, False otherwise.
        '''
        return any(entry['name'] == name for entry in self.config)

    def __repr__(
        self
    ) -> str:
        '''
        Magic method to represent the PluginConfig object as a string.

        Returns:
            str: String representation of the PluginConfig object.
        '''
        return f"<PluginConfig plugins={len(self.config)}>"

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
            "name": "<NEW_NAME>",
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
                entry['name'] = (
                    new_config['name']
                )

                entry['description'] = (
                    new_config['description']
                )

                entry['webhook']['url'] = (
                    new_config['webhook']['url']
                )

                entry['webhook']['secret'] = (
                    new_config['webhook']['secret']
                )

                entry['webhook']['allowed-ip'] = (
                    new_config['webhook']['allowed-ip']
                )

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

    def register(
        self,
        config: dict,
    ) -> bool:
        '''
        Registers a new plugin by adding it to the configuration.

        Args:
            config (dict): Configuration for the new plugin.

        Returns:
            bool: True for successful registration, False otherwise.

        config format:
        {
            "name": "<PLUGIN_NAME>",
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

        # Create a new entry
        entry = {
            "name": config['name'],
            "description": config['description'],
            "webhook": {
                "url": config['webhook']['url'],
                "secret": config['webhook']['secret'],
                "allowed-ip": config['webhook']['allowed-ip']
            }
        }

        # Append the new entry to the existing config
        self.config.append(entry)

        # Save the updated config back to the YAML file
        with open("config/plugins.yaml", "w", encoding="utf-8") as f:
            yaml.dump(
                self.config,
                f,
                default_flow_style=False,
                allow_unicode=True
            )

        print(entry)
        return True

    def delete(
        self,
        name: str,
    ) -> bool:
        '''
        Deletes a plugin from the configuration.

        Args:
            name (str): Name of the plugin to be deleted.

        Returns:
            bool: True if the plugin was deleted successfully, False otherwise.
        '''

        # Find and remove the entry
        for entry in self.config:
            if entry['name'] == name:
                # Remove the entry from the list
                self.config.remove(entry)

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
