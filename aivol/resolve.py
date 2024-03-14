import os
import sys
import yaml

# Global variable to store the root path
ROOT_PATH = None

def find_config_file(starting_directory):
    """Recursively search upwards from the starting directory to find the configuration file."""
    current_dir = starting_directory
    while True:
        local_config_path = os.path.join(current_dir, 'paths.local.yml')
        default_config_path = os.path.join(current_dir, 'paths.yml')
        if os.path.exists(local_config_path):
            return local_config_path
        elif os.path.exists(default_config_path):
            return default_config_path
        else:
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached the root of the file system
                break
            current_dir = parent_dir
    return None

def resolve(path):
    """Resolve the path using the root path, initializing it if necessary."""
    global ROOT_PATH
    if ROOT_PATH is None:
        if '__file__' in dir(sys.modules['__main__']):
            entry_point_path = os.path.abspath(sys.modules['__main__'].__file__)
            config_file_path = find_config_file(os.path.dirname(entry_point_path))
        else:
            # Handle the case when running from an interpreter or a situation where __main__.__file__ is not set
            config_file_path = find_config_file(os.getcwd())
        if config_file_path:
            with open(config_file_path, 'r') as file:
                try:
                    config = yaml.safe_load(file)
                    ROOT_PATH = config.get('root', None)
                except Exception as e:
                    print(f"Error reading or parsing the configuration file: {e}", file=sys.stderr)
                    ROOT_PATH = None
        if ROOT_PATH is None:
            ROOT_PATH = os.getenv('AIVOL_ROOT_PATH', "")
    if path.startswith("/"):
        return os.path.join(ROOT_PATH, path.lstrip('/'))
    else:
        return os.path.join(ROOT_PATH, path)
