from .config import universal_load, flatten_dict, folder_to_file, all_equal
from .resolve import resolve
import sys
import os
import io
import csv

def generate_ascii_table(data):
    # Extracting headers and ensuring consistent row ordering
    headers = ['keys'] + list(data.keys())
    rows = list(next(iter(data.values())).keys())

    # Calculating column widths
    column_widths = [max(len(row) for row in rows)]
    for header in headers[1:]:
        column_width = max(len(header), max(len(str(data[header][row])) for row in rows))
        column_widths.append(column_width)

    # Create the header row
    header_row = " | ".join(headers[i].ljust(column_widths[i]) for i in range(len(headers)))
    separator = "-+-".join("-" * width for width in column_widths)

    # Create data rows
    data_rows = []
    for row in rows:
        row_data = [row] + [str(data[header][row]) if header in data and row in data[header] else '...' for header in headers[1:]]
        data_row = " | ".join(row_data[i].ljust(column_widths[i]) for i in range(len(row_data)))
        data_rows.append(data_row)

    # Combine all parts
    table = [header_row, separator] + data_rows
    return "\n".join(table)

def compare_configs(config_files, output_format=None, path_prefix=''):
    configs = []

    for name in config_files:
        # name is file name
        # first, try to look the name up in the current directory
        if os.path.exists(name):
            name = folder_to_file(name)
            print(f"Selected {name} relative to the current directory.")
        elif os.path.exists(os.path.join(path_prefix, name)):
            name = folder_to_file(os.path.join(path_prefix, name))
            print(f"Selected {name} from the path prefix.")
        else:
            # try to find the name in the storage
            resolved_name = resolve(os.path.join(path_prefix, name))
            if resolved_name is None:
                print(f"Config file {name} not found.")
                continue
            name = folder_to_file(resolved_name)
            print(f"Selected {name} from the storage.")
        config = universal_load(name)
        if config is None:
            print(f"Config file {name} not found or not parsed.")
            continue
        flattened_config = flatten_dict(config, sep='--')
        configs.append(flattened_config)

    keys = set()
    table = {}

    for config in configs:
        keys.update(config.keys())

    for k in keys:
        values = [config.get(k) for config in configs]
        if k == "_from_file":
            continue
        if all_equal(values):
            continue
        for config in configs:
            model_name = os.path.basename(os.path.dirname(config["_from_file"]))
            if model_name == "":
                model_name = config["_from_file"]
            if model_name not in table:
                table[model_name] = {}
            table[model_name][k] = config.get(k, "...")

    if output_format is None:
        return table
    elif output_format == "json":
        import json
        result = json.dumps(table)
        return result
    elif output_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        for k in keys:
            row = [k]
            strs = [str(config.get(k, "...")) for config in configs]
            if all_equal(strs):
                continue
            row.extend(strs)
            writer.writerow(row)
        return output.getvalue()
    elif output_format == "ascii":
        result = generate_ascii_table(table)
        return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compare configuration files and output the result in ASCII, CSV, or JSON format.")
    parser.add_argument('config_files', nargs='+', help='List of configuration files to compare.')
    parser.add_argument('--csv', action='store_true', help='Output in CSV format.')
    parser.add_argument('--json', action='store_true', help='Output in JSON format.')
    parser.add_argument('--path', type=str, default='', help="Prefix to append to the file names if file wasn't found relative to the current directory")
    args = parser.parse_args()

    if args.csv and args.json:
        parser.error("Please choose either --csv or --json, not both.")

    output_format = "ascii"
    if args.csv:
        output_format = "csv"
    elif args.json:
        output_format = "json"

    result = compare_configs(args.config_files, output_format=output_format, path_prefix=args.path)
    print(result)

if __name__ == "__main__":
    main()
