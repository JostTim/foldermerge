[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm-project.org)

# File Hashing and Directory Comparison Tool

This project provides a Python utility for hashing files within directories, comparing directory contents, and assisting with folder merging. It is designed to be used on local filesystems where you need to compare folders, identify duplicates, and potentially merge them.

## Features

- **Hash Generation**: Create SHA1 hashes for files to efficiently compare content.
- **Directory Comparison**: Compare files across directories by name and content.
- **Merging Assistance**: Identify identical, moved, and modified files to help with directory merging.
- **Status Tracking**: Store and track the status of operations in a JSON file.

## Usage

To use this tool, simply instantiate the `FolderMerger` class with the destination repository and the source repositories you want to compare and potentially merge. The class will automatically scan the directories, generate hashes, and prepare comparisons.

Here is a basic example of how to use the tool:


```python
from pathlib import Path
from file_hashing_tool import FolderMerger


# Define the destination directory and the list of source directories

destination_dir = Path("path/to/destination")
source_dirs = [Path("path/to/source1"), Path("path/to/source2")]


# Create a FolderMerger instance

merger = FolderMerger(destination_dir, source_dirs)


# Perform comparison and generate report

comparison_report = merger.report()


# Print the report to view the comparison results

for report in comparison_report:
    print(report)
```

## Requirements

- python 3.7+
- pandas
- tqdm

## Components

- `HashLibrary`: Class responsible for generating and storing file hashes.
- `FolderChecker`: Class for scanning directories and storing file information.
- `FolderComparator`: Class for comparing two folders and identifying differences.
- `Folders`: Utility class to organize and access multiple `FolderChecker` instances.
- `FolderMerger`: Main class to orchestrate directory comparison and merging.

## Clearing Results

To clear any saved results and statuses, you can call the `clear_results` function which will remove all saved `.pickle` and `status.json` files from the default results path (typically `~/Downloads/FILE_HASHES`).

## Development

The project is modular, allowing for easy extension and customization. New comparison strategies or different hashing algorithms can be added by extending the relevant classes.

## License

This project is open-source and available under the [MIT License](LICENSE).