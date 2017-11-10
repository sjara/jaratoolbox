'''
Main objects for working with electrophysiology data
'''

from jaratoolbox import loadopenephys
from jaratoolbox import loadbehavior
from jaratoolbox import settings
import os
import numpy as np



############## NOT FINISHED ##################

CHANNELMAPS = {'am_tuning_curve': {'stim':0, 'trialStart':1, 'laser':2, 'soundDetector':5}}

class CellDataObj(object):
    def __init__(self, dbRow):
        '''
        Things to check at the end:
        * When looping through cells, make sure that nothing is preserved from iteration to the next
        Args:
            dbRow (pandas.core.series.Series): A row from a dataframe. Must contain at least:
            * sessiontype
        '''
        if len(dbRow)!=1:
            raise TypeError('This object must be initialized with only a single dataframe row')
        self.dbRow = dbRow

        # We use these variables many times to load data
        # Date and depth are not really used to load the data
        self.subject = dbRow['subject']
        self.tetrode = dbRow['tetrode']
        self.cluster = dbRow['cluster']
        self.ephysBaseDir = os.path.join(settings.EPHYS_PATH, self.subject)

    def load(self, sessiontype):
        '''
        Load the spikes, events, and behavior data for a single session. Loads the LAST recorded
        session of the type that was recorded from the cell.
        Args:
            sessiontype (str): the type of session to load data for.
        '''
        sessionInds = self.find_session_inds(sessiontype)
        sessionIndToUse = sessionInds[-1] #NOTE: Taking the last session of this type!
        ephysData, behavData = self.load_by_index(sessionIndToUse)
        return ephysData, behavData

    def find_session_inds(self, sessiontype):
        sessionInds = [i for i, st in enumerate(self.dbRow['sessiontype']) if st==sessiontype]
        return sessionInds

    def load_by_index(self, sessionInd):
        ephysData = self.load_ephys_by_index(sessionInd)
        behavData = self.load_behavior_by_index(sessionInd)
        return ephysData, behavData

    def load_ephys_by_index(self, sessionInd):
        #Load the spikes and events
        spikesFilename, eventsFilename = self.get_ephys_filename(sessionInd)
        eventData = loadopenephys.Events(eventFilename)
        spikeData = loadopenephys.DataSpikes(spikesFilename)
        if spikeData.timestamps is not None:
            clustersDir = os.path.join(self.ephysBaseDir, '{}_kk'.format(ephysSession))
            clustersFile = os.path.join(clustersDir,'Tetrode{}.clu.1'.format(self.tetrode))
            spikeData.set_clusters(clustersFile)
            spikeData.samples = spikeData.samples[spikeData.clusters==self.cluster]
            spikeData.timestamps = spikeData.timestamps[spikeData.clusters==self.cluster]
            spikeData = loadopenephys.convert_openephys(spikeData)
            # samples = spikeData.samples
            # timestamps = spikeData.timestamps
        eventData = loadopenephys.convert_openephys(eventData)

        eventDict = {}
        #Choose channel map based on paradigm
        paradigm = self.dbRow['paradigm'][sessionInd]
        channelMap = CHANNELMAPS[paradigm]
        for channelType, channelID in channelMap.iteritems():
            #Add channelTypeOn
            #Add channelTyepOff
            # eventDict.update

        ephysData = {'spiketimes':spikeData.timestamps,
                     'samples':spikeData.samples,
                     'events':eventDict}

        return ephysData

    def get_ephys_filename(sessionInd):
        ephysSession = self.dbRow['ephys'][sessionInd]
        eventsFilename = os.path.join(self.ephysBaseDir, ephysSession,
                                     'all_channels.events')
        spikesFilename = os.path.join(self.ephysBaseDir, ephysSession,
                                      'Tetrode{}.spikes'.format(self.tetrode))
        return spikesFilename, eventsFilename

    def get_behavior_filename():
        pass

    def load_behavior_by_index(self, sessionInd):
        '''
        To implement in the future:
        * Allow use of different readmode for loading partial data
        * Allow use of different loading class for paradigms like FlexCategBehaviorData
        '''
        #Load the behavior data
        behavFile = self.behavior[sessionInd]
        behavDataFilePath=os.path.join(settings.BEHAVIOR_PATH, self.subject, behavFile)
        bdata = loadbehavior.BehaviorData(behavDataFilePath,readmode='full')
        return bdata


"""
class CellData(object):
    '''
    '''
    # def __init__(self, subject, date, depth, tetrode, cluster):
    def __init__(self, subject, date, depth, tetrode, cluster, sessiontype, ephys, behavior, **kwargs):
        '''
        Builds a cell object - meant to be easy to call using a dict of this information, even if the dict
        contains extra keys (this is commonly generated if you convert a celldatabase row, in the form of a
        pandas Series, into a dict to use when initializing this object). The extra keys and vals end up in
        the attribute cellInfo.
        '''
        self.subject = subject
        self.date = date
        self.depth = int(depth)
        self.tetrode = int(tetrode)
        self.cluster = int(cluster)
        self.ephysBaseDir = os.path.join(settings.EPHYS_PATH, subject)
        self.sessiontype = sessiontype
        self.ephys = ephys
        self.behavior = behavior
        self.cellInfo = kwargs #Collect extra key-val pairs

    def get_session_inds(self, sessiontype):
        '''
        Get the index of a particular sessiontype for a cell.
        Args:
            cell (pandas.Series): One row from a pandas cell database created using generate_cell_database or by
                                manually constructing a pandas.Series object that contains the required fields.
                                This function requires the 'sessiontype' field, which must contain a list of strings.
            sessiontype (str): The type of session

        Returns:
            sessionInds (list): Atlist of indices where cell['sessiontype'] and the sessiontype arg match.
        '''
        sessionInds = [i for i, st in enumerate(self.sessiontype) if st==sessiontype]
        return sessionInds

    def load_ephys(self, sessiontype):
        sessionInds = self.get_session_inds(sessiontype)
        sessionInd = sessionInds[0] #FIXME: Just takes the first one for now
        ephysSession = self.ephys[sessionInd]
        eventFilename=os.path.join(self.ephysBaseDir,
                                ephysSession,
                                'all_channels.events')
        spikesFilename=os.path.join(self.ephysBaseDir,
                                    ephysSession,
                                    'Tetrode{}.spikes'.format(self.tetrode))
        eventData=loadopenephys.Events(eventFilename)
        spikeData = loadopenephys.DataSpikes(spikesFilename)
        if spikeData.timestamps is not None:
            clustersDir = os.path.join(self.ephysBaseDir, '{}_kk'.format(ephysSession))
            clustersFile = os.path.join(clustersDir,'Tetrode{}.clu.1'.format(self.tetrode))
            spikeData.set_clusters(clustersFile)
            spikeData.samples=spikeData.samples[spikeData.clusters==self.cluster]
            spikeData.timestamps=spikeData.timestamps[spikeData.clusters==self.cluster]
            spikeData = loadopenephys.convert_openephys(spikeData)
        eventData = loadopenephys.convert_openephys(eventData)
        return spikeData, eventData

    def load_bdata(self, sessiontype):
        sessionInds = self.get_session_inds(sessiontype)
        sessionInd = sessionInds[0] #FIXME: Just takes the first one for now
        behavFile = self.behavior[sessionInd]
        behavDataFilePath=os.path.join(settings.BEHAVIOR_PATH, self.subject, behavFile)
        bdata = loadbehavior.BehaviorData(behavDataFilePath,readmode='full')
        return bdata

    def load_all_spikedata(self):
        '''
        Load the spike data for all recorded sessions into a set of arrays.
        Args:
            cell (pandas.Series): One row from a pandas cell database created using generate_cell_database or by
                                manually constructing a pandas.Series object that contains the required fields.
        Returns:
            timestamps (np.array): The timestamps for all spikes across all sessions
            samples (np.array): The samples for all spikes across all sessions
            recordingNumber (np.array): The index of the session where the spike was recorded
        '''
        samples=np.array([])
        timestamps=np.array([])
        recordingNumber=np.array([])
        for ind, sessionType in enumerate(self.sessiontype):
            dataSpkObj, dataEvents = self.get_session_ephys(sessionType)
            if (dataSpkObj.timestamps is None) or (len(dataSpkObj.timestamps)==0):
                continue
            numSpikes = len(dataSpkObj.timestamps)
            sessionVector = np.zeros(numSpikes)+ind
            if len(samples)==0:
                samples = dataSpkObj.samples
                timestamps = dataSpkObj.timestamps
                recordingNumber = sessionVector
            else:
                samples = np.concatenate([samples, dataSpkObj.samples])
                # Check to see if next session ts[0] is lower than self.timestamps[-1]
                # If so, add self.timestamps[-1] to all new timestamps before concat
                if dataSpkObj.timestamps[0]<timestamps[-1]:
                    dataSpkObj.timestamps = dataSpkObj.timestamps + timestamps[-1]
                timestamps = np.concatenate([timestamps, dataSpkObj.timestamps])
                recordingNumber = np.concatenate([recordingNumber, sessionVector])
        return timestamps, samples, recordingNumber
"""

# class CellData(object):
#     '''
#     Spike data for one cell
#     timestamps is a numpy array in seconds
#     samples is a numpy array of size (nSpikes,nChans,nSamples) in microVolts

#     FIXME: this object results in a very inefficient way to load multiple cells from
#            the same tetrode (it would have to reload the whole data file).
#            We need to find a way to load data once, and split by clusters.
#     '''
#     def __init__(self,onecell):
#         self.animalName = onecell.animalName
#         self.ephysSession = onecell.ephysSession
#         self.behavSession = onecell.behavSession
#         self.tetrode = onecell.tetrode
#         self.cluster = onecell.cluster
#         self.filename = onecell.get_filename()
#         self.spikes=loadopenephys.DataSpikes(self.filename)
#         self.spikes.timestamps = self.spikes.timestamps/self.spikes.samplingRate
#         self.load_clusters()
#         self.select_cluster() # Remove all spikes froopenephysm other clusters
#     def load_clusters(self):
#         # FIXME: all these hardcoded paths should be defined in spikesorting.py
#         kkDataDir = os.path.dirname(self.filename)+'_kk'
#         clusterFilename = 'Tetrode{0}.clu.1'.format(self.tetrode)
#         fullPath = os.path.join(kkDataDir,clusterFilename)
#         self.clusters = np.fromfile(fullPath,dtype='int32',sep=' ')[1:]
#         # FIXME: bad name 'clusters', and it should be defined in __init__
#     def select_cluster(self):
#         spikesMaskThisCluster = self.clusters==self.cluster
#         self.spikes.timestamps = self.spikes.timestamps[spikesMaskThisCluster]
#         self.spikes.samples = self.spikes.samples[spikesMaskThisCluster,:,:]

# class Spikes(object):
#     '''
#     Spike data
#     timestamps is a numpy array in seconds
#     samples is a numpy array of size (nSpikes,nChans,nSamples) in microVolts
#     '''
#     def __init__(self,onecell):
#         animalName = onecell.animalName
#         ephysSession = onecell.ephysSession
#         behavSession = onecell.behavSession
#         tetrode = onecell.tetrode
#         cluster = onecell.cluster


#     def set_clusters(self,clusterFileOrArray):
#         '''Access to KlustaKwik CLU files containing cluster data.'''
#         if isinstance(clusterFileOrArray,str):
#             self.clusters = np.fromfile(clusterFileOrArray,dtype='int32',sep=' ')[1:]
#         else:
#             self.clusters = np.array(clusterFileOrArray)
