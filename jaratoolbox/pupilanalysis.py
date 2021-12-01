"""
Analysis of pupil videos.
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

