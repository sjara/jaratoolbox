from jaratoolbox import loadopenephys

import os
import numpy as np

'''
Load spikes from all sessions in an experiment database into an object. 
'''


ephys_path = '/home/nick/data/ephys/hm4d002/cno_08-14/'
ephys_sessions=sorted(os.listdir(ephys_path))
tetrode = 3

all_session_samples=[]
all_session_timestamps=[]

for session in ephys_sessions:
    ephys_file = os.path.join(ephys_path, session, 'Tetrode{0}.spikes'.format(tetrode))
    spikes = loadopenephys.DataSpikes(ephys_file)
    all_session_samples.append(spikes.samples)
    all_session_timestamps.append(spikes.timestamps)


