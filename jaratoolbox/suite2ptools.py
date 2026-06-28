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
from suite2p.run_s2p import run_s2p, get_save_folder, logger_setup
from suite2p.parameters import default_db, default_settings


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
        binary_path (str): Path to the .bin file created by create_merged_binary(),
            on a fast disk. The parent directory is used as fast_disk.
        Ly (int): Frame height in pixels.
        Lx (int): Frame width in pixels.
        save_path (str): Directory where Suite2p outputs (stat.npy, F.npy, etc.)
            will be saved. Can be on a slow disk.
        extra_ops (dict, optional): Additional Suite2p ops to override defaults.
            Pass {'keep_movie_raw': True} to preserve the original binary and write
            registered frames to a separate data.bin.

    Returns:
        list: Paths to per-plane db.npy files (as returned by run_s2p).
    """
    logger_setup(save_path)
    fast_disk = os.path.dirname(binary_path)
    plane0_dir = os.path.join(save_path, 'suite2p', 'plane0')
    os.makedirs(plane0_dir, exist_ok=True)

    nframes = BinaryFile(Ly=Ly, Lx=Lx, filename=binary_path).n_frames

    keep_raw = (extra_ops or {}).get('keep_movie_raw', False)
    bin_name = 'data_raw.bin' if keep_raw else 'data.bin'
    symlink_path = os.path.join(plane0_dir, bin_name)
    if not os.path.exists(symlink_path):
        os.symlink(os.path.abspath(binary_path), symlink_path)

    ops = {
        'data_path': [fast_disk],
        'save_path0': save_path,
        'Ly': Ly,
        'Lx': Lx,
    }
    if extra_ops:
        ops.update(extra_ops)

    settings = default_settings()
    db = {
        **default_db(),
        **ops,
        'save_path': plane0_dir,
        'reg_file': os.path.join(plane0_dir, 'data.bin'),
        'db_path': os.path.join(plane0_dir, 'db.npy'),
        'settings_path': os.path.join(plane0_dir, 'settings.npy'),
        'nframes': nframes,
    }
    if keep_raw:
        db['raw_file'] = symlink_path
    np.save(os.path.join(plane0_dir, 'db.npy'), db)
    np.save(os.path.join(plane0_dir, 'settings.npy'), settings)

    return run_s2p(db=ops)
