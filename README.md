# CLI CSV Cleaner & Error Handling Utility

A POSIX-compliant command-line utility built in Python to clean CSV files, remove duplicate entries, filter columns, and report missing values.

## Features
- **POSIX-compliant exit codes** for clean scripting integration.
- Handles file I/O errors, invalid formats, and user interrupts safely.
- Gracefully cleans up temporary/unwritten files on early termination.

## Usage

```bash
python main.py input.csv [output.csv]
