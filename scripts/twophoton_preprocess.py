#!/usr/bin/env python3
"""
Concatenate two-photon sessions and run Suite2p using standard paths.

Non-interactive counterpart to twophoton_preprocess_template.py: paths are
derived from jaratoolbox.settings (TWOPHOTON_PATH, SUITE2P_FAST_DIR), and
the functional/anatomical channel assignment is looked up automatically
from the subject's info2p metadata file (settings.INFO2P_PATH), so this
script never needs to be edited.

Usage:
    python twophoton_preprocess.py imag029 20260424 006,007 \\
        --settings s2p_settings_template.py --steps all

Once you have curated the results, use twophoton_split.py to split them
back into per-session folders.
"""

import argparse
from jaratoolbox import suite2ptools


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('subject', help="Subject ID, e.g. 'imag029'.")
    parser.add_argument('session_date', help="Session date, e.g. '20260424'.")
    parser.add_argument('session_ids', type=lambda s: s.split(','),
                         help="Comma-separated session IDs to concatenate, e.g. 006,007.")
    parser.add_argument('--settings', default=None,
                         help='Path to a Python settings-override file (see '
                              's2p_settings_template.py). If omitted, uses '
                              'default_2p_settings() unmodified.')
    parser.add_argument('--steps', nargs='+', default=['all'],
                         help="Steps to run: any of 'concatenate', 'register', 'detect', "
                              "'deconvolve', or 'all' (shorthand for all four). Default: all.")
    return parser.parse_args()


def main():
    args = parse_args()
    channel, anat_channel = suite2ptools.resolve_channels(
        args.subject, args.session_date, args.session_ids)
    settings_2p = suite2ptools.load_s2p_settings(args.settings)
    steps = args.steps[0] if args.steps == ['all'] else args.steps

    result = suite2ptools.process_sessions(
        args.subject, args.session_date, args.session_ids, steps,
        channel=channel, anat_channel=anat_channel, settings_2p=settings_2p)
    print(result)


if __name__ == '__main__':
    main()
