"""
Analysis of pupil videos.

NOTE: functions specific to Facemap have been moved to jaratoolbox/facemapanalysis.py
"""

import os
import numpy as np


def copy_facemap_roi(procfile, videofile, outputfile=None):
    """
    Create a copy of a facemap proc file, but pointing to a new video.

    By default, the new proc file is created in the same folder as the new
    videofile and named videofile_proc.npy.

    Args:
        procfile (str): path to original facemap proc.npy file.
        videofile (str): path to new video.
        outputfile (str): path and filename of new proc file to be created.
                          If None the new proc file is created in the same
                          folder as the new videofile and named VIDEONAME_proc.npy.
    Returns:
        outputfile (str): path to new proc file.
    """
    videodata = np.load(procfile, allow_pickle=True).item()  
    videodata['filenames'] = [[videofile]]
    if outputfile is None:
        outputfile = os.path.splitext(videofile)[0]+'_proc.npy'
    if os.path.isfile(outputfile):
        print(f'File {outputfile} exists. It will not be overwritten.')
        return None
    np.save(outputfile, videodata)
    return outputfile

def find_sync_light_onsets(sync_light, invert=True, fixmissing=False):
    """
    Find the onsets in the array representing the synchronization light.
    This function assumes the onsets are periodic (with randomness within 0.5T and 1.5T).
    The function can also fix missing onsets.

    Args:

    Returns:

    """
    # -- Find changes in synch light --
    sync_light_diff = np.diff(sync_light, prepend=0)
    if invert:
        sync_light_diff = -sync_light_diff
    sync_light_diff[sync_light_diff < 0] = 0
    sync_light_threshold = 0.2*sync_light_diff.max()
    sync_light_onset = sync_light_diff > sync_light_threshold


    # -- Find period of sync_light_onset --
    sync_light_onset_ind = np.where(sync_light_onset)[0]
    sync_light_onset_diff = np.diff(sync_light_onset_ind)  # In units of frames
    expected_onset_period = np.median(sync_light_onset_diff)  # In units of (float) frames

    # -- Remove repeated onsets --
    onset_freq_upper_threshold = int(1.5 * expected_onset_period)
    onset_freq_lower_threshold = int(0.5 * expected_onset_period)
    repeated_onsets = sync_light_onset_diff < onset_freq_lower_threshold
    repeated_onsets_ind = np.where(repeated_onsets)[0]
    fixed_sync_light_onset = sync_light_onset.copy()
    fixed_sync_light_onset[sync_light_onset_ind[repeated_onsets_ind+1]] = False

    # -- Fix missing onsets --
    if fixmissing:
        missing_next_onsets = sync_light_onset_diff > onset_freq_upper_threshold
        missing_next_onsets_ind = np.where(missing_next_onsets)[0]
        for indm, missing_onset_ind in enumerate(missing_next_onsets_ind):
            onset_diff = sync_light_onset_diff[missing_onset_ind]
            n_missing = int(np.round(onset_diff / expected_onset_period))-1
            #print(n_missing)
            last_onset_ind = sync_light_onset_ind[missing_onset_ind]
            next_onset_ind = sync_light_onset_ind[missing_onset_ind+1]
            period_missing = (next_onset_ind - last_onset_ind)//(n_missing+1)
            new_onset_inds = last_onset_ind + np.arange(1, n_missing+1)*period_missing
            #print([last_onset_ind, next_onset_ind])
            #print(new_onset_inds)
            fixed_sync_light_onset[new_onset_inds] = True

    return fixed_sync_light_onset
