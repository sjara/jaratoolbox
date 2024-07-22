"""
Functions for processing data produced by the video analysis tool Facemap.
"""

import os
import numpy as np
import matplotlib.pyplot as plt


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


def find_sync_light_onsets(sync_light, invert=True, fixmissing=False, prepost=False, verbose=False):
    """
    Find the onsets in the array representing the synchronization light.
    This function assumes the onsets are periodic (with randomness within 0.5T and 1.5T).
    The function can also fix missing onsets.

    Args:
        sync_light (np.array): array representing the synchronization light trace.
                               Values when the light is on are usually lower than baseline,
                               so use invert=True to invert the trace if needed.
        invert (bool): if True, the sync_light trace is inverted before processing.
        fixmissing (bool): if True, missing onsets are added to the output.
        prepost (bool): if True, assume there is a pre and post pulse of longer duration,
                        and ignore these in the final list.

    Returns:
        fixed_sync_light_onset (np.array): array of booleans indicating the onsets.
    """
    PRE_POST_DURATION_THRESHOLD = 20  # In units of frames. HARCODED! (should be calculated)

    # -- Find changes in synch light --
    sync_light_diff = np.diff(sync_light, prepend=sync_light[0])
    if invert:
        sync_light_diff = -sync_light_diff

    sync_light_threshold = 0.2*np.abs(sync_light_diff).max()
    sync_light_onset = sync_light_diff > sync_light_threshold
    sync_light_offset = sync_light_diff < -sync_light_threshold
    sync_light_onset_ind = np.where(sync_light_onset)[0]
    sync_light_offset_ind = np.where(sync_light_offset)[0]

    # -- Find period of sync_light_onset --
    sync_light_onset_diff = np.diff(sync_light_onset_ind)  # In units of frames
    expected_onset_period = np.median(sync_light_onset_diff)  # In units of (float) frames

    # -- Remove repeated onsets --
    onset_freq_upper_threshold = int(1.5 * expected_onset_period)
    onset_freq_lower_threshold = int(0.5 * expected_onset_period)
    repeated_onsets = sync_light_onset_diff < onset_freq_lower_threshold
    repeated_onsets_ind = np.where(repeated_onsets)[0]
    fixed_sync_light_onset = sync_light_onset.copy()
    fixed_sync_light_onset[sync_light_onset_ind[repeated_onsets_ind+1]] = False
    sync_light_onset = fixed_sync_light_onset
    sync_light_onset_ind = np.where(fixed_sync_light_onset)[0]
    
    if prepost:
        sync_light_midpoint = (sync_light.max()+sync_light.min())/2
        if sync_light_onset_ind[-1] > sync_light_offset_ind[-1]:
            sync_light_offset_ind = np.append(sync_light_offset_ind, len(sync_light)-1)
            nOffsets = len(sync_light_offset_ind)
        first_sync_duration = sync_light_offset_ind[0] - sync_light_onset_ind[0]
        last_sync_duration = sync_light_offset_ind[-1] - sync_light_onset_ind[-1]
        if first_sync_duration > PRE_POST_DURATION_THRESHOLD:
            if(verbose):
                print('Found pre sync pulse. This pulse will be ignore in the final list.')
            sync_light_onset[sync_light_onset_ind[0]] = False
            sync_light_onset_ind = sync_light_onset_ind[1:]
        else:
            # Raise ValueError exception
            raise ValueError('No pre sync pulse found.')
        if last_sync_duration > PRE_POST_DURATION_THRESHOLD:
            if(verbose):
                print('Found post sync pulse. This pulse will be ignore in the final list.')
            sync_light_onset[sync_light_onset_ind[-1]] = False
            sync_light_onset_ind = sync_light_onset_ind[:-1]
        else:
            # Raise ValueError exception
            raise ValueError('No post sync pulse found.')

    # -- Find period of sync_light_onset --
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


def estimate_running_each_trial(running_trace, trial_onset, smoothsize=10, presamples=4,
                                showfig=False):
    """
    Estimate the magnitude of locomotion during each trial.

    This function first smooths the running trace according to smoothsize (non-causal),
    it then uses the average of N presamples before the onset to estimate locomotion.

    Args:
        running_trace (np.array): running trace (usually from a pixelchange ROI).
        trial_onset (np.array): array of booleans indicating the onset of each trial.
            It should be the same length as running_trace.
        smoothsize (int): window size (in frames) for smoothing the running trace.
        presamples (int): number of (smoothed) samples to use for estimating running.
        showfig (bool): if True, show a figure with the running trace and the threshold.

    Returns:
        running_each_trial (np.array): array of booleans indicating whether the animal
                                       was running during each trial.
    """
    smoothwin = np.ones(smoothsize)/(smoothsize)
    running_trace_smooth = np.convolve(running_trace, smoothwin, mode='same')
    trial_onset_ind = np.where(trial_onset)[0]
    presamples_inds = np.arange(-presamples, 0) + trial_onset_ind[:, np.newaxis]
    running_each_trial = running_trace_smooth[presamples_inds].mean(axis=1)
    if showfig:
        plt.cla()
        plt.plot(running_trace_smooth, '0.8')
        plt.plot(trial_onset_ind, running_each_trial, 'xg')
        plt.legend(['running_trace_smooth', 'running_each_trial'],
                    loc='upper right')
        plt.show()
    return running_each_trial, running_trace_smooth


def guess_sync_light_onsets(nframes, trial_start_time, framerate=30):
    """
    Guess the onsets of the sync light based on the trial start time from the behavior file.

    Args:
        nframes (int): number of frames in the video.
        trial_start_time (np.array): array of floats indicating the start time of each trial.
        framerate (float): frame rate of the video. NOTE: currently not used.
    Returns:
        sync_light_onsets (np.array): array of booleans indicating the onsets of the sync light.
    """
    ntrials = len(trial_start_time)
    #sessionDurationInSec = nframes / framerate
    # -- This method assumes there is little time at the start/end of a session before sync. --
    trial_period_in_frames = int(nframes / (ntrials+1))
    sync_light_onsets = np.zeros(nframes, dtype=bool)
    onset_ind = np.linspace(trial_period_in_frames, nframes-trial_period_in_frames,
                            ntrials).astype(int)
    if 0:
        # -- This method assumes we have an exact framerate. It didn't work well. --
        trial_period_in_sec = np.median(np.diff(trial_start_time))
        trial_period_in_frames = trial_period_in_sec * framerate
        onset_ind = (trial_period_in_frames * np.arange(1, ntrials+1)).astype(int)
    sync_light_onsets[onset_ind] = True
    return sync_light_onsets
    
    
