"""
Tools for preprocessing two-photon imaging data, including merging sessions
and running Suite2p.

Design rationale
----------------
When recording multiple sessions from the same two-photon field of view we
want Suite2p to treat all sessions as a single continuous recording so that
motion registration, ROI detection, and signal extraction are performed
jointly.  Suite2p's ``data_path`` list does NOT achieve this — it processes
each path as an independent session.

The approach taken here is to pre-build a ``suite2p.io.BinaryFile`` that
contains all sessions concatenated in time, then run Suite2p with
``input_format='binary'`` pointing at that file.  This avoids creating a
duplicate large ``.sbx`` file on disk and gives explicit control over what
gets concatenated (e.g. channel selection, bad-frame exclusion).

Memory note
-----------
``create_merged_binary`` currently calls ``SbxReader.get_channel()``, which
loads an entire session's frames into RAM at once before writing them to the
binary.  For very large sessions this may exhaust memory.  If that becomes a
problem, replace the ``get_channel()`` call with a frame-by-frame loop using
``SbxReader.get_frame()`` and write one frame at a time at the cost of
slower I/O.
"""

import os
import numpy as np
from jaratoolbox.loadtwophoton import SbxReader
from suite2p.io import BinaryFile
from suite2p.run_s2p import run_s2p


def create_merged_binary(sbx_file_list, output_path, channel=0):
    """
    Concatenate frames from multiple .sbx sessions into a single Suite2p BinaryFile.

    All sessions must have the same frame dimensions and the same number of
    active PMT channels.  Only one channel is written to the binary (Suite2p
    processes a single channel at a time).

    Args:
        sbx_file_list (list of str): Base paths to .sbx files (without extension).
            Each path must have a companion .mat metadata file.
        output_path (str): Path for the output .bin file.
        channel (int): PMT channel index to extract (0-based, default 0).

    Returns:
        dict: {'Ly': int, 'Lx': int, 'n_frames': int} describing the binary.

    Raises:
        ValueError: If sessions have mismatched frame dimensions or channel count.
    """
    readers = [SbxReader(f) for f in sbx_file_list]
    try:
        Ly = readers[0].lines_per_frame
        Lx = readers[0].pixels_per_line
        for r in readers[1:]:
            if r.lines_per_frame != Ly or r.pixels_per_line != Lx:
                raise ValueError(
                    f"Frame size mismatch: {r.filepath} has "
                    f"({r.lines_per_frame}, {r.pixels_per_line}) "
                    f"but expected ({Ly}, {Lx})."
                )
            if channel >= r.num_channels:
                raise ValueError(
                    f"Channel {channel} not available in {r.filepath} "
                    f"(only {r.num_channels} channel(s))."
                )

        total_frames = sum(r.num_frames for r in readers)
        frame_counts = [r.num_frames for r in readers]

        with BinaryFile(Ly, Lx, output_path, n_frames=total_frames, write=True) as bf:
            frame_idx = 0
            for reader in readers:
                nf = reader.num_frames
                frames = reader.get_channel(channel)  # (nframes, Ly, Lx) uint16
                bf[frame_idx:frame_idx + nf] = frames
                frame_idx += nf
    finally:
        for r in readers:
            r.close()

    return {'Ly': Ly, 'Lx': Lx, 'n_frames': total_frames,
            'frame_counts': frame_counts}


def run_suite2p(binary_path, Ly, Lx, save_path, extra_ops=None):
    """
    Run Suite2p on a pre-built binary file.

    Args:
        binary_path (str): Path to the .bin file created by create_merged_binary().
        Ly (int): Frame height in pixels.
        Lx (int): Frame width in pixels.
        save_path (str): Directory where Suite2p output will be saved.
        extra_ops (dict, optional): Additional Suite2p ops to override defaults.

    Returns:
        str: Path to the Suite2p output directory (as returned by run_s2p).
    """
    ops = {
        'input_format': 'binary',
        'data_path': [os.path.dirname(binary_path)],
        'tiff_list': [os.path.basename(binary_path)],
        'save_path0': save_path,
        'Ly': Ly,
        'Lx': Lx,
    }
    if extra_ops:
        ops.update(extra_ops)
    return run_s2p(ops)
