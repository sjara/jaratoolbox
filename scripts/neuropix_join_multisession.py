"""
Prepare neuropixels data for multisession spike-sorting.

Example usage:
python neuropix_join_multisession.py test000 2020-01-31 3440
                                     SUBJECT   DATE    pDEPTH
"""

import os
import sys
from jaratoolbox import loadneuropix
from jaratoolbox import settings
import importlib
importlib.reload(loadneuropix)

scriptName = os.path.basename(__file__)

if len(sys.argv)<4:
    print('This command requires a subject, date and probe depth as arguments.\n'+
          f'Example: {scriptName} test000 2020-01-31 3440')
    sys.exit()

subject = sys.argv[1]
dateStr = sys.argv[2]
pdepth = int(sys.argv[3])

sessionsRootPath = os.path.join(settings.EPHYS_NEUROPIX_PATH, subject)
multisessionRawDir = os.path.join(sessionsRootPath, f'multisession_{dateStr}_{pdepth}um_raw')
multisessionProcessedDir = os.path.join(sessionsRootPath, f'multisession_{dateStr}_{pdepth}um_processed')
multisessionTempDir = os.path.join(sessionsRootPath, f'multisession_{dateStr}_{pdepth}um_tmp')

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
                siteToProcess = site
if siteToProcess is None:
    print(f'Recording for {subject} on {dateStr} at {pdepth}um not found.')
    sys.exit()
sessions = site.session_ephys_dirs()

# -- Create multisession_folders --
if not os.path.isdir(multisessionRawDir):
    os.mkdir(multisessionRawDir)
    print(f'Created {multisessionRawDir}')
if not os.path.isdir(multisessionTempDir):
    os.mkdir(multisessionTempDir)
    print(f'Created {multisessionTempDir}')
if not os.path.isdir(multisessionProcessedDir):
    os.mkdir(multisessionProcessedDir)
    print(f'Created {multisessionProcessedDir}')

sinfo = loadneuropix.concatenate_sessions(sessionsRootPath, sessions, multisessionRawDir, debug=False)

# -- Save a copy of multisession_info.csv to processed folder --
multisessionInfoFilepath = os.path.join(multisessionProcessedDir,'multisession_info.csv')
sinfo.to_csv(multisessionInfoFilepath)
print(f'Saved {multisessionInfoFilepath}')

