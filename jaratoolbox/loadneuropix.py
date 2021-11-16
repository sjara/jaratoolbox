"""
Module for loading neuropixels data.
"""

import os
import numpy as np
import pandas as pd
import re


def read_processor_info(dataDir, subProcessorIndex=0):
    syncFile = os.path.join(dataDir, 'sync_messages.txt')
    pattern = (f'Processor: Neuropix-PXI Id: 100 subProcessor: {subProcessorIndex} ' +
               'start time: (\d*)@(\d*)Hz')
    with open(syncFile) as sfile:
        syncInfo = sfile.readlines()
    for oneline in syncInfo:
        match = re.search(pattern, oneline)
        if match:
            startTime = int(match.group(1))
            samplingRate = float(match.group(2))
    return(startTime, samplingRate)


'''
def read_sampling_rate(dataDir, processorID):
    structFile = os.path.join(dataDir, 'structure.oebin')
    with open(structFile) as sfile:
        openEphysParams = json.loads(sfile.read()) 
    samplingRate = float(openEphysParams['continuous'][0]['sample_rate'])
    return samplingRate
'''     


class Spikes():
    """
    Class for loading spike timestamps and assigned clusters saved by Kilosort/Phy.
    """
    def __init__(self, dataDir, convert=True):
        """
        Args:
            dataDir (str): path to directory with kilosort/phy results.
            convert(bool): if True, convert timestamps to seconds.
        """
        self.dataDir = dataDir
        self.convertUnits = convert
        self.timestamps = None
        self.clusters = None
        self.clusterGroup = None
        self.samplingRate = None
        
        self.load_data()
    
    def load_data(self):
        spikeTimesFile = os.path.join(self.dataDir, 'spike_times.npy')
        spikeClustersFile = os.path.join(self.dataDir, 'spike_clusters.npy')
        clusterGroupFile = os.path.join(self.dataDir, 'cluster_group.tsv')

        self.samplingRate = self.read_sampling_rate()
        self.clusters = np.load(spikeClustersFile).squeeze()
        self.clusterGroup = pd.read_csv(clusterGroupFile, sep='\t')
        self.timestamps = np.load(spikeTimesFile).squeeze()
        if self.convertUnits:
            self.timestamps = self.timestamps/self.samplingRate

    def get_timestamps(self, cluster=None):
        """
        Return timestamps for a specific cluster.
        """
        if cluster is None:
            return self.timestamps
        else:
            spikesThisCluster = self.clusters==cluster
            return self.timestamps[spikesThisCluster]
        
    def read_sampling_rate(self):
        paramsFile = os.path.join(self.dataDir, 'params.py')
        with open(paramsFile) as pfile:
            paramsList = pfile.readlines()
        for oneline in paramsList:
            if oneline.find('sample_rate') >= 0:
                valueStr = oneline.split('=')[1].strip()
                samplingRate = float(valueStr)
                break
        return samplingRate
    
    
class Events():
    """
    Class for loading TTL events.

    Note that timestamps for events are stored relative to the start of acquisition (play button),
    not recording. This class can make the right conversion to match spike data from kilosort.
    """
    def __init__(self, dataDir, convert=True):
        """
        Args:
            dataDir (str): path to root of neuropixels raw data for a given session.
            convert(bool): if True, convert timestamps to seconds.
        """
        self.convertUnits = convert
        self.recordingDir = os.path.join(dataDir, 'Record Node 101/experiment1/recording1/')
        self.eventsDir = os.path.join(self.recordingDir, 'events/Neuropix-PXI-100.0/TTL_1/')
        channelsFile = 'channels.npy'
        channelStatesFile = 'channel_states.npy'
        fullWordsFile = 'full_words.npy'
        timestampsFile = 'timestamps.npy'
        
        (self.processorStartTime, self.samplingRate) = read_processor_info(self.recordingDir)
        self.channels = np.load(os.path.join(self.eventsDir, channelsFile))
        self.channelStates = np.load(os.path.join(self.eventsDir, channelStatesFile))
        self.fullWords = np.load(os.path.join(self.eventsDir, fullWordsFile))
        self.timestamps = np.load(os.path.join(self.eventsDir, timestampsFile))
        if self.convertUnits:
            self.timestamps = (self.timestamps-self.processorStartTime)/self.samplingRate
        
    def get_onset_times(self, eventChannel=1, channelState=1):
        '''
        Get the onset times for specific events.

        Args:
            eventChannel (int): The openEphys DIO channel that recieves the event.
            channelState (int): 1 for onset, -1 for offset
        Returns:
            eventOnsetTimes (array): An array of the timestamps of the event onsets.
        '''
        eventOnsetTimes=self.timestamps[(self.channelStates==channelState)&(self.channels==eventChannel)]
        return eventOnsetTimes
        
