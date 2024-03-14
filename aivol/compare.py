from .config import universal_load, flatten_dict, folder_to_file, all_equal
import csv
import sys

def compare_configs(config_files):
    configs = []

    for name in config_files:
        name = folder_to_file(name)
        config = universal_load(name)
        if config is None:
            print(f"Config file {name} not found or not parsed.")
            continue
        flattened_config = flatten_dict(config, sep='--')
        configs.append(flattened_config)

    keys = set()

    for config in configs:
        keys.update(config.keys())

    import csv
    writer = csv.writer(sys.stdout)
    for k in keys:
        row = [k]
        strs = [str(config.get(k, "...")) for config in configs]
        if all_equal(strs):
            continue
        row.extend(strs)
        writer.writerow(row)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compare configuration files and optionally output the \
result to a CSV file for opening in Excel. Use '> csv_file.csv' to redirect output.")
    parser.add_argument('config_files', nargs='+', help='List of configuration files to compare.')
    args = parser.parse_args()

    compare_configs(args.config_files)

if __name__ == "__main__":
    main()
