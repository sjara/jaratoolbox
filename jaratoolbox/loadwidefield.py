"""
Load widefield imaging data.
"""

import os
import numpy as np
from jaratoolbox import loadbehavior
from jaratoolbox import settings
import tifffile

def load_timestamps(timestamps_filename):
    timestamps = np.load(timestamps_filename)
    sound_onset = timestamps['ts_sound_rising']
    sound_offset = timestamps['ts_sound_falling']
    ts_frames = timestamps['ts_trigger_rising']
    return sound_onset, sound_offset, ts_frames
    
def load_widefield(subject, date, session, suffix='', memmap=False):
    """
    Load widefield imaging data from TIFF file(s).
    
    Args:
        subject (str): Subject identifier.
        date (str): Date string (e.g., '20241219').
        session (str): Session identifier. Usually a time string (e.g., '161007').
        suffix (str): Optional suffix for the filename.
        memmap (bool): If True, return a memory-mapped array instead of loading
            the entire file into RAM. Useful for large files. Note that memmap
            only works efficiently for a single TIFF file; multiple files will
            still be concatenated in memory.
    
    Returns:
        numpy.ndarray: Array of frames (or memory-mapped array if memmap=True).
    """
    frames_filename = os.path.join(settings.WIDEFIELD_PATH, subject, date, f'{subject}_{date}_{session}_{suffix}.tif')

    # FIXME: Set to 1 for debugging (we'll implement multi-file loading later)
    n_frames_files = 1  

    print(f"Loading data from {frames_filename}...")

    # -- Create list of TIFF files --
    frames_filenames = [frames_filename]
    suffix_pattern = '_@{0:04g}'
    for indf in range(1, n_frames_files):
        new_suffix = suffix_pattern.format(indf)
        new_filename = frames_filename.replace('.tif', new_suffix+'.tif')
        frames_filenames.append(new_filename)

    print(f"Found {len(frames_filenames)} TIFF files to load.")
    print(frames_filenames)

    # -- Load TIFF files --    
    frames = None  # A numpy array to store all frames
    for indf, filename in enumerate(frames_filenames):    
        with tifffile.TiffFile(filename) as tif:
            # NOTE: Memory mapping is not working so it's disabled for now
            # if memmap and n_frames_files == 1:
            #     # Use memory mapping for single file (more efficient for large files)
            #     print('Using memory mapping to load TIFF file...')
            #     frames = tif.asarray(out='memmap')
            # else:
            if 1:
                chunk = tif.asarray()
                # image = tif.asarray()[0] #If I want to see a single image 
                axes = tif.series[0].axes
                if frames is None:
                    frames = chunk
                else:
                    frames = np.concatenate((frames, chunk), axis=0)
    
    return frames

def load_stimulus(subject, date, session, paradigm='2afc'):
    stimulus_filename = loadbehavior.path_to_behavior_data(subject, paradigm, f'{date}_{session}')
    bdata = loadbehavior.BehaviorData(stimulus_filename)
    return bdata


class Widefield:
    """
    Class to load and manage widefield imaging data for a single session.
    
    Attributes:
        subject (str): Subject identifier.
        date (str): Date string (e.g., '20241219').
        session (str): Session identifier. Usually a time string (e.g., '161007').
        suffix (str): Suffix for the TIFF filename (e.g., 'LG' for left-green).
        paradigm (str): Behavioral paradigm name.
        frames (numpy.ndarray): Widefield imaging frames (loaded on demand).
        sound_onset (numpy.ndarray): Timestamps of sound onset events.
        sound_offset (numpy.ndarray): Timestamps of sound offset events.
        ts_frames (numpy.ndarray): Timestamps for each imaging frame.
        bdata (BehaviorData): Behavioral data object.
    
    Example:
        >>> wfs = WidefieldSession('wifi008', '20241219', '161007', suffix='LG')
        >>> wfs.load_frames(memmap=True)
        >>> wfs.load_timestamps()
        >>> wfs.load_behavior()
        >>> print(wfs.frames.shape)
    """
    
    def __init__(self, subject, date, session, suffix='', paradigm='am_tuning_curve'):
        """
        Initialize a WidefieldSession object.
        
        Args:
            subject (str): Subject identifier.
            date (str): Date string (e.g., '20241219').
            session (str): Session identifier. Usually a time string (e.g., '161007').
            suffix (str): Suffix for the TIFF filename (e.g., 'LG' for left-green).
            paradigm (str): Behavioral paradigm name (default: 'am_tuning_curve').
        """
        self.subject = subject
        self.date = date
        self.session = session
        self.suffix = suffix
        self.paradigm = paradigm
        
        # Data attributes (loaded on demand)
        self.frames = None
        self.sound_onset = None
        self.sound_offset = None
        self.ts_frames = None
        self.bdata = None
        
        # File paths
        self.data_path = os.path.join(settings.WIDEFIELD_PATH, subject, date)
        self.frames_filename = os.path.join(
            self.data_path, f'{subject}_{date}_{session}_{suffix}.tif'
        )
        self.timestamps_filename = os.path.join(
            self.data_path, f'{subject}_timestamps_{date}_{session}.npz'
        )
    
    def load_frames(self, memmap=False):
        """
        Load widefield imaging frames from TIFF file(s).
        
        Args:
            memmap (bool): If True, use memory mapping instead of loading
                the entire file into RAM. Useful for large files.
        
        Returns:
            numpy.ndarray: Array of frames (also stored in self.frames).
        """
        self.frames = load_widefield(
            self.subject, self.date, self.session, 
            suffix=self.suffix, memmap=memmap
        )
        return self.frames
    
    def load_timestamps(self):
        """
        Load timestamps for sound events and imaging frames.
        
        Returns:
            tuple: (sound_onset, sound_offset, ts_frames) arrays.
        """
        self.sound_onset, self.sound_offset, self.ts_frames = load_timestamps(
            self.timestamps_filename
        )
        return self.sound_onset, self.sound_offset, self.ts_frames
    
    def load_behavior(self):
        """
        Load behavioral data for this session.
        
        Returns:
            BehaviorData: Behavioral data object (also stored in self.bdata).
        """
        self.bdata = load_stimulus(
            self.subject, self.date, self.session, paradigm=self.paradigm
        )
        return self.bdata
    
    def load_all(self, memmap=False):
        """
        Load all data (frames, timestamps, and behavior) for this session.
        
        Args:
            memmap (bool): If True, use memory mapping for frames.
        """
        self.load_frames(memmap=memmap)
        self.load_timestamps()
        self.load_behavior()
    
    @property
    def n_frames(self):
        """Return the number of frames, or None if frames not loaded."""
        if self.frames is not None:
            return self.frames.shape[0]
        return None
    
    @property
    def frame_shape(self):
        """Return the shape of a single frame (height, width), or None if not loaded."""
        if self.frames is not None:
            return self.frames.shape[1:]
        return None
    
    def __repr__(self):
        frames_info = f"{self.n_frames} frames" if self.frames is not None else "frames not loaded"
        return (
            f"Widefield('{self.subject}', '{self.date}', '{self.session}', "
            f"suffix='{self.suffix}') [{frames_info}]"
        )


if __name__ == '__main__':
    subject = 'wifi008'
    date = '20241219'
    session = '161007'
    suffix = 'LG'

    # Using the class
    wfobj = Widefield(subject, date, session, suffix=suffix)
    wfobj.load_timestamps()
    wfobj.load_frames(memmap=True)
    wfobj.load_behavior()
    print(wfobj)