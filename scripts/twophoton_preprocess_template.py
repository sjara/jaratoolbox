"""
Template: concatenate two-photon sessions and run Suite2p using standard paths.

Paths (data location, fast-disk binary location, and output location) are
all derived automatically by suite2ptools.process_sessions() from
jaratoolbox.settings (TWOPHOTON_PATH, SUITE2P_FAST_DIR). Just specify which
sessions to process, which steps to run, and any extra Suite2p settings.

https://suite2p.readthedocs.io/en/latest/parameters/
"""

from jaratoolbox import suite2ptools

subject = 'imag029'
session_date = '20260424'
session_ids = ['006', '007']

anat_channel = None  # PMT channel index (0-based) of the anatomical channel, or None to skip it

extra_settings = suite2ptools.default_2p_settings()
# extra_settings['diameter'] = [16.0, 16.0]
# extra_settings['detection']['nbins'] = 1000  # If not enough RAM

# -- Anatomical channel (chan2) detection --
# extra_settings['detection']['cellpose_chan2'] = True  # Requires anat_channel above and Cellpose installed
# extra_settings['detection']['chan2_threshold'] = 0.25  # IOU threshold for Cellpose overlap red-cell classification
# extra_settings['registration']['align_by_chan2'] = True  # Align by anatomical channel instead of functional

# Steps to run: any of 'concatenate', 'register', 'detect', 'deconvolve', 'split', or 'all'
# (shorthand for concatenate+register+detect+deconvolve; 'split' is never
# implied by 'all', opt in explicitly once you are ready to split results).
steps = ['concatenate', 'register', 'detect', 'deconvolve']
# steps = ['split']  # Run this after you have curated the results of Suite2p

result = suite2ptools.process_sessions(subject, session_date, session_ids, steps,
                                        anat_channel=anat_channel, settings_2p=extra_settings)
print(result)
