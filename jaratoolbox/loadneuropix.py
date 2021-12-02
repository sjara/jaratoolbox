"""
Module for loading neuropixels data.
"""

import os
import sys
import numpy as np
import pandas as pd
import re
import shutil


def read_processor_info(infoDir, subProcessorIndex=0):
    syncFile = os.path.join(infoDir, 'sync_messages.txt')
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
    def __init__(self, processedDataDir, convert=True):
        """
        Args:
            processedDataDir (str): path to root of neuropixels raw data for a given session.
            convert(bool): if True, convert timestamps to seconds.
        """
        self.convertUnits = convert
        #self.recordingDir = os.path.join(dataDir, 'Record Node 101/experiment1/recording1/')
        #self.eventsDir = os.path.join(self.recordingDir, 'events/Neuropix-PXI-100.0/TTL_1/')
        self.eventsDir = os.path.join(processedDataDir,'events/Neuropix-PXI-100.0/TTL_1/')
        self.infoDir = os.path.join(processedDataDir,'info')
        channelsFile = 'channels.npy'
        channelStatesFile = 'channel_states.npy'
        fullWordsFile = 'full_words.npy'
        timestampsFile = 'timestamps.npy'

        (self.processorStartTime, self.samplingRate) = read_processor_info(self.infoDir)
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
        

def copy_events_and_info(dataDir, suffix='_processed_multi'):
    """
    Copy events data and OpenEphys info files to the processed data folder for a session.
    
    Args:
        dataDir (str): neuropixels session data folder. Usually in format YYYY-MM-DD_HH-MM-SS
    """
    dataDir = dataDir[:-1] if dataDir.endswith(os.sep) else dataDir  # Remove last sep

    relativePathToRecording = 'Record Node 101/experiment1/recording1/'
    eventsDir = os.path.join(dataDir, relativePathToRecording, 'events')
    structFile = os.path.join(dataDir, relativePathToRecording, 'structure.oebin')
    syncFile = os.path.join(dataDir, relativePathToRecording, 'sync_messages.txt')

    processedDir = dataDir+suffix
    if not os.path.isdir(processedDir):
        print(f'{processedDir} does not exist.')
        print('WARNING! This session has not been processed. No files will be copied.')
        return
    newEventsDir = os.path.join(processedDir, 'events')
    infoDir = os.path.join(processedDir, 'info')
    try:
        shutil.copytree(eventsDir, newEventsDir)
    except FileExistsError:
        print(f'WARNING! {newEventsDir} already exists. It was not modified.')
    else:
        print(f'Copied {eventsDir} to {newEventsDir}')
    try:
        os.mkdir(infoDir)
    except FileExistsError:
        print(f'WARNING! {infoDir} already exists. It was not modified.')
        return
    else:
        print(f'Created {infoDir}')
    shutil.copy2(structFile, infoDir)
    print(f'Copied {structFile} to {infoDir+os.sep}')
    shutil.copy2(syncFile, infoDir)
    print(f'Copied {syncFile} to {infoDir+os.sep}')
    return processedDir

def progress_bar(sofar, total, size=60):
    nBoxes = int(size*sofar/total)
    nWhites = size-nBoxes
    sys.stdout.write('[{}{}]'.format('-'*nBoxes, ' '*nWhites))
    sys.stdout.flush()
    sys.stdout.write('\b'*(size+2)) # return to start of line, after '['


def concatenate_sessions(sessionsRootPath, sessions, outputDir, debug=False):
    """
    Save file with concatenated neurpixels data, ready for spike sorting.

    Args:
        sessionsRootPath (str): path to where session directories are located.
        sessionDirs (list): list of full paths to sessions to concatenate.
        outputDir (bool): directory where concatenated files will be saved.
        debug (bool): if False, don't create directories or save anything.
    Returns:
        sessionsInfo (pandas.DataFrame): information about each session.
    """
    import pandas as pd  # Imported here to avoid dependency if using other functions
    blockSize = 4096  # Typical size in Bytes
    nBlocks = 2048
    chunkSize = nBlocks * blockSize

    recordingPath = 'Record Node 101/experiment1/recording1/continuous/Neuropix-PXI-100.0/'

    dataPath = os.path.join(sessionsRootPath, '{}', recordingPath)
    dataFile = 'continuous.dat'
    timestampsFile = 'timestamps.npy'

    tmpDataFile = 'multisession_continuous.dat'
    sessionsInfoFile = 'multisession_info.csv'
    outputDataFile = os.path.join(outputDir, tmpDataFile)
    outputInfoFile = os.path.join(outputDir, sessionsInfoFile)

    if not os.path.isdir(outputDir):
        if debug:
            print(f'DEBUG MESSAGE: this step would create {outputDir}')
        else:
            os.mkdir(outputDir)
            print(f'Created {outputDir}')

    if os.path.isfile(outputDataFile):
        overwrite = 'y' #input(f'File {outputFile} exists. Overwrite? (Y/n): ')
        if overwrite.lower() != 'y':
            sys.exit()
        print(f'Overwriting {outputDataFile}')

    if debug:
        print(f'DEBUG MESSAGE: this step would open {outputDataFile}')
    else:
        ofile = open(outputDataFile, 'wb')

    sessionsInfo = [] #pd.DataFrame()

    for oneSession in sessions:
        oneSessionDataFile = os.path.join(dataPath.format(oneSession), dataFile)
        oneSessionTimestampsFile = os.path.join(dataPath.format(oneSession), timestampsFile)

        tsThisSession = np.load(oneSessionTimestampsFile, mmap_mode='r')
        with open(oneSessionDataFile, 'rb') as dfile:
            fileSize = dfile.seek(0, os.SEEK_END)
            dfile.seek(0, 0)  # Back to the beginning
            nChunks = fileSize//chunkSize + 1  # Plus one to include a partial chunk
            print(oneSessionDataFile)
            print(f'Size: {fileSize/(2**30):0.2f} GB')
            if debug:
                print(f'DEBUG MESSAGE: this step would concatenate the file.')
            else:
                for oneChunk in range(nChunks):
                    dataChunk = dfile.read(chunkSize)
                    ofile.write(dataChunk)
                    progress_bar(oneChunk, nChunks)
                print('\n')
        sessionsInfo.append({'session':oneSession,
                             'firstTimestamp':tsThisSession[0],
                             'lastTimestamp': tsThisSession[-1],
                             'fileSize':fileSize })

    if debug:
        print(f'DEBUG MESSAGE: this step would close {outputDataFile}')
    else:
        ofile.close()

    sessionsInfo = pd.DataFrame(sessionsInfo)
    print(sessionsInfo)
    if debug:
        print(f'DEBUG MESSAGE: this step would save {outputInfoFile}')
    else:
        sessionsInfo.to_csv(outputInfoFile)
        print(f'Saved {outputInfoFile}')
    return sessionsInfo


def split_sessions(multisessionPath, debug=False):
    """
    Split results of multisession spike-sorting back to individual sessions.

    Args:
        multisessionPath (str): path to multisession processed directory.
        debug (bool): if False, don't create directories or save anything.
    Returns:
        sessionsInfo (pandas.DataFrame): information about each session.
    """
    import pandas as pd  # Imported here to avoid dependency if using other functions
    rootDir = os.path.dirname(multisessionPath)
    sessionsInfoFile = 'multisession_info.csv'
    multiSpikeTimesFile = 'spike_times.npy'
    multiSpikeClustersFile = 'spike_clusters.npy'
    firstTimestampFile = 'first_timestamp.csv'
    #filesToCopy = ['params.py', 'templates.npy', 'multisession_info.csv']
    filesToCopy = ['params.py', 'multisession_info.csv']
    
    sessionsInfo = pd.read_csv(os.path.join(multisessionPath, sessionsInfoFile), index_col=0)
    multiSpikeTimes = np.load(os.path.join(multisessionPath, multiSpikeTimesFile))
    multiSpikeClusters = np.load(os.path.join(multisessionPath, multiSpikeClustersFile))

    nSamplesEachSession = sessionsInfo.lastTimestamp - sessionsInfo.firstTimestamp + 1
    lastSampleEachSession = np.cumsum(nSamplesEachSession)
    firstSampleEachSession = np.r_[0, lastSampleEachSession[:-1]]

    for inds, oneRow in sessionsInfo.iterrows():
        sessionDir = os.path.join(rootDir, f'{oneRow.session}_processed_multi')
        spikeIndsThisSession = ( (multiSpikeTimes>=firstSampleEachSession[inds]) & 
                                 (multiSpikeTimes<lastSampleEachSession[inds]) )
        spikeTimesThisSession = multiSpikeTimes[spikeIndsThisSession]-firstSampleEachSession[inds]
        spikeClustersThisSession = multiSpikeClusters[spikeIndsThisSession]

        if os.path.isdir(sessionDir):
            print(f'WARNING! {sessionDir} exists. Data will be overwritten.')
        else:
            if not debug:
                os.mkdir(sessionDir)
            print(f'Created {sessionDir}')
        thisSessionSpikeTimesFile = os.path.join(sessionDir, multiSpikeTimesFile)
        thisSessionSpikeClustersFile = os.path.join(sessionDir, multiSpikeClustersFile)
        thisSessionFirstTimestampFile = os.path.join(sessionDir, firstTimestampFile)

        if not debug:
            np.save(thisSessionSpikeTimesFile, spikeTimesThisSession)
        print(f'Saved {thisSessionSpikeTimesFile}')
        if not debug:
            np.save(thisSessionSpikeClustersFile, spikeClustersThisSession)
        print(f'Saved {thisSessionSpikeClustersFile}')
        for oneFile in filesToCopy:
            if not debug:
                shutil.copy2(os.path.join(multisessionPath, oneFile), sessionDir)
            print(f'Copied {oneFile} to {sessionDir}{os.sep}')
        if not debug:
            with open(thisSessionFirstTimestampFile, 'w') as firstTSfile:
                firstTSfile.write(f'{sessionsInfo.firstTimestamp[inds]}')
        print(f'Saved {sessionsInfo.firstTimestamp[inds]} to {thisSessionFirstTimestampFile}')
        print('')

    sessionList = list(sessionsInfo.session)
    return sessionList
    

def spikeshapes_from_templates(clusterFolder, save=False, ignorezero=True):
    """
    Extract a spike shape from each template.
    """
    templates = np.load(os.path.join(clusterFolder,'templates.npy'))
    (nOrigClusters, nTimePoints, nChannels) = templates.shape
    spikeShapes = np.empty([nOrigClusters, nTimePoints], dtype=templates.dtype)
    bestChannel = np.empty(nOrigClusters, dtype=int)
    for indt, oneTemplate in enumerate(templates):
        indMax = np.argmax(np.abs(oneTemplate))
        (rowMax, colMax) = np.unravel_index(indMax, oneTemplate.shape)
        spikeShapes[indt,:] = oneTemplate[:,colMax]
        bestChannel[indt] = colMax
    if ignorezero:
        nonzerosamples = (spikeShapes.sum(axis=0)!=0)
        firstnonzero = np.flatnonzero(nonzerosamples)[0]
        spikeShapes = spikeShapes[:,firstnonzero:]
    if save:
        spikeShapesFile = os.path.join(clusterFolder, 'spike_shapes.npy')
        bestChannelFile = os.path.join(clusterFolder, 'cluster_bestChannel.npy')
        np.save(spikeShapesFile, spikeShapes)
        print(f'Saved {spikeShapesFile}')
        np.save(bestChannelFile, bestChannel)
        print(f'Saved {bestChannelFile}\n')
    return (spikeShapes, bestChannel)


def spikes_per_cluster(datadir, nClusters):
    """
    Calculate the number of spikes for each cluster.
    """
    spikeClustersFile = os.path.join(datadir, 'spike_clusters.npy')
    nSpikes = np.empty(nClusters, dtype=int)
    for indc in range(nClusters):
        nSpikes[indc] = np.count_nonzero(spikeClusters==clusterID)
    return nSpikes

    
