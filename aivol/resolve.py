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

def get_root_from_config(config_file_path):
    """Get the root path from the configuration file."""
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config.get('root', None)

def resolve_root_path():
    """Resolve the root path."""
    # sort of a fallback if nothing helped: just use environment variable
    root_path = os.getenv('AIVOL_ROOT_PATH')
    if root_path is not None:
        return root_path

    # next, check if /ai/paths.yml exists. If it exists, return /ai.
    if os.path.exists("/ai/paths.yml"):
        return "/ai"

    # next, start to look for the configuration file from the current directory
    try:
        config_file_path = find_config_file(os.getcwd())
        return get_root_from_config(config_file_path)
    except Exception as e:
        print(f"Error looking for the configuration file: {e}", file=sys.stderr)
        config_file_path = None

    # next, try to look in the script dir (__main__)
    if '__file__' in dir(sys.modules['__main__']):
        entry_point_path = os.path.abspath(sys.modules['__main__'].__file__)
        config_file_path = find_config_file(os.path.dirname(entry_point_path))
        return get_root_from_config(config_file_path)

    if root_path is None:
        raise OSError("""
Can't find AIVOL_ROOT_PATH. Set the environment variable AIVOL_ROOT_PATH to where you have mounted it.
On linux, temporarily:
    AIVOL_ROOT_PATH=/path/to/aivol python ...
or
    export AIVOL_ROOT_PATH=/path/to/aivol
On linux, permanently:
    echo "export AIVOL_ROOT_PATH=/ai" >> ~/.bashrc
    source ~/.bashrc

On windows, temporarily:
    set AIVOL_ROOT_PATH=/path/to/aivol
""")

def resolve(path):
    """Resolve the path using the root path, initializing it if necessary."""
    global ROOT_PATH
    if ROOT_PATH is None:
        ROOT_PATH = resolve_root_path()
    if path.startswith("/"):
        return os.path.join(ROOT_PATH, path.lstrip('/'))
    else:
        return os.path.join(ROOT_PATH, path)