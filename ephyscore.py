'''
Main objects for working with electrophysiology data
'''

from jaratoolbox import loadopenephys
from jaratoolbox import celldatabase
import os
import numpy as np


############## NOT FINISHED ##################



class CellData(object):
    '''
    Spike data for one cell
    timestamps is a numpy array in seconds
    samples is a numpy array of size (nSpikes,nChans,nSamples) in microVolts

    FIXME: this object results in a very inefficient way to load multiple cells from
           the same tetrode (it would have to reload the whole data file).
           We need to find a way to load data once, and split by clusters.
    '''
    def __init__(self,onecell):
        self.animalName = onecell.animalName
        self.ephysSession = onecell.ephysSession
        self.behavSession = onecell.behavSession
        self.tetrode = onecell.tetrode
        self.cluster = onecell.cluster
        self.filename = onecell.get_filename()
        self.spikes=loadopenephys.DataSpikes(self.filename)
        self.spikes.timestamps = self.spikes.timestamps/self.spikes.samplingRate
        self.load_clusters()
        self.select_cluster() # Remove all spikes from other clusters
    def load_clusters(self):
        # FIXME: all these hardcoded paths should be defined in spikesorting.py
        kkDataDir = os.path.dirname(self.filename)+'_kk'
        clusterFilename = 'Tetrode{0}.clu.1'.format(self.tetrode)
        fullPath = os.path.join(kkDataDir,clusterFilename)
        self.clusters = np.fromfile(fullPath,dtype='int32',sep=' ')[1:]
        # FIXME: bad name 'clusters', and it should be defined in __init__
    def select_cluster(self):
        spikesMaskThisCluster = self.clusters==self.cluster
        self.spikes.timestamps = self.spikes.timestamps[spikesMaskThisCluster]
        self.spikes.samples = self.spikes.samples[spikesMaskThisCluster,:,:]



class Spikes(object):
    '''
    Spike data
    timestamps is a numpy array in seconds
    samples is a numpy array of size (nSpikes,nChans,nSamples) in microVolts
    '''
    def __init__(self,onecell):
        animalName = onecell.animalName
        ephysSession = onecell.ephysSession
        behavSession = onecell.behavSession
        tetrode = onecell.tetrode
        cluster = onecell.cluster


    def set_clusters(self,clusterFileOrArray):
        '''Access to KlustaKwik CLU files containing cluster data.'''
        if isinstance(clusterFileOrArray,str):
            self.clusters = np.fromfile(clusterFileOrArray,dtype='int32',sep=' ')[1:]
        else:
            self.clusters = np.array(clusterFileOrArray)
