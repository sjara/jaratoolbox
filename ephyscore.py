'''
Main objects for working with electrophysiology data
'''

import os
import numpy as np
import pandas as pd
from jaratoolbox import loadopenephys
from jaratoolbox import loadbehavior
from jaratoolbox import settings

# Define the event channel mapping for each paradigm. For each paradigm, you
# should include a dict like this: {eventName:intanEventChannel}
# where intanEventChannel is the digital input channel that your event TTL is connected to
CHANNELMAPS = {'am_tuning_curve': {'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'bandwidth_am':{'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5},
               'laser_tuning_curve':{'stim':0, 'trialStart':1, 'laser':2},
               '2afc':{'stim':0, 'trialStart':1}}

class Cell(object):
    def __init__(self, dbRow):
        '''
        Things to check at the end:
        * When looping through cells, make sure that nothing is preserved from iteration to the next
        Args:
            dbRow (pandas.core.series.Series): A row from a dataframe. Must contain at least:
            * sessionType
        '''
        if not isinstance(dbRow, pd.core.series.Series):
            raise TypeError('This object must be initialized with a pandas Series object.')
        self.dbRow = dbRow

        # We use these variables many times to load data
        # Date and depth are not really used to load the data
        self.subject = dbRow['subject']
        self.tetrode = dbRow['tetrode']
        self.cluster = dbRow['cluster']
        self.ephysBaseDir = os.path.join(settings.EPHYS_PATH, self.subject)

    def load(self, sessiontype, behavClass=None):
        '''
        Load the spikes, events, and behavior data for a single session. Loads the LAST recorded
        session of the type that was recorded from the cell.
        Args:
            sessiontype (str): the type of session to load data for.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of behavData will have different methods.
        Returns:
            ephysData (list): Spiketimes (array), samples (array) and events (dict)
            behavData (jaratoolbox.loadbehavior.BehaviorData): Behavior data dict
        '''
        sessionInds = self.get_session_inds(sessiontype)
        sessionIndToUse = sessionInds[-1] #NOTE: Taking the last session of this type!
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
        Load both ephys and behavior data for a session using the absolute index in the list of sessions for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of behavData will have different methods.
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
        #Load the spikes and events
        spikesFilename, eventsFilename = self.get_ephys_filename(sessionInd)
        eventData = loadopenephys.Events(eventsFilename)
        spikeData = loadopenephys.DataSpikes(spikesFilename)
        if spikeData.timestamps is not None:
            clustersDir = os.path.join(self.ephysBaseDir, '{}_{}_kk'.format(self.dbRow['date'],
                                                                            self.dbRow['ephysTime'][sessionInd]))
            clustersFile = os.path.join(clustersDir,'Tetrode{}.clu.1'.format(self.tetrode))
            spikeData.set_clusters(clustersFile)
            spikeData.samples = spikeData.samples[spikeData.clusters==self.cluster]
            spikeData.timestamps = spikeData.timestamps[spikeData.clusters==self.cluster]
            spikeData = loadopenephys.convert_openephys(spikeData)
        else:
            raise ValueError('File {} contains no spikes.'.format(spikesFilename))
        eventData = loadopenephys.convert_openephys(eventData)
        #Choose channel map based on paradigm
        paradigm = self.dbRow['paradigm'][sessionInd]
        channelMap = CHANNELMAPS[paradigm]
        eventDict = {}
        for channelType, channelID in channelMap.iteritems():
            thisChannelOn = eventData.get_event_onset_times(eventID=1, eventChannel=channelID)
            thisChannelOff = eventData.get_event_onset_times(eventID=0, eventChannel=channelID)
            eventDict.update({'{}On'.format(channelType):thisChannelOn,
                              '{}Off'.format(channelType):thisChannelOff})
        ephysData = {'spikeTimes':spikeData.timestamps,
                     'samples':spikeData.samples,
                     'events':eventDict}
        return ephysData

    def get_ephys_filename(self, sessionInd):
        '''
        Return the full path for the .spikes and .events files for a session.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
        Returns:
            spikesFilename (str): Full path to the .spikes file
            eventsFilename (str): Full path to the .events file
        '''
        ephysTime = self.dbRow['ephysTime'][sessionInd]
        ephysSessionFolder = '{}_{}'.format(self.dbRow['date'], ephysTime)
        eventsFilename = os.path.join(self.ephysBaseDir, ephysSessionFolder,
                                     'all_channels.events')
        spikesFilename = os.path.join(self.ephysBaseDir, ephysSessionFolder,
                                      'Tetrode{}.spikes'.format(self.tetrode))
        return spikesFilename, eventsFilename

    def load_behavior_by_index(self, sessionInd, behavClass=None):
        '''
        Load the behavior data for a session using the absolute index in the list of sessions for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of behavData will have different methods.
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
            dateStr = ''.join(self.dbRow['date'].split('-'))
            fullSessionStr = '{}{}'.format(dateStr, self.dbRow['behavSuffix'][sessionInd])
            behavDataFilePath = loadbehavior.path_to_behavior_data(self.subject,
                                                                self.dbRow['paradigm'][sessionInd],
                                                                fullSessionStr)
            bdata = behavClass(behavDataFilePath,readmode='full')
        else:
            bdata = None
        return bdata
