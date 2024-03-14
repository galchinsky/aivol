import glob
import os
from config import universal_load, universal_store
import sys
import os

# data format comparison for sidecar files:
# json: the worst, because it's hard to append to it
# yaml: ok
# toml: ok
# but text files are bad to store large chunks of data
# pkl: fast, but not human-readable



class Handler:
    def __init__(self, file_path: str, load=True):
        """
        Initializes the Handler with a specific file path.

        Args:
        - file_path (str): The path to the original file.
        """
        self.file_path = file_path
        self.directory, self.base_name = os.path.split(file_path)
        if load:
            self.sidecar_files = self._find()

    def _find(self):
        """
        Looks for sidecar files with any extension and returns a list of the unique identifiers for those sidecar files.

        Returns:
        - list: A list of unique identifiers for the sidecar files found.
        """
        # Define the pattern to search for sidecar files
        pattern = f"{self.base_name}.*"

        # Collect all matching sidecar files
        matching_files = glob.glob(os.path.join(self.directory, pattern))

        # Filter out the original file if it's included in the matching files
        matching_files = [file for file in matching_files if file != self.file_path]

        # Extract the unique identifiers from the file names
        unique_identifiers = set()
        for file in matching_files:
            # Extract the part of the file name between the base name and the extension
            identifier = file.replace(f"{self.base_name}---", "")
            unique_identifiers.add(identifier)

        return list(unique_identifiers)

    def get(self, identifier: str):
        """
        Loads the metadata from the sidecar file with the given identifier.

        Args:
        - identifier (str): The unique identifier for the sidecar file.

        Returns:
        - dict: The metadata from the sidecar file with the given identifier.
        """
        sidecar_file_path = os.path.join(self.directory, f"{self.base_name}---{identifier}")

        # Load the metadata from the sidecar file
        metadata = universal_load(sidecar_file_path)

        return metadata

    def get_all(self):
        """
        Loads the metadata from all sidecar files.

        Returns:
        - dict: A dictionary of metadata from all sidecar files.
        """
        all_metadata = {}
        for identifier in self.sidecar_files:
            metadata = self.get(identifier)
            all_metadata[identifier] = metadata

def list_directory(directory: str):
    all_files = set(os.listdir(directory))
    non_sidecar_files = set()
    sidecar_files = {}

    # Organize files into source and sidecar categories
    for file in all_files:
        if '---' in file:
            base_file, _, _ = file.rpartition('---')
            if base_file in all_files:
                sidecar_files.setdefault(base_file, []).append(file)
            else:
                non_sidecar_files.add(file)
        else:
            non_sidecar_files.add(file)
    return non_sidecar_files, sidecar_files

def load_to_pandas(directory: str, identifier: str):
    """
    Loads the data for the whole directory and returns a pandas dataframe
    """
    import pandas as pd

    # Check if the given identifier is a directory
    if not os.path.isdir(directory):
        sys.stderr.write(f"Error: The provided identifier '{identifier}' is not a directory.\n")
        return pd.DataFrame()  # Return an empty DataFrame if the identifier is not a directory

    # Use load_directory to organize files and then process sidecar files
    all_metadata = []
    non_sidecar_files, sidecar_files = load_directory(directory)

    for base_file, sidecar_file_list in sidecar_files.items():
        sidecar_handler = Handler(directory, base_file, load=False)
        for sidecar_file in sidecar_file_list:
            _, _, identifier = os.path.basename(sidecar_file).rpartition('---')
            metadata = sidecar_handler.get(identifier)
            if metadata:
                all_metadata.append(metadata)
            else:
                sys.stderr.write(f"Warning: No {identifier} metadata found for '{sidecar_file}' in directory '{directory}'\n")

    # Convert the list of metadata dictionaries to a pandas DataFrame
    df = pd.DataFrame(all_metadata)

    return df

def update_and_store_sidecar_files(directory: str, identifier: str, function: Callable[[Dict], Dict], save_interval: int = 10) -> None:
    """
    Unlike process_sidecar_files, it expects the function to return the updated file and stores it itself
    Kind of wasteful (rewriting the whole file instead of appending), but it will work for most of cases

    Parameters:
    - directory (str): The path to the directory where the non-sidecar and sidecar files are located.
    - identifier (str): A unique identifier used to distinguish between different sidecar files.
    - function (callable): A function that takes a single argument (the current state of the sidecar file's data) and returns the updated state.
    - save_interval (int): This parameter controls how often the updated sidecar file data is saved back to disk.
    """
    non_sidecar_files, sidecar_files = list_directory(directory)

    for file in non_sidecar_files:
        file_path = os.path.join(directory, file)
        handler = Handler(file_path)
        working_file = handler.get(identifier)
        if working_file is None:
            working_file = {}
        counter = 0
        while True:
            working_file = function(working_file)
            counter += 1
            if counter % save_interval == 0:
                universal_store(sidecar_file_path, working_file)

        if counter % save_interval != 0:
            universal_store(sidecar_file_path, working_file)


def process_sidecar_files(directory: str, identifier: str, function: Callable[[str, str], None]) -> None:
    """
    For each non-sidecar file calls the function(file_path, sidecar_file_path)
    It expects the function to check whether the sidecar file exists, fully filled and so on

    Parameters:
    - directory (str): The path to the directory containing the files to process.
    - identifier (str): The identifier used to distinguish sidecar files. Example: "identifier.json"
    - function (callable): A function that takes two arguments (file_path, sidecar_file_path)
    """

    non_sidecar_files, sidecar_files = list_directory(directory)

    for file in non_sidecar_files:
        file_path = os.path.join(directory, file)
        sidecar_file_path = os.path.join(self.directory, f"{self.base_name}---{identifier}")
        function(file_path, sidecar_file_path)