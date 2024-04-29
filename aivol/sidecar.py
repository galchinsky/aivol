import glob
import os
from .config import universal_load, universal_store
import sys
import os
from typing import Callable, Dict, Iterator
import logging
logging.basicConfig(level=logging.ERROR, format='%(message)s')

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
        # Collect all files in the directory
        all_files = os.listdir(self.directory)

        # Filter files that match the base name pattern
        matching_files = [file for file in all_files if file.startswith(self.base_name) and file != self.base_name]

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
    non_sidecar_files = set()
    sidecar_files = {}

    # Walk through the directory structure recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            if '---' in file:
                base_file, _, _ = file.rpartition('---')
                # Check if the base file exists in the directory structure
                base_file_path = os.path.join(root, base_file)
                if os.path.exists(base_file_path):
                    sidecar_files.setdefault(base_file, []).append(relative_path)
                else:
                    non_sidecar_files.add(relative_path)
            else:
                non_sidecar_files.add(relative_path)
    return non_sidecar_files, sidecar_files

def load_to_pandas(directory: str, identifier: str):
    """
    Loads the data for the whole directory and returns a pandas dataframe
    """
    import pandas as pd

    if not os.path.isdir(directory):
        sys.stderr.write(f"Error: '{directory}' is not a directory.\n")
        return pd.DataFrame()

    # Use list_directory to organize files and then process sidecar files
    all_metadata = []
    non_sidecar_files, sidecar_files = list_directory(directory)

    print ("Loading to pandas...")
    for base_file in non_sidecar_files:
        print (base_file, end='\r')
        sidecar_handler = Handler(os.path.join(directory, base_file), load=False)
        metadata = sidecar_handler.get(identifier)
        if metadata:
            all_metadata.append(metadata)
        else:
            sys.stderr.write(f"\nWarning: No {identifier} metadata found for '{base_file}'\n")
    print ("...done")
    df = pd.DataFrame(all_metadata)

    return df

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
        sidecar_file_path = os.path.join(self.directory, f"{file_path}---{identifier}")
        function(file_path, sidecar_file_path)

def update_and_store_sidecar_file(file, directory, identifier, function, save_interval, index, total_files):
    """
     Helper function for update_and_store_sidecar_files
    """
    try:
        print(f"update_and_store_sidecar_files: [{index+1}/{total_files}] {file}")
        file_path = os.path.join(directory, file)
        handler = Handler(file_path, load=False)
        initial_state = handler.get(identifier) or {}
        sidecar_file_path = f"{file_path}---{identifier}"
        updates_generator = function(file_path, initial_state)

        counter = 0
        for updated_state in updates_generator:
            counter += 1
            if counter % save_interval == 0:
                universal_store(sidecar_file_path, updated_state)

        if counter % save_interval != 0:
            universal_store(sidecar_file_path, updated_state)
    except Exception as e:
        print (e)
        exit(-1)

def update_and_store_sidecar_files(directory: str, identifier: str, function: Callable[[str, Dict], Iterator[Dict]], save_interval: int = 10) -> None:
    """
    Unlike process_sidecar_files, it expects the function to return the updated file and stores it itself
    Kind of wasteful (rewriting the whole file instead of appending), but it will work for most of cases

    Parameters:
    - directory (str): The path to the directory where the non-sidecar and sidecar files are located.
    - identifier (str): A unique identifier used to distinguish between different sidecar files.
    - function (callable): A function that takes (source file path, current state of the sidecar file's data) and returns the updated state.
    - save_interval (int): This parameter controls how often the updated sidecar file data is saved back to disk.
    """
    non_sidecar_files, sidecar_files = list_directory(directory)

    total_files = len(non_sidecar_files)
    for index, file in enumerate(non_sidecar_files):
        update_and_store_sidecar_file(file, directory, identifier, function, save_interval, index, total_files)

def update_and_store_sidecar_files_multiprocess(directory: str,
                                                identifier: str,
                                                function: Callable[[str, Dict],
                                                Iterator[Dict]],
                                                save_interval: int = 10,
                                                workers: int = 16) -> None:
    """
    Multiprocess version of update_and_store_sidecar_files
    """

    import multiprocessing as mp
    ctx = mp.get_context('spawn')
    non_sidecar_files, sidecar_files = list_directory(directory)
    total_files = len(non_sidecar_files)

    # non-multiprocess for sanity check first
    #update_and_store_sidecar_file(non_sidecar_files.pop(), directory, identifier, function, save_interval, 0, total_files)

    with ctx.Pool(workers, ) as p:
        tasks = [(file, directory, identifier, function, save_interval, index, total_files) for index, file in enumerate(non_sidecar_files)]
        p.starmap(update_and_store_sidecar_file, tasks, 1)
