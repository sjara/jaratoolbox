"""
"jaratoolbox" is a set of python modules for the analysis of behavioral and electrophysiological data.

It is developed by the Jaramillo Lab at the Institute of Neuroscience, University of Oregon.
http://jaralab.uoregon.edu/
"""

import os
import sys
import pathlib
import importlib.util

# -- Load jaratoolbox/settings.py file --
_packageDir = os.path.dirname(os.path.abspath(__file__))
_settingsDir = os.path.split(_packageDir)[0] # One directory above
_settingsBasename = 'settings.py'
settingPath = os.path.join(_settingsDir,_settingsBasename)
_spec = importlib.util.spec_from_file_location('jaratoolbox.settings', settingPath)
settings = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(settings)


