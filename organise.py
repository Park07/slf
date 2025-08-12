#!/usr/bin/env python3

import os
import shutil
import glob
from pathlib import Path
import re

def organize_test_files():
    """Organize full_test_ files into 12/Aug directory structure"""

    # Create base directory
    base_dir = "12/Aug"
    os.makedirs(base_dir, exist_ok=True)

    # Get all files that start with full_test_ only
    test_files = glob.glob("full_test_*")

    # Dictionary to group files by test identifier
    test_groups = {}

    for file in test_files:
        # Extract the test identifier from filename
        # Examples:
        # full_test_small_dense_4_1_query_dense_4_1.graph.log -> small_dense_4_1_query_dense_4_1
        # full_test_small_dense_4_1_query_dense_4_1.graph.json -> small_dense_4_1_query_dense_4_1

        # Remove "full_test_" prefix and file extension
        identifier = file[10:]  # Remove "full_test_"
        if identifier.endswith(".graph.log"):
            identifier = identifier[:-10]  # Remove ".graph.log"
        elif identifier.endswith(".graph.json"):
            identifier = identifier[:-11]  # Remove ".graph.json"
        elif identifier.endswith(".graph"):
            identifier = identifier[:-6]   # Remove ".graph"
        elif identifier.endswith(".log"):
            identifier = identifier[:-4]   # Remove ".log"

        # Group files by identifier
        if identifier not in test_groups:
            test_groups[identifier] = []
        test_groups[identifier].append(file)

    print(f"Found {len(test_files)} test files to organize into {len(test_groups)} groups")

    # Create directories and move files
    for test_id, files in test_groups.items():
        test_dir = os.path.join(base_dir, test_id)
        os.makedirs(test_dir, exist_ok=True)

        print(f"\nMoving {len(files)} files to {test_dir}/")
        for file in files:
            if os.path.exists(file):
                dest_path = os.path.join(test_dir, file)
                shutil.move(file, dest_path)
                print(f"  {file} -> {dest_path}")

    print(f"\nOrganization complete! Check the '{base_dir}' directory.")

    # Show the directory structure
    print(f"\nDirectory structure created:")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    # Change to the directory where your test files are
    # Uncomment and modify this line if needed:
    # os.chdir("/path/to/your/test/files")

    organize_test_files()