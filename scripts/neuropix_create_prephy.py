"""
Create '...processed_prephy' folder with files from Kilosort that are changed by Phy.

This is useful if we want to do Phy again on the dataset without having
to run Kilosort again (which would take long).

Example usage:
python neuropix_create_prephy.py test000 2020-01-31 3440
                                 SUBJECT   DATE    pDEPTH

To debug (without saving anything), use:
python neuropix_create_prephy.py test000 2020-01-31 3440 debug
"""

import os
import sys
from jaratoolbox import settings

if len(sys.argv)<4:
    print('This command requires a subject, date and probe depth as arguments.\n'+
          f'Example: {scriptName} test000 2020-01-31 3440')
    sys.exit()

subject = sys.argv[1]
dateStr = sys.argv[2]
pdepth = int(sys.argv[3])
debug = True if (len(sys.argv)==5 and sys.argv[4]=='debug') else False

sessionsRootPath = os.path.join(settings.EPHYS_NEUROPIX_PATH, subject)
multisessionProcessedDir = os.path.join(sessionsRootPath, f'multisession_{dateStr}_{pdepth}um_processed')

filesToCopy = ['cluster_Amplitude.tsv', 'cluster_ContamPct.tsv',
               'cluster_group.tsv', 'cluster_KSLabel.tsv', 'spike_clusters.npy']

prephyDir = f'{multisessionProcessedDir}_prephy'
if not debug:
    try:
        os.makedirs(prephyDir, exist_ok=False)
    except FileExistsError as e:
        print(f'ERROR: {prephyDir}/ already exists.\nDelete it, if you want it replaced.')
        sys.exit()
print(f'Created {prephyDir}/')
    
for oneFile in filesToCopy:
    if not debug:
        os.system(f'rsync -a {multisessionProcessedDir}/{oneFile} {multisessionProcessedDir}_prephy/')
    print(f'Copied {oneFile} to {multisessionProcessedDir}_prephy/')


