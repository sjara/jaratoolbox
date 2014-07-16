'''
Load data saved by OpenEphysGUI software

https://github.com/open-ephys/GUI/wiki/Data-format


BUGS (for OpenEphys to fix)
- timestamp on continuous: signed or unsigned?
- wiki does not include recording number

'''

import numpy as np
import re
import os
from struct import unpack

FORMAT_VERSION = '0.2'
HEADER_SIZE = 1024 # in bytes
CONT_RECORD_SIZE = 2070 # 8+2+2+2048+10 bytes

#class DataCont(object):
 
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

        self.timestamps = []
        self.samplesPerRecord = []
        self.samples = []
        self.recordingNumber = []
        self.recordMarker = []

        for indr in range(nRecordsToLoad):
            self.timestamps.extend(unpack('q', fid.read(8)))  # signed or unsigned? (header not clear)
            self.samplesPerRecord.extend(unpack('H', fid.read(2)))
            self.recordingNumber.extend(unpack('H', fid.read(2)))
            self.samples.extend(unpack('>'+1024*'h', fid.read(1024*2))) # Big-endian byte order
            self.recordMarker.append(unpack(10*'B', fid.read(10)))
        fid.close()
        self.samples = np.array(self.samples)




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

        self.timestamps = []
        self.samplePosition = []
        self.eventType = []
        self.processorID = []
        self.eventID = []
        self.eventChannel = []
        self.recordingNumber = []
        for indr in range(self.nRecords):
            buf=fid.read(8)
            if len(buf) == 8:
                self.timestamps.extend(unpack('Q', buf))  # reading as unsigned although docs say signed
            else:
                print "error figured out: 8 bytes not available"
                print "bytes available: {0}".format(len(buf))
            self.samplePosition.extend(unpack('H', fid.read(2))) #reading as unsigned, although documentation says signed.
            self.eventType.extend(unpack('B', fid.read(1)))
            self.processorID.extend(unpack('B', fid.read(1)))
            self.eventID.extend(unpack('B', fid.read(1)))
            self.eventChannel.extend(unpack('B', fid.read(1)))
            self.recordingNumber.extend(unpack('H', fid.read(2)))
        fid.close()

        
class DataSpikes(object):
    '''
    Spike data
    timestamps is a numpy array
    samples is a numpy array of size (nSpikes,nChans,nSamples)
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
        nChannels = unpack('H', fid.read(2))[0]
        nSamplesPerSpike = unpack('H', fid.read(2))[0]
        fid.seek(HEADER_SIZE)
        SPIKES_RECORD_SIZE = 1 + 8 + 2 + 2 + 2 + nChannels*nSamplesPerSpike*2 + nChannels*2 + nChannels*2 + 2

        # -- Find number of records --
        if (self.filesize-HEADER_SIZE)%SPIKES_RECORD_SIZE:
            print 'The file size does not match a integer number of records'
        self.nRecords = (self.filesize-HEADER_SIZE)/SPIKES_RECORD_SIZE

        if self.header['version']!=FORMAT_VERSION:
            print 'The version of the file does not correspond to that of this script'

        self.eventType = []
        self.timestamps = []
        self.electrodeID = []
        self.nChannels = []
        self.nSamplesPerSpike = []
        self.samples = []
        self.gain = []
        self.threshold = []
        self.recordingNumber = []
        self.clusters = None # To store the cluster assignment for each spike
        for indr in range(self.nRecords):
            self.eventType.extend(unpack('B', fid.read(1)))
            self.timestamps.extend(unpack('Q', fid.read(8)))  # unsigned
            self.electrodeID.extend(unpack('H', fid.read(2)))
            self.nChannels.extend(unpack('H', fid.read(2)))
            self.nSamplesPerSpike.extend(unpack('H', fid.read(2)))
            nChannels = self.nChannels[-1]
            nSamplesPerRecord = nChannels*self.nSamplesPerSpike[-1]
            self.samples.append(unpack(nSamplesPerRecord*'H', fid.read(nSamplesPerRecord*2)))
            self.gain.append(unpack(nChannels*'H', fid.read(nChannels*2))) # this value is actually 1000*gain
            self.threshold.append(unpack(nChannels*'H', fid.read(nChannels*2)))
            self.recordingNumber.extend(unpack('H', fid.read(2)))
        fid.close()
        self.timestamps = np.array(self.timestamps)
        self.samples = np.array(self.samples)
        self.samples = self.samples.reshape((-1,self.nChannels[0],self.nSamplesPerSpike[0]),order='C') # (nSpikes,nChans,nSamples)


    def set_clusters(self,clusterFileOrArray):
        '''Access to KlustaKwik CLU files containing cluster data.'''
        if isinstance(clusterFileOrArray,str):
            self.clusters = np.fromfile(clusterFileOrArray,dtype='int32',sep=' ')[1:]
        else:
            self.clusters = np.array(clusterFileOrArray)


if __name__=='__main__':
    from pylab import *
    CASE = 2
    if CASE==1:
        dataDir = '/var/tmp/2014-04-25_12-19-27/'
        filenameOnly = '100_CH1.continuous'
        filename = os.path.join(dataDir,filenameOnly)
        datacont = DataCont(filename)
        plot(datacont.samples[:10000],'.-')
        draw()
        show()

    elif CASE==2:
        dataDir = '/var/tmp/2014-04-25_12-19-27/'
        filenameOnly = '100_CH1.continuous'
        filename = os.path.join(dataDir,filenameOnly)
        datacont = DataCont(filename,nRecordsToLoad=10)
        plot(datacont.samples[:10000],'.-')
        draw()
        show()

    elif CASE==3:
        dataDir = '/var/tmp/2014-04-25_12-19-27/'
        filenameOnly = 'Tetrode8.spikes'
        filename = os.path.join(dataDir,filenameOnly)
        dataspikes = DataSpikes(filename)
        plot(dataspikes.samples[:10,:].T,'.')
        draw()
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
