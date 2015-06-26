from jaratoolbox import celldatabase
from jaratoolbox import settings
from jaratoolbox import spikesanalysis
from jaratoolbox import spikesorting
from jaratoolbox import loadbehavior
from jaratoolbox import loadopenephys
from collections import defaultdict
import os
import subprocess
from pylab import *
import numpy as np


class EphysExperiment(object):

    def __init__(self, animalName, date, experimenter='nick', serverUser='jarauser', serverName='jarahub', serverBehavPathBase='/data/behavior', paradigm='laser_tuning_curve'):
        self.SAMPLING_RATE = 30000.0
        self.animalName = animalName
        self.date = date
        self.paradigm=paradigm
        self.serverUser = serverUser
        self.serverName = serverName
        self.serverBehavPathBase = serverBehavPathBase
        self.experimenter = experimenter
        self.serverBehavPath = os.path.join(self.serverBehavPathBase, self.experimenter, self.animalName)
        self.remoteBehavLocation = '{0}@{1}:{2}'.format(self.serverUser, self.serverName, self.serverBehavPath)
        self.localBehavPath = os.path.join(settings.BEHAVIOR_PATH, self.experimenter)
        self.localEphysDir = os.path.join(settings.EPHYS_PATH, self.animalName)
        self.behavFileBaseName = '_'.join([self.animalName, self.paradigm, ''.join(self.date.split('-'))])

    def getBehavior(self):
        transferCommand = ['rsync', '-a', '--progress', self.remoteBehavLocation, self.localBehavPath]
        print ' '.join(transferCommand)
        subprocess.call(transferCommand)

    def get_session_ephys_data(self, session, tetrode, convert_to_seconds=True):
        '''
        Method to retrieve the ephys data for a session/tetrode. Automatically loads the 
        clusters if clustering has been done for the session

        '''
        
        SAMPLING_RATE = 30000.0

        if isinstance(session, str):
            ephysSession = session
        else:
            ephysRoot = self.localEphysDir
            ephysSession = sort(os.listdir(ephysRoot))[session]

        ephysDir=os.path.join(self.localEphysDir, ephysSession)
        plotTitle = ephysDir
        event_filename=os.path.join(ephysDir, 'all_channels.events')

        eventData=loadopenephys.Events(event_filename)

        spikeFilename = os.path.join(ephysDir, 'Tetrode{}.spikes'.format(tetrode))
        spikeData = loadopenephys.DataSpikes(spikeFilename)
        
        if convert_to_seconds:
            spikeData.timestamps = spikeData.timestamps/SAMPLING_RATE
        
        #If clustering has been done for the tetrode, add the clusters to the spikedata object
        clustersDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(self.animalName,ephysSession))
        clustersFile = os.path.join(clustersDir,'Tetrode%d.clu.1'%tetrode)
        if os.path.isfile(clustersFile):
            spikeData.set_clusters(clustersFile)

        return spikeData, eventData, plotTitle
        
    def get_event_onset_times(self, eventData):
        '''
        Crappy method. Needs work. Takes an Events object and gives you the event onset times. 
        Returns the event times divided by the sampling rate, so they are in seconds. 
        '''
        
        evID=np.array(eventData.eventID)
        evChannel = np.array(eventData.eventChannel)

        eventTimes=np.array(eventData.timestamps)/self.SAMPLING_RATE
        eventOnsetTimes=eventTimes[(evID==1)&(evChannel==0)]
        evdiff = np.r_[1.0, np.diff(eventOnsetTimes)]
        eventOnsetTimes=eventOnsetTimes[evdiff>0.5]
        
        return eventOnsetTimes
                                              

    def get_session_behav_data(self, session, behavFileIdentifier):
        behaviorDir=os.path.join(self.localBehavPath, self.animalName)
        fullBehavFilename = ''.join([self.behavFileBaseName, behavFileIdentifier, '.h5'])
        behavDataFileName=os.path.join(behaviorDir, fullBehavFilename)

        #Extract the frequency presented each trial from the behavior data
        bdata = loadbehavior.BehaviorData(behavDataFileName,readmode='full')

        return bdata

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

    def plot_session_raster(self, session, tetrode, cluster = None, replace=0):
        spikeData, eventData, plotTitle= self.get_session_ephys_data(session, tetrode)
        eventOnsetTimes = self.get_event_onset_times(eventData)
        spikeTimestamps=spikeData.timestamps
        
        if cluster:
            spikeTimestamps = spikeTimestamps[spikeData.clusters==cluster]
        
        self.plot_raster(spikeTimestamps, eventOnsetTimes, plotTitle, replace)
        
    def plot_raster(self, spikeTimestamps, eventOnsetTimes, plotTitle, replace = 0, timeRange = [-0.5, 1]):
        
        if replace:
            clf()
        else:
            figure()

        spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(spikeTimeStamps,eventOnsetTimes,timeRange)
        plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.', ms=1)
        axvline(x=0, ymin=0, ymax=1, color='r')
        title(plotTitle)


    def plot_array_raster(self, session, replace=0, SAMPLING_RATE = 30000.0, timeRange = [-0.5, 1], numTetrodes=4, tetrodeIDs=[3,4,5,6]):
        
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

        figure()
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
    
    def plot_tc_raster(self, session, tetrode, behavFileIdentifier, cluster=None):
        '''
        Watch out - uses spike timestamps in samples and event timestamps in seconds...
        '''
        if isinstance(session, str):
            ephysSession = session
        else:
            ephysRoot = self.localEphysDir
            ephysSession = sort(os.listdir(ephysRoot))[session]

        ephysDir=os.path.join(self.localEphysDir, ephysSession)
        behaviorDir=os.path.join(self.localBehavPath, self.animalName)
        fullBehavFilename = ''.join([self.behavFileBaseName, behavFileIdentifier, '.h5'])
        behavDataFileName=os.path.join(behaviorDir, fullBehavFilename)
        event_filename=os.path.join(ephysDir, 'all_channels.events')
        spike_filename=os.path.join(ephysDir, 'Tetrode{}.spikes'.format(tetrode))
        
    def plot_tc_psth(self, session, tetrode, behavFileIdentifier, cluster=None):
        
        SAMPLING_RATE = 30000.0
        PLOTTING_WINDOW = 0.1 #Window to plot, in seconds
        
        if isinstance(session, str):
            ephysSession = session
        else:
            ephysRoot = self.localEphysDir
            ephysSession = sort(os.listdir(ephysRoot))[session]

        ephysDir=os.path.join(self.localEphysDir, ephysSession)
        event_filename=os.path.join(ephysDir, 'all_channels.events')

        behaviorDir=os.path.join(self.localBehavPath, self.animalName)
        fullBehavFilename = ''.join([self.behavFileBaseName, behavFileIdentifier, '.h5'])
        behavDataFileName=os.path.join(behaviorDir, fullBehavFilename)

        #Extract the frequency presented each trial from the behavior data
        bdata = loadbehavior.BehaviorData(behavDataFileName,readmode='full')
        freqEachTrial = bdata['currentFreq']
        intensityEachTrial = bdata['currentIntensity']

        possibleFreq = np.unique(freqEachTrial) 
        possibleIntensity = np.unique(intensityEachTrial)

        #Get the event timestamps from openEphys
        ev=loadopenephys.Events(event_filename)
        evID=np.array(ev.eventID)
        eventOnsetTimes=ev.timestamps[evID==1] #The timestamps of all of the stimulus onsets

        tetrode = 6 #The tetrode to plot
        spikeFilename = os.path.join(ephysDir, 'Tetrode{}.spikes'.format(tetrode))
        spikeData = loadopenephys.DataSpikes(spikeFilename)
        
        if cluster:
            clustersDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(self.animalName,ephysSession))
            clustersFile = os.path.join(clustersDir,'Tetrode%d.clu.1'%tetrode)
            spikeData.set_clusters(clustersFile)

            spikeTimestamps = spikeData.timestamps[spikeData.clusters==cluster]
        else:
            spikeTimestamps = spikeData.timestamps
            


        allSettingsSpikes = defaultdict(dict) #2D dictionary to hold the spiketimes arrays organized by frequency and intensity

        for indFreq, currentFreq in enumerate(possibleFreq):
            for indIntensity, currentIntensity in enumerate(possibleIntensity):

                #Determine which trials this setting was presented on. 
                trialsThisSetting = np.flatnonzero((freqEachTrial == currentFreq) & (intensityEachTrial == currentIntensity))

                #Get the onset timestamp for each of the trials of this setting. 
                timestampsThisSetting = eventOnsetTimes[trialsThisSetting]

                spikesAfterThisSetting = np.array([])
                #Loop through all of the trials for this setting, extracting the trace after each presentation
                for indts, eventTimestamp in enumerate(timestampsThisSetting):
                    spikes = spikeTimestamps[(spikeTimestamps >= eventTimestamp) & (spikeTimestamps <= eventTimestamp + SAMPLING_RATE * PLOTTING_WINDOW)]
                    spikes = spikes - eventTimestamp
                    spikes = spikes / 30 #Spikes in ms after the stimulus

                    spikesAfterThisSetting = np.concatenate((spikesAfterThisSetting, spikes))
                allSettingsSpikes[indFreq][indIntensity] = spikesAfterThisSetting #Put the spikes into the 2d dict
        figure()

        maxBinCount = []
        for indI, intensity in enumerate(possibleIntensity):
            for indF, frequency in enumerate(possibleFreq):
                h, bin_edges = histogram(allSettingsSpikes[indF][indI]) #Dict is ordered by freq and then by Int.
                maxBinCount.append(max(h))

        maxNumSpikesperBin = max(maxBinCount)

        for intensity in range(len(possibleIntensity)):
            #Subplot2grid plots from top to bottom, but we need to plot from bottom to top
            #on the intensity scale. So we make an array of reversed intensity indices.
            intensPlottingInds = range(len(possibleIntensity))[::-1]
            for frequency in range(len(possibleFreq)):
                if (intensity == len(possibleIntensity) - 1) & (frequency == len(possibleFreq) -1):
                    ax2 = subplot2grid((len(possibleIntensity), len(possibleFreq)), (intensPlottingInds[intensity], frequency))
                    if len(allSettingsSpikes[frequency][intensity]) is not 0:
                        ax2.hist(allSettingsSpikes[frequency][intensity])
                    else:
                        pass

                    ax2.set_ylim([0, maxNumSpikesperBin])
                    ax2.get_xaxis().set_ticks([])
                else:
                    ax = subplot2grid((len(possibleIntensity), len(possibleFreq)), (intensPlottingInds[intensity], frequency))
                    if len(allSettingsSpikes[frequency][intensity]) is not 0:
                        ax.hist(allSettingsSpikes[frequency][intensity])
                    else:
                        pass
                    ax.set_ylim([0, maxNumSpikesperBin])
                    ax.set_axis_off()

        def getXlabelpoints(n):
            rawArray = array(range(1, n+1))/float(n+1) #The positions in a perfect (0,1) world
            diffFromCenter = rawArray - 0.6
            partialDiffFromCenter = diffFromCenter * 0.175 #Percent change has to be determined empirically
            finalArray = rawArray - partialDiffFromCenter
            return finalArray

        #Not sure yet if similar modification to the locations will be necessary. 
        def getYlabelpoints(n):
            rawArray = array(range(1, n+1))/float(n+1) #The positions in a perfect (0,1) world
            return rawArray

        freqLabelPositions = getXlabelpoints(len(possibleFreq))
        for indp, position in enumerate(freqLabelPositions):
            figtext(position, 0.065, "%.1f"% (possibleFreq[indp]/1000), ha = 'center')

        intensLabelPositions = getYlabelpoints(len(possibleIntensity))
        for indp, position in enumerate(intensLabelPositions):
            figtext(0.075, position, "%d"% possibleIntensity[indp])

        figtext(0.525, 0.025, "Frequency (kHz)", ha = 'center')
        figtext(0.025, 0.5, "Intensity (dB SPL)", va = 'center', rotation = 'vertical')
        show()
        

            

    def plot_session_tc_heatmap(self, session, tetrode, behavFileIdentifier, cluster = None, norm=False):
        spikeData, eventData = self.get_session_ephys_data(session, tetrode)
        bdata = self.get_session_behav_data(session, behavFileIdentifier)
        eventOnsetTimes = self.get_event_onset_times(eventData)
        
        if cluster:
            spikeTimestamps = spikeTimestamps[spikeData.clusters==cluster]
        
        self.plot_tc_heatmap(spikeTimestamps, eventOnsetTimes, bdata, norm)

    def plot_tc_heatmap(self, spikeTimestamps, eventOnsetTimes, bdata, norm=False):
        
        '''
        Takes spikeTimestamps in SECONDS, eventOnsetTimes in SECONDS
        '''
        
        SAMPLING_RATE = 30000.0
        
        PLOTTING_WINDOW = 0.1 #Window to plot, in seconds

        freqEachTrial = bdata['currentFreq']
        intensityEachTrial = bdata['currentIntensity']

        possibleFreq = np.unique(freqEachTrial) 
        possibleIntensity = np.unique(intensityEachTrial)

        allSettingsSpikeCount = np.zeros([len(possibleIntensity), len(possibleFreq)]) 

        for indFreq, currentFreq in enumerate(possibleFreq):
            for indIntensity, currentIntensity in enumerate(possibleIntensity):

                #Determine which trials this setting was presented on. 
                trialsThisSetting = np.flatnonzero((freqEachTrial == currentFreq) & (intensityEachTrial == currentIntensity))

                #Get the onset timestamp for each of the trials of this setting. 
                timestampsThisSetting = eventOnsetTimes[trialsThisSetting]

                spikesAfterThisSetting = np.array([])
                #Loop through all of the trials for this setting, extracting the trace after each presentation
                for indts, eventTimestamp in enumerate(timestampsThisSetting):
                    spikes = spikeTimestamps[(spikeTimestamps >= eventTimestamp) & (spikeTimestamps <= eventTimestamp + PLOTTING_WINDOW)]
                    spikes = spikes - eventTimestamp
                    spikes = spikes / 30 #Spikes in ms after the stimulus

                    spikesAfterThisSetting = np.concatenate((spikesAfterThisSetting, spikes))
                    spikeCountThisSetting = len(spikesAfterThisSetting)
                allSettingsSpikeCount[indIntensity, indFreq] = spikeCountThisSetting
                
        if norm:
            allSettingsSpikeCount = allSettingsSpikeCount/allSettingsSpikeCount.max()
                
        fig = figure()
        ax = fig.add_subplot(111)
        ax.set_ylabel('Intensity (dB SPL)')
        ax.set_xlabel('Frequency (kHz)')
        cax = ax.imshow(np.flipud(allSettingsSpikeCount), interpolation='none', aspect='auto')
        cbar=colorbar(cax)
        if norm:
            cbar.ax.set_ylabel('Proportion of max firing')
        else:
            cbar.ax.set_ylabel('Spikes in 0.1sec after stim')
        ax.set_xticks(range(len(possibleFreq)))
        xticks = ["%.1f" % freq for freq in possibleFreq/1000.0]
        ax.set_xticklabels(xticks)
        ax.set_yticks([0, 1, 2, 3])
        
        ax.set_yticklabels(possibleIntensity)

class RecordingSite(object):

    def __init__(self,
                 depth,
                 noiseburstEphysSession,
                 laserPulseEphysSession,
                 laserTrainEphysSession,
                 tuningCurveEphysSession,
                 tuningCurveBehavIdentifier,
                 bfEphysSession,
                 bfBehavIdentifier,
                 laserPulseEphysSession3mW,
                 laserPulseEphysSession1mW,
                 goodTetrodes):

        self.depth = depth
        self.noiseburstephyssession = noiseburstephyssession
        self.laserPulseEphysSession = laserPulseEphysSession
        self.laserTrainEphysSession = laserTrainEphysSession
        self.tuningCurveEphysSession = tuningCurveEphysSession
        self.tuningCurveBehavIdentifier = tuningCurveBehavIdentifier
        self.bfEphysSession = bfEphysSession
        self.bfBehavIdentifier = bfBehavIdentifier
        self.laserPulseEphysSession3mW = laserPulseEphysSession3mW
        self.laserPulseEphysSession1mW = laserPulseEphysSession1mW
        self.goodTetrodes = goodTetrodes


        
