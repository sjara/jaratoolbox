#!/usr/bin/env python3
"""
Split concatenated Suite2p results back into per-session folders.

Run this after twophoton_preprocess.py and after you have curated the
results (e.g. manually reviewed/cleaned ROIs). Uses the same standard
paths as twophoton_preprocess.py, derived from jaratoolbox.settings.

Usage:
    python twophoton_split.py imag029 20260424 006,007
"""

import argparse
from jaratoolbox import suite2ptools


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('subject', help="Subject ID, e.g. 'imag029'.")
    parser.add_argument('session_date', help="Session date, e.g. '20260424'.")
    parser.add_argument('session_ids', type=lambda s: s.split(','),
                         help="Comma-separated session IDs that were concatenated, e.g. 006,007.")
    return parser.parse_args()


def main():
    args = parse_args()
    paths = suite2ptools.session_paths(args.subject, args.session_date, args.session_ids)
    print(f"Splitting results in {paths['output_dir']} back into per-session folders")
    sessionsInfo, sessionsDirs = suite2ptools.split_sessions(paths['output_dir'])
    print(f"Per-session output folders: {sessionsDirs}")


if __name__ == '__main__':
    main()
