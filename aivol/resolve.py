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

def resolve_path(path):
    """Resolve the path using the root path, initializing it if necessary."""
    global ROOT_PATH
    if ROOT_PATH is None:
        entry_point_path = os.path.abspath(sys.modules['__main__'].__file__)
        config_file_path = find_config_file(os.path.dirname(entry_point_path))
        if config_file_path:
            with open(config_file_path, 'r') as file:
                try:
                    config = yaml.safe_load(file)
                    ROOT_PATH = config.get('root', None)
                except Exception as e:
                    print(f"Error reading or parsing the configuration file: {e}", file=sys.stderr)
                    ROOT_PATH = None
        if ROOT_PATH is None:
            raise RuntimeError("Root path has not been set. Configuration file not found or not parsed.")
    if path.startswith("/"):
        return os.path.join(ROOT_PATH, path.lstrip('/'))
    else:
        return os.path.join(ROOT_PATH, path)

def main():
    # Example path resolution
    example_paths = ["ai/datasets", "/ai/datasets", "datasets"]
    try:
        for path in example_paths:
            resolved_path = resolve_path(path)
            print(f"Original: {path}, Resolved: {resolved_path}")
    except RuntimeError as e:
        print(e)

if __name__ == "__main__":
    main()
