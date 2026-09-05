import argparse
import csv
from pathlib import Path
import sys
import time

# Helper function to clean whitespace from row fields
def clean_rows(rows):
    return [field.strip() for field in rows]

# Argument parser setup
parser = argparse.ArgumentParser(
    description="Clean, filter, and process a CSV file."
)

parser.add_argument("input_file", help="Path to the CSV file you want to clean")

parser.add_argument(
    "-o",
    "--output",
    help="Path to save the cleaned CSV file (default: cleaned_<filename>.csv)",
    default=None,
)

parser.add_argument(
    "-c",
    "--columns",
    help="Comma-separated list of column names to keep (e.g., -c 'Name, Age')",
    default=None,
)

# Parse CLI arguments (Preserve exit code 0 for -h/--help, Exit Code 2 on invalid flags)
try:
    args = parser.parse_args()
except SystemExit as e:
    if e.code == 0:
        sys.exit(0)
    sys.exit(2)

file_path = Path(args.input_file)
output_path = (
    Path(args.output)
    if args.output
    else file_path.parent / f"cleaned_{file_path.name}"
)

# Exit Code 2: File Extension Check (Checked first so data.txt fails here)
if file_path.suffix.lower() != ".csv":
    print("Error: The selected file must be a CSV file.", file=sys.stderr)
    sys.exit(2)

# Exit Code 2: Input File Existence Check
if not file_path.exists():
    print(f"Error: File '{args.input_file}' was not found.", file=sys.stderr)
    sys.exit(2)

# Exit Code 2: Output Directory Validation
if not output_path.parent.exists():
    print(
        f"Error: Output directory '{output_path.parent}' does not exist.",
        file=sys.stderr,
    )
    sys.exit(2)

# Wrap execution to catch Ctrl+C (KeyboardInterrupt)
try:
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)

        try:
            raw_header = next(reader, None)
        except csv.Error as e:
            print(f"Error: Invalid CSV structure in '{args.input_file}': {e}", file=sys.stderr)
            sys.exit(1)

        if not raw_header:
            print(f"Error: '{args.input_file}' is empty.", file=sys.stderr)
            sys.exit(1)

        original_header = clean_rows(raw_header)
        active_header = list(original_header)

        # Handle column selection
        col_indices = None
        if args.columns:
            requested_cols = [
                c.strip() for c in args.columns.split(",") if c.strip()
            ]

            invalid_cols = [c for c in requested_cols if c not in original_header]
            if invalid_cols:
                print(
                    f"Error: Specified column(s) {invalid_cols} not found in header.",
                    file=sys.stderr,
                )
                sys.exit(2)

            col_indices = [original_header.index(c) for c in requested_cols]
            active_header = requested_cols

        seen = set()
        rows = []
        duplicate_count = 0
        missing_counts = {col: 0 for col in active_header}

        # Process data rows
        for row in reader:
            if not row or not any(field.strip() for field in row):
                continue

            cleaned_full_row = clean_rows(row)

            # Filter columns if -c flag was passed
            if col_indices:
                processed_row = [
                    cleaned_full_row[i] if i < len(cleaned_full_row) else ""
                    for i in col_indices
                ]
            else:
                processed_row = cleaned_full_row

            # Track missing values for active columns
            for col_name, val in zip(active_header, processed_row):
                if val == "":
                    missing_counts[col_name] += 1

            row_tuple = tuple(processed_row)

            if row_tuple not in seen:
                seen.add(row_tuple)
                rows.append(processed_row)
            else:
                duplicate_count += 1

        # Summary statistics report
        print(f"Successfully opened '{args.input_file}'.")
        print(f"Headers: {active_header}")
        print(f"Unique rows retained: {len(rows)}")
        print(f"Duplicates removed: {duplicate_count}")

        print("\n--- Missing Data Report ---")
        has_missing = False
        for col_name, count in missing_counts.items():
            if count > 0:
                print(f" - Column '{col_name}': {count} missing value(s)")
                has_missing = True
        if not has_missing:
            print(" - No missing values detected!")

        # 2-SECOND DELAY TO ALLOW PRESSING CTRL+C
        print("\nProcessing... Press Ctrl+C within  seconds to cancel execution.")
        time.sleep(2)

        # Write cleaned data to target output file
        try:
            with open(
                output_path, mode="w", newline="", encoding="utf-8"
            ) as out_file:
                writer = csv.writer(out_file)
                writer.writerow(active_header)
                writer.writerows(rows)
            print(f"\nCleaned file successfully saved to '{output_path.name}'.")

        except PermissionError:
            print(
                f"Error: Permission denied when writing to '{output_path}'.",
                file=sys.stderr,
            )
            sys.exit(1)

except KeyboardInterrupt:
    # Exit Code 130: Cancelled by user Ctrl+C with file cleanup
    print("\nOperation cancelled due to press ctrl+c... Cleaning up", file=sys.stderr)
    if output_path.exists():
        try:
            output_path.unlink()
        except OSError:
            pass
    sys.exit(130)

except PermissionError:
    print(
        f"Error: Permission denied when reading '{args.input_file}'.",
        file=sys.stderr,
    )
    sys.exit(1)

except UnicodeDecodeError:
    print(
        f"Error: Could not decode '{args.input_file}'. Ensure it is UTF-8 encoded.",
        file=sys.stderr,
    )
    sys.exit(1)

except csv.Error as e:
    print(
        f"Error: Malformed CSV file structure in '{args.input_file}': {e}",
        file=sys.stderr,
    )
    sys.exit(1)

except Exception as e:
    print(
        f"Error: An unexpected error occurred: {e}",
        file=sys.stderr,
    )
    sys.exit(1)