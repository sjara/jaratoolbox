"""
Tools for preprocessing two-photon imaging data, including concatenating
sessions and running Suite2p.

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
By default ``create_concatenated_binary`` calls ``SbxReader.get_channel()``, which
loads an entire session's frames into RAM at once before writing them to the
binary.  For very large sessions this may exhaust memory.  Pass
``chunk_size=N`` to load and write N frames at a time instead, at the cost of
slower I/O.
"""

import os
import shutil
import time
import datetime
import contextlib
import importlib.util
import numpy as np
import pandas as pd
from jaratoolbox import settings
from jaratoolbox.loadtwophoton import SbxReader, load_scanbox_mat_file
from suite2p.io import BinaryFile
from suite2p.run_s2p import run_s2p, get_save_folder, logger_setup
from suite2p.parameters import default_db, default_settings

REGISTERED_MARKER_SUFFIX = '.registration.log'
SESSION_MANIFEST_FILENAME = 'multisession.csv'
PROCESSED_SUBJECT_SUFFIX = '_processed'


def default_s2p_settings():
    """
    Return a dict of Suite2p settings with lab defaults for two-photon recordings.

    This includes preferred values (some of which the user may need to
    change between sessions), and Suite2p already fills in everything else
    via default_settings() — see run_suite2p(). As of Suite2p's current
    release, the 'settings' dict (distinct from 'db') is organized into
    nested sub-dicts by pipeline stage. Override or add values before
    passing to run_suite2p(), including experiment-specific ones not listed
    below (e.g. 'diameter', which should be checked every session). See
    https://suite2p.readthedocs.io/en/latest/parameters/ for the full list
    of Suite2p parameters:

        settings = suite2ptools.default_s2p_settings()
        settings['fs'] = 9.96
        settings['diameter'] = [8.0, 8.0]
        settings['registration']['nonrigid'] = False
        ops_path = suite2ptools.run_suite2p(..., settings=settings)

    Note: 'nchannels' and 'functional_chan' are 'db' parameters (not
    'settings') in the current Suite2p version.

    Returns:
        dict with the following keys (Suite2p's own default shown in
        parentheses):

        fs (float): Sampling (frame) rate per plane, in Hz. Must match the
            actual acquisition rate; verify against the session before
            running. (Suite2p default: 10.0)
        tau (float): Timescale for deconvolution and binning, in seconds
            (Ca2+ indicator decay time constant). 0.6 = GCaMP6f, 1.0 =
            GCaMP6s, 1.5 = RCaMP. (Suite2p default: 1.0)
        diameter (float or [float, float]): ROI diameter in Y and X pixels,
            used for sourcery and cellpose detection. Pass [Ly, Lx] if cells
            are not round. (Suite2p default: [12.0, 12.0])
        registration (dict):
            align_by_chan2 (bool): For two-channel recordings, align using
                the non-functional (anatomical) channel instead of the
                functional one. Lab default False: harmless when there is no
                second channel, since Suite2p ignores this setting whenever
                no chan2 data is present. (Suite2p default: False)
            batch_size (int): Number of frames per batch during
                registration. Lower this if registration runs out of GPU
                memory (large frames + many nonrigid blocks can need a lot
                of memory per batch). (Suite2p default: 100)
        detection (dict):
            cellpose_chan2 (bool): Detect red cells in the anatomical
                channel using Cellpose. Lab default True: harmless when
                there is no second channel, since Suite2p ignores this
                setting whenever no chan2 data is present. (Suite2p
                default: False)
            threshold_scaling (float): Scalar multiplier that adjusts the
                automatically determined ROI detection threshold in sparsery
                and sourcery. Lower = more ROIs detected; higher = fewer,
                higher-quality ROIs. (Suite2p default: 1.0)
            max_overlap (float): ROIs with more overlap than this fraction
                with other ROIs are discarded. (Suite2p default: 0.75)
    """
    return {
        'fs': 9.96,
        'tau': 0.6,
        'diameter': [16.0, 16.0],
        'registration': {
            'align_by_chan2': False,
            'batch_size': 100,
        },
        'detection': {
            'threshold_scaling': 0.75,
            'max_overlap': 0.25,
            'cellpose_chan2': True,
        },
    }


def create_concatenated_binary(sbx_file_list, output_path, channel=0, anat_channel=None,
                                chunk_size=None):
    """
    Concatenate frames from multiple .sbx sessions into a single Suite2p BinaryFile.

    All sessions must have the same frame dimensions and the same number of
    active PMT channels. The functional channel is written to output_path.
    If anat_channel is given, a second binary is also written (see
    chan2_binary_path_for_binary()) with that channel's frames, for
    anatomical-channel ROI detection (e.g. settings['detection']['cellpose_chan2']).
    Suite2p expects the two channels as separate binaries, not interleaved
    frames in one file.

    Alongside the binary, this also writes a session manifest CSV (see
    manifest_path_for_binary()) recording each session's name, source path,
    and frame range within the concatenated binary. This lets you experiment
    with concatenation without committing to running Suite2p yet.
    run_suite2p() copies this manifest into the Suite2p output folder, where
    split_sessions() then reads it from to split results back apart.

    Args:
        sbx_file_list (list of str): Base paths to .sbx files (without extension).
            Each path must have a companion .mat metadata file.
        output_path (str): Path for the output .bin file.
        channel (int): PMT channel index of the functional channel to extract
            (0-based, default 0).
        anat_channel (int or None): PMT channel index of the anatomical
            channel to extract into a second binary (0-based). None (default)
            skips writing a second binary.
        chunk_size (int or None): Number of frames to load into memory at a time.
            None (default) loads each session all at once, which is fastest but
            requires enough RAM to hold a full session.  Set to e.g. 1000 to
            cap memory use at roughly chunk_size * Ly * Lx * 2 bytes.

    Returns:
        dict: {'Ly': int, 'Lx': int, 'n_frames': int, 'frame_counts': list}
            describing the binary. frame_counts is the number of frames
            contributed by each session, in the order given in sbx_file_list.

    Raises:
        ValueError: If sessions have mismatched frame dimensions or channel count,
            or if anat_channel equals channel.
    """
    if anat_channel is not None and anat_channel == channel:
        raise ValueError("anat_channel must differ from channel.")

    start_time = time.time()
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
            if anat_channel is not None and anat_channel >= r.num_channels:
                raise ValueError(
                    f"Channel {anat_channel} not available in {r.filepath} "
                    f"(only {r.num_channels} channel(s))."
                )

        total_frames = sum(r.num_frames for r in readers)
        frame_counts = [r.num_frames for r in readers]

        if os.path.exists(output_path):
            os.remove(output_path)
        chan2_output_path = chan2_binary_path_for_binary(output_path) if anat_channel is not None else None
        if chan2_output_path is not None and os.path.exists(chan2_output_path):
            os.remove(chan2_output_path)

        with BinaryFile(Ly, Lx, output_path, n_frames=total_frames, write=True) as bf, \
             (BinaryFile(Ly, Lx, chan2_output_path, n_frames=total_frames, write=True)
              if chan2_output_path is not None else contextlib.nullcontext()) as bf2:
            frame_idx = 0
            for reader in readers:
                nf = reader.num_frames
                if chunk_size is None:
                    frames = reader.get_channel(channel)  # (nframes, Ly, Lx) uint16
                    bf[frame_idx:frame_idx + nf] = frames
                    if bf2 is not None:
                        bf2[frame_idx:frame_idx + nf] = reader.get_channel(anat_channel)
                    frame_idx += nf
                else:
                    for start in range(0, nf, chunk_size):
                        end = min(start + chunk_size, nf)
                        print(f"  Writing frames {start}–{end - 1} of {nf - 1}...")
                        chunk = np.stack(
                            [reader.get_frame(i)[channel] for i in range(start, end)]
                        )
                        bf[frame_idx:frame_idx + (end - start)] = chunk
                        if bf2 is not None:
                            chunk2 = np.stack(
                                [reader.get_frame(i)[anat_channel] for i in range(start, end)]
                            )
                            bf2[frame_idx:frame_idx + (end - start)] = chunk2
                        frame_idx += end - start
    finally:
        for r in readers:
            r.close()

    last_frame = np.cumsum(frame_counts) - 1
    first_frame = last_frame - np.array(frame_counts) + 1
    manifest = pd.DataFrame({
        'session': [os.path.basename(f) for f in sbx_file_list],
        'sbx_path': sbx_file_list,
        'n_frames': frame_counts,
        'first_frame': first_frame,
        'last_frame': last_frame,
        'channel': channel,
        'anat_channel': anat_channel,
        'Ly': Ly,
        'Lx': Lx,
    })
    manifest_path = manifest_path_for_binary(output_path)
    manifest.to_csv(manifest_path, index=False)
    print(f'Saved {manifest_path}')

    elapsed = time.time() - start_time
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
    print(f'{timestamp} [INFO] ----------- Total {elapsed:.2f} sec')

    return {'Ly': Ly, 'Lx': Lx, 'n_frames': total_frames,
            'frame_counts': frame_counts}


def manifest_path_for_binary(binary_path):
    """Return the path of the session-manifest sidecar CSV for binary_path."""
    return os.path.splitext(binary_path)[0] + '.' + SESSION_MANIFEST_FILENAME


def chan2_binary_path_for_binary(binary_path):
    """Return the path of the anatomical-channel sidecar binary for binary_path."""
    return os.path.splitext(binary_path)[0] + '.chan2.bin'


def _registered_marker_path(binary_path):
    """Return the path of the sidecar marker file for binary_path."""
    return os.path.splitext(binary_path)[0] + REGISTERED_MARKER_SUFFIX


def _archive_run_log(save_path):
    """
    Archive an existing save_path/run.log before Suite2p overwrites it.

    Suite2p's logger_setup() unconditionally deletes and recreates run.log
    on every run_s2p() call, so when running the pipeline in stages (e.g.
    registration then detection as separate calls), each stage's log
    replaces the previous one. This renames any existing run.log to
    run.<YYYYMMDDHHMMSS>.log (based on the file's modification time) so
    logs from earlier stages are preserved.
    """
    log_path = os.path.join(save_path, 'run.log')
    if not os.path.exists(log_path):
        return
    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(log_path)).strftime('%Y%m%d%H%M%S')
    archived_path = os.path.join(save_path, f'run.{timestamp}.log')
    suffix = 1
    while os.path.exists(archived_path):
        archived_path = os.path.join(save_path, f'run.{timestamp}_{suffix}.log')
        suffix += 1
    shutil.move(log_path, archived_path)
    print(f'Archived previous log to {archived_path}')


def is_registered(binary_path):
    """
    Check whether binary_path has already been through Suite2p registration.

    Registration overwrites the binary in place, so re-registering an
    already-registered binary applies the shift-and-resample twice, which
    can introduce artifacts near the frame borders. run_suite2p() writes the
    sidecar marker checked here after a successful registration run.

    Args:
        binary_path (str): Path to the .bin file, as passed to run_suite2p().

    Returns:
        bool: True if a registered-marker sidecar file exists.
    """
    return os.path.exists(_registered_marker_path(binary_path))


def mark_as_registered(binary_path):
    """
    Create a sidecar marker file recording that binary_path was registered.

    Args:
        binary_path (str): Path to the .bin file, as passed to run_suite2p().
    """
    with open(_registered_marker_path(binary_path), 'w') as marker_file:
        marker_file.write(f"Registered via jaratoolbox.suite2ptools on {datetime.datetime.now().isoformat()}\n")


def run_suite2p(binary_path, Ly, Lx, save_path, db=None, settings=None, allow_reregister=False):
    """
    Run Suite2p on a pre-built binary file.

    Args:
        binary_path (str): Path to the .bin file created by create_concatenated_binary(),
            on a fast disk. The parent directory is used as fast_disk.
        Ly (int): Frame height in pixels.
        Lx (int): Frame width in pixels.
        save_path (str): Directory where Suite2p outputs (stat.npy, F.npy, etc.)
            will be saved. Can be on a slow disk. If create_concatenated_binary()
            wrote a session manifest next to binary_path, it is copied into
            save_path/suite2p/plane0/ so split_sessions() can later use it.
            If create_concatenated_binary() also wrote an anatomical-channel
            binary next to binary_path (anat_channel argument), it is symlinked
            in alongside the functional binary and db['nchannels']/['reg_file_chan2']
            are set accordingly, so e.g. settings['detection']['cellpose_chan2']
            can be used.
        db (dict, optional): Override suite2p db parameters (I/O config:
            nplanes, nchannels, keep_movie_raw, etc.). See suite2p docs "db" section.
        settings (dict, optional): Override suite2p settings parameters
            (pipeline: fs, tau, diameter, etc.). See suite2p docs "settings" section.
        allow_reregister (bool): If False (default), raise a RuntimeError when
            registration is requested (settings['run']['do_registration']) but
            binary_path is already marked as registered (see is_registered()).
            Registration overwrites the binary in place, so running it twice
            can introduce artifacts near the frame borders. Set to True to
            force re-registration anyway.

    Returns:
        list: Paths to per-plane db.npy files (as returned by run_s2p).

    Raises:
        RuntimeError: If registration is requested on an already-registered
            binary_path and allow_reregister is False.
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

    settings_params = default_settings()
    if settings:
        for key, val in settings.items():
            if isinstance(val, dict) and isinstance(settings_params.get(key), dict):
                settings_params[key].update(val)
            else:
                settings_params[key] = val

    keep_raw = (db or {}).get('keep_movie_raw', False)
    do_registration = bool(settings_params['run']['do_registration'])
    overwrites_binary = do_registration and not keep_raw
    if overwrites_binary and is_registered(binary_path) and not allow_reregister:
        raise RuntimeError(
            f"{binary_path} is already marked as registered "
            f"({_registered_marker_path(binary_path)} exists). Re-registering "
            "overwrites the binary again and can introduce border artifacts. "
            "Pass allow_reregister=True to force it."
        )

    _archive_run_log(save_path)
    logger_setup(save_path)
    fast_disk = os.path.dirname(binary_path)
    plane0_dir = os.path.join(save_path, 'suite2p', 'plane0')
    os.makedirs(plane0_dir, exist_ok=True)

    manifest_path = manifest_path_for_binary(binary_path)
    if os.path.exists(manifest_path):
        shutil.copy2(manifest_path, os.path.join(plane0_dir, SESSION_MANIFEST_FILENAME))

    nframes = BinaryFile(Ly=Ly, Lx=Lx, filename=binary_path).n_frames

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

    chan2_binary_path = chan2_binary_path_for_binary(binary_path)
    if os.path.exists(chan2_binary_path):
        chan2_bin_name = 'data_raw_chan2.bin' if keep_raw else 'data_chan2.bin'
        chan2_symlink_path = os.path.join(plane0_dir, chan2_bin_name)
        if not os.path.exists(chan2_symlink_path):
            os.symlink(os.path.abspath(chan2_binary_path), chan2_symlink_path)
        db_params['nchannels'] = 2
        db_params['functional_chan'] = 1
        db_params['reg_file_chan2'] = os.path.join(plane0_dir, 'data_chan2.bin')
        if keep_raw:
            db_params['raw_file_chan2'] = chan2_symlink_path

    if db:
        db_params.update(db)

    db_path = os.path.join(plane0_dir, 'db.npy')
    if not os.path.exists(db_path):
        np.save(db_path, db_params)
    np.save(os.path.join(plane0_dir, 'settings.npy'), settings_params)

    ops_path = run_s2p(db=db_params, settings=settings_params)

    if overwrites_binary:
        mark_as_registered(binary_path)

    return ops_path


def split_sessions(save_path, debug=False):
    """
    Split concatenated Suite2p results back into per-session folders.

    Uses the session manifest CSV written by create_concatenated_binary() and
    copied into place by run_suite2p() to slice the frame-indexed outputs
    (F.npy, Fneu.npy, spks.npy) of save_path/suite2p/plane0/ back into one
    folder per original session. Outputs that describe ROIs/registration
    rather than individual frames (stat.npy, iscell.npy) are copied unchanged
    into each session's folder, since they are shared across all sessions.
    ops.npy is large (it stores data, not just parameters) and is shared
    across sessions, so instead of copying it, each session's folder gets a
    symlink to the multisession ops.npy. Note this means 'nframes' in each
    session's ops.npy reflects the full concatenated recording, not that
    session alone (this has been tested to work fine when curating in the
    Suite2p GUI).

    Each session's output is saved as a sibling of save_path, named after
    just that session's ID (the part of its name after the last
    underscore, e.g. '006' from 'imag029_20260424_006'), rather than
    nesting it inside save_path under its full SUBJECT_DATE_SESSIONID name.
    For example, if save_path is
    '/data/twophoton/imag029_processed/20260424/006-007', results for
    session 'imag029_20260424_006' are saved to
    '/data/twophoton/imag029_processed/20260424/006/suite2p/plane0/'.

    Args:
        save_path (str): Suite2p save_path used with run_suite2p(), i.e. the
            directory containing suite2p/plane0/.
        debug (bool): if True, only print what would be done without writing
            any files.

    Returns:
        sessionsInfo (pandas.DataFrame): the session manifest.
        sessionsDirs (list of str): path to each session's plane0 output dir.
    """
    plane0_dir = os.path.join(save_path, 'suite2p', 'plane0')
    manifest_path = os.path.join(plane0_dir, SESSION_MANIFEST_FILENAME)
    sessionsInfo = pd.read_csv(manifest_path)
    parent_dir = os.path.dirname(save_path)

    framesToSlice = ['F.npy', 'Fneu.npy', 'spks.npy', 'F_chan2.npy', 'Fneu_chan2.npy']
    filesToCopy = ['stat.npy', 'iscell.npy']

    sliceArrays = {}
    for fname in framesToSlice:
        fpath = os.path.join(plane0_dir, fname)
        if os.path.exists(fpath):
            sliceArrays[fname] = np.load(fpath, allow_pickle=True)
        elif debug:
            print(f'\nWARNING! File {fpath} does not exist.')

    opsPath = os.path.join(plane0_dir, 'ops.npy')
    opsExists = os.path.exists(opsPath)
    if not opsExists and debug:
        print(f'\nWARNING! File {opsPath} does not exist.')

    sessionsDirsList = []
    for _, oneRow in sessionsInfo.iterrows():
        sessionID = oneRow.session.rsplit('_', 1)[-1]
        sessionDir = os.path.join(parent_dir, sessionID, 'suite2p', 'plane0')
        if os.path.isdir(sessionDir):
            print(f'WARNING! {sessionDir} exists. Data will be overwritten.')
        else:
            if not debug:
                os.makedirs(sessionDir)
            print(f'Created {sessionDir}')

        firstFrame = int(oneRow.first_frame)
        lastFrame = int(oneRow.last_frame)
        for fname, arr in sliceArrays.items():
            slicedArr = arr[:, firstFrame:lastFrame + 1]
            outPath = os.path.join(sessionDir, fname)
            if not debug:
                np.save(outPath, slicedArr)
            print(f'Saved {outPath}')

        for fname in filesToCopy:
            srcPath = os.path.join(plane0_dir, fname)
            if os.path.exists(srcPath):
                if not debug:
                    shutil.copy2(srcPath, sessionDir)
                print(f'Copied {fname} to {sessionDir}{os.sep}')
            elif debug:
                print(f'\nWARNING! File {srcPath} does not exist.')

        if opsExists:
            sessionOpsPath = os.path.join(sessionDir, 'ops.npy')
            if not debug:
                if os.path.islink(sessionOpsPath) or os.path.exists(sessionOpsPath):
                    os.remove(sessionOpsPath)
                os.symlink(os.path.relpath(opsPath, sessionDir), sessionOpsPath)
            print(f'Linked {sessionOpsPath} -> {opsPath}')

        if not debug:
            shutil.copy2(manifest_path, sessionDir)
        print(f'Copied {SESSION_MANIFEST_FILENAME} to {sessionDir}{os.sep}')
        print('')
        sessionsDirsList.append(sessionDir)

    return (sessionsInfo, sessionsDirsList)


def session_paths(subject, session_date, session_ids):
    """
    Compute standard paths for concatenating/processing a set of sessions.

    Reads settings.TWOPHOTON_RAW_PATH, settings.TWOPHOTON_PATH, and
    settings.SUITE2P_FAST_DIR from jaratoolbox.settings. Raw session data is
    read from TWOPHOTON_RAW_PATH (e.g. an external drive), while processed
    output is written under TWOPHOTON_PATH, so the two can point to
    different disks. All sessions must belong to the same subject and
    session_date, and follow the SUBJECT_DATE_SESSIONID naming convention
    (see loadtwophoton.py).

    Args:
        subject (str): Subject ID, e.g. 'imag029'.
        session_date (str): Session date string, e.g. '20260424'.
        session_ids (list of str): Session IDs to concatenate, e.g. ['006', '007'].

    Returns:
        dict with:
            data_dir (str): TWOPHOTON_RAW_PATH/subject/session_date
            sbx_file_list (list of str): data_dir/subject_session_date_sid,
                one per session_id, in the given order.
            mat_path (str): .mat companion of the first session, for reading
                Ly/Lx via load_scanbox_mat_file().
            concat_binary_path (str): SUITE2P_FAST_DIR/subject_session_date_id1-id2....bin
            output_dir (str): TWOPHOTON_PATH/subject+PROCESSED_SUBJECT_SUFFIX/session_date/id1-id2-.../
                the save_path to use with run_suite2p() and split_sessions().
    """
    sessions_str = '-'.join(session_ids)
    data_dir = os.path.join(settings.TWOPHOTON_RAW_PATH, subject, session_date)
    sbx_file_list = [os.path.join(data_dir, f'{subject}_{session_date}_{sid}')
                      for sid in session_ids]
    mat_path = os.path.join(data_dir, f'{subject}_{session_date}_{session_ids[0]}.mat')
    concat_binary_path = os.path.join(settings.SUITE2P_FAST_DIR,
                                       f'{subject}_{session_date}_{sessions_str}.bin')
    output_dir = os.path.join(f'{settings.TWOPHOTON_PATH}', f'{subject}{PROCESSED_SUBJECT_SUFFIX}',
                               session_date, sessions_str)
    return {
        'data_dir': data_dir,
        'sbx_file_list': sbx_file_list,
        'mat_path': mat_path,
        'concat_binary_path': concat_binary_path,
        'output_dir': output_dir,
    }


def process_sessions(subject, session_date, session_ids, steps, channel=0, anat_channel=None,
                      chunk_size=100, settings_2p=None, db=None, allow_reregister=False):
    """
    Concatenate and/or run Suite2p on a set of sessions, using standard paths.

    A high-level wrapper around session_paths(), create_concatenated_binary(),
    run_suite2p(), and split_sessions() so a template script only needs to
    specify which sessions to process, which steps to run, and any extra
    Suite2p settings.

    Args:
        subject (str): Subject ID, e.g. 'imag029'.
        session_date (str): Session date string, e.g. '20260424'.
        session_ids (list of str): Session IDs to concatenate, e.g. ['006', '007'].
        steps (list of str or 'all'): Which pipeline steps to run, drawn from
            'concatenate', 'register', 'detect', 'deconvolve', 'split'.
            'all' is shorthand for ['concatenate', 'register', 'detect',
            'deconvolve'] ('split' is never implied by 'all'; opt in
            explicitly once you are ready to split results back apart).
        channel (int): PMT channel index of the functional channel (0-based,
            default 0). Only used if 'concatenate' is in steps.
        anat_channel (int or None): PMT channel index of the anatomical
            channel (0-based). Only used if 'concatenate' is in steps.
        chunk_size (int or None): Passed to create_concatenated_binary().
        settings_2p (dict, optional): Suite2p settings, e.g. from
            default_s2p_settings() with overrides. do_registration/
            do_detection/do_deconvolution are set automatically from steps
            and should not be included here.
        db (dict, optional): Passed to run_suite2p() as db.
        allow_reregister (bool): Passed to run_suite2p().

    Returns:
        dict with:
            paths: the dict returned by session_paths().
            binary_info: return value of create_concatenated_binary(), if
                'concatenate' was in steps, else None.
            ops_path: return value of run_suite2p(), if any of 'register',
                'detect', 'deconvolve' were in steps, else None.
            split_result: (sessionsInfo, sessionsDirs) tuple from
                split_sessions(), if 'split' was in steps, else None.
    """
    valid_steps = {'concatenate', 'register', 'detect', 'deconvolve', 'split'}
    if steps == 'all':
        steps = ['concatenate', 'register', 'detect', 'deconvolve']
    steps = set(steps)
    invalid = steps - valid_steps
    if invalid:
        raise ValueError(f"Invalid steps {sorted(invalid)}. Valid steps are {sorted(valid_steps)}.")

    paths = session_paths(subject, session_date, session_ids)
    result = {'paths': paths, 'binary_info': None, 'ops_path': None, 'split_result': None}

    run_stages = {'register', 'detect', 'deconvolve'} & steps

    if 'concatenate' in steps:
        os.makedirs(settings.SUITE2P_FAST_DIR, exist_ok=True)
        print(f"Creating concatenated binary for sessions: {'-'.join(session_ids)}")
        result['binary_info'] = create_concatenated_binary(
            paths['sbx_file_list'], paths['concat_binary_path'],
            channel=channel, anat_channel=anat_channel, chunk_size=chunk_size)
        print(f"Concatenated binary: {result['binary_info']}")

    if run_stages:
        sbxinfo = load_scanbox_mat_file(paths['mat_path'])
        Ly, Lx = int(sbxinfo['sz'][0]), int(sbxinfo['sz'][1])
        merged_settings = dict(settings_2p) if settings_2p else default_s2p_settings()
        merged_settings['run'] = {
            'do_registration': 'register' in steps,
            'do_detection': 'detect' in steps,
            'do_deconvolution': 'deconvolve' in steps,
        }
        os.makedirs(paths['output_dir'], exist_ok=True)
        print(f"Running Suite2p ({', '.join(sorted(run_stages))}) on: {paths['concat_binary_path']}")
        result['ops_path'] = run_suite2p(
            paths['concat_binary_path'], Ly, Lx, paths['output_dir'],
            db=db, settings=merged_settings, allow_reregister=allow_reregister)
        print(f"Suite2p output: {result['ops_path']}")

    if 'split' in steps:
        print(f"Splitting results in {paths['output_dir']} back into per-session folders")
        result['split_result'] = split_sessions(paths['output_dir'])
        print(f"Per-session output folders: {result['split_result'][1]}")

    return result


def load_info2p(subject):
    """
    Load a subject's info2p metadata file and return its list of sessions.

    Reads <subject>_info2p.py from settings.INFO2P_PATH, following the same
    executable-Python-module convention as celldatabase.read_inforec().

    Args:
        subject (str): Subject ID, e.g. 'imag029'.

    Returns:
        list of dict: The module's 'sessions' list, one dict per recording
            session (keys typically include 'date', 'session', 'pmt', etc.).
    """
    filename = os.path.join(settings.INFO2P_PATH, f'{subject}_info2p.py')
    spec = importlib.util.spec_from_file_location('info2p_module', filename)
    info2p_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(info2p_module)
    assert info2p_module.subject == subject, \
        f"info2p file subject '{info2p_module.subject}' does not match requested '{subject}'"
    return info2p_module.sessions


def resolve_channels(subject, session_date, session_ids):
    """
    Determine (channel, anat_channel) for a set of sessions from info2p metadata.

    Looks up each session's 'pmt' entry (list of PMT channel indices
    recorded) in the subject's info2p file. Convention: PMT index 0 is
    always the functional channel; PMT index 1, if present, is always the
    anatomical channel.

    Args:
        subject (str): Subject ID, e.g. 'imag029'.
        session_date (str): Session date string, e.g. '20260424'.
        session_ids (list of str): Session IDs, e.g. ['006', '007'].

    Returns:
        channel (int): PMT channel index of the functional channel (always 0).
        anat_channel (int or None): PMT channel index of the anatomical
            channel (always 1), or None if no session recorded a second channel.

    Raises:
        ValueError: If no info2p entry is found for a given session, or if
            sessions being concatenated disagree on which PMTs were recorded.
    """
    sessions = load_info2p(subject)
    pmt_sets = []
    for session_id in session_ids:
        matches = [s for s in sessions if s['date'] == session_date and s['session'] == session_id]
        if not matches:
            raise ValueError(f"No info2p entry found for {subject} {session_date} {session_id}")
        pmt_sets.append(tuple(sorted(matches[0]['pmt'])))
    if len(set(pmt_sets)) > 1:
        raise ValueError(f"Sessions {session_ids} have inconsistent pmt channels: {pmt_sets}")
    pmt = pmt_sets[0]
    channel = 0
    anat_channel = 1 if len(pmt) > 1 else None
    return channel, anat_channel


def load_s2p_settings(settings_path):
    """
    Load a Suite2p settings-override file for use with process_sessions().

    The file is a Python module exposing a top-level 'settings' dict,
    typically built from default_s2p_settings() with overrides (see
    scripts/s2p_settings_template.py for an example).

    Args:
        settings_path (str or None): Path to the settings file, or None to
            use default_s2p_settings() unmodified.

    Returns:
        dict: The settings dict to pass to process_sessions() as settings_2p.
    """
    if settings_path is None:
        return default_s2p_settings()
    spec = importlib.util.spec_from_file_location('s2p_settings_module', settings_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.settings
