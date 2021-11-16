'''
Main objects for working with electrophysiology data
'''

import os
import numpy as np
import pandas as pd
from jaratoolbox import loadopenephys
from jaratoolbox import loadneuropix
from jaratoolbox import loadbehavior
from jaratoolbox import settings

# Define the event channel mapping for each paradigm. For each paradigm, you
# should include a dict like this: {eventName:intanEventChannel}
# where intanEventChannel is the digital input channel that your event TTL is connected to
CHANNELMAPS = {'threetones_sequence': {'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'oddball_sequence': {'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'am_tuning_curve': {'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'bandwidth_am':{'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'twochoice':{'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'laser_tuning_curve':{'stim':0, 'trialStart':1, 'laser':2},
               '2afc':{'stim':0, 'trialStart':1},
               '2afc_speech':{'stim':0, 'trialStart':1} }

class Cell():
    def __init__(self, dbRow, useModifiedClusters=False):
        '''
        Args:
            dbRow (pandas.core.series.Series): A row from a dataframe created by celldatabase.
            useModifiedClusters (bool): Whether to load the modified cluster files created after
                                        cleaning clusters, if they exist.
        '''
        # FIXME: When looping through cells, make sure that nothing is
        #        preserved from iteration to the next
        if not isinstance(dbRow, pd.core.series.Series):
            raise TypeError('This object must be initialized with a pandas Series object.')
        self.dbRow = dbRow
        self.useModifiedClusters = useModifiedClusters

        self.subject = dbRow['subject']
        self.date = dbRow['date']
        if 'pdepth' in dbRow:
            self.pdepth = dbRow['pdepth']
        else:
            self.pdepth = dbRow['depth']  # Legacy option for celldatabase v3.0
        if 'egroup' in dbRow:
            self.egroup = dbRow['egroup']
        else:
            self.egrouptetrode = dbRow['tetrode']  # Legacy option for celldatabase v3.0
        self.cluster = dbRow['cluster']
        self.ephysBaseDir = os.path.join(settings.EPHYS_PATH, self.subject)

    def __str__(self):
        objStr = '{} {} ({:0.0f}um) g{}c{}'.format(self.subject, self.date, self.pdepth,
                                                   self.egroup, self.cluster)
        return objStr
        
    def load(self, sessiontype, behavClass=None):
        '''
        Load the spikes, events, and behavior data for a single session. Loads the LAST recorded
        session of the type that was recorded from the cell.
        Args:
            sessiontype (str): the type of session to load data for.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class
                                                         of behavData will have different methods.
        Returns:
            ephysData (dict):'spikeTimes' (array), 'samples' (array) and 'events' (dict)
                              The dictionary 'events' contains two keys for each type of event
                              used in the paradigm - one for the eventOn, when the event turns on,
                              and one for the eventOff, when the event turns off. These will look like
                              'stimOn' and 'stimOff' for the event type 'stim' defined in the paradigm.
            behavData (jaratoolbox.loadbehavior.BehaviorData): Behavior data dict
        '''
        sessionInds = self.get_session_inds(sessiontype)
        try:
            sessionIndToUse = sessionInds[-1]  # NOTE: Taking the last session of this type!
        except IndexError as ierror:
            ierror.args += ('Session type "{}" does not exist for this cell.'.format(sessiontype),)
            raise
        ephysData, behavData = self.load_by_index(sessionIndToUse, behavClass=behavClass)
        return ephysData, behavData

    def get_session_inds(self, sessiontype):
        '''
        Get the indices of sessions of a particular sessiontype that were recorded for the cell.
        Args:
            sessiontype (str): The type of session to look for (as written in the inforec file)
        Returns:
            sessionInds (list): List of the indices for this session type
        '''
        sessionInds = [i for i, st in enumerate(self.dbRow['sessionType']) if st==sessiontype]
        return sessionInds

    def load_by_index(self, sessionInd, behavClass=None):
        '''
        Load both ephys and behavior data for a session using the absolute index in the list
        of sessions for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of
                                                         behavData will have different methods.
        Returns:
            ephysData (list): Spiketimes (array), samples (array) and events (dict)
            behavData (jaratoolbox.loadbehavior.BehaviorData): Behavior data dict
        '''
        ephysData = self.load_ephys_by_index(sessionInd)
        behavData = self.load_behavior_by_index(sessionInd, behavClass=behavClass)
        return ephysData, behavData

    def load_ephys_by_index(self, sessionInd):
        '''
        Load the ephys data for a session using the absolute index in the list of sessions for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
        Returns:
            ephysData (list): Spiketimes (array), samples (array) and events (dict)
        '''
        sessionDir = self.get_ephys_dir(sessionInd)
        paradigm = self.dbRow['paradigm'][sessionInd]
        if self.dbRow['probe'] == 'A4x2-tet':
            ephysData = load_ephys_neuronexus_tetrodes(self.subject, paradigm, sessionDir,
                                                       self.egroup, self.cluster,
                                                       useModifiedClusters=self.useModifiedClusters)
        elif self.dbRow['probe'][:4] == 'NPv1':
            ephysData = load_ephys_neuropixels_v1(self.subject, paradigm, sessionDir,
                                                  self.egroup, self.cluster)
        return ephysData

    def get_ephys_dir(self, sessionInd):
        '''
        Return the full path to the ephys data for a given session.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
        Returns:
            sessionDir (str): Full path to the ephys data
        '''
        ephysTime = self.dbRow['ephysTime'][sessionInd]
        sessionDir = '{}_{}'.format(self.date, ephysTime)
        return sessionDir

    def load_behavior_by_index(self, sessionInd, behavClass=None):
        '''
        Load the behavior data for a session using the absolute index in the list of sessions
        for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of
                                                         behavData will have different methods.
        Returns:
            behavData (jaratoolbox.loadbehavior.BehaviorData): Behavior data dict

        To implement in the future:
        * Allow use of different readmode for loading partial data
        * Allow use of different loading class for paradigms like FlexCategBehaviorData
        '''
        #Set the loading class for behavior data
        if behavClass==None:
            behavClass = loadbehavior.BehaviorData

        #Load the behavior data
        if self.dbRow['behavSuffix'][sessionInd] is not None:
            dateStr = ''.join(self.date.split('-'))
            fullSessionStr = '{}{}'.format(dateStr, self.dbRow['behavSuffix'][sessionInd])
            behavDataFilePath = loadbehavior.path_to_behavior_data(self.subject,
                                                                   self.dbRow['paradigm'][sessionInd],
                                                                   fullSessionStr)
            bdata = behavClass(behavDataFilePath,readmode='full')
        else:
            bdata = None
        return bdata

    def load_all_spikedata(self):
        '''
        Load the spike data for all recorded sessions into a set of arrays.
        Returns:
            timestamps (np.array): The timestamps for all spikes across all sessions
            samples (np.array): The samples for all spikes across all sessions
            recordingNumber (np.array): The index of the session where the spike was recorded
        '''
        samples=np.array([])
        timestamps=np.array([])
        recordingNumber=np.array([])
        for sessionInd, sessionType in enumerate(self.dbRow['sessionType']):
            try:
                ephysData = self.load_ephys_by_index(sessionInd)
            except ValueError as vError:
                errMsg = 'File probably contains no spikes'
                print('{} -- {}'.format(vError, errMsg))
                continue
            numSpikes = len(ephysData['spikeTimes'])
            sessionVector = np.zeros(numSpikes)+sessionInd
            if len(samples)==0:
                samples = ephysData['samples']
                timestamps = ephysData['spikeTimes']
                recordingNumber = sessionVector
            else:
                samples = np.concatenate([samples, ephysData['samples']])
                # Check to see if next session ts[0] is lower than self.timestamps[-1]
                # If so, add self.timestamps[-1] to all new timestamps before concat
                if not len(ephysData['spikeTimes'])==0:
                    if ephysData['spikeTimes'][0]<timestamps[-1]:
                        ephysData['spikeTimes'] = ephysData['spikeTimes'] + timestamps[-1]
                    timestamps = np.concatenate([timestamps, ephysData['spikeTimes']])
                    recordingNumber = np.concatenate([recordingNumber, sessionVector])
        recordingNumber = recordingNumber.astype(int)
        return timestamps, samples, recordingNumber


def load_ephys_neuronexus_tetrodes(subject, paradigm, sessionDir, tetrode, cluster=None,
                                   useModifiedClusters=False):
    # -- Setup path and filenames --
    ephysBaseDir = os.path.join(settings.EPHYS_PATH, subject)
    eventsFilename = os.path.join(ephysBaseDir, sessionDir,
                                    'all_channels.events')
    spikesFilename = os.path.join(ephysBaseDir, sessionDir,
                                    'Tetrode{}.spikes'.format(tetrode))
    # -- Load the spikes and events --
    eventData = loadopenephys.Events(eventsFilename)
    spikeData = loadopenephys.DataSpikes(spikesFilename)

    # -- Fail if there are no spikes for the tetrode --
    if spikeData.timestamps is None:
        raise ValueError('File {} contains no spikes.'.format(spikesFilename))

    #Set clusters and limits spikes and samples to one cluster
    if cluster is not None:
        clustersDir = os.path.join(ephysBaseDir, '{}_kk'.format(sessionDir))
        # Get clusters file name, load and set the clusters
        if useModifiedClusters is False:
            # Always use the original .clu.1 file
            clustersFile = os.path.join(clustersDir,'Tetrode{}.clu.1'.format(tetrode))
            spikeData.set_clusters(clustersFile)
        elif useModifiedClusters is True:
            # Use the modified .clu file if it exists, otherwise use the original one
            clustersFileModified = os.path.join(clustersDir,'Tetrode{}.clu.modified'.format(tetrode))
            if os.path.exists(clustersFileModified):
                print("Loading modified .clu file for session {}".format(spikesFilename))
                spikeData.set_clusters(clustersFileModified)
            else:
                print(f'Modified .clu file does not exist, loading standard .clu file ' +
                      'for session {spikesFilename}')
                clustersFile = os.path.join(clustersDir,'Tetrode{}.clu.1'.format(tetrode))
                spikeData.set_clusters(clustersFile)
        spikeData.samples = spikeData.samples[spikeData.clusters==cluster]
        spikeData.timestamps = spikeData.timestamps[spikeData.clusters==cluster]

    # -- Convert to standard units --
    spikeData = loadopenephys.convert_openephys(spikeData)
    eventData = loadopenephys.convert_openephys(eventData)

    # -- Choose channel map based on paradigm --
    channelMap = CHANNELMAPS[paradigm]
    eventDict = {}
    for channelType, channelID in channelMap.items():
        thisChannelOn = eventData.get_event_onset_times(eventID=1, eventChannel=channelID)
        thisChannelOff = eventData.get_event_onset_times(eventID=0, eventChannel=channelID)
        eventDict.update({'{}On'.format(channelType):thisChannelOn,
                            '{}Off'.format(channelType):thisChannelOff})
    ephysData = {'spikeTimes':spikeData.timestamps,
                    'samples':spikeData.samples,
                    'events':eventDict}
    return ephysData


def load_ephys_neuropixels_v1(subject, paradigm, sessionDir, egroup, cluster=None):
    ephysBaseDir = os.path.join(settings.EPHYS_NEUROPIX_PATH, subject)
    eventsDir = os.path.join(ephysBaseDir, sessionDir)
    spikesDir = os.path.join(ephysBaseDir, sessionDir+'_processed') # This may fail if ends in /

    # -- Load spikes and events --
    spikesData = loadneuropix.Spikes(spikesDir, convert=True)
    eventsData = loadneuropix.Events(eventsDir, convert=True)
    eventOnsetTimes = eventsData.get_onset_times()

    # -- Find events on each channel of the channel map for this paradigm --
    channelMap = CHANNELMAPS[paradigm]
    eventDict = {}
    for channelType, channelID in channelMap.items():
        channelID = channelID+1   # FIXME: it looks like neuropix system uses Channel 1 not 0
        thisChannelOn = eventsData.get_onset_times(channelID, channelState=1)
        thisChannelOff = eventsData.get_onset_times(channelID, channelState=-1)
        eventDict.update({'{}On'.format(channelType):thisChannelOn,
                          '{}Off'.format(channelType):thisChannelOff})
    ephysData = {'spikeTimes': spikesData.get_timestamps(cluster),
                 'events': eventDict}
    return ephysData
 
