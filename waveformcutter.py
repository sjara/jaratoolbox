'''
Clean up clusters from KK

TODO:
- Allow saving and loading clusters (and bounds)


'''

from jaratoolbox import settings
from jaratoolbox import loadopenephys
import numpy as np
import os
from pylab import *
from jaratoolbox import spikesorting
reload(spikesorting)


SAMPLES_PER_SPIKE = 32
N_CHANNELS = 4

selectedChannel = 3

class WaveformCutterSession(object):
    def __init__(self, animalName, ephysSession, tetrode):
        self.animalName = animalName
        self.ephysSession = ephysSession
        self.tetrode = tetrode
        self.dataTT = []
        self.channel = 0
        self.activeCluster = 0

        self.clustersBool = []
        self.notInClusterBool = []
        self.clusterEachSpike = []
        self.clusters = []
        self.nClusters = 0
        self.nSpikes = 0
        self.clustersFile = ''
        self.outputFile = ''

        self.dataDir = os.path.join(settings.EPHYS_PATH,self.animalName,self.ephysSession)
        self.clustersDir = os.path.join(settings.EPHYS_PATH,self.animalName,self.ephysSession+'_kk')
        self.tetrodeFile = os.path.join(self.dataDir,'Tetrode{0}.spikes'.format(self.tetrode))

        self.load_data(self.animalName, self.ephysSession, self.tetrode)

    def __str__(self):
        objstr = ''
        for indc in range(self.nClusters):
            objstr += 'c%d  %s\n'%(indc,str(self.clusters[indc].bounds))
        return objstr

    def bounds(self,clusterID):
        return wc.clusters[clusterID].bounds

    def load_data(self,animalName,ephysSession,tetrode):
        print 'Loading data...'
        self.dataTT = loadopenephys.DataSpikes(self.tetrodeFile) #,readWaves=True)
        self.nSpikes = self.dataTT.nRecords# FIXME: this is specific to the OpenEphys format
        self.dataTT.samples = self.dataTT.samples.astype(float)-2**15# FIXME: this is specific to OpenEphys
        print 'Aligning to peak...'
        self.dataTT.samples = spikesorting.align_waveforms(self.dataTT.samples)
        # FIXME: This assumes the gain is the same for all channels and records
        self.dataTT.samples = (1000.0/self.dataTT.gain[0,0]) * self.dataTT.samples
        self.dataTT.timestamps = self.dataTT.timestamps/self.dataTT.samplingRate
        # -- Load clusters if required --
        self.clustersFile = os.path.join(self.clustersDir,'Tetrode%d.clu.1'%tetrode)
        if os.path.isfile(self.clustersFile):
            self.dataTT.set_clusters(self.clustersFile)
            self.assign_clusters()
        else:
            print('Clusters file does not exist for this tetrode: {0}'.format(self.clustersFile))
        self.set_attributes()

    def assign_clusters(self):
        self.nClusters = np.max(self.dataTT.clusters)
        for clusterID in range(self.nClusters):
            spikesBool = self.dataTT.clusters==(clusterID+1)
            oneCluster = Cluster(self.dataTT,spikesBool)
            self.clusters.append(oneCluster)

    def set_data(self,dataTT):
        self.dataTT = dataTT
        self.set_attributes()

    def set_attributes(self):
        self.nSpikes = len(self.dataTT.timestamps)
        self.notInClusterBool = np.ones(self.nSpikes,dtype=bool)

    def plot_waveforms(self,nTraces=100,exclude=[]):
        if len(exclude)==0:
            spikesToPlot = np.random.randint(self.nSpikes,size=nTraces)
        else:
            spkSubset = flatnonzero(self.spikes_subset(exclude=exclude))
            spikesToPlot = spkSubset[np.random.randint(len(spkSubset),size=nTraces)]
        hold(True)
        hp = plot(self.dataTT.samples[spikesToPlot,self.channel,:].T,color='0.5',lw=0.5)
        hold(False)
        title('Channel %d'%self.channel)    
        show()
        return hp

    def toggle(self,clusterID):
        '''
        NEEDS FIXING  (hp does not exist in this scope)
        '''
        if hp[clusterID][0].get_visible():
            setp(hp[clusterID],visible=0)
        else:
            setp(hp[clusterID],visible=1)
        draw() 

    '''
    def plot_waveforms_allchannels(self,channelsToPlot=range(4),nspikes=40):
        spikesToPlot = spikeInds[np.random.randint(len(spikeInds),size=nspikes)]
        clf()
        fig, axs = plt.subplots(1, len(channelsToPlot), sharex=True, sharey=True, num=1)
        if not isinstance(axs,list):
            axs = [axs]
        for indp,indchan in enumerate(channelsToPlot):
            axes(axs[indp])
            plot(dataTT.samples[spikesToPlot,indchan,:].T,color='0.5',lw=0.5)
        hold(False)    
        show()
        return axs
    '''

    def set_channel(self,channel):
        self.channel = channel

    def add_cluster(self,bounds=[]):
        self.clusters.append(Cluster(self.dataTT))
        self.nClusters += 1
        if len(bounds)>0:
            for onebound in bounds:
                self.clusters[-1].set_bound(onebound)
            self.clusters[-1].find_spikes() ##### Maybe it should go somewhere else
            self.set_clusters_bool()
        self.activeCluster = self.nClusters-1

    def set_active_cluster(self,clusterID):
        self.activeCluster = clusterID
        self.activeSpikes = (self.dataTT.clusters==clusterID)

    def add_bound(self,clusterID=None):
        if clusterID is None:
            clusterID = self.activeCluster
        else:
            clusterID = clusterID
        self.clusters[clusterID].add_bound(self.channel)
        self.clusters[clusterID].find_spikes() ##### Maybe it should go somewhere else
        self.set_clusters_bool()

    def plot_cluster_waveforms(self,clusterID,nTraces=100,color='k'):
        hp = self.clusters[clusterID].plot_waveforms(self.channel,nTraces=nTraces,color=color)
        title('Channel %d'%self.channel)    
        return hp

    def show_report(self):
        self.find_cluster_each_spike()
        self.dataTT.set_clusters(self.clusterEachSpike)
        spikesorting.ClusterReportFromData(self.dataTT,nrows=self.nClusters+1)

    def show_report_onecluster(self,clusterID):
        figure()
        subplot(1,2,1)
        self.clusters[clusterID].plot_isi()
        subplot(1,2,2)
        self.clusters[clusterID].plot_events_in_time()
        show()

    def align_to_peak(self):
        nSpikes = len(self.dataTT.timestamps)
        maxIndEachChannel = np.argmax(self.dataTT.samples,axis=1)
        maxValEachChannel = np.max(self.dataTT.samples,axis=1) # Inefficient
        #maxValEachChannel = dataTT.samples[0,:,:][(maxIndEachChannel[0,:],range(473828))]
        maxChannelInd = np.argmax(maxValEachChannel,axis=0)
        posOfMax = maxIndEachChannel[(maxChannelInd,range(self.nSpikes))]
        nShift = 7 - posOfMax  ### HARDCODED
        print('Aligning to peak, please wait...')
        for inds in range(self.nSpikes):  # It takes >10sec
            self.dataTT.samples[inds,:,:] = np.roll(self.dataTT.samples[inds,:,:],nShift[inds],axis=1)

    def OLDfind_cluster_each_spike(self):
        '''
        Note that assignment to clusters is made backwards, so if one spike fits in two
        clusters it will be assigned to the one created first.
        '''
        self.clusterEachSpike = -np.ones(self.nSpikes,dtype=uint)
        for indc,onecluster in enumerate(reversed(self.clusters)):
            self.clusterEachSpike[onecluster.spikesInds] = self.nClusters-indc-1

    def find_cluster_each_spike(self):
        '''
        Note that assignment to clusters is made backwards, so if one spike fits in two
        clusters it will be assigned to the one created first.
        '''
        self.clusterEachSpike = np.zeros(self.nSpikes,dtype=uint) # Default is cluster 0
        for indc,onecluster in enumerate(reversed(self.clusters)):
            self.clusterEachSpike[onecluster.spikesInds] = self.nClusters-indc-1

    def set_clusters_bool(self):
        self.clustersBool = []
        for indc,onecluster in enumerate(self.clusters):
            self.clustersBool.append(onecluster.spikesBool)
            self.notInClusterBool = self.notInClusterBool & ~onecluster.spikesBool

    def spikes_subset(self,exclude=[]):
        spikesSubset = self.notInClusterBool
        for indc,onecluster in enumerate(self.clusters):
            if indc in exclude:
                continue
            else:
                spikesSubset = spikesSubset | onecluster.spikesBool
        return spikesSubset

    def save_clusters(self,confirm=True):
        '''
        Save text file (following KK convention)
        First item is how many clusters. Then nSpikes numbers with the cluster for each spikes.
        (in the files indices start with 1)
        '''
        #self.outputFile = self.clustersFile[:-1]+'0'
        #self.outputFile = '/tmp/clu.0'
        #self.outputFile = self.clustersFile
        self.outputFile = os.path.join(self.clustersDir,'Tetrode%d.clu.2'%self.tetrode)    
        if os.path.exists(self.outputFile):
            if confirm:
                ovwr = raw_input('Overwrite file? [y/n]  ')
                if ovwr!='y':
                    print 'Nothing was saved'
                    return
        print 'Saving clusters to %s'%self.outputFile
        self.find_cluster_each_spike()
        dataToSave = np.concatenate(([self.nClusters],self.clusterEachSpike+1))
        np.savetxt(self.outputFile, dataToSave, fmt="%d")

    def update_plot(self):
        clf()
        ax1 = subplot(1,2,1)
        self.plot_waveforms(200,exclude=range(self.nClusters))
        ax2 = subplot(1,2,2,sharey=ax1)
        colorEach = ['b','g','r','m','c','k','y','g','r','y','c','m']
        hp = self.nClusters*[0]
        for indc in range(self.nClusters):
            hp[indc] = self.plot_cluster_waveforms(indc,nTraces=100,color=colorEach[indc])
        show()
        axes(ax1)
        return hp

    def backup_orig_clusters(self):
        cmdFormat = 'rsync -a %s %s'
        origFile = self.clustersFile
        backupFile = origFile+'.orig'
        fullCommand = cmdFormat%(origFile,backupFile)
        print 'Executing: %s'%fullCommand
        os.system(fullCommand)


class Boundary(object):
    def __init__(self,channel,xval,yvals):
        self.channel = channel
        self.xval = xval
        self.yvals = yvals
    def __str__(self):
        return 'Ch:%d  x=%d  y=(%0.2f,%0.2f)'%(self.channel,self.xval,self.yvals[0],self.yvals[1])
    def __repr__(self):
        return 'Boundary(%d,%d,(%0.2f,%0.2f))'%(self.channel,self.xval,self.yvals[0],self.yvals[1])


class Cluster(object):
    def __init__(self,dataTT,spikesBool=None):
        self.dataTT = dataTT
        self.nTotalSpikes = len(self.dataTT.timestamps)
        if spikesBool is None:
            self.spikesBool = np.zeros(self.nTotalSpikes,dtype=bool)
        else:
            self.spikesBool = spikesBool
        self.spikesInds = np.flatnonzero(self.spikesBool) #np.empty(0,dtype=int)
        self.nSpikes = len(self.spikesInds)
        self.bounds = [] # Array of bounds of the form (x,[y1,y2])
    def set_bound(self,bound):
        self.bounds.append(bound)
    def add_bound(self,channel):
        '''Asks for clicks to define a bound (chan, x,[y1,y2])'''
        print('Click two points (same x position) to define boundary')
        lims = np.array(ginput(2))
        xvals = int(round(np.mean(lims[:,0])))
        yvals = np.sort(lims[:,1])
        self.bounds.append(Boundary(channel,xvals,yvals))
    def spikes_in_bound(self,bound):
        '''
        bound: (x,[y1,y2])
        selectedChannel is a global so far
        '''
        selectedSpikes = (self.dataTT.samples[:,bound.channel,bound.xval]>bound.yvals[0]) & \
                         (self.dataTT.samples[:,bound.channel,bound.xval]<bound.yvals[1])
        return selectedSpikes
    def find_spikes(self):
        '''
        Finds all spikes that fall within it.
        '''
        # FIXME: No need to re-do the whole thing everytime a new bound is set!
        #self.spikesBool = np.ones(self.nTotalSpikes,dtype=bool)
        for onebound in self.bounds:
            selectedSpikes = self.spikes_in_bound(onebound)
            self.spikesBool = self.spikesBool & selectedSpikes
        self.spikesInds = np.flatnonzero(self.spikesBool)
        self.nSpikes = len(self.spikesInds)
        print(self.bounds)
        print(self.nSpikes)
    def plot_waveforms(self,channel,nTraces=40,color='k'):
        spikesToPlot = self.spikesInds[np.random.randint(self.nSpikes,size=nTraces)]
        hold(True)
        hp = plot(self.dataTT.samples[spikesToPlot,channel,:].T,color=color,lw=0.5)
        hold(False)
        return hp
    def plot_isi(self):
        (hp,ISIhistogram,ISIbins) = spikesorting.plot_isi_loghist(self.dataTT.timestamps[self.spikesInds])
    def plot_events_in_time(self):
        hp = spikesorting.plot_events_in_time(self.dataTT.timestamps[self.spikesInds])

"""
def load_waveforms():
    animalName   = 'saja125'
    #ephysSession = '2012-01-30_14-54-07'
    ephysSession = '2012-01-31_15-26-57'
    tetrode = 2

    dataDir = os.path.join(settings.EPHYS_PATH,'%s/%s/'%(animalName,ephysSession))
    clustersDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(animalName,ephysSession))

    # -- Load spikes --
    tetrodeFile = os.path.join(dataDir,'TT%d.ntt'%tetrode)
    dataTT = loadneuralynx.DataTetrode(tetrodeFile,readWaves=True)
    #dataTT.timestamps = dataTT.timestamps.astype(np.float64)*1e-6  # in sec
    #wavesEachSpike = dataTT.samples.reshape((N_CHANNELS,SAMPLES_PER_SPIKE,-1),order='F')
    dataTT.samples = dataTT.samples.reshape((N_CHANNELS,SAMPLES_PER_SPIKE,-1),order='F')

    # -- Load clusters if required --
    clustersFile = os.path.join(clustersDir,'TT%d.clu.1'%tetrode)
    dataTT.set_clusters(clustersFile)
    return dataTT

def plot_all(dataTT,channelsToPlot,nspikes=40):
    spikesToPlot = spikeInds[np.random.randint(len(spikeInds),size=nspikes)]
    clf()
    fig, axs = plt.subplots(1, len(channelsToPlot), sharex=True, sharey=True, num=1)
    if not isinstance(axs,list):
        axs = [axs]
    for indp,indchan in enumerate(channelsToPlot):
        axes(axs[indp])
        plot(dataTT.samples[indchan,:,spikesToPlot].T,color='0.5',lw=0.5)
    hold(False)    
    draw()
    show()
    return axs

def plot_selected(dataTT,selectedSpikesBool,nspikes=40,color='k'):
    '''So far it allows only one channel '''
    spikeInds = np.flatnonzero(selectedSpikesBool)
    spikesToPlot = spikeInds[np.random.randint(len(spikeInds),size=nspikes)]
    hold(True)
    hp = plot(wavesEachSpike[indchan,:,spikesToPlot].T,color=color,lw=1)
    hold(False)
    return hp

def get_bound():
    '''Returns a bound (x,[y1,y2])'''
    print('Click two points (same x position) to define boundary')
    lims = np.array(ginput(2))
    xvals = int(round(np.mean(lims[:,0])))
    yvals = np.sort(lims[:,1])
    return (xvals,yvals)

def spikes_in_bound(dataTT,bound):
    '''
    bound: (x,[y1,y2])
    selectedChannel is a global so far
    '''
    selectedSpikes = (dataTT.samples[selectedChannel,bound[0],:]>bound[1][0]) & \
                     (dataTT.samples[selectedChannel,bound[0],:]<bound[1][1])
    return selectedSpikes

def spikes_in_bounds(dataTT,bounds):
    spikesAllConditions = np.ones(len(dataTT.timestamps),dtype=bool)
    for onebound in bounds:
        selectedSpikes = spikes_in_bound(dataTT,onebound)
        spikesAllConditions = spikesAllConditions & selectedSpikes
    return spikesAllConditions

def addbound(selspikes):
    if len(selspikes)==0:
        plot_all(dataTT,channelsToPlot)
        selspikes = np.ones(len(dataTT.timestamps),dtype=bool)
    else:
        plot_all(dataTT,channelsToPlot)
        plot_selected(dataTT,selspikes)
    bound = get_bound()
    moreSelSpikes = spikes_in_bound(dataTT,bound)
    newSelSpikes = selspikes & moreSelSpikes
    hp=plot_selected(dataTT,newSelSpikes,color='b')
    return newSelSpikes
"""

# ---------------------------------------------------------- #

if __name__ == "__main__":
    animalName   = 'test089'
    ephysSession = '2015-08-21_16-16-16'
    tetrode = 2
    wc = WaveformCutterSession(animalName,ephysSession,tetrode)
    dataTT = wc.dataTT

    wc.set_channel(0)
    wc.set_active_cluster(10)

    '''
    # -- Add cluster/bound graphically --
    wc.add_cluster()
    wc.add_bound(0)
    '''

    clf()
    #wc.plot_waveforms(200)
    clf();wc.plot_cluster_waveforms(11-1,200)
    # wc.show_report_onecluster(11-1)

    #[Boundary(0,8,(-378.01,-268.72))]

    show()
    sys.exit()

    wc.add_cluster([Boundary(0,8,(-282.10,-82.51))])
    wc.plot_cluster_waveforms(0)
    # wc.show_report_onecluster(0)

    '''
    # -- Add cluster from code (T2) --
    wc.add_cluster([Boundary(3,11,(-21000,-7900)), Boundary(3,15,(-4100,7500))])
    wc.add_cluster([Boundary(3,11,(-11000,-1500)), Boundary(3,14,(-11635,-3730)),
                    Boundary(3,15,(-10700,-3160)), Boundary(3,7,(8000,23500))])
    wc.add_cluster([Boundary(3,7,(6000,13500)), Boundary(3,4,(-12800,-1760))])
    # -- Add cluster from code (T8) --
    wc.add_cluster([Boundary(0,7,(-11859.66,-1928.68)), Boundary(0,11,(3734.66,18075.15))])
    wc.add_cluster([Boundary(0,12,(-10500,2047.55)), Boundary(0,7,(3734.66,25000))])
    wc.add_cluster([Boundary(0,7,(-13649.03,-765.59)), Boundary(0,11,(-2332.85,5637.11)),
                    Boundary(0,12,(-2645.71,6326.69))])

    '''
    #wc.plot_cluster_waveforms(0)
    #wc.set_clusters_bool()

 


    figure(1)
    clf()
    ax1 = gca()
    #wc.plot_waveforms(200)
    wc.plot_waveforms(200,exclude=range(wc.nClusters)); draw()
    show()

    figure(2)
    clf()
    ax2 = axes(sharey=ax1)
    colorEach = ['b','g','r','y','c','m']
    hp = wc.nClusters*[0]
    for indc in range(wc.nClusters):
        hp[indc] = wc.plot_cluster_waveforms(indc,nTraces=100,color=colorEach[indc])

    draw()
    show()

    #wc.save_clusters()

    # wc.clusters[0].bounds
    # wc.clusters[0].spikesBool
    #sum(wc.clusters[0].spikesBool)


    '''
    clu = Cluster(wc.dataTT)
    clu.add_bound(wc.channel)
    clu.find_spikes()
    clu.plot_waveforms(wc.channel)

    clu.spikes_in_bound(wc.channel
    '''


