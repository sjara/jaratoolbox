'''
Load data saved by OpenEphysGUI software

https://github.com/open-ephys/GUI/wiki/Data-format


BUGS (for OpenEphys to fix)
- timestamp on continuous: signed or unsigned?
  Official wiki (2015-01-03) says signed for Cont, Events and Spikes.
- samplePosition on events: signed or unsigned?
- wiki does not include recording number

'''

import numpy as np
import re
import os

FORMAT_VERSION = '0.2'
HEADER_SIZE = 1024 # in bytes
CONT_RECORD_SIZE = 2070 # 8+2+2+2048+10 bytes

 
def parse_header(headerfull):
    ###patt = re.compile(r'\s*header\.(\w+)\s*=\s*(.*)')
    # FIXME: the items are currently stored as strings (even if they are numbers)
    # FIXME: strings are surrounded by single quotes, we should remove those
    headerlist = headerfull.split(';')
    header = {}
    for oneline in headerlist:
        if not oneline.isspace():
            keyitem = oneline.strip().split('=')
            key = keyitem[0].split('.')[1].strip()
            item = keyitem[1].strip()
            header[key] = item
    if header['version']!=FORMAT_VERSION:
        print 'The version of the file does not correspond to that of this script'
    return header


class DataCont(object):
    '''
    Continuous data.
    timestamps is a python list with one value per record
    samples is a numpy array
    '''
    def __init__(self,filename,nRecordsToLoad=None):
        # -- Find number of records --
        self.filesize = os.path.getsize(filename)
        if (self.filesize-HEADER_SIZE)%CONT_RECORD_SIZE:
            print 'The file size does not match a integer number of records'
        self.nRecords = (self.filesize-HEADER_SIZE)/CONT_RECORD_SIZE
        if nRecordsToLoad is None:
            nRecordsToLoad = self.nRecords

        fid = open(filename,'rb')
        headerfull = fid.read(HEADER_SIZE)
        self.header = parse_header(headerfull)
        if self.header['version']!=FORMAT_VERSION:
            print 'The version of the file does not correspond to that of this script'
        self.samplingRate = float(self.header['sampleRate'])

        dt = np.dtype([('timestamps','<i8'), ('samplesPerRecord','<u2'), ('recordingNumber','<u2'),
                       ('samples','>1024i2'), ('recordMarker','<10u1')])
        data=np.fromfile(fid, dtype=dt, count=nRecordsToLoad)
        fid.close()
        '''
        self.timestamps = data['timestamps']
        self.samplesPerRecord = data['samplesPerRecord']
        #self.samples = data['samples'].flatten(order='C')
        #self.samples = data['samples'].ravel(order='C')
        self.samples = data['samples']
        self.recordingNumber = data['recordingNumber']
        self.recordMarker = data['recordMarker']
        '''
        # -- We make copies of all fields, to garbage-collect 'data' after init. --
        self.timestamps = data['timestamps'].copy()
        self.samplesPerRecord = data['samplesPerRecord'].copy()
        self.samples = data['samples'].flatten(order='C')
        self.recordingNumber = data['recordingNumber'].copy()
        self.recordMarker = data['recordMarker'].copy()
    def lock_to_event(self,eventOnsetTimes,timeRange):
        '''Make matrix of LFP traces locked to stimulus
        As of 2015-01-03, 
        eventOnsetTimes should be in samples
        timeRange should be in seconds
        '''
        if np.any(np.diff(np.diff(self.timestamps))):
            print('WARNING: Not all LFP records are contiguous. lock_to_event() will not work properly.')
        samplesVec = np.arange(int(timeRange[0]*self.samplingRate),
                               int(timeRange[-1]*self.samplingRate))
        timeVec = samplesVec/self.samplingRate
        nSamples = len(timeVec)
        nTrials = len(eventOnsetTimes)
        lockedLFP = np.empty((nTrials,nSamples))
        for inde,eventTime in enumerate(eventOnsetTimes):
            if not np.isnan(eventTime):
                zeroSampleThisEvent = eventTime-self.timestamps[0]
                samplesIndexes = samplesVec + zeroSampleThisEvent
                lockedLFP[inde,:] = self.samples[samplesIndexes]
            else:
                lockedLFP[inde,:] = np.NaN
        return (lockedLFP,timeVec)


class Events(object):
    def __init__(self,filename):

        fid = open(filename,'rb')
        headerfull = fid.read(HEADER_SIZE)
        self.header = parse_header(headerfull)

        self.filesize = os.path.getsize(filename)
        if self.filesize==HEADER_SIZE:
            print 'File is empty'
            return

        # -- Find record size --
        fid.seek(HEADER_SIZE)
        EVENT_RECORD_SIZE= 8 + 2 + 1 + 1 + 1 + 1 + 2 #One int64, one int16, four uint8 numbers, and one int16

        # -- Find number of records --
        if (self.filesize-HEADER_SIZE)%EVENT_RECORD_SIZE:
            print 'The file size does not match a integer number of records'
        self.nRecords = (self.filesize-HEADER_SIZE)/EVENT_RECORD_SIZE

        if self.header['version']!=FORMAT_VERSION:
            print 'The version of the file does not correspond to that of this script'
        self.samplingRate = float(self.header['sampleRate'])

        # -- Reading timestamps and samplePosition as unsigned, although documentation says signed. --
        dt = np.dtype([('timestamps','<i8'), ('samplePosition','<u2'), ('eventType','<u1'), ('processorID','<u1'),
                       ('eventID','<u1'), ('eventChannel','<u1'), ('recordingNumber','<u2')])
        data=np.fromfile(fid, dtype=dt, count=-1)
        fid.close()

        self.timestamps = data['timestamps'].copy()
        self.samplePosition = data['samplePosition'].copy()
        self.eventType = data['eventType'].copy()
        self.processorID = data['processorID'].copy()
        self.eventID = data['eventID'].copy()
        self.eventChannel = data['eventChannel'].copy()
        self.recordingNumber = data['recordingNumber'].copy()
    def get_event_onset_times(self, eventID=1, eventChannel=0):
        '''
        Get the onset times for specific events.

        Args:
            eventID (int): 1 for onset, 0 for offset
            eventChannel (int): The openEphys DIO channel that recieves the event.
                                0 picks up both sound and laser-driven events from our paradigms
        Returns:
            eventOnsetTimes (array): An array of the timestamps of the event onsets.
        '''
        if self.eventID is not None:
            eventOnsetTimes=self.timestamps[(self.eventID==eventID)&(self.eventChannel==eventChannel)]
        else:
            eventOnsetTimes=self.timestamps[self.eventChannel==eventChannel]
        return eventOnsetTimes

class DataSpikes(object):
    '''
    Spike data
    timestamps is a numpy array
    samples is a numpy array of size (nSpikes,nChans,nSamples)

    It assumes that nChannels and nSamplesPerSpike do not change from record to record.
    '''
    def __init__(self,filename):

        fid = open(filename,'rb')
        headerfull = fid.read(HEADER_SIZE)
        self.header = parse_header(headerfull)

        self.filesize = os.path.getsize(filename)
        if self.filesize==HEADER_SIZE:
            print 'File is empty'
            return

        # -- Find record size --
        currentPos = fid.tell()
        fid.seek(1+8+2,1) # Move from current position
        dtpre = np.dtype([('nChannels','<u2'),('nSamplesPerSpike','<u2')])
        datapre = np.fromfile(fid, dtype=dtpre, count=1)[0]
        nChannels = datapre['nChannels']
        nSamplesPerSpike = datapre['nSamplesPerSpike']
        nSamplesPerRecord = nChannels*nSamplesPerSpike
        fid.seek(HEADER_SIZE)
        SPIKES_RECORD_SIZE = 1 + 8 + 2 + 2 + 2 + nChannels*nSamplesPerSpike*2 + nChannels*2 + nChannels*2 + 2

        # -- Find number of records --
        if (self.filesize-HEADER_SIZE)%SPIKES_RECORD_SIZE:
            print 'The file size does not match a integer number of records'
        self.nRecords = (self.filesize-HEADER_SIZE)/SPIKES_RECORD_SIZE

        if self.header['version']!=FORMAT_VERSION:
            print 'The version of the file does not correspond to that of this script'
        self.samplingRate = float(self.header['sampleRate'])

        dt = np.dtype([('eventType','<u1'), ('timestamps','<i8'), ('electrodeID','<u2'), ('nChannels','<u2'),
                       ('nSamplesPerSpike','<u2'),('samples','{0}<u2'.format(nSamplesPerRecord)),
                       ('gain','{0}<u2'.format(nChannels)),('threshold','{0}<u2'.format(nChannels)),
                       ('recordingNumber','<u2')])
        data=np.fromfile(fid, dtype=dt, count=-1)
        fid.close()
        # -- We make copies of all fields, to garbage-collect 'data' after init. --
        self.eventType = data['eventType'].copy()
        self.timestamps = data['timestamps'].copy()
        self.electrodeID = data['electrodeID'].copy()
        self.nChannels = data['nChannels'].copy()
        self.nSamplesPerSpike = data['nSamplesPerSpike'].copy()
        self.samples = data['samples'].reshape((self.nRecords,nChannels,nSamplesPerSpike),order='C')
        self.gain = data['gain'].copy()  # This value is actually 1000*gain
        self.threshold = data['threshold'].copy()
        self.recordingNumber = data['recordingNumber'].copy()
        self.clusters = None # To store the cluster assignment for each spike

    def set_clusters(self,clusterFileOrArray):
        '''Access to KlustaKwik CLU files containing cluster data.'''
        if isinstance(clusterFileOrArray,str):
            self.clusters = np.fromfile(clusterFileOrArray,dtype='int32',sep=' ')[1:]
        else:
            self.clusters = np.array(clusterFileOrArray)


if __name__=='__main__':
    from pylab import *
    CASE = 7
    if CASE==1:
        dataDir = '/var/tmp/2014-04-25_12-19-27/'
        filenameOnly = '100_CH1.continuous'
        filename = os.path.join(dataDir,filenameOnly)
        datacont = DataCont(filename)
        if 1:
            plot(datacont.samples[:10000],'.-')
            draw(); show()

    elif CASE==2:
        dataDir = '/data/ephys/test030/2014-06-25_18-33-30_TT6goodGND'
        filenameOnly = '100_CH21.continuous'
        filename = os.path.join(dataDir,filenameOnly)
        datacont = DataCont(filename)
        if 1:
            plot(datacont.samples[:10000],'.-')
            draw(); show()
        '''
        d=[]
        for ind in range(10):
            d.append(DataCont(filename))
        '''
    elif CASE==3:
        dataDir = '/data/ephys/test030/2014-06-25_18-33-30_TT6goodGND'
        filenameOnly = 'Tetrode6.spikes'
        filename = os.path.join(dataDir,filenameOnly)
        dataspikes = DataSpikes(filename)
        if 1:
            plot(dataspikes.samples[2,:,:].T,'.-')
            draw(); show()
        '''
        for ind in range(1000):
            plot(dataspikes.samples[ind,:,:].T,'.-')
            draw(); show()
            waitforbuttonpress()
        '''
    elif CASE==4:
        dataDir = '/var/tmp/2014-04-25_12-19-27/'
        filenameOnly = '100_CH1.continuous'
        filename = os.path.join(dataDir,filenameOnly)
        datacont = DataCont(filename,nRecordsToLoad=10)
        plot(datacont.samples[:10000],'.-')
        draw()
        show()

    elif CASE==5:
        dataDir = '/var/tmp/2014-04-25_12-19-27/'
        filenameOnly = 'Tetrode8.spikes'
        filename = os.path.join(dataDir,filenameOnly)
        dataspikes = DataSpikes(filename)
        plot(dataspikes.samples[:10,:].T,'.')
        draw()
        show()

    elif CASE==6:
        dataDir = '/data/ephys/test030/2014-07-30_13-25-28/'
        filenameOnly = 'all_channels.events'
        filename = os.path.join(dataDir,filenameOnly)
        events = Events(filename)
        #plot(events.timestamps,'.')
        plot(events.samplePosition,'.')
        draw(); show()

    elif CASE==7:
        from jaratoolbox import spikesanalysis
        dataDir = '/home/nick/data/ephys/pinp015/2017-01-26_13-39-55'
        eventFn = 'all_channels.events'
        spikesFn = 'Tetrode2.spikes'
        eventFile = os.path.join(dataDir,eventFn)
        spikesFile = os.path.join(dataDir,spikesFn)
        eventOnsetTimes = Events(eventFile).get_event_onset_times()
        dataSpikes = DataSpikes(spikesFile)
        spikeTimestamps = dataSpikes.timestamps

        #convert to seconds
        spikeTimestamps = spikeTimestamps/30000.0
        eventOnsetTimes = eventOnsetTimes/30000.0

        timeRange = [-0.5, 1.0]

        #Remove events except from frist pulse in laser train
        eventOnsetTimes = spikesanalysis.minimum_event_onset_diff(eventOnsetTimes, 0.5)

        (spikeTimesFromEventOnset,
        trialIndexForEachSpike,
        indexLimitsEachTrial) = spikesanalysis.eventlocked_spiketimes(spikeTimestamps,
                                                                     eventOnsetTimes,
                                                                     timeRange)

        plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.')
        show()
'''
    One int64 timestamp (actually a sample number; this can be converted to seconds using the sampleRate variable in the header)
    One uint16 number (N) indicating the samples per record (always 1024, at least for now)
    1024 int16 samples
    10-byte record marker (0 1 2 3 4 5 6 7 8 255)
If a file is opened or closed in the middle of a record, the leading or trailing samples are set to zero.

Each record contains an individual spike event (saved for one or more channels), and is written in the following format:

    uint8 eventType (always 4)
    int64 timestamp (to align with timestamps from the continuous records)
    uint16 electrodeID
    uint16 number of channels (N)
    uint16 number of samples per spike (M)
    N*M uint16 samples (individual channels are contiguous)
    N uint16 gains (actually gain*1000, to increase resolution)
    N uint16 thresholds used for spike extraction

'''
