'''
Main objects for working with electrophysiology data
'''

import os
import numpy as np
import pandas as pd
from jaratoolbox import loadopenephys
from jaratoolbox import loadneuropix
from jaratoolbox import loadbehavior
from jaratoolbox import spikesanalysis
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


class SessionData():
    """
    Container of ephys and behavior data for a session.

    These objects can be used when creating a Cell object to make loading more efficient,
    since the files containing spikes, events and behavior are common across cells in a session.

    See also: CellEnsemble()
    """
    def __init__(self, dbRow, sessiontype):
        if not isinstance(dbRow, pd.core.series.Series):
            raise TypeError('This object must be initialized with a pandas Series object.')
        tempCell = Cell(dbRow)
        tempCell.cluster = None
        self.ephysData, self.behavData = tempCell.load(sessiontype)
    def get_ephys(self, cluster=None):
        if cluster is None:
            return self.ephysData
        else:
            spikesThisCluster = self.ephysData['clusterEachSpike']==cluster
            ephysDataOneCluster = {k:v for k,v in self.ephysData.items() if k!='spikeTimes'}
            ephysDataOneCluster['spikeTimes'] = self.ephysData['spikeTimes'][spikesThisCluster]
            return ephysDataOneCluster
    def get_behavior(self):
        return self.behavData


class CellEnsemble():
    def __init__(self, celldb, dirsuffix='_processed_multi'):
        """
        Args:
            celldb (pandas DataFrame): A dataframe created by celldatabase for a single site.
                                       All rows must have the same subject, date and pdepth.
            useModifiedClusters (bool): Whether to load the modified cluster files created after
                                        cleaning clusters, if they exist.
        """
        if not isinstance(celldb, pd.core.frame.DataFrame):
            raise TypeError('This object must be initialized with a pandas DataFrame object.')
        if (len(celldb.subject.unique())>1 or len(celldb.date.unique())>1 or
            len(celldb.pdepth.unique())>1):
            msg = 'The database must contain only neurons from one site (same date and pdepth).'
            raise TypeError(msg)
        if len(celldb.egroup.unique())>1:
            raise TypeError('Currently, this class works only for a single electrode group (probe).')
        self.celldb = celldb
        refRow = celldb.iloc[0]
        self.subject = refRow.subject
        self.date = refRow.date
        self.pdepth = refRow.pdepth
        self.egroup = refRow.egroup
        self.behavData = None
        self.ephysData = None
        self.dirsuffix = dirsuffix
        self.refCell = Cell(refRow) # Reference cell
        self.refCell.cluster = None  # The reference cell helps load data for all cells
        self.spikeTimesFromEventOnsetAll = []
        self.trialIndexForEachSpikeAll = []
        self.indexLimitsEachTrialAll = []
        self.eventOnsetTimes = []
    def __str__(self):
        objStr = f'{self.subject} {self.date} {self.pdepth:0.0f}um g{self.egroup}'
        return objStr
    def load(self, sessiontype, behavClass=None):
        """
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
        """
        sessionInds = self.refCell.get_session_inds(sessiontype)
        try:
            sessionIndToUse = sessionInds[-1]  # NOTE: Taking the last session of this type!
        except IndexError as ierror:
            ierror.args += ('Session type "{}" does not exist for this cell.'.format(sessiontype),)
            raise
        self.behavData = self.refCell.load_behavior_by_index(sessionIndToUse, behavClass=behavClass)
        self.ephysData = self.refCell.load_ephys_by_index(sessionIndToUse)
        return self.ephysData, self.behavData
    def get_spiketimes(self, cluster):
        """
        Get spikes times for a single cluster.
        """
        spikesThisCluster = (self.ephysData['clusterEachSpike']==cluster)
        spikeTimes = self.ephysData['spikeTimes'][spikesThisCluster]
        return spikeTimes
    def eventlocked_spiketimes(self, eventOnsetTimes, timeRange):
        """
        Align spikes from each cell to an event.
        Args:
            eventOnsetTimes: (np.array) the time of each instance of the event to lock to.
            timeRange: (list) two-element list specifying time-range to extract around event.
        Returns:
            spikeTimesFromEventOnsetAll (list): list of spikeTimesFromEventOnset arrays.
            trialIndexForEachSpikeAll (list): list of trialIndexForEachSpike arrays.
            indexLimitsEachTrialAll (list): list of indexLimitsEachTrial arrays.
        See spikesanalysis.eventlocked_spiketimes() for a description of the arrays.
        """
        if self.ephysData is None:
            msg = 'You need to run load() for this object first.'
            raise RuntimeError(msg)
        self.eventOnsetTimes = eventOnsetTimes
        self.spikeTimesFromEventOnsetAll = []
        self.trialIndexForEachSpikeAll = []
        self.indexLimitsEachTrialAll = []
        for cluster in self.celldb.cluster:
            spikeTimes = self.get_spiketimes(cluster)
            (spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial) = \
                spikesanalysis.eventlocked_spiketimes(spikeTimes, eventOnsetTimes, timeRange)
            self.spikeTimesFromEventOnsetAll.append(spikeTimesFromEventOnset)
            self.trialIndexForEachSpikeAll.append(trialIndexForEachSpike)
            self.indexLimitsEachTrialAll.append(indexLimitsEachTrial)
        return (self.spikeTimesFromEventOnsetAll,
                self.trialIndexForEachSpikeAll,
                self.indexLimitsEachTrialAll)
    def sort_trials(self, trialsEachCond):
        """Note implemented yet"""
        pass
    def spiketimes_to_spikecounts(self, binEdges):
        """
        Get spike count for each time bin for each cell.
        Args:
            binEdges (np.arrat): edges of time bins, including left-most and right-most edges.
        Returns:
            spikeCountMat (np.array): spike counts for each bin. Shape is (nCells, nTrials, nBins).
        """
        if len(self.spikeTimesFromEventOnsetAll) == 0:
            msg = 'You need to run eventlocked_spiketimes() for this object first'
            raise RuntimeError(msg)
        nBins = len(binEdges) - 1
        nTrials = len(self.eventOnsetTimes)
        nClusters = len(self.celldb)
        spikeCountMatAll = np.empty((nClusters, nTrials, nBins), dtype=int)
        for indc in range(nClusters):
            cMat = spikesanalysis.spiketimes_to_spikecounts(self.spikeTimesFromEventOnsetAll[indc],
                                                            self.indexLimitsEachTrialAll[indc],
                                                            binEdges)
            spikeCountMatAll[indc,:,:] = cMat
        return spikeCountMatAll


class Cell():
    def __init__(self, dbRow, sessionData=None, dirsuffix='_processed_multi',
                 useModifiedClusters=False):
        """
        Args:
            dbRow (pandas.core.series.Series): A row from a dataframe created by celldatabase.
            sessionData (SessionData): object contaning data for the session (when spikes and
                                       behavior are already loaded).
            useModifiedClusters (bool): Whether to load the modified cluster files created after
                                        cleaning clusters, if they exist.
        """
        # FIXME: When looping through cells, make sure that nothing is
        #        preserved from iteration to the next
        if not isinstance(dbRow, pd.core.series.Series):
            raise TypeError('This object must be initialized with a pandas Series object.')
        self.dbRow = dbRow
        self.sessionData = sessionData
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
        self.dirsuffix = dirsuffix
        
    def __str__(self):
        objStr = '{} {} {:0.0f}um g{}c{}'.format(self.subject, self.date, self.pdepth,
                                                 self.egroup, self.cluster)
        return objStr
        
    def load(self, sessiontype, behavClass=None):
        """
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
        """
        sessionInds = self.get_session_inds(sessiontype)
        try:
            sessionIndToUse = sessionInds[-1]  # NOTE: Taking the last session of this type!
        except IndexError as ierror:
            ierror.args += ('Session type "{}" does not exist for this cell.'.format(sessiontype),)
            raise
        ephysData, behavData = self.load_by_index(sessionIndToUse, behavClass=behavClass)
        return ephysData, behavData

    def get_session_inds(self, sessiontype):
        """
        Get the indices of sessions of a particular sessiontype that were recorded for the cell.
        Args:
            sessiontype (str): The type of session to look for (as written in the inforec file)
        Returns:
            sessionInds (list): List of the indices for this session type
        """
        sessionInds = [i for i, st in enumerate(self.dbRow['sessionType']) if st==sessiontype]
        return sessionInds

    def load_by_index(self, sessionInd, behavClass=None):
        """
        Load both ephys and behavior data for a session using the absolute index in the list
        of sessions for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of
                                                         behavData will have different methods.
        Returns:
            ephysData (list): Spiketimes (array), samples (array) and events (dict)
            behavData (jaratoolbox.loadbehavior.BehaviorData): Behavior data dict
        """
        if self.sessionData is None:
            ephysData = self.load_ephys_by_index(sessionInd)
            behavData = self.load_behavior_by_index(sessionInd, behavClass=behavClass)
        else:
            ephysData = self.sessionData.get_ephys(self.cluster)
            behavData = self.sessionData.get_behavior()
        return ephysData, behavData

    def load_ephys_by_index(self, sessionInd):
        """
        Load ephys data for a session using the absolute index in the list of sessions for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
        Returns:
            ephysData (list): Spiketimes (array), samples (array) and events (dict)
        """
        sessionDir = self.get_ephys_dir(sessionInd)
        paradigm = self.dbRow['paradigm'][sessionInd]
        if self.dbRow['probe'] == 'A4x2-tet':
            ephysData = load_ephys_neuronexus_tetrodes(self.subject, paradigm, sessionDir,
                                                       self.egroup, self.cluster,
                                                       useModifiedClusters=self.useModifiedClusters)
        elif self.dbRow['probe'][:4] == 'NPv1':
            ephysData = load_ephys_neuropixels_v1(self.subject, paradigm, sessionDir,
                                                  self.egroup, self.cluster,
                                                  self.dirsuffix)
        return ephysData

    def get_ephys_dir(self, sessionInd):
        """
        Return the full path to the ephys data for a given session.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
        Returns:
            sessionDir (str): Full path to the ephys data
        """
        ephysTime = self.dbRow['ephysTime'][sessionInd]
        sessionDir = '{}_{}'.format(self.date, ephysTime)
        return sessionDir

    def load_behavior_by_index(self, sessionInd, behavClass=None):
        """
        Load the behavior data for a session using the absolute index in the list of sessions
        for the cell.
        Args:
            sessionInd (int): The index of the session in the list of sessions recorded for the cell.
            behavClass (jaratoolbox.loadbehavior Class): The loading class to use, each class of
                                                         behavData will have different methods.
        Returns:
            behavData (jaratoolbox.loadbehavior.BehaviorData): Behavior data dict

        To implement in the future:
        * Allow use of valist for loading partial behavior data
        * Allow use of different loading class for paradigms like FlexCategBehaviorData
        """
        #Set the loading class for behavior data
        if behavClass==None:
            behavClass = loadbehavior.BehaviorData

        # -- Load the behavior data --
        # NOTE: this section could use get_behavior_path()
        if self.dbRow['behavSuffix'][sessionInd] is not None:
            dateStr = ''.join(self.date.split('-'))
            fullSessionStr = '{}{}'.format(dateStr, self.dbRow['behavSuffix'][sessionInd])
            thisParadigm = self.dbRow['paradigm'][sessionInd]
            behavDataFilePath = loadbehavior.path_to_behavior_data(self.subject,
                                                                   thisParadigm,
                                                                   fullSessionStr)
            bdata = behavClass(behavDataFilePath)
        else:
            bdata = None
        return bdata

    def load_all_spikedata(self):
        """
        Load the spike data for all recorded sessions into a set of arrays.
        Returns:
            timestamps (np.array): The timestamps for all spikes across all sessions
            samples (np.array): The samples for all spikes across all sessions
            recordingNumber (np.array): The index of the session where the spike was recorded
        """
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

    def get_behavior_path(self, sessiontype):
        """
        Return the full path to the behavior file.
        Args:
           sessiontype (str): the type of session to load data for.
        Returns:
            behavDataFilePath (str): Full path to the behavior data
        """
        sessionInd = self.get_session_inds(sessiontype)[-1]
        if self.dbRow['behavSuffix'][sessionInd] is not None:
            dateStr = ''.join(self.date.split('-'))
            fullSessionStr = '{}{}'.format(dateStr, self.dbRow['behavSuffix'][sessionInd])
            thisParadigm = self.dbRow['paradigm'][sessionInd]
            behavDataFilePath = loadbehavior.path_to_behavior_data(self.subject,
                                                                   thisParadigm,
                                                                   fullSessionStr)
        else:
            behavDataFilePath = None
        return behavDataFilePath

    
def load_ephys_neuronexus_tetrodes(subject, paradigm, sessionDir, tetrode, cluster=None,
                                   useModifiedClusters=False, verbose=False):
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
            clustersFileModified = os.path.join(clustersDir, f'Tetrode{tetrode}.clu.modified')
            if os.path.exists(clustersFileModified):
                if verbose:
                    print("Loading modified .clu file for session {}".format(spikesFilename))
                spikeData.set_clusters(clustersFileModified)
            else:
                if verbose:
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


def load_ephys_neuropixels_v1(subject, paradigm, sessionDir, egroup, cluster=None,
                              dirsuffix='_processed_multi'):
    ephysBaseDir = os.path.join(settings.EPHYS_NEUROPIX_PATH, subject)
    sessionDir = sessionDir[:-1] if sessionDir.endswith(os.sep) else sessionDir # Remove last sep
    spikesDir = os.path.join(ephysBaseDir, sessionDir+dirsuffix)
    #eventsDir = os.path.join(ephysBaseDir, sessionDir)
    if not os.path.isdir(spikesDir):
        print(f'{spikesDir} does not exist.')
        raise IOError(f'{spikesDir} does not exist.\n' +
                      'This session has not been spike sorted yet.')
    # -- Load spikes and events --
    spikesData = loadneuropix.Spikes(spikesDir, convert=True)
    eventsData = loadneuropix.Events(spikesDir, convert=True)
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
                 'events': eventDict,
                 'clusterEachSpike': spikesData.clusters}
    return ephysData


def spiketimes_each_cell(spikeTimesAllCells, clusterEachSpike, clusters=None):
    """
    Return a dictionary with the spike times for each cell.
    Args:
        spikeTimesAllCells (np.array): spike times for all cells (before spike sorting).
        clusterEachSpike (np.array): cluster index for each spike.
        clusters (np.array): which clusters to include. If None, include all clusters.
    """
    spikeTimesEachCell = {}
    if clusters is None:
        clusters = np.unique(clusterEachSpike)
    for cluster in clusters:
        spikesThisCluster = (clusterEachSpike==cluster)
        spikeTimesEachCell[cluster] = spikeTimesAllCells[spikesThisCluster]
    return spikeTimesEachCell


