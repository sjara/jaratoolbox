"""
Classes and methods for analysis of widefield imaging data.
"""

import os
import importlib
import numpy as np
import matplotlib.pyplot as plt
from jaratoolbox import loadwidefield
from jaratoolbox import behavioranalysis
from jaratoolbox import settings

# Channel colors for RGB merged images (Red, Green, Light Blue)
CHANNEL_COLORS = [
    [1, 0, 0],       # Red
    [0, 1, 0],       # Green
    [0.25, 0.5, 1],  # Light blue (adjusted for similar perceived luminosity)
]
CHANNEL_NAMES = ['Red', 'Green', 'Blue']

def load_infowidefield(subject):
    """
    Load the infowidefield file for a given subject.

    The file is expected to be located at settings.INFOWIDEFIELD_PATH and named
    '{subject}_infowidefield.py'. It must define a list called 'sessions', where
    each element is a dictionary with keys: 'subject', 'date', 'session',
    'suffix', and 'paradigm'.

    Args:
        subject (str): Subject identifier (e.g., 'test000').

    Returns:
        module: The loaded infowidefield module (access sessions via module.sessions).
    """
    infowidefield_file = os.path.join(settings.INFOWIDEFIELD_PATH,
                                      f'{subject}_infowidefield.py')
    if not os.path.isfile(infowidefield_file):
        raise FileNotFoundError(f'Infowidefield file not found: {infowidefield_file}')
    spec = importlib.util.spec_from_file_location('infowidefield_module', infowidefield_file)
    infowidefield = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(infowidefield)
    return infowidefield


def preprocess_widefield(subject, date='', stime='', suffix='wf', paradigm='am_tuning_curve',
                         camera_rotation=90, hemisphere='right', stim_param='currentFreq'):
    """
    Preprocess widefield data and save results to disk.
    
    This function loads the widefield data, computes the evoked response for each
    stimulus type, and saves the results in a .npz file for later use.

    If only 'subject' is provided (date and time are empty), the function loads
    the infowidefield file for that subject and processes all sessions listed in it.
    If 'subject' and 'date' are provided but 'stime' is empty, all sessions for
    that date are processed from the infowidefield file.
    Each session dictionary must contain 'date', 'stime', and 'subject' keys.
    Optional keys: 'suffix', 'paradigm', 'cameraRotation', 'hemisphere', 'intensities'.
    
    Args:
        subject (str): Subject identifier.
        date (str): Date string (e.g., '20241219'). If empty, all sessions from the
            infowidefield file will be processed. If provided without 'stime', all
            sessions for that date will be processed.
        stime (str): Start time of the session (e.g., '161007'). If empty, all
            sessions matching the given date will be processed.
        suffix (str): Suffix for the TIFF filename. Used as fallback (default: 'wf')
            if 'suffix' is not present in the session dict.
        paradigm (str): Behavioral paradigm name (default: 'am_tuning_curve'). Used
            as fallback if 'paradigm' is not present in the session dict.
        camera_rotation (int or float): Physical rotation of the camera in degrees CCW.
            Default is 90 (camera rotated 90° CCW). Used as fallback if 'cameraRotation'
            is not present in the session dict.
        hemisphere (str): Which side of the brain is being imaged, 'right' (default) or
            'left'. Used as fallback if 'hemisphere' is not present in the session dict.
        stim_param (str or list of str): Stimulus parameter(s) passed to
            compute_evoked_response(). Default is 'currentFreq'. Used as fallback if
            'intensities' is not present in the session dict. Automatically set to
            ['currentFreq', 'currentIntensity'] if 'intensities' has more than one value.
    """
    if not date or not stime:
        infowidefield = load_infowidefield(subject)
        for sessionInfo in infowidefield.sessions:
            if date and sessionInfo['date'] != date:
                continue
            print(f"\nProcessing {sessionInfo['subject']} {sessionInfo['date']} "
                  f"{sessionInfo['time']}")
            intensities = sessionInfo.get('intensities', [])
            if len(intensities) > 1:
                session_stim_param = ['currentFreq', 'currentIntensity']
            else:
                session_stim_param = stim_param
            # print(f"***** Using stim_param={session_stim_param} for this session")
            preprocess_widefield(sessionInfo['subject'],
                                 date=sessionInfo['date'],
                                 stime=sessionInfo['time'],
                                 suffix=sessionInfo.get('suffix', suffix),
                                 paradigm=sessionInfo.get('paradigm', paradigm),
                                 camera_rotation=sessionInfo.get('cameraRotation', camera_rotation),
                                 hemisphere=sessionInfo.get('hemisphere', hemisphere),
                                 stim_param=session_stim_param)
        return

    # -- Try to look up session in infowidefield to determine stim_param --
    try:
        infowidefield = load_infowidefield(subject)
        matched_session = next(
            (s for s in infowidefield.sessions if s['date'] == date and s['time'] == stime),
            None
        )
        if matched_session is not None:
            intensities = matched_session.get('intensities', [])
            if len(intensities) > 1:
                stim_param = ['currentFreq', 'currentIntensity']
            print(f"Found infowidefield entry; using stim_param='{stim_param}'")
        else:
            print(f"No infowidefield entry found for {subject} {date} {stime}; "
                  f"defaulting to stim_param='{stim_param}'")
    except FileNotFoundError:
        print(f"No infowidefield file found for {subject}; "
              f"defaulting to stim_param='{stim_param}'")

    # -- Load data --
    wfobj = Widefield(subject, date, stime, suffix=suffix, paradigm=paradigm,
                     camera_rotation=camera_rotation, hemisphere=hemisphere)
    wfobj.load_timestamps()
    wfobj.load_frames()
    wfobj.load_behavior()

    # -- Compute evoked responses --
    signal_change = wfobj.compute_evoked_response(stim_param=stim_param)
    print(f"Computed responses for {len(wfobj.possible_values[0])} frequencies")
    wfobj.save()


class Widefield(loadwidefield.WidefieldData):
    """
    Extended Widefield class with additional analysis methods.
    
    Inherits from loadwidefield.WidefieldData.
    """
    
    def __init__(self, subject, date, session, suffix='', paradigm='am_tuning_curve',
                 camera_rotation=90, hemisphere='right'):
        """
        Initialize a Widefield object.
        
        Args:
            subject (str): Subject identifier.
            date (str): Date string (e.g., '20241219').
            session (str): Session identifier. Usually a time string (e.g., '161007').
            suffix (str): Suffix for the TIFF filename (e.g., 'SJ' initials).
            paradigm (str): Behavioral paradigm name (default: 'am_tuning_curve').
            camera_rotation (int or float): Physical rotation of the camera in degrees CCW.
                Default is 90 (camera rotated 90° CCW). Use 0 if camera is not rotated.
            hemisphere (str): Which side of the brain is being imaged. 
                'right' (default) or 'left'. This affects the anterior-posterior
                orientation in the final image.
        """
        super().__init__(subject, date, session, suffix=suffix, paradigm=paradigm,
                         camera_rotation=camera_rotation, hemisphere=hemisphere)
        
        # Analysis results (computed on demand)
        self.stim_param_names = None  # str, list of str, or None; mirrors stim_param passed to compute_evoked_response
        self.possible_values = None   # list of arrays, one per param: [values_param0] or [values_param0, values_param1, ...]
        self.trials_each_cond = None  # bool array (n_trials, n_v1) or (n_trials, n_v1, n_v2, ...)
        self.avg_evoked_each_cond = None    # (n_v1[, n_v2, ...], H, W)
        self.avg_baseline_each_cond = None  # (n_v1[, n_v2, ...], H, W)
        self.signal_change_each_cond = None # (n_v1[, n_v2, ...], H, W)
    
    def compute_evoked_response(self, stim_param='currentFreq'):
        """
        Compute average evoked response for each stimulus condition.
        
        This method calculates the average fluorescence during the stimulus
        (evoked) and before the stimulus (baseline) for each unique stimulus
        condition, then computes the relative change in fluorescence (dF/F).
        
        Args:
            stim_param (str, list of str, or None): Behavioral parameter(s) used to
                group trials.
                - str (default: 'currentFreq'): group by a single parameter. Output
                  arrays have shape (n_freq, H, W).
                - list of str (e.g. ['currentFreq', 'currentIntensity']): group by
                  all unique combinations of the listed parameters using
                  behavioranalysis.find_trials_each_combination_n(). Output arrays
                  have shape (n_v1, n_v2, ..., H, W), so indexing is natural:
                  signal_change_each_cond[i_freq, i_intensity] corresponds to
                  possible_values[0][i_freq] x possible_values[1][i_intensity].
                - None: treat all trials as a single condition (no behavioural data
                  required). Output shape is (1, H, W).
        
        Returns:
            numpy.ndarray: Signal change (dF/F) for each stimulus condition.
                Shape: (n_v1[, n_v2, ...], height, width)
        
        Note:
            Results are also stored in:
            - self.stim_param_names: the value of stim_param that was passed
            - self.possible_values: list of arrays with unique values per parameter;
              e.g. [array([4k,8k,16k]), array([30,50,70])] for freq x intensity.
              Use this to map indices back to physical values.
            - self.trials_each_cond: bool array (n_trials, n_v1[, n_v2, ...])
            - self.avg_evoked_each_cond: average evoked image per condition
            - self.avg_baseline_each_cond: average baseline image per condition
            - self.signal_change_each_cond: dF/F per condition
        """
        # Ensure data is loaded
        if self.frames is None:
            raise ValueError("Frames not loaded. Call load_frames() first.")
        if self.sound_onset is None:
            raise ValueError("Timestamps not loaded. Call load_timestamps() first.")
        
        self.stim_param_names = stim_param
        H, W = self.frames.shape[1], self.frames.shape[2]

        # -- Build trials_each_cond and possible_values --
        if stim_param is None:
            # Single condition: all trials treated the same
            n_trials = len(self.sound_offset)
            self.possible_values = [np.array([0])]
            self.trials_each_cond = np.ones((n_trials, 1), dtype=bool)
        elif isinstance(stim_param, list):
            # Multi-parameter case: use find_trials_each_combination_n
            if self.bdata is None:
                raise ValueError("Behavior data not loaded. Call load_behavior() first.")
            n_trials = min(len(self.bdata[stim_param[0]]), len(self.sound_offset))
            param_arrays = [self.bdata[p][:n_trials] for p in stim_param]
            self.possible_values = [np.unique(p) for p in param_arrays]
            # trials_each_cond shape: (n_trials, n_v1, n_v2, ...)
            self.trials_each_cond = behavioranalysis.find_trials_each_combination_n(
                param_arrays, self.possible_values
            )
        else:
            # Single-parameter case (original behaviour)
            if self.bdata is None:
                raise ValueError("Behavior data not loaded. Call load_behavior() first.")
            n_trials = min(len(self.bdata[stim_param]), len(self.sound_offset))
            current_stim = self.bdata[stim_param][:n_trials]
            self.possible_values = [np.unique(current_stim)]
            # trials_each_cond shape: (n_trials, n_freq)
            self.trials_each_cond = behavioranalysis.find_trials_each_type(
                current_stim, self.possible_values[0]
            )

        # Fix the length of sound onsets to match bdata trials
        sound_onset = self.sound_onset[:n_trials]
        sound_offset = self.sound_offset[:n_trials]
        
        # -- Calculate timing parameters --
        sound_duration = np.mean(sound_offset - sound_onset)
        frame_rate = 1 / np.mean(np.diff(self.timestamps))
        sound_duration_in_frames = int(round(sound_duration * frame_rate))
        
        # Find frames corresponding to sound onset
        frame_after_onset = np.searchsorted(self.timestamps, sound_onset, side='left')

        # -- Allocate output arrays with shape (n_v1[, n_v2, ...], H, W) --
        condition_shape = tuple(len(v) for v in self.possible_values)
        self.avg_evoked_each_cond = np.zeros(condition_shape + (H, W))
        self.avg_baseline_each_cond = np.zeros(condition_shape + (H, W))
        self.signal_change_each_cond = np.zeros(condition_shape + (H, W))

        # -- Compute evoked response for each condition --
        # np.ndindex iterates over (0,), (1,), ... for 1-param
        # or (0,0), (0,1), ..., (n1-1,n2-1) for 2-param, etc.
        for idx in np.ndindex(*condition_shape):
            # Index into trials_each_cond: first axis is trials, rest are param dims
            trials_this_cond = self.trials_each_cond[(slice(None),) + idx]
            frame_after_onset_this_cond = frame_after_onset[trials_this_cond]
            
            # Create array of all evoked frame indices
            evoked_frames = np.tile(
                frame_after_onset_this_cond, (sound_duration_in_frames, 1)
            )
            evoked_frames += np.arange(sound_duration_in_frames)[:, None]
            evoked_frames = np.sort(evoked_frames.ravel())
            
            # Handle case where video may be split into multiple recordings
            final_frames = np.searchsorted(evoked_frames, len(self.frames))
            evoked_indices = evoked_frames[:final_frames]
            
            # Compute average evoked and baseline fluorescence
            avg_evoked = np.mean(self.frames[evoked_indices], axis=0)
            baseline_indices = evoked_indices - sound_duration_in_frames
            avg_baseline = np.mean(self.frames[baseline_indices], axis=0)
            
            # Compute relative change in fluorescence (dF/F)
            self.avg_evoked_each_cond[idx] = avg_evoked
            self.avg_baseline_each_cond[idx] = avg_baseline
            self.signal_change_each_cond[idx] = (avg_evoked - avg_baseline) / avg_baseline
        
        return self.signal_change_each_cond

    def save(self):
        """
        Save analysis results to disk.
        """
        save_dir = os.path.join(settings.WIDEFIELD_PATH, self.subject+'_processed')
        os.makedirs(save_dir, exist_ok=True)

        output_file = os.path.join(save_dir , f'{self.subject}_{self.date}_{self.session}_processed.npz')

        # Encode stim_param_names as a numpy string array so it survives npz round-trips.
        # None -> empty array; str -> 1-element array; list -> array of strings.
        if self.stim_param_names is None:
            param_names_arr = np.array([], dtype=str)
        elif isinstance(self.stim_param_names, str):
            param_names_arr = np.array([self.stim_param_names])
        else:
            param_names_arr = np.array(self.stim_param_names)

        # Build keyword arguments: one array per parameter (possible_values_0, _1, ...)
        save_kwargs = dict(
            avg_evoked_each_cond=self.avg_evoked_each_cond,
            avg_baseline_each_cond=self.avg_baseline_each_cond,
            signal_change_each_cond=self.signal_change_each_cond,
            stim_param_names=param_names_arr,
            possible_values=np.array(self.possible_values, dtype=object),
            camera_rotation=self.camera_rotation,
            hemisphere=self.hemisphere,
        )

        np.savez(output_file, **save_kwargs)
        print(f"Saved {output_file}")

    def add_scale_bar(self, ax, bar_length_mm=1.0, location='lower right', 
                     color='white', linewidth=3, fontsize=10, pad=0.05):
        """
        Add a scale bar to a matplotlib axis.
        
        Args:
            ax (matplotlib.axes.Axes): The axis to add the scale bar to.
            bar_length_mm (float): Length of the scale bar in millimeters (default: 1.0).
            location (str): Location of the scale bar. Options: 'lower right', 'lower left',
                'upper right', 'upper left' (default: 'lower right').
            color (str): Color of the scale bar and text (default: 'white').
            linewidth (float): Width of the scale bar line (default: 3).
            fontsize (int): Font size for the label text (default: 10).
            pad (float): Padding from the edge as a fraction of axis size (default: 0.05).
        """
        # Calculate bar length in pixels
        bar_length_pixels = bar_length_mm / self.resolution
        
        # Get axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        
        # Calculate position based on location
        pad_x = x_range * pad
        pad_y = y_range * pad
        
        if 'right' in location:
            x_start = xlim[1] - pad_x - bar_length_pixels
        else:  # 'left'
            x_start = xlim[0] + pad_x
        
        # For images, y-axis is inverted: ylim[0] is top, ylim[1] is bottom
        if 'lower' in location:
            y_pos = ylim[1] - pad_y
            text_y_offset = -pad_y * 0.5  # Text above bar (lower y value)
            text_va = 'top'
        else:  # 'upper'
            y_pos = ylim[0] + pad_y
            text_y_offset = pad_y * 0.5  # Text below bar (higher y value)
            text_va = 'bottom'
        
        x_end = x_start + bar_length_pixels
        
        # Draw the scale bar
        line = ax.plot([x_start, x_end], [y_pos, y_pos], color=color, 
                       linewidth=linewidth, solid_capstyle='butt')[0]
        
        # Add text label
        text_x = x_start + bar_length_pixels / 2
        text_y = y_pos + text_y_offset
        text = ax.text(text_x, text_y, f'{bar_length_mm:.1f} mm', 
                       ha='center', va=text_va, color=color, fontsize=fontsize,
                       weight='bold')
        
        return line, text

    def show_response_summary(self, clim=None):
        """
        Display baseline, evoked, and signal change (dF/F) images for all conditions.

        Rows correspond to frequencies (possible_values[0]). Columns are grouped in
        sets of three (Baseline, Evoked, dF/F) — one group per intensity level
        (possible_values[1]). When only one parameter was used the grid is simply
        (n_freq, 3).

        Args:
            clim (tuple): Color limits for the dF/F colorbar (vmin, vmax).
                If None, uses auto scaling.

        Returns:
            numpy.ndarray: Array of axes with shape (n_freq, 3 * n_intensity).
        """
        if self.signal_change_each_cond is None:
            raise ValueError("No computed results. Call compute_evoked_response() first.")

        n_params = len(self.possible_values)
        n_freq = len(self.possible_values[0])
        n_intensity = len(self.possible_values[1]) if n_params > 1 else 1

        fig = plt.gcf()
        fig.clf()
        axes = fig.subplots(n_freq, 3 * n_intensity, sharex=True, sharey=True, squeeze=False)

        for indt in range(n_intensity):
            col_offset = indt * 3
            intensity_label = (f' ({self.possible_values[1][indt]:.0f} dB)'
                               if n_intensity > 1 else '')
            # Always use a 2nd index when data has 2 param dimensions
            idx_suffix = (indt,) if n_params > 1 else ()

            for indf in range(n_freq):
                idx = (indf,) + idx_suffix

                # Baseline average
                im0 = axes[indf, col_offset + 0].imshow(
                    self.avg_baseline_each_cond[idx], cmap='gray')
                axes[indf, col_offset + 0].set_aspect('equal')
                plt.colorbar(im0, ax=axes[indf, col_offset + 0])

                # Evoked average
                im1 = axes[indf, col_offset + 1].imshow(
                    self.avg_evoked_each_cond[idx], cmap='gray')
                axes[indf, col_offset + 1].set_aspect('equal')
                plt.colorbar(im1, ax=axes[indf, col_offset + 1])

                # Signal change
                im2 = axes[indf, col_offset + 2].imshow(
                    self.signal_change_each_cond[idx], cmap='viridis',
                    vmin=clim[0] if clim else None,
                    vmax=clim[1] if clim else None)
                axes[indf, col_offset + 2].set_aspect('equal')
                plt.colorbar(im2, ax=axes[indf, col_offset + 2], label='dF/F')

            # Column group titles on the first row
            axes[0, col_offset + 0].set_title(f'Baseline{intensity_label}')
            axes[0, col_offset + 1].set_title(f'Evoked{intensity_label}')
            axes[0, col_offset + 2].set_title(f'dF/F{intensity_label}')

        # Row labels: frequency values
        for indf in range(n_freq):
            axes[indf, 0].set_ylabel(f'{self.possible_values[0][indf]:.0f} Hz')

        plt.tight_layout()
        return axes


class WidefieldAverage:
    """
    Class to load and manage precomputed widefield averages for a session.
    
    Attributes:
        subject (str): Subject identifier.
        date (str): Date string (e.g., '20241219').
        session (str): Session identifier. Usually a time string (e.g., '161007').
        avg_evoked_each_cond (numpy.ndarray): Average evoked images for each stimulus.
        avg_baseline_each_cond (numpy.ndarray): Average baseline images for each stimulus.
        signal_change_each_cond (numpy.ndarray): dF/F images for each stimulus.
        stim_param_names (str, list of str, or None): Parameter name(s) used to group trials.
        possible_values (list of numpy.ndarray): Unique values for each parameter;
            e.g. [array([4k,8k,16k]), array([30,50,70])] for freq x intensity.
        camera_rotation (int or float): Camera rotation in degrees CCW.
        hemisphere (str): Which hemisphere is being imaged ('right' or 'left').
        orientation (dict): Anatomical directions for image sides (top, bottom, left, right).
    """
    
    def __init__(self, subject, date, session, resolution=None):
        """
        Initialize a WidefieldAverages object and load data from disk.
        
        Args:
            subject (str): Subject identifier.
            date (str): Date string (e.g., '20241219').
            session (str): Session identifier. Usually a time string (e.g., '161007').
            resolution (float): Image resolution in mm/pixel. If None, uses
                loadwidefield.DEFAULT_RESOLUTION.
        """
        self.subject = subject
        self.date = date
        self.session = session
        self.resolution = resolution if resolution is not None else loadwidefield.DEFAULT_RESOLUTION
        
        # Load data
        save_dir = os.path.join(settings.WIDEFIELD_PATH, self.subject+'_processed')
        input_file = os.path.join(save_dir , f'{self.subject}_{self.date}_{self.session}_processed.npz')
        
        data = np.load(input_file, allow_pickle=True)
        self.avg_evoked_each_cond = data['avg_evoked_each_cond']
        self.avg_baseline_each_cond = data['avg_baseline_each_cond']
        self.signal_change_each_cond = data['signal_change_each_cond']
        self.camera_rotation = int(data['camera_rotation'])
        self.hemisphere = str(data['hemisphere'])

        # possible_values is stored as a numpy object array; convert back to a plain list.
        self.possible_values = list(data['possible_values'])

        # Reconstruct stim_param_names (None / str / list of str).
        if 'stim_param_names' in data:
            names = data['stim_param_names']
            if names.size == 0:
                self.stim_param_names = None
            elif names.size == 1:
                self.stim_param_names = str(names[0])
            else:
                self.stim_param_names = names.tolist()
        else:
            self.stim_param_names = None  # legacy file

        # Load orientation information (with defaults for backward compatibility)
        # self.hemisphere = str(data['hemisphere']) if 'hemisphere' in data else 'right'
        # self.camera_rotation = int(data['camera_rotation']) if 'camera_rotation' in data else 1
        
        # Compute image orientation (anatomical directions)
        self.orientation = loadwidefield.compute_orientation(self.camera_rotation, self.hemisphere)
        
        print(f"Loaded {input_file}")

    def show_signal_change(self, clim=None):
        """
        Display the signal change (dF/F) images for all conditions.

        Rows correspond to frequencies (possible_values[0]). Columns correspond to
        intensity levels (possible_values[1]). When only one parameter was used the
        grid is simply (n_freq, 1).

        Args:
            clim (tuple): Color limits for the colorbar (vmin, vmax). If None, uses auto scaling.

        Returns:
            numpy.ndarray: Array of axes with shape (n_freq, n_intensity).
        """
        n_params = len(self.possible_values)
        n_freq = len(self.possible_values[0])
        n_intensity = len(self.possible_values[1]) if n_params > 1 else 1

        fig = plt.gcf()
        fig.clf()
        axes = fig.subplots(n_freq, n_intensity, sharex=True, sharey=True, squeeze=False)

        for indt in range(n_intensity):
            intensity_label = (f'{self.possible_values[1][indt]:.0f} dB'
                               if n_intensity > 1 else 'dF/F')
            idx_suffix = (indt,) if n_params > 1 else ()

            for indf in range(n_freq):
                idx = (indf,) + idx_suffix
                im = axes[indf, indt].imshow(
                    self.signal_change_each_cond[idx], cmap='viridis',
                    vmin=clim[0] if clim else None,
                    vmax=clim[1] if clim else None)
                axes[indf, indt].set_aspect('equal')
                plt.colorbar(im, ax=axes[indf, indt], label='dF/F')

            axes[0, indt].set_title(intensity_label)

        for indf in range(n_freq):
            axes[indf, 0].set_ylabel(f'{self.possible_values[0][indf]:.0f} Hz')

        plt.tight_layout()
        return axes

    def add_scale_bar(self, ax, bar_length_mm=1.0, location='lower right', 
                     color='white', linewidth=3, fontsize=10, pad=0.05):
        """
        Add a scale bar to a matplotlib axis.
        
        Args:
            ax (matplotlib.axes.Axes): The axis to add the scale bar to.
            bar_length_mm (float): Length of the scale bar in millimeters (default: 1.0).
            location (str): Location of the scale bar. Options: 'lower right', 'lower left',
                'upper right', 'upper left' (default: 'lower right').
            color (str): Color of the scale bar and text (default: 'white').
            linewidth (float): Width of the scale bar line (default: 3).
            fontsize (int): Font size for the label text (default: 10).
            pad (float): Padding from the edge as a fraction of axis size (default: 0.05).
        """
        # Calculate bar length in pixels
        bar_length_pixels = bar_length_mm / self.resolution
        
        # Get axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        
        # Calculate position based on location
        pad_x = x_range * pad
        pad_y = y_range * pad
        
        if 'right' in location:
            x_start = xlim[1] - pad_x - bar_length_pixels
        else:  # 'left'
            x_start = xlim[0] + pad_x
        
        # For images, y-axis is inverted: ylim[0] is top, ylim[1] is bottom
        if 'upper' in location:
            # Lower = bottom of image = higher y value (near ylim[1])
            y_pos = ylim[1] - pad_y
            text_y_offset = -pad_y * 0.5  # Text above bar (lower y value)
            text_va = 'top'
        else:  # 'lower'
            # Upper = top of image = lower y value (near ylim[0])
            y_pos = ylim[0] + pad_y
            text_y_offset = pad_y * 0.5  # Text below bar (higher y value)
            text_va = 'bottom'
        
        x_end = x_start + bar_length_pixels
        
        # Draw the scale bar
        line = ax.plot([x_start, x_end], [y_pos, y_pos], color=color, 
                       linewidth=linewidth, solid_capstyle='butt')[0]
        
        # Add text label
        text_x = x_start + bar_length_pixels / 2
        text_y = y_pos + text_y_offset
        text = ax.text(text_x, text_y, f'{bar_length_mm:.1f} mm', 
                       ha='center', va=text_va, color=color, fontsize=fontsize,
                       weight='bold')
        
        return line, text

    def show_response_summary(self, clim=None):
        """
        Display baseline, evoked, and signal change (dF/F) images for all conditions.

        Rows correspond to frequencies (possible_values[0]). Columns are grouped in
        sets of three (Baseline, Evoked, dF/F) — one group per intensity level
        (possible_values[1]). When only one parameter was used the grid is simply
        (n_freq, 3).

        Args:
            clim (tuple): Color limits for the dF/F colorbar (vmin, vmax).
                If None, uses auto scaling.

        Returns:
            numpy.ndarray: Array of axes with shape (n_freq, 3 * n_intensity).
        """
        n_params = len(self.possible_values)
        n_freq = len(self.possible_values[0])
        n_intensity = len(self.possible_values[1]) if n_params > 1 else 1

        fig = plt.gcf()
        fig.clf()
        axes = fig.subplots(n_freq, 3 * n_intensity, sharex=True, sharey=True, squeeze=False)

        for indt in range(n_intensity):
            col_offset = indt * 3
            intensity_label = (f' ({self.possible_values[1][indt]:.0f} dB)'
                               if n_intensity > 1 else '')
            # Always use a 2nd index when data has 2 param dimensions
            idx_suffix = (indt,) if n_params > 1 else ()

            for indf in range(n_freq):
                idx = (indf,) + idx_suffix

                # Baseline average
                axes[indf, col_offset + 0].imshow(
                    self.avg_baseline_each_cond[idx], cmap='gray')
                axes[indf, col_offset + 0].set_aspect('equal')

                # Evoked average
                axes[indf, col_offset + 1].imshow(
                    self.avg_evoked_each_cond[idx], cmap='gray')
                axes[indf, col_offset + 1].set_aspect('equal')

                # Signal change
                im = axes[indf, col_offset + 2].imshow(
                    self.signal_change_each_cond[idx], cmap='viridis',
                    vmin=clim[0] if clim else None,
                    vmax=clim[1] if clim else None)
                axes[indf, col_offset + 2].set_aspect('equal')
                plt.colorbar(im, ax=axes[indf, col_offset + 2], label='dF/F')

            # Column group titles on the first row
            axes[0, col_offset + 0].set_title(f'Baseline{intensity_label}')
            axes[0, col_offset + 1].set_title(f'Evoked{intensity_label}')
            axes[0, col_offset + 2].set_title(f'dF/F{intensity_label}')

        # Row labels: frequency values
        for indf in range(n_freq):
            axes[indf, 0].set_ylabel(f'{self.possible_values[0][indf]:.0f} Hz')

        plt.tight_layout()
        return axes

    def normalize_signal_change(self, method='percentile', roi=None):
        """
        Normalize the signal change images.
        
        Args:
            method (str): Normalization method. Options:
                - 'std': Divide each condition's signal by its standard deviation.
                - 'percentile': Normalize using 1-99 percentile range. Values are
                  scaled so that the 1st percentile maps to 0 and 99th to 1.
            roi (tuple or None): Region of interest for calculating normalization
                parameters. Format: ((x_min, x_max), (y_min, y_max)). 
                If None, uses the entire image.
        
        Returns:
            numpy.ndarray: Normalized signal change array with same shape as 
                signal_change_each_cond.
        """
        normed = np.zeros_like(self.signal_change_each_cond)
        condition_shape = tuple(len(v) for v in self.possible_values)

        for idx in np.ndindex(*condition_shape):
            img = self.signal_change_each_cond[idx]
            
            # Extract ROI for normalization calculation if specified
            if roi is not None:
                (x_min, x_max), (y_min, y_max) = roi
                roi_data = img[y_min:y_max, x_min:x_max]
            else:
                roi_data = img
            
            if method == 'std':
                std_val = np.std(roi_data)
                if std_val != 0:
                    normed[idx] = img / std_val
                else:
                    normed[idx] = img
            elif method == 'percentile':
                p10 = np.percentile(roi_data, 1)
                p90 = np.percentile(roi_data, 99)
                if p90 != p10:
                    normed[idx] = (img - p10) / (p90 - p10)
                else:
                    normed[idx] = img - p10  # Avoid division by zero
            else:
                raise ValueError(f"Unknown normalization method: {method}")
        
        return normed

    def compute_merged_image(self, normed_signal_change, thresholds=None, enabled=None, 
                              weights=None, bg_image=None, alpha=1.0):
        """
        Compute the merged RGB image from normalized signal change data.
        
        Creates an RGB image where each pixel is colored according to which 
        frequency channel has the maximum response. Uses the first N channels up to 3
        (Red, Green, Blue). For fewer than 3 channels, missing channels are set to zero.
        
        Args:
            normed_signal_change (numpy.ndarray): Normalized signal change array.
                Shape: (n_freq, height, width). Uses up to the first 3 channels.
            thresholds (list or None): Per-channel thresholds. Pixels below threshold
                won't contribute to the max comparison. If a single float, applies to
                all channels. If None, no thresholding is applied.
            enabled (list or None): List of booleans indicating which channels are
                enabled. Disabled channels won't contribute. If None, all enabled.
                Length should match number of channels.
            weights (tuple or list): Weights to apply to each channel before
                finding the max. If None, equal weights are used.
            bg_image (numpy.ndarray or None): If provided, pixels below threshold
                will show this grayscale image (normalized to 0-1) instead of black.
                Shape should be (height, width).
            alpha (float): Transparency of color channels (0-1). When less than 1,
                the baseline image will show through the colored pixels. Requires
                bg_image to be provided. Default is 1.0 (fully opaque).
        
        Returns:
            numpy.ndarray: Merged RGB image with shape (height, width, 3), values clipped to [0, 1].
        """
        if normed_signal_change.ndim != 3:
            raise ValueError(
                f"normed_signal_change must be 3D (n_freq, H, W), "
                f"got shape {normed_signal_change.shape}. "
                "If the data has a second stimulus parameter, slice it first "
                "(e.g. normed[:, param2_idx])."
            )
        n_freq = len(normed_signal_change)
        n_channels = min(n_freq, 3)  # Use up to 3 channels for RGB
        
        # Default values
        if thresholds is None:
            thresholds = [None] * n_freq
        elif isinstance(thresholds, (int, float)):
            thresholds = [thresholds] * n_freq
        if enabled is None:
            enabled = [True] * n_freq
        
        # Pad to ensure we have 3 channels (fill missing with zeros)
        first_three = np.zeros((3, *normed_signal_change.shape[1:]))
        first_three[:n_channels] = normed_signal_change[:n_channels].copy()
        
        # Apply weights if provided
        if weights is not None:
            weights_arr = np.array(weights)[:3]
            first_three = first_three * weights_arr[:, None, None]
        
        # Apply thresholds and enabled state
        thresholded = first_three.copy()
        for i in range(3):
            # Only process channels that exist in the input
            if i < n_freq:
                if not enabled[i]:
                    thresholded[i] = -np.inf
                elif thresholds[i] is not None:
                    thresholded[i] = np.where(first_three[i] >= thresholds[i],
                                              first_three[i], -np.inf)
            else:
                # Non-existent channels set to -inf
                thresholded[i] = -np.inf
        
        # Find which channel has max value at each pixel
        max_channel = np.argmax(thresholded, axis=0)
        max_values = np.max(thresholded, axis=0)
        
        # Create RGB image where each pixel gets the color of its max channel
        merged_image = np.zeros((*normed_signal_change.shape[1:], 3))
        for channel in range(3):
            # Only process channels that exist and are enabled
            if channel < n_freq and enabled[channel]:
                mask = (max_channel == channel) & (max_values > -np.inf)
                for c in range(3):
                    merged_image[mask, c] = max_values[mask] * CHANNEL_COLORS[channel][c]
        
        # Add baseline image to pixels below threshold
        if bg_image is not None:
            # Normalize baseline using percentiles for better contrast
            p_low = np.percentile(bg_image, 1)
            p_high = np.percentile(bg_image, 99)
            baseline_norm = (bg_image - p_low) / (p_high - p_low)
            baseline_norm = np.clip(baseline_norm, 0, 1)
            # Find pixels where no channel crossed threshold (black pixels)
            below_threshold_mask = (max_values == -np.inf)
            # Set those pixels to grayscale baseline
            for c in range(3):
                merged_image[below_threshold_mask, c] = baseline_norm[below_threshold_mask]
            
            # Blend colored pixels with baseline if alpha < 1
            if alpha < 1.0:
                above_threshold_mask = ~below_threshold_mask
                for c in range(3):
                    merged_image[above_threshold_mask, c] = (
                        alpha * merged_image[above_threshold_mask, c] + 
                        (1 - alpha) * baseline_norm[above_threshold_mask]
                    )
        
        return np.clip(merged_image, 0, 1)

    def compute_clim(self, normed_signal_change, n_std_low=2, n_std_high=8):
        """
        Compute color limits based on standard deviation of normalized data.
        
        Args:
            normed_signal_change (numpy.ndarray): Normalized signal change array.
            n_std_low (float): Number of standard deviations for lower bound.
            n_std_high (float): Number of standard deviations for upper bound.
        
        Returns:
            tuple: (vmin, vmax) color limits.
        """
        global_std = np.std(normed_signal_change[:3])
        return (-n_std_low * global_std, n_std_high * global_std)

    def show_merged_signal_change(self, fig=None, clim=None, weights=None, roi=None,
                                  threshold=None, thresholds=None, enabled=None,
                                  bg=True, alpha=1.0, param2_idx=0):
        """
        Display merged signal change (dF/F) images for the first three frequencies.

        Shows two columns: the left column displays the normalized signal change
        for each of the first three frequencies, and the right column shows
        a merged RGB image where each pixel is colored according to which
        frequency has the maximum response. Red = freq[0], Green = freq[1], Blue = freq[2].

        When data has a second stimulus parameter (e.g. intensity, AM depth, …),
        use ``param2_idx`` to select which value of that parameter to display.

        Args:
            fig (matplotlib.figure.Figure or None): Figure to plot into. If None,
                uses plt.gcf() and clears it.
            clim (tuple): Color limits for the individual frequency images (vmin, vmax).
                If None, estimated from standard deviations of the normalized data.
            weights (tuple or list): Weights to apply to each channel (R, G, B) before
                finding the max. If None, equal weights are used.
            roi (tuple or None): Region of interest for normalization.
                Format: ((x_min, x_max), (y_min, y_max)). If None, uses the entire image.
            threshold (float or None): Applies the same threshold to all channels.
                Pixels below threshold will be black. (Legacy; prefer thresholds.)
            thresholds (list or None): Per-channel thresholds [red, green, blue].
                Overrides threshold if both are provided.
            enabled (list or None): List of 3 booleans indicating which channels are enabled.
            bg (bool): If True, pixels below threshold show the average baseline image
                (grayscale) instead of black. Default is True.
            alpha (float): Transparency of color channels (0–1). Requires bg=True.
                Default is 1.0 (fully opaque).
            param2_idx (int): Index into possible_values[1] selecting which value of the
                second stimulus parameter to display (e.g., which intensity to show).
                Ignored when there is only one parameter. Default is 0.

        Returns:
            tuple: (axes_left, ax_merged) — list of left-column axes and merged image axis.
        """
        n_params = len(self.possible_values)
        n_freq = len(self.possible_values[0])
        if n_freq < 3:
            raise ValueError("Need at least 3 frequencies to create RGB merged image.")

        # Build a human-readable label for the second parameter value, if present.
        param2_label = ''
        if n_params > 1:
            param2_name = (self.stim_param_names[1]
                           if isinstance(self.stim_param_names, list)
                           else 'param2')
            param2_val = self.possible_values[1][param2_idx]
            param2_label = f'{param2_name}={param2_val:.4g}'

        # Normalize all conditions, then slice to the requested second-param value.
        normed_all = self.normalize_signal_change(roi=roi)
        if n_params > 1:
            normed_signal_change = normed_all[:, param2_idx]   # (n_freq, H, W)
        else:
            normed_signal_change = normed_all                  # (n_freq, H, W)

        # Set clim based on standard deviation if not provided
        if clim is None:
            clim = self.compute_clim(normed_signal_change)

        # Handle legacy threshold parameter
        if thresholds is None and threshold is not None:
            thresholds = threshold  # Will be expanded in compute_merged_image

        # Average baseline image for the selected second-param slice
        baseline_image = None
        if bg:
            if n_params > 1:
                baseline_image = np.mean(self.avg_baseline_each_cond[:3, param2_idx], axis=0)
            else:
                baseline_image = np.mean(self.avg_baseline_each_cond[:3], axis=0)

        # Compute merged image
        merged_image = self.compute_merged_image(normed_signal_change, thresholds=thresholds,
                                                  enabled=enabled, weights=weights,
                                                  bg_image=baseline_image, alpha=alpha)

        # Create figure with 3 rows, 2 columns
        if fig is None:
            fig = plt.gcf()
            fig.clf()

        # Create first axis to use as reference for sharing
        ax_first = fig.add_subplot(3, 2, 1)

        # Left column: individual normalized signal change images
        axes_left = []
        for indf in range(3):
            if indf == 0:
                ax = ax_first
            else:
                ax = fig.add_subplot(3, 2, 2 * indf + 1, sharex=ax_first, sharey=ax_first)
            im = ax.imshow(normed_signal_change[indf], cmap='viridis',
                           vmin=clim[0], vmax=clim[1])

            status = ''
            if enabled is not None and not enabled[indf]:
                status = ' [DISABLED]'
            ax.set_ylabel(f'{self.possible_values[0][indf]:.0f} Hz\n({CHANNEL_NAMES[indf]}){status}')
            ax.set_aspect('equal')
            if indf == 0:
                title = 'Normalized dF/F'
                if param2_label:
                    title += f'\n{param2_label}'
                ax.set_title(title)
            fig.colorbar(im, ax=ax)
            axes_left.append(ax)

        # Right column: merged RGB image (spanning all 3 rows, sharing axes)
        ax_merged = fig.add_subplot(1, 2, 2, sharex=ax_first, sharey=ax_first)
        ax_merged.imshow(merged_image)
        merged_title = 'Merged (RGB: max channel)'
        if param2_label:
            merged_title += f'\n{param2_label}'
        ax_merged.set_title(merged_title)
        ax_merged.set_aspect('equal')

        # Zoom into ROI if provided
        if roi is not None:
            (x_min, x_max), (y_min, y_max) = roi
            ax_first.set_xlim(x_min, x_max)
            ax_first.set_ylim(y_max, y_min)  # Inverted for image coordinates

        fig.tight_layout()
        return axes_left, ax_merged


if __name__ == '__main__':
    subject = 'wifi008'
    date = '20241219'
    session = '161007'
    suffix = 'LG'

    if 1:
        # Using the extended class
        wfobj = Widefield(subject, date, session, suffix=suffix)
        wfobj.load_timestamps()
        wfobj.load_frames(memmap=True)
        wfobj.load_behavior()
        print(wfobj)

        # Compute evoked responses
        signal_change = wfobj.compute_evoked_response()
        print(f"Computed responses for {len(wfobj.possible_values[0])} frequencies")
        print(f"Signal change shape: {wfobj.signal_change_each_cond.shape}")
        wfobj.save()

    if 0:
        # Load precomputed averages
        wfavg = WidefieldAverage(subject, date, session)
        #print(f"Loaded averages for {len(wfavg.possible_values[0])} frequencies")
        print(f"Signal change shape: {wfavg.signal_change_each_cond.shape}")
        # Display all frequencies
        #wfavg.show_signal_change() #clim=(-0.1, 0.3))
        wfavg.show_response_summary() #clim=(-0.1, 0.3))

    if 0:
        roi = [[150, 350], [200, 400]]
        wfavg = WidefieldAverage(subject, date, session)
        axes = wfavg.show_signal_change()
        #axes = wfavg.show_signal_change(clim=(-1,12))  # If normalized
        # Set xlim and ylim for all axes
        for ax in axes.ravel():
            ax.set_xlim(roi[0])
            ax.set_ylim(roi[1])

    if 0:
        roi = [[170, 370], [250, 450]]  #[[200, 400], [150, 350]]
        wfavg = WidefieldAverage(subject, date, session)
        #ax, axm = wfavg.show_merged_signal_change(weights=(1.1, 0.99, 1))
        ax, axm = wfavg.show_merged_signal_change(roi=roi, threshold=0.6, alpha=0.3) 
        wfavg.add_scale_bar(axm, bar_length_mm=1.0, location='lower left')
        #, weights=(1.0, 1, 0.95))
        normed = wfavg.normalize_signal_change(roi=roi)
        # Set xlim and ylim
        #axm.set_xlim(roi[0])
        #axm.set_ylim(roi[1])

    if 1:
        #roi = [[170, 370], [250, 450]]
        wfobj = Widefield(subject, date, session, suffix=suffix)
        wfobj.load_timestamps()
        wfobj.load_frames(memmap=True)
        signal_change = wfobj.compute_evoked_response(stim_param=None)
        wfobj.show_response_summary()
        plt.suptitle(f'{subject} {date} {session} - All stimuli', fontweight='bold')
