from .resolve import resolve
from .config import universal_load, universal_store

import os
import shutil
import yaml
from collections import OrderedDict

def start_experiment(project_name, experiment_name, config, group="models"):
    # Resolve the path for the experiment
    experiment_path = resolve(f'{group}/{project_name}/{experiment_name}')

    # Ensure the directory exists
    if not os.path.exists(experiment_path):
        os.makedirs(experiment_path)

    # Determine the config type and handle accordingly
    if isinstance(config, dict):
        config_file_path = os.path.join(experiment_path, 'config.yml')
        with open(config_file_path, 'w') as file:
            yaml.safe_dump(config, file)
    elif isinstance(config, str):
        # Assuming config is a file path
        if os.path.exists(config):
            shutil.copy(config, experiment_path)
        else:
            raise FileNotFoundError(f"Config file {config} not found.")
    else:
        raise ValueError("Config must be a dictionary or file path.")
    return experiment_path

def resume_experiment(project_name, experiment_name, config, group="models"):
    # Resolve the path for the experiment
    experiment_path = resolve(f'{group}/{project_name}/{experiment_name}')

    # Ensure the directory and config file exist
    config_file_path = os.path.join(experiment_path, 'config.yml')
    if not os.path.exists(experiment_path) or not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Experiment or config file not found in path: {experiment_path}")

    # Load existing config
    with open(config_file_path, 'r') as file:
        existing_config = yaml.safe_load(file)

    # Compare the existing config with the provided one
    if isinstance(config, dict):
        if config != existing_config:
            raise ValueError("Provided config does not match the existing one.")
    elif isinstance(config, str):
        # Assuming config is a file path
        if os.path.exists(config):
            with open(config, 'r') as file:
                new_config = yaml.safe_load(file)
                if new_config != existing_config:
                    raise ValueError("Provided config file does not match the existing one.")
        else:
            raise FileNotFoundError(f"Config file {config} not found.")
    else:
        raise ValueError("Config must be a dictionary or file path.")
    return experiment_path

