"""
Rename widefield data files to the new naming convention.

Changes applied:
  1. SUBJECT_timestamps_YYMMDD_HHMMSS.npz  ->  SUBJECT_YYMMDD_HHMMSS_timestamps.npz
  2. SUBJECT_YYMMDD_HHMMSS_XX.tif          ->  SUBJECT_YYMMDD_HHMMSS_wf.tif
     (where XX is two or three letters)
  3. SUBJECT_YYMMDD_HHMMSS_XX@000Z.tif     ->  SUBJECT_YYMMDD_HHMMSS_wf@000Z.tif
     (where XX is two or three letters and Z is a digit)
  4. SUBJECT_YYMMDD_HHMMSS_XX.tif.rec      ->  SUBJECT_YYMMDD_HHMMSS_wf.tif.rec
     (where XX is two or three letters)

Usage:
    python update_widefield_filenames.py [folder]

If no folder is provided, the script will prompt for one.
"""

import os
import re
import sys


# -- Patterns and their replacement logic --

# 1. SUBJECT_timestamps_YYMMDD_HHMMSS.npz
RE_TIMESTAMPS = re.compile(
    r'^(?P<subject>.+)_timestamps_(?P<date>\d{8})_(?P<session>\d{6})\.npz$'
)

# 2. SUBJECT_YYMMDD_HHMMSS_XX.tif  (suffix = 2-3 letters, no @)
RE_TIFF_SINGLE = re.compile(
    r'^(?P<subject>.+)_(?P<date>\d{8})_(?P<session>\d{6})_(?P<suffix>[A-Za-z]{2,3})\.tif$'
)

# 3. SUBJECT_YYMMDD_HHMMSS_XX@000Z.tif
RE_TIFF_MULTI = re.compile(
    r'^(?P<subject>.+)_(?P<date>\d{8})_(?P<session>\d{6})_(?P<suffix>[A-Za-z]{2,3})(?P<chunk>@\d+)\.tif$'
)

# 4. SUBJECT_YYMMDD_HHMMSS_XX.tif.rec  (suffix = 2-3 letters)
RE_TIFFREC = re.compile(
    r'^(?P<subject>.+)_(?P<date>\d{8})_(?P<session>\d{6})_(?P<suffix>[A-Za-z]{2,3})\.tif\.rec$'
)


def new_name(filename):
    """
    Return the new filename if it matches a rename pattern, else None.
    """
    m = RE_TIMESTAMPS.match(filename)
    if m:
        return f"{m['subject']}_{m['date']}_{m['session']}_timestamps.npz"

    m = RE_TIFF_SINGLE.match(filename)
    if m:
        # Skip files already using the 'wf' suffix
        if m['suffix'] == 'wf':
            return None
        return f"{m['subject']}_{m['date']}_{m['session']}_wf.tif"

    m = RE_TIFF_MULTI.match(filename)
    if m:
        if m['suffix'] == 'wf':
            return None
        return f"{m['subject']}_{m['date']}_{m['session']}_wf{m['chunk']}.tif"

    m = RE_TIFFREC.match(filename)
    if m:
        if m['suffix'] == 'wf':
            return None
        return f"{m['subject']}_{m['date']}_{m['session']}_wf.tif.rec"

    return None


def collect_renames(root_folder):
    """Walk root_folder and collect (old_path, new_path) pairs."""
    renames = []
    for dirpath, _dirnames, filenames in os.walk(root_folder):
        for filename in sorted(filenames):
            candidate = new_name(filename)
            if candidate is not None:
                old_path = os.path.join(dirpath, filename)
                new_path = os.path.join(dirpath, candidate)
                renames.append((old_path, new_path))
    return renames


def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("Enter the folder path to search: ").strip()

    folder = os.path.abspath(folder)

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    print(f"\nSearching for files to rename in:\n  {folder}\n")

    renames = collect_renames(folder)

    if not renames:
        print("No files matched the rename patterns. Nothing to do.")
        return

    print(f"Found {len(renames)} file(s) to rename:\n")
    for old_path, new_path in renames:
        rel_old = os.path.relpath(old_path, folder)
        rel_new = os.path.relpath(new_path, folder)
        print(f"  {rel_old}")
        print(f"    -> {rel_new}")
    print()

    answer = input("Proceed with renaming? [y/N] ").strip().lower()
    if answer != 'y':
        print("Aborted. No files were renamed.")
        return

    errors = []
    for old_path, new_path in renames:
        if os.path.exists(new_path):
            errors.append(f"  SKIP (target exists): {new_path}")
            continue
        try:
            os.rename(old_path, new_path)
            print(f"  Renamed: {os.path.relpath(old_path, folder)}")
        except OSError as e:
            errors.append(f"  ERROR renaming {old_path}: {e}")

    if errors:
        print("\nThe following issues occurred:")
        for err in errors:
            print(err)
    else:
        print("\nAll files renamed successfully.")


if __name__ == '__main__':
    main()
