"""
Classes and methods for analysis of widefield imaging data.
"""

import os
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


class Widefield(loadwidefield.WidefieldData):
    """
    Extended Widefield class with additional analysis methods.
    
    Inherits from loadwidefield.WidefieldData.
    """
    
    def __init__(self, subject, date, session, suffix='', paradigm='am_tuning_curve',
                 camera_rotation=1, hemisphere='right'):
        """
        Initialize a Widefield object.
        
        Args:
            subject (str): Subject identifier.
            date (str): Date string (e.g., '20241219').
            session (str): Session identifier. Usually a time string (e.g., '161007').
            suffix (str): Suffix for the TIFF filename (e.g., 'LG' for left-green).
            paradigm (str): Behavioral paradigm name (default: 'am_tuning_curve').
            camera_rotation (int): Physical rotation of the camera in units of 
                90-degree CCW rotations. Default is 1 (camera rotated 90° CCW).
                Use 0 if camera is not rotated.
            hemisphere (str): Which side of the brain is being imaged. 
                'right' (default) or 'left'. This affects the anterior-posterior
                orientation in the final image.
        """
        super().__init__(subject, date, session, suffix=suffix, paradigm=paradigm,
                         camera_rotation=camera_rotation, hemisphere=hemisphere)
        
        # Analysis results (computed on demand)
        self.possible_freq = None
        self.trials_each_freq = None
        self.avg_evoked_each_freq = None
        self.avg_baseline_each_freq = None
        self.signal_change_each_freq = None
    
    def compute_evoked_response(self, stim_param='currentFreq'):
        """
        Compute average evoked response for each stimulus type.
        
        This method calculates the average fluorescence during the stimulus
        (evoked) and before the stimulus (baseline) for each unique stimulus
        value, then computes the relative change in fluorescence (dF/F).
        
        Args:
            stim_param (str or None): Name of the behavioral parameter to group trials by
                (default: 'currentFreq'). If None, treats all trials as having the same
                stimulus (useful when there's no behavioral variation).
        
        Returns:
            numpy.ndarray: Signal change (dF/F) for each stimulus type.
                Shape: (n_stim_types, height, width)
        
        Note:
            Results are also stored in:
            - self.possible_freq: unique stimulus values
            - self.trials_each_freq: boolean array of trials for each stimulus
            - self.avg_evoked_each_freq: average evoked image for each stimulus
            - self.avg_baseline_each_freq: average baseline image for each stimulus
            - self.signal_change_each_freq: dF/F for each stimulus
        """
        # Ensure data is loaded
        if self.frames is None:
            raise ValueError("Frames not loaded. Call load_frames() first.")
        if self.sound_onset is None:
            raise ValueError("Timestamps not loaded. Call load_timestamps() first.")
        
        # -- Align trials with sound events --
        if stim_param is None:
            # Treat all trials as having the same stimulus
            n_trials = len(self.sound_onset)
            current_stim = np.zeros(n_trials)  # All trials have the same value
            self.possible_freq = np.array([0])
        else:
            # Use behavioral data to group trials
            if self.bdata is None:
                raise ValueError("Behavior data not loaded. Call load_behavior() first.")
            n_trials = min(len(self.bdata[stim_param]), len(self.sound_onset))
            current_stim = self.bdata[stim_param][:n_trials]
            self.possible_freq = np.unique(current_stim)
        
        self.trials_each_freq = behavioranalysis.find_trials_each_type(
            current_stim, self.possible_freq
        )
        
        # Fix the length of sound onsets to match bdata trials
        sound_onset = self.sound_onset[:n_trials]
        sound_offset = self.sound_offset[:n_trials]
        
        # -- Calculate timing parameters --
        sound_duration = np.mean(sound_offset - sound_onset)
        frame_rate = 1 / np.mean(np.diff(self.ts_frames))
        sound_duration_in_frames = int(round(sound_duration * frame_rate))
        
        # Find frames corresponding to sound onset
        frame_after_onset = np.searchsorted(self.ts_frames, sound_onset, side='left')
        
        # -- Compute evoked response for each stimulus type --
        avg_evoked_each_freq = []
        avg_baseline_each_freq = []
        signal_change_each_freq = []
        
        for indf, freq in enumerate(self.possible_freq):
            # Get frames after sound onset for this stimulus type
            frame_after_onset_this_freq = frame_after_onset[self.trials_each_freq[:, indf]]
            
            # Create array of all evoked frame indices
            evoked_frames_this_freq = np.tile(
                frame_after_onset_this_freq, (sound_duration_in_frames, 1)
            )
            evoked_frames_this_freq += np.arange(sound_duration_in_frames)[:, None]
            evoked_frames_this_freq = np.sort(evoked_frames_this_freq.ravel())
            
            # Handle case where video may be split into multiple recordings
            final_frames = np.searchsorted(evoked_frames_this_freq, len(self.frames))
            evoked_indices = evoked_frames_this_freq[:final_frames]
            
            # Compute average evoked fluorescence
            avg_evoked_this_freq = np.mean(self.frames[evoked_indices], axis=0)
            
            # Compute average baseline fluorescence (same duration before onset)
            baseline_indices = evoked_indices - sound_duration_in_frames
            avg_baseline_this_freq = np.mean(self.frames[baseline_indices], axis=0)
            
            # Compute relative change in fluorescence (dF/F)
            signal_change = (avg_evoked_this_freq - avg_baseline_this_freq) / avg_baseline_this_freq
            
            avg_evoked_each_freq.append(avg_evoked_this_freq)
            avg_baseline_each_freq.append(avg_baseline_this_freq)
            signal_change_each_freq.append(signal_change)
        
        # Convert lists to arrays and store
        self.avg_evoked_each_freq = np.array(avg_evoked_each_freq)
        self.avg_baseline_each_freq = np.array(avg_baseline_each_freq)
        self.signal_change_each_freq = np.array(signal_change_each_freq)
        
        return self.signal_change_each_freq

    def save(self):
        """
        Save analysis results to disk.
        """
        save_dir = os.path.join(settings.WIDEFIELD_PATH, self.subject+'_processed')
        os.makedirs(save_dir, exist_ok=True)

        output_file = os.path.join(save_dir , f'{self.subject}_{self.date}_{self.session}_processed.npz')

        np.savez(output_file, avg_evoked_each_freq=self.avg_evoked_each_freq,
                 avg_baseline_each_freq=self.avg_baseline_each_freq,
                 signal_change_each_freq=self.signal_change_each_freq, 
                 possible_freq=self.possible_freq,
                 camera_rotation=self.camera_rotation,
                 hemisphere=self.hemisphere)
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
        Display baseline, evoked, and signal change (dF/F) images for all frequencies.
        
        Shows three columns: Baseline (pre-stimulus average), Evoked (during-stimulus 
        average), and dF/F (relative fluorescence change). Each row corresponds to
        one frequency.
        
        Args:
            clim (tuple): Color limits for the dF/F colorbar (vmin, vmax). 
                If None, uses auto scaling.
        
        Returns:
            numpy.ndarray: Array of axes objects.
        """
        if self.signal_change_each_freq is None:
            raise ValueError("No computed results. Call compute_evoked_response() first.")
        
        n_freq = len(self.possible_freq)
        fig = plt.gcf()
        fig.clf()
        axes = fig.subplots(n_freq, 3, sharex=True, sharey=True, squeeze=False)
        
        for indf in range(n_freq):
            # Baseline average
            im0 = axes[indf, 0].imshow(self.avg_baseline_each_freq[indf], cmap='gray')
            axes[indf, 0].set_aspect('equal')
            plt.colorbar(im0, ax=axes[indf, 0])
            
            # Evoked average
            im1 = axes[indf, 1].imshow(self.avg_evoked_each_freq[indf], cmap='gray')
            axes[indf, 1].set_aspect('equal')
            plt.colorbar(im1, ax=axes[indf, 1])
            
            # Signal change
            im2 = axes[indf, 2].imshow(self.signal_change_each_freq[indf], cmap='viridis',
                           vmin=clim[0] if clim else None,
                           vmax=clim[1] if clim else None)
            axes[indf, 2].set_aspect('equal')
            plt.colorbar(im2, ax=axes[indf, 2], label='dF/F')
            
            # Add frequency label on the left
            axes[indf, 0].set_ylabel(f'{self.possible_freq[indf]:.0f} Hz')
        
        # Column titles on first row
        axes[0, 0].set_title('Baseline')
        axes[0, 1].set_title('Evoked')
        axes[0, 2].set_title('dF/F')
        plt.tight_layout()
        return axes


class WidefieldAverage:
    """
    Class to load and manage precomputed widefield averages for a session.
    
    Attributes:
        subject (str): Subject identifier.
        date (str): Date string (e.g., '20241219').
        session (str): Session identifier. Usually a time string (e.g., '161007').
        avg_evoked_each_freq (numpy.ndarray): Average evoked images for each stimulus.
        avg_baseline_each_freq (numpy.ndarray): Average baseline images for each stimulus.
        signal_change_each_freq (numpy.ndarray): dF/F images for each stimulus.
        possible_freq (numpy.ndarray): Unique stimulus values.
        camera_rotation (int): Camera rotation in units of 90-degree CCW rotations.
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
        
        data = np.load(input_file)
        self.avg_evoked_each_freq = data['avg_evoked_each_freq']
        self.avg_baseline_each_freq = data['avg_baseline_each_freq']
        self.signal_change_each_freq = data['signal_change_each_freq']
        self.possible_freq = data['possible_freq']
        self.camera_rotation = int(data['camera_rotation'])
        self.hemisphere = str(data['hemisphere'])

        # Load orientation information (with defaults for backward compatibility)
        # self.hemisphere = str(data['hemisphere']) if 'hemisphere' in data else 'right'
        # self.camera_rotation = int(data['camera_rotation']) if 'camera_rotation' in data else 1
        
        # Compute image orientation (anatomical directions)
        self.orientation = loadwidefield.compute_orientation(self.camera_rotation, self.hemisphere)
        
        print(f"Loaded {input_file}")

    def show_signal_change(self, clim=None):
        """
        Display the signal change (dF/F) images for all frequencies.
        
        Args:
            clim (tuple): Color limits for the colorbar (vmin, vmax). If None, uses auto scaling.
        """
        n_freq = len(self.possible_freq)
        fig = plt.gcf()
        fig.clf()
        axes = fig.subplots(n_freq, 1, sharex=True, sharey=True, squeeze=False)
        
        if 0:
            # Normalize signal change by the standard deviation for each frequency
            normed_signal_change = self.signal_change_each_freq / np.std(self.signal_change_each_freq,
                                                                          axis=(1,2), keepdims=True)
            signal_change = normed_signal_change
        else:
            signal_change = self.signal_change_each_freq
    
        for indf in range(n_freq):
            im = axes[indf, 0].imshow(signal_change[indf], cmap='viridis',
                           vmin=clim[0] if clim else None,
                           vmax=clim[1] if clim else None)
            axes[indf, 0].set_ylabel(f'{self.possible_freq[indf]:.0f} Hz')
            axes[indf, 0].set_aspect('equal')
            plt.colorbar(im, ax=axes[indf, 0], label='dF/F')
        
        axes[0, 0].set_title('dF/F')
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
        Display baseline, evoked, and signal change (dF/F) images for all frequencies.
        
        Shows three columns: Baseline (pre-stimulus average), Evoked (during-stimulus 
        average), and dF/F (relative fluorescence change). Each row corresponds to
        one frequency.
        
        Args:
            clim (tuple): Color limits for the dF/F colorbar (vmin, vmax). 
                If None, uses auto scaling.
        """
        n_freq = len(self.possible_freq)
        fig = plt.gcf()
        fig.clf()
        axes = fig.subplots(n_freq, 3, sharex=True, sharey=True, squeeze=False)
        
        for indf in range(n_freq):
            # Baseline average
            axes[indf, 0].imshow(self.avg_baseline_each_freq[indf], cmap='gray')
            axes[indf, 0].set_aspect('equal')
            
            # Evoked average
            axes[indf, 1].imshow(self.avg_evoked_each_freq[indf], cmap='gray')
            axes[indf, 1].set_aspect('equal')
            
            # Signal change
            im = axes[indf, 2].imshow(self.signal_change_each_freq[indf], cmap='viridis',
                           vmin=clim[0] if clim else None,
                           vmax=clim[1] if clim else None)
            axes[indf, 2].set_aspect('equal')
            plt.colorbar(im, ax=axes[indf, 2], label='dF/F')
            
            # Add frequency label on the left
            axes[indf, 0].set_ylabel(f'{self.possible_freq[indf]:.0f} Hz')
        
        # Column titles on first row
        axes[0, 0].set_title('Baseline')
        axes[0, 1].set_title('Evoked')
        axes[0, 2].set_title('dF/F')
        plt.tight_layout()
        return axes

    def normalize_signal_change(self, method='percentile', roi=None):
        """
        Normalize the signal change images.
        
        Args:
            method (str): Normalization method. Options:
                - 'std': Divide each frequency's signal by its standard deviation.
                - 'percentile': Normalize using 10-90 percentile range. Values are
                  scaled so that the 10th percentile maps to 0 and 90th to 1.
            roi (tuple or None): Region of interest for calculating normalization
                parameters. Format: ((x_min, x_max), (y_min, y_max)). 
                If None, uses the entire image.
        
        Returns:
            numpy.ndarray: Normalized signal change array with same shape as 
                signal_change_each_freq.
        """
        normed = np.zeros_like(self.signal_change_each_freq)
        
        for indf in range(len(self.possible_freq)):
            img = self.signal_change_each_freq[indf]
            
            # Extract ROI for normalization calculation if specified
            if roi is not None:
                (x_min, x_max), (y_min, y_max) = roi
                roi_data = img[y_min:y_max, x_min:x_max]
            else:
                roi_data = img
            
            if method == 'std':
                std_val = np.std(roi_data)
                if std_val != 0:
                    normed[indf] = img / std_val
                else:
                    normed[indf] = img
            elif method == 'percentile':
                # Calculate 10th and 90th percentiles
                # p10 = np.min(roi_data)
                # p90 = np.max(roi_data)
                p10 = np.percentile(roi_data, 1)
                p90 = np.percentile(roi_data, 99)
                
                # Normalize: map p10 to 0, p90 to 1
                if p90 != p10:
                    normed[indf] = (img - p10) / (p90 - p10)
                else:
                    normed[indf] = img - p10  # Avoid division by zero
            else:
                raise ValueError(f"Unknown normalization method: {method}")
        
        return normed

    def compute_merged_image(self, normed_signal_change, thresholds=None, enabled=None, 
                              weights=None, bg_image=None, alpha=1.0):
        """
        Compute the merged RGB image from normalized signal change data.
        
        Creates an RGB image where each pixel is colored according to which 
        frequency channel has the maximum response. Red = freq[0], Green = freq[1], 
        Blue = freq[2].
        
        Args:
            normed_signal_change (numpy.ndarray): Normalized signal change array.
                Shape: (n_freq, height, width). Only the first 3 channels are used.
            thresholds (list or None): Per-channel thresholds. Pixels below threshold
                won't contribute to the max comparison. If a single float, applies to
                all channels. If None, no thresholding is applied.
            enabled (list or None): List of 3 booleans indicating which channels are
                enabled. Disabled channels won't contribute. If None, all enabled.
            weights (tuple or list): Weights to apply to each channel (R, G, B) before
                finding the max. For example, weights=(1, 0.5, 1) would reduce the 
                contribution of the green channel. If None, equal weights are used.
            bg_image (numpy.ndarray or None): If provided, pixels below threshold
                will show this grayscale image (normalized to 0-1) instead of black.
                Shape should be (height, width).
            alpha (float): Transparency of color channels (0-1). When less than 1,
                the baseline image will show through the colored pixels. Requires
                bg_image to be provided. Default is 1.0 (fully opaque).
        
        Returns:
            numpy.ndarray: Merged RGB image with shape (height, width, 3), values clipped to [0, 1].
        """
        if len(normed_signal_change) < 3:
            raise ValueError("Need at least 3 frequencies to create RGB merged image.")
        
        # Default values
        if thresholds is None:
            thresholds = [None, None, None]
        elif isinstance(thresholds, (int, float)):
            thresholds = [thresholds, thresholds, thresholds]
        if enabled is None:
            enabled = [True, True, True]
        
        first_three = normed_signal_change[:3].copy()
        
        # Apply weights if provided
        if weights is not None:
            weights_arr = np.array(weights)[:3]
            first_three = first_three * weights_arr[:, None, None]
        
        # Apply thresholds and enabled state
        thresholded = first_three.copy()
        for i in range(3):
            if not enabled[i]:
                thresholded[i] = -np.inf
            elif thresholds[i] is not None:
                thresholded[i] = np.where(first_three[i] >= thresholds[i],
                                          first_three[i], -np.inf)
        
        # Find which channel has max value at each pixel
        max_channel = np.argmax(thresholded, axis=0)
        max_values = np.max(thresholded, axis=0)
        
        # Create RGB image where each pixel gets the color of its max channel
        merged_image = np.zeros((*normed_signal_change.shape[1:], 3))
        for channel in range(3):
            if enabled[channel]:
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
                                  bg=True, alpha=1.0):
        """
        Display merged signal change (dF/F) images for all frequencies.
        
        Shows two columns: the left column displays the normalized signal change
        for each of the first three frequencies, and the right column shows
        a merged RGB image where each pixel is colored according to which 
        frequency has the maximum response. Red = freq[0], Green = freq[1], Blue = freq[2].
        
        Args:
            fig (matplotlib.figure.Figure or None): Figure to plot into. If None,
                uses plt.gcf() and clears it.
            clim (tuple): Color limits for the individual frequency images (vmin, vmax). 
                If None, it estimates it from standard deviations of the normalized data.
            weights (tuple or list): Weights to apply to each channel (R, G, B) before
                finding the max. For example, weights=(1, 0.5, 1) would reduce the 
                contribution of the green channel. If None, equal weights are used.
            roi (tuple or None): Region of interest for calculating normalization
                parameters. Format: ((x_min, x_max), (y_min, y_max)). 
                If None, uses the entire image.
            threshold (float or None): If provided, applies same threshold to all channels.
                Pixels below threshold will be black. (Legacy parameter, use thresholds instead.)
            thresholds (list or None): Per-channel thresholds [red, green, blue].
                Overrides threshold if both are provided.
            enabled (list or None): List of 3 booleans indicating which channels are enabled.
            bg (bool): If True, pixels below threshold will show the average
                baseline image (grayscale) as background instead of black. Default is False.
            alpha (float): Transparency of color channels (0-1). When less than 1,
                the baseline image will show through the colored pixels. Requires
                bg=True. Default is 1.0 (fully opaque).
        
        Returns:
            tuple: (axes_left, ax_merged) - list of left column axes and merged image axis.
        """
        n_freq = len(self.possible_freq)
        if n_freq < 3:
            raise ValueError("Need at least 3 frequencies to create RGB merged image.")
        
        # Normalize signal change for merging
        normed_signal_change = self.normalize_signal_change(roi=roi)
        
        # Set clim based on standard deviation if not provided
        if clim is None:
            clim = self.compute_clim(normed_signal_change)
        
        # Handle legacy threshold parameter
        if thresholds is None and threshold is not None:
            thresholds = threshold  # Will be expanded in compute_merged_image
        
        # Compute average baseline image if needed
        baseline_image = None
        if bg:
            baseline_image = np.mean(self.avg_baseline_each_freq[:3], axis=0)
        
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
            
            # Add indicator if channel is disabled
            status = ''
            if enabled is not None and not enabled[indf]:
                status = ' [DISABLED]'
            ax.set_ylabel(f'{self.possible_freq[indf]:.0f} Hz\n({CHANNEL_NAMES[indf]}){status}')
            ax.set_aspect('equal')
            if indf == 0:
                ax.set_title('Normalized dF/F')
            fig.colorbar(im, ax=ax)
            axes_left.append(ax)
        
        # Right column: merged RGB image (spanning all 3 rows, sharing axes)
        ax_merged = fig.add_subplot(1, 2, 2, sharex=ax_first, sharey=ax_first)
        ax_merged.imshow(merged_image)
        ax_merged.set_title('Merged (RGB: max channel)')
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
        print(f"Computed responses for {len(wfobj.possible_freq)} frequencies")
        print(f"Signal change shape: {wfobj.signal_change_each_freq.shape}")
        wfobj.save()

    if 0:
        # Load precomputed averages
        wfavg = WidefieldAverage(subject, date, session)
        #print(f"Loaded averages for {len(wfavg.possible_freq)} frequencies")
        print(f"Signal change shape: {wfavg.signal_change_each_freq.shape}")
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
