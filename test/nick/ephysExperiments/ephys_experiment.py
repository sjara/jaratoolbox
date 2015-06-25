from jaratoolbox import celldatabase
from jaratoolbox import settings
from jaratoolbox import spikesanalysis
from jaratoolbox import spikesorting
from jaratoolbox import loadbehavior
from jaratoolbox import loadopenephys
import os
import subprocess
from pylab import *
import numpy as np


class EphysExperiment(object):

    def __init__(self, animalName, date, experimenter='nick', serverUser='jarauser', serverName='jarahub', serverBehavPathBase='/data/behavior'):
        self.animalName = animalName
        self.date = date
        self.serverUser = serverUser
        self.serverName = serverName
        self.serverBehavPathBase = serverBehavPathBase
        self.experimenter = experimenter
        self.serverBehavPath = os.path.join(self.serverBehavPathBase, self.experimenter, self.animalName)
        self.remoteBehavLocation = '{0}@{1}:{2}'.format(self.serverUser, self.serverName, self.serverBehavPath)
        self.localBehavPath = os.path.join(settings.BEHAVIOR_PATH, self.experimenter)
        self.localEphysDir = os.path.join(settings.EPHYS_PATH, self.animalName)

    def getBehavior(self):
        transferCommand = ['rsync', '-a', '--progress', self.remoteBehavLocation, self.localBehavPath]
        print ' '.join(transferCommand)
        subprocess.call(transferCommand)

    def plot_raster(self, session, replace=0, SAMPLING_RATE = 30000.0, timeRange = [-0.5, 1], numTetrodes=4, tetrodeIDs=[3,4,5,6]):
        
        if isinstance(session, str):
            ephysDir=os.path.join(self.localEphysDir, session)
        else: 
            ephysRoot= self.localEphysDir
            lastSession=sort(os.listdir(ephysRoot))[session]
            ephysDir=os.path.join(ephysRoot, lastSession)

        event_filename=os.path.join(ephysDir, 'all_channels.events')

        #Load event data and convert event timestamps to ms
        ev=loadopenephys.Events(event_filename)
        eventTimes=np.array(ev.timestamps)/SAMPLING_RATE
        evID=np.array(ev.eventID)
        evChannel = np.array(ev.eventChannel)
        eventOnsetTimes=eventTimes[(evID==1)&(evChannel==0)]

        evdiff = np.r_[1.0, np.diff(eventOnsetTimes)]
        eventOnsetTimes=eventOnsetTimes[evdiff>0.5]

        if replace:
            clf()
        else:
            figure()

        for ind , tetrodeID in enumerate(tetrodeIDs):
            spike_filename=os.path.join(ephysDir, 'Tetrode{0}.spikes'.format(tetrodeID))
            sp=loadopenephys.DataSpikes(spike_filename)
            try:
                spkTimeStamps=np.array(sp.timestamps)/SAMPLING_RATE
                (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial) = spikesanalysis.eventlocked_spiketimes(spkTimeStamps,eventOnsetTimes,timeRange)

                subplot(numTetrodes,1,ind+1)

                plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.', ms=1)
                axvline(x=0, ymin=0, ymax=1, color='r')
                if ind == 0:
                    title(ephysDir)
                #title('Channel {0} spikes'.format(ind+1))
            except AttributeError:  #Spikes files without any spikes will throw an error
                pass

        xlabel('time(sec)')
        #tight_layout()
        draw()
        show()

    def cluster_session(self, session, tetrode):
            
        if isinstance(session, str):
            ephysSession = session
        else:
            ephysRoot = self.localEphysDir
            ephysSession = sort(os.listdir(ephysRoot))[session]

        oneTT = spikesorting.TetrodeToCluster(self.animalName,ephysSession,tetrode)

        oneTT.load_waveforms()
        oneTT.create_fet_files()
        oneTT.run_clustering()
        oneTT.save_report()

    def plot_clustered_raster(self, session, tetrode, clustersToPlot):

        if isinstance(session, str):
            ephysSession = session
        else:
            ephysRoot = self.localEphysDir
            ephysSession = sort(os.listdir(ephysRoot))[session]

        animalName = self.animalName
        SAMPLING_RATE = 30000.0
        timeRange = [-0.5, 1] #FIXME: These should be object methods, not just specific to this function
        spike_filename=os.path.join(settings.EPHYS_PATH, animalName, ephysSession, 'Tetrode{0}.spikes'.format(tetrode))
        sp=loadopenephys.DataSpikes(spike_filename)
        clustersDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(animalName,ephysSession))
        clustersFile = os.path.join(clustersDir,'Tetrode%d.clu.1'%tetrode)
        sp.set_clusters(clustersFile)
        event_filename=os.path.join(settings.EPHYS_PATH, animalName, ephysSession, 'all_channels.events')
        ev=loadopenephys.Events(event_filename)

        eventTimes=np.array(ev.timestamps)/SAMPLING_RATE
        evID=np.array(ev.eventID)
        evChannel = np.array(ev.eventChannel)
        eventOnsetTimes=eventTimes[(evID==1)&(evChannel==0)]


        evdiff = np.r_[1.0, np.diff(eventOnsetTimes)]
        eventOnsetTimes=eventOnsetTimes[evdiff>0.5]

        #Already divided by the sampling rate in spikesorting
        allSpkTimestamps = np.array(sp.timestamps)/SAMPLING_RATE
        #allSpkTimestamps = np.array(oneTT.dataTT.timestamps)
        spkClusters = sp.clusters

        clf()
        for ind, clusterNum in enumerate(clustersToPlot):
            clusterspikes = allSpkTimestamps[spkClusters==clusterNum]

            spkTimeStamps = clusterspikes


            (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial) = spikesanalysis.eventlocked_spiketimes(spkTimeStamps,eventOnsetTimes,timeRange)

            subplot(len(clustersToPlot), 1, ind+1)

            plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.', ms=1)
            title('Cluster {}'.format(clusterNum))
            axvline(x=0, ymin=0, ymax=1, color='r')

        xlabel('Time (sec)')
        #tight_layout()
        draw()
        show()
