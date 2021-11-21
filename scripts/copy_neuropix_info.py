"""
This script copies the events data and OpenEphys info files to the
processed data folder for each session on a given date.

Example usage:
python copy_neuropix_info.py test000 2020-01-31
"""

import os
import sys
import glob
from jaratoolbox import settings
from jaratoolbox import loadneuropix


scriptName = os.path.basename(__file__)

if len(sys.argv)<3:
    print('This command requires a subject and date as arguments.\n'+
          f'Example: {scriptName} test000 2020-01-31')
    sys.exit()

subject = sys.argv[1]
dateStr = sys.argv[2]

pathRoot = os.path.abspath(os.path.join(settings.EPHYS_NEUROPIX_PATH, subject, dateStr))
pathPattern = pathRoot+'_??-??-??'
dirsToProcess = glob.glob(pathPattern)

if not dirsToProcess:
    print(f'No data folders for {subject} on {dateStr} were found.')
    sys.exit()
    
for oneDir in dirsToProcess:
    print(f'\n--- Processing {oneDir} ---')
    loadneuropix.copy_events_and_info(oneDir)

