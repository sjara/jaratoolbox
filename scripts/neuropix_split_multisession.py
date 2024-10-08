"""
Split results of multisession spike-sorting back to individual sessions.

Example usage:
python neuropix_split_multisession.py test000 2020-01-31 3440
                                      SUBJECT   DATE    pDEPTH

You can also run this for all multisession folders in a subject's folder:
python neuropix_split_multisession.py test000
"""

import os
import sys
import shutil
from jaratoolbox import loadneuropix
from jaratoolbox import settings
import importlib
importlib.reload(loadneuropix)

scriptName = os.path.basename(__file__)

subject = sys.argv[1]
sessionsRootPath = os.path.join(settings.EPHYS_NEUROPIX_PATH, subject)

if len(sys.argv)>3:
    dateList = [sys.argv[2]]
    pdepthList = [int(sys.argv[3])]
    debug = True if (len(sys.argv)==5 and sys.argv[4]=='debug') else False
elif len(sys.argv)==2:
    # List all folders that follow pattern multisession_*_processed
    multiProcessedDirs = [f for f in sorted(os.listdir(sessionsRootPath)) if
                          f.startswith('multisession_') and f.endswith('_processed')]
    dateList = [f.split('_')[1] for f in multiProcessedDirs]
    pdepthList = [int(f.split('_')[2][:-2]) for f in multiProcessedDirs]
    debug = False
else:
    print('This command requires a subject, date and probe depth as arguments.\n'+
          f'Example: {scriptName} test000 2020-01-31 3440')
    sys.exit()

for inds in range(len(dateList)):
    dateStr = dateList[inds]
    pdepth = pdepthList[inds]

    multisessionProcessedDir = os.path.join(sessionsRootPath,
                                            f'multisession_{dateStr}_{pdepth}um_processed')

    if debug:
        print('\nRunning in DEBUG mode. Messages will appear, but nothing will be created/saved.\n')

    # -- Extract and save spike shapes --
    if not debug:
        loadneuropix.spikeshapes_from_templates(multisessionProcessedDir, save=True)
    else:
        print('DEBUG: This would save cluster waveforms (spike shapes).\n')

    # -- Split spike times into sessions --
    sessionsList, sessionsDirs = loadneuropix.split_sessions(multisessionProcessedDir,
                                                             debug=debug)

    # -- Copy Events and Info to each session --
    for inds, oneSessionProcessedDir in enumerate(sessionsDirs):
        subDir = os.path.join(multisessionProcessedDir, sessionsList[inds])
        if not debug:
            shutil.copytree(os.path.join(subDir, 'events'),
                            os.path.join(oneSessionProcessedDir, 'events'), dirs_exist_ok=True)
        print(f'Copied events to {oneSessionProcessedDir}/')
        if not debug:
            shutil.copytree(os.path.join(subDir, 'info'),
                            os.path.join(oneSessionProcessedDir, 'info'), dirs_exist_ok=True)
        print(f'Copied info to {oneSessionProcessedDir}/')
        '''
        sessionFullPath = os.path.join(sessionsRootPath, oneSession)
        processedDir = loadneuropix.copy_events_and_info(sessionFullPath)
        '''
        multiDirFile = os.path.join(oneSessionProcessedDir, 'multisession_dir.txt')
        if not debug:
            with open(multiDirFile, 'w') as dirFile:
                dirFile.write(multisessionProcessedDir)
        print(f'Saved {multiDirFile}\n')
