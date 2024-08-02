"""
Copy settings.xml from raw data folder to multisession folders.

Example usage:
python neuropix_copy_settings.py test000 2020-01-31 3440
                                 SUBJECT   DATE    pDEPTH

"""

import os
import sys
from jaratoolbox import loadneuropix
from jaratoolbox import settings
import importlib
import shutil

scriptName = os.path.basename(__file__)

if len(sys.argv)<4:
    print('This command requires a subject, date and probe depth as arguments.\n'+
          f'Example: {scriptName} test000 2020-01-31 3440')
    sys.exit()

subject = sys.argv[1]
dateStr = sys.argv[2]
pdepth = int(sys.argv[3])
debug = True if (len(sys.argv)==5 and sys.argv[4]=='debug') else False

sessionsRootPath = os.path.join(settings.EPHYS_NEUROPIX_PATH, subject)
multisessionRawDir = os.path.join(sessionsRootPath, f'multisession_{dateStr}_{pdepth}um_raw')
multisessionProcessedDir = os.path.join(sessionsRootPath, f'multisession_{dateStr}_{pdepth}um_processed')
relativePathToNode = 'Record Node 101/'

# -- Load inforec file --
inforecFile = os.path.join(settings.INFOREC_PATH, f'{subject}_inforec.py')
spec = importlib.util.spec_from_file_location('inforec_module', inforecFile)
inforec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inforec)

# -- Find sessions to concatenate --
siteToProcess = None
for experiment in inforec.experiments:
    if experiment.date==dateStr:
        for site in experiment.sites:
            if site.pdepth==pdepth:
                probeStr = experiment.probe
                siteToProcess = site
if siteToProcess is None:
    print(f'Recording for {subject} on {dateStr} at {pdepth}um not found.')
    sys.exit()
sessions = siteToProcess.session_ephys_dirs()

# -- Copy settings.xml --
for oneSession in sessions:
    processedSessionSubDir = os.path.join(multisessionProcessedDir, oneSession)
    settingsFile = os.path.join(sessionsRootPath, oneSession, relativePathToNode, 'settings.xml')
    infoDir = os.path.join(processedSessionSubDir, 'info')
    shutil.copy2(settingsFile, infoDir)
    print(f'Copied {settingsFile} to {infoDir+os.sep}')
    

