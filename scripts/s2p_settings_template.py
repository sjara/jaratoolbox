"""
Template extra-settings file for twophoton_preprocess.py.

Copy this file, uncomment/edit what you need, then pass its path via
--settings. If you don't need any overrides, you can omit --settings
entirely and default_2p_settings() will be used unmodified.

https://suite2p.readthedocs.io/en/latest/parameters/
"""

from jaratoolbox import suite2ptools

settings = suite2ptools.default_2p_settings()
# settings['diameter'] = [16.0, 16.0]
# settings['detection']['nbins'] = 1000  # If not enough RAM

# -- Anatomical channel (chan2) detection --
# settings['detection']['cellpose_chan2'] = True  # Requires Cellpose installed
# settings['detection']['chan2_threshold'] = 0.25  # IOU threshold for Cellpose overlap red-cell classification
# settings['registration']['align_by_chan2'] = True  # Align by anatomical channel instead of functional
