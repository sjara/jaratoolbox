"""
Methods for analyzing two-photon imaging data.

Based on 
jaratest/santiago/test158_mesoscope_alignment_to_sound.py
jaratest/santiago/test160_mesoscope_sound_evoked.py
"""

import os
import numpy as np
from jaratoolbox import settings
from jaratoolbox import loadbehavior
from jaratoolbox import loadtwophoton
from jaratoolbox import behavioranalysis
from matplotlib import pyplot as plt
from importlib import reload
reload(loadtwophoton)


def calculate_dFoverF(signal, baseline_method='mean'):
    """
    Calculate deltaF/F (fractional change in fluorescence).
    
    Args:
        signal (numpy.ndarray): Fluorescence traces to process.
            Shape: (n_ROIs, n_timepoints) or (n_timepoints,) for single trace.
        baseline_method (str): Method for baseline calculation. 
            Options: 'mean' (default).
    
    Returns:
        numpy.ndarray: dF/F traces with same shape as input signal.
    
    Example:
        >>> roiF = np.random.rand(50, 1000)  # 50 ROIs, 1000 timepoints
        >>> dfof = calculate_dFoverF(roiF)
        >>> # Or with neuropil correction
        >>> corrected = roiF - 0.7 * neuropilF
        >>> dfof = calculate_dFoverF(corrected)
    """
    if baseline_method == 'mean':
        if signal.ndim == 1:
            baseline = signal.mean()
        else:
            baseline = signal.mean(axis=1, keepdims=True)
    else:
        raise ValueError(f"Unknown baseline method: {baseline_method}")
    
    df_over_f = (signal - baseline) / baseline
    return df_over_f


class TwoPhoton:
    """
    Class for loading and analyzing two-photon calcium imaging data.
    
    This class handles loading Suite2P processed data, optional behavioral data, and provides
    methods for common analysis tasks like calculating dF/F and extracting event-locked responses.
    
    Attributes:
        subject (str): Subject identifier (e.g., 'imag022').
        date (str): Recording date in YYYYMMDD format (e.g., '20260123').
        session (str): Session identifier (e.g., '012').
        plane (int): Imaging plane number (default: 0).
        data_path (str): Full path to the Suite2P output directory.
        roiF (numpy.ndarray): Fluorescence traces, shape (n_ROIs, n_timepoints).
        neuropilF (numpy.ndarray): Neuropil fluorescence traces, shape (n_ROIs, n_timepoints).
        spks (numpy.ndarray): Deconvolved spike traces, shape (n_ROIs, n_timepoints).
        stat (numpy.ndarray): ROI statistics from Suite2P.
        ops (dict): Suite2P operations/parameters dictionary.
        iscell (numpy.ndarray): Cell classification array, shape (n_ROIs, 2).
        srate (float): Sampling rate in Hz, extracted from ops['fs'].
        bdata (BehaviorData or None): Behavior data object if paradigm is specified.
    
    Example:
        >>> # Load imaging data only
        >>> tp = TwoPhoton('imag022', '20260123', '012')
        >>> print(f"Loaded {tp.roiF.shape[0]} ROIs")
        >>> print(f"Sampling rate: {tp.srate} Hz")
        >>> 
        >>> # Load with behavioral data
        >>> tp = TwoPhoton('imag022', '20260123', '012', paradigm='am_tuning_curve')
        >>> print(f"Number of trials: {tp.bdata['nTrials']}")
        >>>
        >>> # Filter to cells only and get event-locked responses
        >>> tp.filter_cells(prob_threshold=0.6)
        >>> locked, tvec = tp.event_locked_average(time_range=(-0.5, 2.0), 
        ...                                        apply_dFoverF=True)
        >>> # locked has shape (n_cells, n_trials, n_timepoints)
        >>> mean_response = locked.mean(axis=0)  # Average across cells
    """
    
    def __init__(self, subject, date, session, plane=0, paradigm=None):
        """
        Initialize TwoPhoton object, loading imaging and optional behavioral data.
        
        Args:
            subject (str): Subject identifier (e.g., 'imag022').
            date (str): Recording date in YYYYMMDD format (e.g., '20260123').
            session (str): Session identifier (e.g., '012').
            plane (int): Imaging plane number (default: 0).
            paradigm (str, optional): Behavioral paradigm name for loading behavior data.
                Examples: 'am_tuning_curve', '2afc', 'tuning_curve'.
        """
        self.subject = subject
        self.date = date
        self.session = session
        self.plane = plane
        
        # Construct path and load Suite2P data
        self.data_path = os.path.join(settings.TWOPHOTON_PATH, subject+'_processed', date,
                                      session, 'suite2p', f'plane{plane}')
        self.roiF, self.neuropilF, self.spks, self.stat, self.ops, self.iscell = \
            loadtwophoton.load_suite2p_data(self.data_path)
        self.srate = self.ops['fs']  # Sampling rate
        
        # Load ScanBox .mat file for stimulus sync data
        filepath = os.path.join(settings.TWOPHOTON_PATH, subject+'_processed', date,
                                session, f'{subject}_{date}_{session}.mat')
        self.info = loadtwophoton.load_scanbox_mat_file(filepath)
        self.event_onset, self.event_id = loadtwophoton.get_event_onset(self.info)

        # Load behavioral data if paradigm is specified
        if paradigm is not None:
            self.bdata = self.load_behavior(paradigm=paradigm)
        else:
            self.bdata = None
    
    def load_behavior(self, paradigm):
        """
        Load behavioral data associated with the imaging session.
        
        Args:
            paradigm (str): Name of the behavioral paradigm used during the session.
                Examples: 'am_tuning_curve', '2afc', 'tuning_curve'.
        
        Returns:
            BehaviorData: Object containing behavioral data for the session.
        
        Example:
            >>> tp = TwoPhoton('imag022', '20260123', '012')
            >>> bdata = tp.load_behavior('am_tuning_curve')
            >>> print(bdata['nTrials'])
        """
        stimulus_filename = loadbehavior.path_to_behavior_data(self.subject, paradigm,
                                                               f'{self.date}_{self.session}')
        bdata = loadbehavior.BehaviorData(stimulus_filename)
        return bdata
    
    def filter_cells(self, prob_threshold=0.5):
        """
        Filter ROI data to include only cells classified by Suite2P.
        
        This method filters self.roiF, self.neuropilF, self.spks, and self.stat
        to include only ROIs classified as cells.
        
        Args:
            prob_threshold (float): Minimum probability threshold for cell classification.
                Default: 0.5.
        
        Returns:
            None: Modifies the following attributes in place:
                - self.roiF
                - self.neuropilF
                - self.spks
                - self.stat
                - self.iscell
        
        Example:
            >>> tp = TwoPhoton('imag022', '20260123', '012')
            >>> print(f"Before filtering: {tp.roiF.shape[0]} ROIs")
            >>> tp.filter_cells(prob_threshold=0.6)
            >>> print(f"After filtering: {tp.roiF.shape[0]} cells")
        """
        is_cell_bool = (self.iscell[:, 0] == 1) & (self.iscell[:, 1] > prob_threshold)
        self.roiF = self.roiF[is_cell_bool]
        self.neuropilF = self.neuropilF[is_cell_bool]
        self.spks = self.spks[is_cell_bool]
        self.stat = self.stat[is_cell_bool]
        self.iscell = self.iscell[is_cell_bool]
    
    def event_locked_average(self, time_range, dff=False):
        """
        Calculate event-locked average of fluorescence signal.
        
        This method uses self.roiF and self.event_onset to extract event-locked responses.
        
        Args:
            time_range (tuple): Time window (start, end) around each event in seconds.
                Example: (-0.5, 2.0) for 500ms before to 2s after event.
            dff (bool): If True, applies dF/F calculation before locking.
                Default: False (uses raw fluorescence).
        
        Returns:
            tuple: (locked_signal, time_vec, valid_events)
                locked_signal (numpy.ndarray): Event-locked signal array.
                    Shape: (n_ROIs, n_events, n_timepoints)
                time_vec (numpy.ndarray): Time vector for the locked signal in seconds.
                valid_events (numpy.ndarray): Boolean array indicating which events were valid.
        
        Example:
            >>> tp = TwoPhoton('imag022', '20260123', '012', paradigm='am_tuning_curve')
            >>> tp.filter_cells(prob_threshold=0.6)
            >>> # Get event-locked raw fluorescence
            >>> locked_F, tvec, valid = tp.event_locked_average(time_range=(-0.5, 2.0))
            >>> # Or with dF/F applied
            >>> locked_dff, tvec, valid = tp.event_locked_average(time_range=(-0.5, 2.0), 
            ...                                            dff=True)
            >>> # Calculate mean response across cells
            >>> mean_response = locked_dff.mean(axis=0)
        """
        # Choose signal to use
        if dff:
            signal = calculate_dFoverF(self.roiF)
        else:
            signal = self.roiF
        
        # Convert time to frames
        frame_range = (time_range[0] * self.srate, time_range[1] * self.srate)
        
        locked_signal, frames_vec, valid_events = lock_to_event(signal, self.event_onset, frame_range)
        time_vec = frames_vec / self.srate  # Convert frames back to seconds
        
        return (locked_signal, time_vec, valid_events)
        
        return (locked_signal, time_vec)


def lock_to_event(signal, event_onset_frame, frame_range):
    """
    Extracts a window of signal around each event.

    Args:
        signal (numpy.ndarray): The input signal, shape (n_ROIs, n_timepoints).
        event_onset_frame (numpy.ndarray): Array of event onset frames.
            Can be fractional for sub-frame timing precision.
        frame_range (tuple): Frame window (start, end) to extract around each event.
            Example: (-5, 20) for 5 frames before to 20 frames after event.

    Returns:
        tuple: A 3-element tuple containing:
            locked_signal (numpy.ndarray): Event-locked signal array.
                Shape: (n_ROIs, n_events, n_frames)
            frames_vec (numpy.ndarray): Frame vector corresponding to the columns in the locked signal.
            valid_events (numpy.ndarray): Boolean array indicating which events were valid (no IndexError).
                Shape: (n_events,)

    Note:
        If there are not enough samples to extract within the specified frame range for an event,
        the corresponding entries in the locked signal array will be filled with NaN values and
        that event will be marked as invalid in valid_events.
    
    Example:
        >>> signal = np.random.rand(50, 1000)  # 50 ROIs, 1000 frames
        >>> event_frames = np.array([100, 200, 300])  # 3 events
        >>> locked, frames, valid = lock_to_event(signal, event_frames, frame_range=(-10, 30))
        >>> # locked has shape (50, 3, 40)
        >>> # valid is a boolean array of length 3
    """
    frames_vec = np.arange(int(frame_range[0]), int(frame_range[1]))
    n_frames = len(frames_vec)
    n_events = len(event_onset_frame)
    event_onset_samples = np.round(event_onset_frame).astype(int)
    
    # 2D signal: (n_ROIs, n_timepoints)
    n_rois = signal.shape[0]
    locked_signal = np.empty((n_rois, n_events, n_frames))
    valid_events = np.ones(n_events, dtype=bool)
    
    for inde, event_sample in enumerate(event_onset_samples):
        try:
            locked_signal[:, inde, :] = signal[:, frames_vec + event_sample]
        except IndexError:
            locked_signal[:, inde, :] = np.full((n_rois, n_frames), np.nan)
            valid_events[inde] = False
    
    return (locked_signal, frames_vec, valid_events)

# -- Calculate dF/F (poor man's version) --
# meanF = rawF.mean(axis=1)
# dFoverF = (rawF-meanF[:,np.newaxis])/meanF[:,np.newaxis]
# iscellBool = (iscell[:,0] == 1) & (iscell[:,1] > 0.50)
# dFoverF = dFoverF[iscellBool]

if __name__ == "__main__":
    subject = 'imag022'
    date = '20260123'
    session = '012'
    plane = 0

    data2p = TwoPhoton(subject, date, session, plane, paradigm='am_tuning_curve')
    print(f"Loaded {data2p.roiF.shape[0]} ROIs from {data2p.data_path}")
    print(f"Sampling rate: {data2p.srate} Hz")

    if 1:
        time_range = [-1, 3.0]  # Time window around event in seconds
        # Filter cells with low probability
        data2p.filter_cells(prob_threshold=0.5)
        signal_type = 'dF/F' #'raw F'
        if signal_type == 'dF/F':
            eventlocked, tvec, valid_events = data2p.event_locked_average(time_range=time_range, dff=True)
        else:
            eventlocked, tvec, valid_events = data2p.event_locked_average(time_range=time_range, dff=False)
        trialavg = eventlocked[:, valid_events, :].mean(axis=1)

        # -- Plot evoked response (of the mean across cells) --
        fig = plt.gcf()
        fig.clf()
        fig.set_constrained_layout(True)
        ax0 = plt.subplot(4, 1, (1,3))
        plt.imshow(trialavg, interpolation='nearest', extent=[*time_range, eventlocked.shape[0], 0])
        plt.colorbar(label=f'Signal ({signal_type})')
        plt.axvline(0, color='darkred', ls='-')
        plt.title(f'Event-locked average ({subject} {date} {session} p{plane})')
        #plt.xlabel('Time from sound onset (s)')
        plt.ylabel('Neuron')
        plt.setp(ax0.get_xticklabels(), visible=False)
        ax1 = plt.subplot(4, 1, 4, sharex=ax0)
        plt.plot(tvec, np.nanmean(trialavg, axis=0), lw=2)
        plt.axvline(0, color='darkred', ls='-')
        plt.xlabel('Time from sound onset (s)')
        plt.ylabel(f'Avg signal\nacross cells ({signal_type})')
        plt.show()

    if 0:
        # -- Create frequency tuning curves for each cell --
        time_range = [0, 1.0]  # Time window for calculating response
        data2p.filter_cells(prob_threshold=0.5)
        
        # Fix number of trials if behavior and 2p data mismatch
        n_trials_2p = len(data2p.event_onset)
        n_trials_behavior = len(data2p.bdata['currentFreq'])
        if n_trials_2p < n_trials_behavior:
            data2p.bdata['currentFreq'] = data2p.bdata['currentFreq'][:n_trials_2p]
            print(f"Warning: Fewer 2p trials ({n_trials_2p}) than behavior trials ({n_trials_behavior})." +
                  " Truncating behavior trials.")
        elif n_trials_2p > n_trials_behavior:
            data2p.event_onset = data2p.event_onset[:n_trials_behavior]
            print(f"Warning: More 2p trials ({n_trials_2p}) than behavior trials ({n_trials_behavior})." +
                  " Truncating 2p trials.")

        # Get event-locked responses with dF/F
        eventlocked, tvec, valid_events = data2p.event_locked_average(time_range=time_range, dff=True)
        n_cells, n_trials, n_timepoints = eventlocked.shape
        
        # Get unique frequencies and find trials for each frequency
        n_trials_2p = len(data2p.event_onset)

        current_freq = data2p.bdata['currentFreq']
        possible_freq = np.unique(current_freq)
        n_freq = len(possible_freq)
        trials_each_freq = behavioranalysis.find_trials_each_type(current_freq, possible_freq)
        
        # Calculate mean response for each frequency for each cell
        tuning_curves = np.zeros((n_cells, n_freq))
        for ind_freq, this_freq in enumerate(possible_freq):
            trials_this_freq = trials_each_freq[:, ind_freq]
            # Average across trials and time for this frequency
            tuning_curves[:, ind_freq] = eventlocked[:, trials_this_freq, :].mean(axis=(1, 2))
        
        # -- Plot tuning curves for all cells --
        fig = plt.gcf()
        fig.clf()
        fig.set_constrained_layout(True)
        
        # Plot individual tuning curves
        ax1 = plt.subplot(2, 1, 1)
        for ind_cell in range(n_cells):
            plt.plot(possible_freq, tuning_curves[ind_cell, :], 'o-', alpha=0.3, lw=0.5)
        plt.xscale('log')
        ax1.set_xticks(possible_freq)
        ax1.set_xticklabels([f'{freq/1000:.1f}' for freq in possible_freq])
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('Mean dF/F')
        plt.title(f'Frequency tuning curves - all cells ({subject} {date} {session} p{plane})')
        plt.grid(True, alpha=0.3)
        
        # Plot average tuning curve across cells
        ax2 = plt.subplot(2, 1, 2)
        mean_tuning = tuning_curves.mean(axis=0)
        sem_tuning = tuning_curves.std(axis=0) / np.sqrt(n_cells)
        plt.errorbar(possible_freq, mean_tuning, yerr=sem_tuning, 
                     marker='o', capsize=5, lw=2)
        plt.xscale('log')
        ax2.set_xticks(possible_freq)
        ax2.set_xticklabels([f'{freq/1000:.1f}' for freq in possible_freq])
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('Mean dF/F')
        plt.title(f'Average tuning curve (n={n_cells} cells)')
        plt.grid(True, alpha=0.3)
        
        plt.show()
