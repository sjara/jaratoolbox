"""
Spike-sort Neuropixels data using Kilosort 4.
"""

import os
import sys
import importlib
import numpy as np
from jaratoolbox import settings
from jaratoolbox import celldatabase
from jaratoolbox import loadneuropix


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
rawFilename = os.path.join(multisessionRawDir , 'multisession_continuous.dat')

# -- Load inforec file --
inforec = celldatabase.Inforec(subject)
sessions = inforec.find_site_ephys_dirs(dateStr, pdepth)  # Folder of each ephys session

# -- Get probe map --
xmlpath = os.path.join(multisessionProcessedDir , sessions[0] , 'info' , 'settings.xml')
pmap = loadneuropix.ProbeMap(xmlpath)

probe = {'chanMap': pmap.channelID,
         'xc': pmap.xpos,
         'yc': pmap.ypos,
         'kcoords': np.zeros(pmap.nActiveChannels)}

# -- Run kilosort --
settings = {'n_chan_bin': pmap.nActiveChannels}

if not debug:
    ops, st, clu, tF, Wall, similar_templates, is_ref, est_contam_rate, kept_spikes = \
        run_kilosort(settings=settings,
                     filename=rawFilename,
                     probe_name=pmap.probeName,
                     probe=probe,
                     results_dir=multisessionProcessedDir)
else:
    print('This script will run Kilosort with the following parameters:')
    print(f'Number of channels: {pmap.nActiveChannels}')
    print(f'Probe name: {pmap.probeName}')
    print(f'Raw data file: {rawFilename}')
    print(f'Results directory: {multisessionProcessedDir}')
print('Since you are running in debug mode, no files were created or modified.')

