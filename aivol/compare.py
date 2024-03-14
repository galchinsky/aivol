from config import universal_load, flatten_dict

def compare_configs(config_files):
    configs = []

    for name in config_files:
        config = universal_load(name)
        flattened_config = flatten_dict(config)
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