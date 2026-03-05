"""
Load widefield imaging data.
"""

import os
import numpy as np
from jaratoolbox import loadbehavior
from jaratoolbox import settings
import tifffile

# Default resolution in mm/pixel
DEFAULT_RESOLUTION = 0.0156

# Orientation mapping for different camera rotations
# Maps camera rotation (in degrees CCW) to (top, bottom, left, right) anatomical directions
ORIENTATION_MAP = {
      0: ('posterior', 'anterior', 'ventral', 'dorsal'),  # No camera rotation
     90: ('dorsal', 'ventral', 'posterior', 'anterior'),  # Camera 90° CCW
    180: ('anterior', 'posterior', 'dorsal', 'ventral'),  # Camera 180°
    270: ('ventral', 'dorsal', 'anterior', 'posterior'),  # Camera 270° CCW
}

def compute_orientation(camera_rotation, hemisphere):
    """
    Compute image orientation (anatomical directions) based on camera rotation and hemisphere.
    
    Args:
        camera_rotation (int or float): Physical rotation of the camera in degrees CCW.
            Will be rounded to the nearest multiple of 90°.
        hemisphere (str): Which side of the brain is being imaged ('right' or 'left').
    
    Returns:
        dict: Dictionary with keys 'top', 'bottom', 'left', 'right', 'hemisphere' and their
              corresponding anatomical direction values.
    """
    key = round(camera_rotation / 90) % 4 * 90
    top, bottom, left, right = ORIENTATION_MAP.get(key, ORIENTATION_MAP[90])
    
    # Swap anterior-posterior for left hemisphere
    if hemisphere == 'left':
        left, right = right, left
    
    return {
        'top': top,
        'bottom': bottom,
        'left': left,
        'right': right,
        'hemisphere': hemisphere
    }

def load_timestamps(timestamps_filename):
    ts_data = np.load(timestamps_filename)
    sound_onset = ts_data['ts_sound_rising']
    sound_offset = ts_data['ts_sound_falling']
    timestamps = ts_data['ts_trigger_rising']
    return sound_onset, sound_offset, timestamps
    
def load_widefield(subject, date, session, suffix='', memmap=False):
    """
    Load widefield imaging data from TIFF file(s).
    
    Args:
        subject (str): Subject identifier.
        date (str): Date string (e.g., '20241219').
        session (str): Session identifier. Usually a time string (e.g., '161007').
        suffix (str): Optional suffix for the filename.
        memmap (bool): If True, attempt to return a memory-mapped array instead 
            of loading the entire file into RAM. Useful for large files. Note 
            that memory mapping only works if TIFF files are uncompressed and 
            stored contiguously. If memory mapping fails, falls back to loading 
            into RAM. For single file: returns memory-mapped array. For multiple 
            files: returns list of memory-mapped arrays (one per file).
    
    Returns:
        numpy.ndarray or list: Array of frames (or memory-mapped array/list if memmap=True).
            If memmap=True and multiple files exist, returns a list of memory-mapped arrays.
            If memmap fails (e.g., compressed TIFF), returns regular numpy array(s) loaded into RAM.
    """
    frames_filename = os.path.join(settings.WIDEFIELD_PATH, subject, date, f'{subject}_{date}_{session}_{suffix}.tif')

    #print(f"Loading data from {frames_filename}...")

    # -- Create list of TIFF files --
    frames_filenames = [frames_filename]
    # Check for additional TIFF files with pattern @0001, @0002, etc.
    indf = 1
    while True:
        new_filename = frames_filename.replace('.tif', f'@{indf:04d}.tif')
        if os.path.exists(new_filename):
            frames_filenames.append(new_filename)
            indf += 1
        else:
            break

    n_files = len(frames_filenames)
    print(f"Found {n_files} TIFF file(s) to load.")

    # -- Handle memory mapping --
    if memmap:
        try:
            if n_files == 1:
                # Single file: use tifffile's memory mapping
                print(f"Using memory mapping for single TIFF file: {frames_filenames[0]}")
                frames = tifffile.memmap(frames_filenames[0])
            else:
                # Multiple files: return list of memory-mapped arrays
                print(f"Multiple TIFF files detected. Returning list of {n_files} memory-mapped arrays.")
                frames = [tifffile.memmap(filename) for filename in frames_filenames]
            return frames
        except ValueError as e:
            if 'not memory-mappable' in str(e):
                print(f"Warning: TIFF file(s) are not memory-mappable (likely compressed).")
                print(f"Falling back to loading into RAM...")
                # Fall through to regular loading below
            else:
                raise
    
    # -- Load TIFF files into memory --
    if n_files == 1:
        # Single file: load directly
        print(f"Loading TIFF file: {frames_filenames[0]}")
        with tifffile.TiffFile(frames_filenames[0]) as tif:
            frames = tif.asarray()
    else:
        # Multiple files: pre-allocate array and fill in place for efficiency
        # First, get the shape and total number of frames
        frame_counts = []
        frame_shape = None
        dtype = None
        
        for filename in frames_filenames:
            with tifffile.TiffFile(filename) as tif:
                if frame_shape is None:
                    # Get shape from first file
                    frame_shape = tif.series[0].shape
                    dtype = tif.series[0].dtype
                frame_counts.append(tif.series[0].shape[0])
        
        total_frames = sum(frame_counts)
        full_shape = (total_frames,) + frame_shape[1:]
        
        print(f"Pre-allocating array for {total_frames} frames with shape {full_shape}...")
        frames = np.empty(full_shape, dtype=dtype)
        
        # Load each file and copy directly into the pre-allocated array
        current_frame = 0
        for indf, filename in enumerate(frames_filenames):
            n_frames_in_file = frame_counts[indf]
            print(f"Loading TIFF file {indf+1}/{n_files}: {filename} ({n_frames_in_file} frames)")
            with tifffile.TiffFile(filename) as tif:
                frames[current_frame:current_frame + n_frames_in_file] = tif.asarray()
            current_frame += n_frames_in_file
    
    return frames

def load_stimulus(subject, date, session, paradigm='tuning_curve'):
    stimulus_filename = loadbehavior.path_to_behavior_data(subject, paradigm, f'{date}_{session}')
    bdata = loadbehavior.BehaviorData(stimulus_filename)
    return bdata


class WidefieldData:
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
        timestamps (numpy.ndarray): Timestamps for each imaging frame.
        bdata (BehaviorData): Behavioral data object.
    
    Example:
        >>> wfdata = WidefieldData('wifi008', '20241219', '161007', suffix='LG')
        >>> wfdata.load_frames()
        >>> wfdata.load_timestamps()
        >>> wfdata.load_behavior()
        >>> print(wfdata.frames.shape)
    """
    
    def __init__(self, subject, date, session, suffix='', paradigm='am_tuning_curve',
                 camera_rotation=90, hemisphere='right', resolution=None):
        """
        Initialize a WidefieldData object.
        
        Args:
            subject (str): Subject identifier.
            date (str): Date string (e.g., '20241219').
            session (str): Session identifier. Usually a time string (e.g., '161007').
            suffix (str): Suffix for the TIFF filename (e.g., 'LG' for left-green).
            paradigm (str): Behavioral paradigm name (default: 'am_tuning_curve').
            camera_rotation (int or float): Physical rotation of the camera in degrees CCW.
                Default is 90 (camera rotated 90° CCW). Use 0 if camera is not rotated.
            hemisphere (str): Which side of the brain is being imaged. 
                'right' (default) or 'left'. This affects the anterior-posterior
                orientation in the final image.
            resolution (float): Image resolution in mm/pixel. If None, uses
                DEFAULT_RESOLUTION (0.0156 mm/pixel).
        """
        self.subject = subject
        self.date = date
        self.session = session
        self.suffix = suffix
        self.paradigm = paradigm
        self.camera_rotation = camera_rotation
        self.hemisphere = hemisphere
        self.resolution = resolution if resolution is not None else DEFAULT_RESOLUTION
        
        # Calculate the rotation needed to correct for camera orientation
        # We rotate by the same amount as the camera to undo its effect
        self.rotate = round(camera_rotation / 90) % 4
        
        # Data attributes (loaded on demand)
        self.frames = None
        self.sound_onset = None
        self.sound_offset = None
        self.timestamps = None
        self.bdata = None
        
        # Compute image orientation (anatomical directions)
        self.orientation = compute_orientation(camera_rotation, hemisphere)
        
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
            memmap (bool): If True, attempt to use memory mapping instead of 
                loading the entire file into RAM. Useful for large files. 
                Memory mapping only works for uncompressed TIFF files; if it 
                fails, automatically falls back to loading into RAM. For multiple
                TIFF files, returns a list of memory-mapped arrays.
        
        Returns:
            numpy.ndarray or list: Array of frames (also stored in self.frames).
                If memmap=True and multiple files exist, may return a list.
        """
        self.frames = load_widefield(
            self.subject, self.date, self.session, 
            suffix=self.suffix, memmap=memmap
        )
        # Apply rotation to correct for camera orientation
        if self.rotate != 0:
            if isinstance(self.frames, list):
                # Rotate each memory-mapped array in the list
                self.frames = [np.rot90(arr, k=self.rotate, axes=(1, 2)) for arr in self.frames]
            else:
                # Rotate single array
                self.frames = np.rot90(self.frames, k=self.rotate, axes=(1, 2))
        return self.frames
    
    def load_timestamps(self):
        """
        Load timestamps for sound events and imaging frames.
        
        Returns:
            tuple: (sound_onset, sound_offset, timestamps) arrays.
        """
        self.sound_onset, self.sound_offset, self.timestamps = load_timestamps(
            self.timestamps_filename
        )
        return self.sound_onset, self.sound_offset, self.timestamps
    
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
            if isinstance(self.frames, list):
                # Sum frames from all memory-mapped arrays
                return sum(arr.shape[0] for arr in self.frames)
            else:
                return self.frames.shape[0]
        return None
    
    @property
    def frame_shape(self):
        """Return the shape of a single frame (height, width), or None if not loaded."""
        if self.frames is not None:
            if isinstance(self.frames, list):
                # Return shape from first array (all should be same)
                return self.frames[0].shape[1:]
            else:
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
    wfobj = WidefieldData(subject, date, session, suffix=suffix)
    wfobj.load_timestamps()
    wfobj.load_frames(memmap=True)
    wfobj.load_behavior()
    print(wfobj)