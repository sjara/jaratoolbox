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
By default ``create_merged_binary`` calls ``SbxReader.get_channel()``, which
loads an entire session's frames into RAM at once before writing them to the
binary.  For very large sessions this may exhaust memory.  Pass
``chunk_size=N`` to load and write N frames at a time instead, at the cost of
slower I/O.
"""

import os
import numpy as np
from jaratoolbox.loadtwophoton import SbxReader
from suite2p.io import BinaryFile
from suite2p.run_s2p import run_s2p, get_save_folder, logger_setup
from suite2p.parameters import default_db, default_settings


def create_merged_binary(sbx_file_list, output_path, channel=0, chunk_size=None):
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
        chunk_size (int or None): Number of frames to load into memory at a time.
            None (default) loads each session all at once, which is fastest but
            requires enough RAM to hold a full session.  Set to e.g. 1000 to
            cap memory use at roughly chunk_size * Ly * Lx * 2 bytes.

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

        if os.path.exists(output_path):
            os.remove(output_path)
        with BinaryFile(Ly, Lx, output_path, n_frames=total_frames, write=True) as bf:
            frame_idx = 0
            for reader in readers:
                nf = reader.num_frames
                if chunk_size is None:
                    frames = reader.get_channel(channel)  # (nframes, Ly, Lx) uint16
                    bf[frame_idx:frame_idx + nf] = frames
                    frame_idx += nf
                else:
                    for start in range(0, nf, chunk_size):
                        end = min(start + chunk_size, nf)
                        print(f"  Writing frames {start}–{end - 1} of {nf - 1}...")
                        chunk = np.stack(
                            [reader.get_frame(i)[channel] for i in range(start, end)]
                        )
                        bf[frame_idx:frame_idx + (end - start)] = chunk
                        frame_idx += end - start
    finally:
        for r in readers:
            r.close()

    return {'Ly': Ly, 'Lx': Lx, 'n_frames': total_frames,
            'frame_counts': frame_counts}


def run_suite2p(binary_path, Ly, Lx, save_path, db=None, settings=None):
    """
    Run Suite2p on a pre-built binary file.

    Args:
        binary_path (str): Path to the .bin file created by create_merged_binary(),
            on a fast disk. The parent directory is used as fast_disk.
        Ly (int): Frame height in pixels.
        Lx (int): Frame width in pixels.
        save_path (str): Directory where Suite2p outputs (stat.npy, F.npy, etc.)
            will be saved. Can be on a slow disk.
        db (dict, optional): Override suite2p db parameters (I/O config:
            nplanes, nchannels, keep_movie_raw, etc.). See suite2p docs "db" section.
        settings (dict, optional): Override suite2p settings parameters
            (pipeline: fs, tau, diameter, etc.). See suite2p docs "settings" section.

    Returns:
        list: Paths to per-plane db.npy files (as returned by run_s2p).
    """
    valid_db_keys = set(default_db().keys())
    valid_settings_keys = set(default_settings().keys())
    for key in (db or {}):
        if key not in valid_db_keys:
            raise ValueError(f"'{key}' is not a valid db parameter. "
                             f"Did you mean to pass it in settings?")
    for key in (settings or {}):
        if key not in valid_settings_keys:
            raise ValueError(f"'{key}' is not a valid settings parameter. "
                             f"Did you mean to pass it in db?")

    logger_setup(save_path)
    fast_disk = os.path.dirname(binary_path)
    plane0_dir = os.path.join(save_path, 'suite2p', 'plane0')
    os.makedirs(plane0_dir, exist_ok=True)

    nframes = BinaryFile(Ly=Ly, Lx=Lx, filename=binary_path).n_frames

    keep_raw = (db or {}).get('keep_movie_raw', False)
    bin_name = 'data_raw.bin' if keep_raw else 'data.bin'
    symlink_path = os.path.join(plane0_dir, bin_name)
    if not os.path.exists(symlink_path):
        os.symlink(os.path.abspath(binary_path), symlink_path)

    db_params = {
        **default_db(),
        'data_path': [fast_disk],
        'save_path0': save_path,
        'Ly': Ly,
        'Lx': Lx,
        'save_path': plane0_dir,
        'reg_file': os.path.join(plane0_dir, 'data.bin'),
        'db_path': os.path.join(plane0_dir, 'db.npy'),
        'settings_path': os.path.join(plane0_dir, 'settings.npy'),
        'nframes': nframes,
    }
    if keep_raw:
        db_params['raw_file'] = symlink_path
    if db:
        db_params.update(db)

    settings_params = default_settings()
    if settings:
        for key, val in settings.items():
            if isinstance(val, dict) and isinstance(settings_params.get(key), dict):
                settings_params[key].update(val)
            else:
                settings_params[key] = val

    db_path = os.path.join(plane0_dir, 'db.npy')
    if not os.path.exists(db_path):
        np.save(db_path, db_params)
    np.save(os.path.join(plane0_dir, 'settings.npy'), settings_params)

    ops_path = run_s2p(db=db_params, settings=settings_params)
    return ops_path
