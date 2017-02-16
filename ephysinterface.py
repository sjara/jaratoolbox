'''
2016-08-29 Nick Ponvert and Anna Lakunina

This module will provide a frontend for plotting data during an ephys experiment

The job of the module will be to take session names, get the data, and then pass the data to the correct plotting function
'''

import os
import imp
from jaratest.nick.database import dataloader_v2 as dataloader
from jaratest.nick.database import dataplotter
reload(dataplotter)
reload(dataloader)
import numpy as np
from matplotlib import pyplot as plt
import functools
from jaratoolbox import extraplots
from jaratoolbox import spikesanalysis
from jaratoolbox import spikesorting
from jaratoolbox import behavioranalysis

class EphysInterface(object):

    def __init__(self, filepath):

        self.filepath = filepath
        self.inforec = self.load_inforec()
        self.loader = dataloader.DataLoader(self.inforec.subject)

    def load_inforec(self):
        inforec = imp.load_source('module.name', self.filepath)
        return inforec

    def get_colours(self, ncolours):
        ''' returns n distinct colours for plotting purpouses when you don't want to manually specify colours'''
        from matplotlib.pyplot import cm
        colours = cm.rainbow(np.linspace(0,1,ncolours))
        return colours

    def get_session_obj(self, session, experiment, site):

        '''
        Return the inforec session object - can be used to get ephys,
        behavior filenames and session types

        Args:
            session (int or str): Can be an integer index, to be used
                                  on the list of sessions for this site/experiment,
                                  or a string with the timestamp of the session.
            experiment (int): The index of the experiment to use
            site (int): The index of the site to use

        TODO: Allow date to be used to select experiment
        TODO: Allow depth to be used to select site
        '''

        self.inforec = self.load_inforec()
        #List of session objects and session ephys names for the specified experiment and site
        sessions = self.inforec.experiments[experiment].sites[site].sessions
        sessionNames = self.inforec.experiments[experiment].sites[site].session_ephys_dirs()
        if isinstance(session, int):
            #Do something with the session index
            sessionIndex = session #Use session as an index directly
        elif isinstance(session, str):
            #Get the session by name
            date = self.inforec.experiments[experiment].date
            session = '_'.join([date, session])
            sessionIndex = sessionNames.index(session)
        else:
            print "Unrecognized session format"
            pass
        sessionObj = sessions[sessionIndex] #Get the right session object
        return sessionObj

    def plot_session_raster(self, session, tetrode, experiment=-1, site=-1, cluster = None, sortArray = 'currentFreq', timeRange=[-0.5, 1], replace=0, ms=4, colorEachCond=None):
        ##  ---  ###
        #TODO: Use this to get the data for all the plots we do
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        if not behavFile:
            sortArray = []
        else:
            bdata = self.loader.get_session_behavior(behavFile)
            sortArray = bdata[sortArray]
        spikeData= self.loader.get_session_spikes(sessionDir, tetrode, cluster)
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        spikeTimestamps=spikeData.timestamps
        plotTitle = sessionDir
        ##  ---  ##
        if replace:
            plt.cla()
        else:
            plt.figure()
        dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = sortArray, timeRange=timeRange, ms=ms, colorEachCond=colorEachCond)

    def plot_session_PSTH(self, session, tetrode, experiment=-1, site=-1, cluster = None, sortArray = 'currentFreq', timeRange = [-0.5, 1], replace=0, lw=3, colorEachCond=None):
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        if not behavFile:
            sortArray = []
        else:
            bdata = self.loader.get_session_behavior(behavFile)
            sortArray = bdata[sortArray]
            if colorEachCond is None:
                colorEachCond = self.get_colours(len(np.unique(sortArray)))
        plotTitle = sessionDir
        spikeData= self.loader.get_session_spikes(sessionDir, tetrode, cluster)
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        spikeTimestamps=spikeData.timestamps
        if replace:
            plt.cla()
        else:
            plt.figure()
        dataplotter.plot_psth(spikeTimestamps, eventOnsetTimes, sortArray = sortArray, timeRange=timeRange, lw=lw, colorEachCond=colorEachCond, plotLegend=1)

    def plot_am_freq_tuning(self, freqsession, amsession, tetrode, experiment=-1, site=-1, freqTimeRange = [-0.1, 0.3], amTimeRange = [-0.2, 0.8], colorEachCond=None, replace=1, ms=1, lw=3):
        if replace:
            plt.cla()
        else:
            plt.figure()
        #FIXME: currently hardcoded for number of am rates Anna uses
        if colorEachCond is None:
            colorEachCond = self.get_colours(5)
        plt.subplot(221)
        self.plot_session_raster(amsession, tetrode, experiment, site, replace=1, timeRange=amTimeRange, ms=ms, colorEachCond=colorEachCond)
        plt.xlabel('Time from event onset (sec)')
        plt.ylabel('Modulation rate (Hz)')
        plt.subplot(223)
        self.plot_session_PSTH(amsession, tetrode, experiment, site, replace=1, timeRange=amTimeRange, lw=lw, colorEachCond=colorEachCond)
        plt.xlabel('Time from event onset (sec)')
        plt.ylabel('Firing rate (Hz)')
        plt.subplot(222)
        self.plot_session_raster(freqsession, tetrode, experiment, site, replace=1, timeRange=freqTimeRange, ms=ms)
        plt.xlabel('Time from event onset (sec)')
        plt.ylabel('Frequency (Hz)')
        plt.subplot(224)
        self.plot_session_freq_tuning(freqsession, tetrode, experiment, site, replace=1, timeRange=[0, 0.1])
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('Average number of spikes in range [0, 0.1]')
        plt.suptitle('TT{}'.format(tetrode))

    def plot_session_freq_tuning(self, session, tetrode, experiment = -1, site = -1, cluster = None, sortArray='currentFreq', replace=0, timeRange=[0,0.1]):
        if replace:
            plt.cla()
        else:
            plt.figure()
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        bdata = self.loader.get_session_behavior(behavFile)
        freqEachTrial = bdata[sortArray]
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        plotTitle = sessionDir
        freqLabels = ["%.1f"%freq for freq in np.unique(freqEachTrial)/1000]
        spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)
        spikeTimestamps = spikeData.timestamps
        dataplotter.one_axis_tc_or_rlf(spikeTimestamps, eventOnsetTimes, freqEachTrial, timeRange=timeRange)
        ax = plt.gca()
        ax.set_xticks(range(len(freqLabels)))
        ax.set_xticklabels(freqLabels, rotation='vertical')

    def plot_array_freq_tuning(self, session, experiment=-1, site=-1, tetrodes=None, replace=0, timeRange=[0, 0.1]):

        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        if not tetrodes:
            tetrodes=sessionObj.tetrodes
        numTetrodes = len(tetrodes)
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        plotTitle = sessionDir
        bdata=self.loader.get_session_behavior(behavFile)
        freqEachTrial = bdata['currentFreq']
        freqLabels = ["%.1f"%freq for freq in np.unique(freqEachTrial)/1000]

        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()


        for ind , tetrode in enumerate(tetrodes):

            spikeData = self.loader.get_session_spikes(sessionDir, tetrode)

            if ind == 0:
                ax = fig.add_subplot(numTetrodes,1,ind+1)
            else:
                ax = fig.add_subplot(numTetrodes,1,ind+1, sharex = fig.axes[0], sharey = fig.axes[0])

            spikeTimestamps = spikeData.timestamps
            dataplotter.one_axis_tc_or_rlf(spikeTimestamps, eventOnsetTimes, freqEachTrial, timeRange=timeRange)

            ax.set_xticks(range(len(freqLabels)))

            if ind == numTetrodes-1:
                ax.set_xticklabels(freqLabels, rotation='vertical')
                plt.xlabel('Frequency (kHz)')
            else:
                plt.setp(ax.get_xticklabels(), visible=False)


            plt.ylabel('TT {}'.format(tetrode))


        plt.figtext(0.05, 0.5, 'Average number of spikes in range {}'.format(timeRange), rotation='vertical', va='center', ha='center')
        plt.show()



    def plot_array_raster(self, session, experiment=-1, site=-1, tetrodes=None, replace=0, sortArray='currentFreq', timeRange = [-0.5, 1], ms=4, electrodeName='Tetrode'):
        '''
        This is the much-improved version of a function to plot a raster for each tetrode. All rasters
        will be plotted using standardized plotting code, and we will simply call the functions.
        In this case, we get the event data once, and then loop through the tetrodes, getting the
        spike data and calling the plotting code for each tetrode.
        '''
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        if not behavFile:
            sortArray = []
        else:
            bdata = self.loader.get_session_behavior(behavFile)
            sortArray = bdata[sortArray]
        if not tetrodes:
            tetrodes=sessionObj.tetrodes
        numTetrodes = len(tetrodes)
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        plotTitle = sessionDir
        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()
        for ind , tetrode in enumerate(tetrodes):
            spikeData = self.loader.get_session_spikes(sessionDir, tetrode)
            if ind == 0:
                ax = fig.add_subplot(numTetrodes,1,ind+1)
            else:
                ax = fig.add_subplot(numTetrodes,1,ind+1, sharex = fig.axes[0], sharey = fig.axes[0])
            spikeTimestamps = spikeData.timestamps
            dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes, sortArray=sortArray, ms=ms, timeRange = timeRange)
            if ind == 0:
                plt.title(plotTitle)
            plt.ylabel('TT {}'.format(tetrode))
        plt.xlabel('time (sec)')
        plt.show()

    def plot_two_axis_sorted_raster(self, session, tetrode, experiment=-1, site=-1, firstSort='currentFreq', secondSort='currentIntensity', cluster = None, replace=0, timeRange = [-0.5, 1], ms = 1, firstLabels=None, secondLabels=None, yLabel=None, plotTitle=None):
        '''
        Plot rasters sorted by 2 arrays.
        By default, sorts by frequency and intensity to copy functionality of old plot_sorted_tuning_raster method. 
        However, can specify different arrays to sort by.
        '''
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        bdata = self.loader.get_session_behavior(behavFile)
        plotTitle = sessionDir
        eventData = self.loader.get_session_events(sessionDir)
        spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)
         
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        spikeTimestamps=spikeData.timestamps
        
        firstSortArray = bdata[firstSort]
        secondSortArray = bdata[secondSort]

        if not firstLabels:
            possibleFirst = np.unique(firstSortArray)
            if firstSort == 'currentFreq':
                firstLabels = ['{0:.1f}'.format(freq/1000.0) for freq in possibleFirst]
            else:
                firstLabels = ['{}'.format(val) for val in possibleFirst]

        if not secondLabels:
            possibleSecond = np.unique(secondSortArray)
            if secondSort == 'currentIntensity':
                secondLabels = ['{:.0f} dB'.format(intensity) for intensity in possibleSecond]
            else:
                secondLabels = ['{}'.format(val) for val in possibleSecond]

        xLabel="Time from sound onset (sec)"

        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()

        dataplotter.two_axis_sorted_raster(spikeTimestamps,
                                           eventOnsetTimes,
                                           firstSortArray,
                                           secondSortArray,
                                           firstLabels,
                                           secondLabels,
                                           xLabel,
                                           yLabel,
                                           plotTitle,
                                           flipFirstAxis=False,
                                           flipSecondAxis=True,
                                           timeRange=timeRange,
                                           ms=ms)

        plt.show()

    #Relies on external TC heatmap plotting functions
    def plot_session_tc_heatmap(self, session, tetrode, experiment=-1, site=-1, cluster=None, replace=True, timeRange=[0, 0.1]):
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        behavFile = sessionObj.behav_filename()
        bdata = self.loader.get_session_behavior(behavFile)
        plotTitle = sessionDir
        eventData = self.loader.get_session_events(sessionDir)
        spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)

        spikeTimestamps = spikeData.timestamps

        eventOnsetTimes = self.loader.get_event_onset_times(eventData)

        freqEachTrial = bdata['currentFreq']
        intensityEachTrial = bdata['currentIntensity']

        possibleFreq = np.unique(freqEachTrial)
        possibleIntensity = np.unique(intensityEachTrial)

        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()


        xlabel='Frequency (kHz)'
        ylabel='Intensity (dB SPL)'

        freqLabels = ["%.1f" % freq for freq in possibleFreq/1000.0] #FIXME: This should be outside this function
        intenLabels = ['{}'.format(inten) for inten in possibleIntensity]

        dataplotter.two_axis_heatmap(spikeTimestamps=spikeTimestamps,
                                            eventOnsetTimes=eventOnsetTimes,
                                            firstSortArray=intensityEachTrial,
                                            secondSortArray=freqEachTrial,
                                            firstSortLabels=intenLabels,
                                            secondSortLabels=freqLabels,
                                            xlabel='Frequency (kHz)',
                                            ylabel='Intensity (dB SPL)',
                                            plotTitle=plotTitle,
                                            flipFirstAxis=False,
                                            flipSecondAxis=False,
                                            timeRange=[0, 0.1])

        plt.show()


    #Relies on module for clustering multiple sessions
    #Also relies on methods for plotting rasters and cluster waveforms
    def cluster_session(self, session, tetrode, experiment=-1, site=-1):
        from jaratoolbox import spikesorting

        print 'Clustering tetrode {}'.format(tetrode)
        sessionObj = self.get_session_obj(session, experiment, site)

        oneTT = spikesorting.TetrodeToCluster(sessionObj.subject,
                                              sessionObj.ephys_dir(),
                                              tetrode)

        clusterFile = os.path.join(oneTT.clustersDir,
                                   'Tetrode{}.clu.1'.format(int(oneTT.tetrode)))
        oneTT.load_waveforms()
        if os.path.isfile(clusterFile):
            oneTT.set_clusters_from_file()
        else:
            oneTT.create_fet_files()
            oneTT.run_clustering(MinClusters=6, MaxClusters=6, MaxPossibleClusters=6)
            oneTT.save_report()

    def cluster_array(self, session, site=-1, experiment=-1):

        sessionObj = self.get_session_obj(session, experiment, site)
        tetrodes=sessionObj.tetrodes
        for tetrode in tetrodes:
            self.cluster_session(session, tetrode, experiment, site)

    def flip_cluster_tuning(self, session, behavSuffix, tetrode, rasterRange=[-0.5, 1]):

        from jaratoolbox import extraplots

        sessions = []
        tetrodes = []
        behavSuffixs = []
        clusters = []

        bdata = self.loader.get_session_behavior(behavSuffix)
        currentFreq = bdata['currentFreq']
        currentIntensity = bdata['currentIntensity']

        spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)
        if spikeData.clusters is None:
            self.cluster_session(session, tetrode)
            spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)

        possibleClusters = np.unique(spikeData.clusters)

        for cluster in possibleClusters:
            sessions.append(session)
            tetrodes.append(tetrode)
            behavSuffixs.append(behavSuffix)
            clusters.append(cluster)

        dataList = zip(sessions, tetrodes, behavSuffixs, clusters)
        flipper = extraplots.FlipThrough(self.plot_sorted_tuning_raster, dataList)
        return flipper

    # def _cluster_tuning(self, session, tetrode, behavSuffix, cluster):

    #     #session, tetrode, behavSuffix, cluster = dataTuple
    #     self.plot_sorted_tuning_raster(session, tetrode, behavSuffix, cluster)

    def flip_tetrode_tuning(self, session, behavSuffix, tetrodes=None , rasterRange=[-0.5, 1], tcRange=[0, 0.1]):

        if not tetrodes:
            tetrodes=self.defaultTetrodes

        plotTitle = sessionDir

        spikesList=[]
        eventsList=[]
        freqList=[]
        rasterRangeList=[]
        tcRangeList=[]

        bdata = self.loader.get_session_behavior(behavSuffix)
        freqEachTrial = bdata['currentFreq']
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)

        for tetrode in tetrodes:
            spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)
            spikeTimestamps = spikeData.timestamps

            spikesList.append(spikeTimestamps)
            eventsList.append(eventOnsetTimes)
            freqList.append(freqEachTrial)
            rasterRangeList.append(rasterRange)
            tcRangeList.append(tcRange)

        dataList = zip(sessions, tetrodes, behavSuffixs, clusters)
        flipper = extraplots.FlipThrough(self.plot_sorted_tuning_raster, dataList)
        return flipper

    def flip_freq_am_tuning(self, freqsession, amsession, experiment=-1, site=-1, tetrodes=None, freqRange = [-0.1, 0.3], amRange = [-0.2, 0.8], colorEachCond=None):
        freqsessionList=[]
        amsessionList=[]
        experimentList=[]
        siteList=[]
        tetrodeList=[]
        amRangeList=[]
        freqRangeList=[]
        colorList=[]
        
        sessionObj = self.get_session_obj(freqsession, experiment, site)
        if not tetrodes:
            tetrodes=sessionObj.tetrodes

        from jaratoolbox import extraplots

        for tetrode in tetrodes:
            freqsessionList.append(freqsession)
            amsessionList.append(amsession)
            experimentList.append(experiment)
            siteList.append(site)
            tetrodeList.append(tetrode)
            amRangeList.append(amRange)
            freqRangeList.append(freqRange)
            colorList.append(colorEachCond)

        dataList=zip(freqsessionList, amsessionList, tetrodeList, experimentList, siteList, freqRangeList, amRangeList, colorList)
        flipper=extraplots.FlipThrough(self.plot_am_freq_tuning, dataList)
        return flipper

    # @dataplotter.FlipThroughData
    @staticmethod
    def _tetrode_tuning(dataTuple):

        '''
        The data tuple must be exactly this: (spikeTimestamps, eventOnsetTimes, freqEachTrial, tetrode, rasterRange, tcRange)
        '''

        #Unpack the data tuple (Watch out - make sure things from the above method are in the right order)
        spikeTimestamps, eventOnsetTimes, freqEachTrial, tetrode, rasterRange, tcRange = dataTuple

        possibleFreq=np.unique(freqEachTrial)
        freqLabels = ['{0:.1f}'.format(freq/1000.0) for freq in possibleFreq]
        fig = plt.gcf()

        ax1=plt.subplot2grid((3, 3), (0, 0), rowspan=3, colspan=2)
        dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = freqEachTrial, ms=1, labels=freqLabels, timeRange=rasterRange)
        plt.title("Tetrode {}".format(tetrode))
        ax1.set_ylabel('Freq (kHz)')
        ax1.set_xlabel('Time from sound onset (sec)')

        ax2=plt.subplot2grid((3, 3), (0, 2), rowspan=3, colspan=1)
        dataplotter.one_axis_tc_or_rlf(spikeTimestamps, eventOnsetTimes, freqEachTrial, timeRange=tcRange)

        ax2.set_ylabel("Avg spikes in range {}".format(tcRange))
        ax2.set_xticks(range(len(freqLabels)))
        ax2.set_xticklabels(freqLabels, rotation='vertical')
        ax2.set_xlabel('Freq (kHz)')

    def plot_LFP_tuning(self, session, channel, behavSuffix): #FIXME: Time range??

        bdata = self.loader.get_session_behavior(behavSuffix)
        plotTitle = sessionDir
        eventData = self.loader.get_session_events(sessionDir, convertToSeconds=False)

        contData = self.loader.get_session_cont(session, channel)

        startTimestamp = contData.timestamps[0]

        eventOnsetTimes = self.loader.get_event_onset_times(eventData, diffLimit=False)

        freqEachTrial = bdata['currentFreq']
        intensityEachTrial = bdata['currentIntensity']

        possibleFreq = np.unique(freqEachTrial)
        possibleIntensity = np.unique(intensityEachTrial)

        secondsEachTrace = 0.1
        meanTraceEachSetting = np.empty((len(possibleIntensity), len(possibleFreq), secondsEachTrace*self.loader.EPHYS_SAMPLING_RATE))


        for indFreq, currentFreq in enumerate(possibleFreq):
            for indIntensity, currentIntensity in enumerate(possibleIntensity):

                #Determine which trials this setting was presented on.
                trialsThisSetting = np.flatnonzero((freqEachTrial == currentFreq) & (intensityEachTrial == currentIntensity))

                #Get the onset timestamp for each of the trials of this setting.
                timestampsThisSetting = eventOnsetTimes[trialsThisSetting]

                #Subtract the starting timestamp value to get the sample number
                sampleNumbersThisSetting = timestampsThisSetting - startTimestamp

                #Preallocate an array to store the traces for each trial on which this setting was presented.
                traces = np.empty((len(sampleNumbersThisSetting), secondsEachTrace*self.loader.EPHYS_SAMPLING_RATE))

                #Loop through all of the trials for this setting, extracting the trace after each presentation
                for indSamp, sampNumber in enumerate(sampleNumbersThisSetting):
                    trace = contData.samples[sampNumber:sampNumber + secondsEachTrace*self.loader.EPHYS_SAMPLING_RATE]
                    trace = trace - trace[0]
                    traces[indSamp, :] = trace

                #Take the mean of all of the samples for this setting, and store it according to the freq and intensity
                mean_trace = np.mean(traces, axis = 0)
                meanTraceEachSetting[indIntensity, indFreq, :] = mean_trace

        maxVoltageAllSettings = np.max(np.max(meanTraceEachSetting, axis = 2))
        minVoltageAllSettings = np.min(np.min(meanTraceEachSetting, axis = 2))

        #Plot all of the mean traces in a grid according to frequency and intensity
        for intensity in range(len(possibleIntensity)):
            #Subplot2grid plots from top to bottom, but we need to plot from bottom to top
            #on the intensity scale. So we make an array of reversed intensity indices.
            intensPlottingInds = range(len(possibleIntensity))[::-1]
            for frequency in range(len(possibleFreq)):
                plt.subplot2grid((len(possibleIntensity), len(possibleFreq)), (intensPlottingInds[intensity], frequency))
                plt.plot(meanTraceEachSetting[intensity, frequency, :], 'k-')
                plt.ylim([minVoltageAllSettings, maxVoltageAllSettings])
                plt.axis('off')

        #This function returns the location of the text labels
        #We have to mess with the ideal locations due to the geometry of the plot
        def getXlabelpoints(n):
            rawArray = np.array(range(1, n+1))/float(n+1) #The positions in a perfect (0,1) world
            diffFromCenter = rawArray - 0.6
            partialDiffFromCenter = diffFromCenter * 0.175 #Percent change has to be determined empirically
            finalArray = rawArray - partialDiffFromCenter
            return finalArray

        #Not sure yet if similar modification to the locations will be necessary.
        def getYlabelpoints(n):
            rawArray = np.array(range(1, n+1))/float(n+1) #The positions in a perfect (0,1) world
            return rawArray

        freqLabelPositions = getXlabelpoints(len(possibleFreq))
        for indp, position in enumerate(freqLabelPositions):
            plt.figtext(position, 0.075, "%.1f"% (possibleFreq[indp]/1000), ha = 'center')

        intensLabelPositions = getYlabelpoints(len(possibleIntensity))
        for indp, position in enumerate(intensLabelPositions):
            plt.figtext(0.075, position, "%d"% possibleIntensity[indp])

        plt.figtext(0.525, 0.025, "Frequency (kHz)", ha = 'center')
        plt.figtext(0.025, 0.5, "Intensity (dB SPL)", va = 'center', rotation = 'vertical')
        plt.show()

    def calculate_cluster_response_significance(self, session):
        pass

    def cluster_color_raster(self, session, site=-1, experiment=-1):
        '''
        Display cluster waveforms and a colormap-style psth. Could also just do lines for each cluster.
        could also just plot spikes in color for each cluster.
        '''
        #Cluster the site, all tetrodes
        #TODO: Make sure this function is using nice new cms with numclusters=6
        self.cluster_array(session, site=site, experiment=experiment)

        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        tetrodes=sessionObj.tetrodes

        from matplotlib import gridspec
        gs = gridspec.GridSpec(2*len(tetrodes), 12)

        nClusters=6 #FIXME hardcoded number of clusters to plot

        # colors = plt.cm.Paired(np.linspace(0, 1, nClusters))
        from jaratoolbox import colorpalette
        cp = colorpalette.TangoPalette
        colors = [cp['SkyBlue3'], cp['Chameleon3'], cp['Orange3'],
                  cp['Plum3'], cp['ScarletRed2'], cp['Butter3']]

        for indt, tetrode in enumerate(tetrodes):
            raster_ax = plt.subplot(gs[indt*2:(indt*2)+2, 6:12])
            for indc, cluster in enumerate(range(1, nClusters+1)):
                clusterColor = colors[indc]
                spikeData= self.loader.get_session_spikes(sessionDir, tetrode, cluster)
                spikeTimestamps = spikeData.timestamps
                timeRange = [-0.2, 0.3]
                spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
                    spikeTimestamps, eventOnsetTimes, timeRange)
                raster_ax.plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.', color=colors[indc])
                raster_ax.axvline(x=0, color='k')
                raster_ax.set_xlim(timeRange)


                crow = indc/3 + (indt*2)
                ccolStart = (indc%3)*2
                ccolEnd = ccolStart+2
                cluster_ax = plt.subplot(gs[crow, ccolStart:ccolEnd])
                print 'r{}c{} : Cluster {}, {} spikes'.format(crow, ccolStart, cluster, len(spikeData.timestamps))
                self.plot_colored_waveforms(spikeData.samples, clusterColor, ax=cluster_ax)


    def cluster_color_psth(self, session, site=-1, experiment=-1):
        '''
        Display cluster waveforms and a colormap-style psth. Could also just do lines for each cluster.
        could also just plot spikes in color for each cluster.
        '''
        #Cluster the site, all tetrodes
        #TODO: Make sure this function is using nice new cms with numclusters=6
        self.cluster_array(session, site=site, experiment=experiment)

        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()
        eventData = self.loader.get_session_events(sessionDir)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        tetrodes=sessionObj.tetrodes

        self.fig = plt.gcf()
        self.fig.clf()
        self.fig.set_facecolor('w')

        from matplotlib import gridspec
        gs = gridspec.GridSpec(2*len(tetrodes), 12)
        gs.update(wspace=0.5, hspace=0.5)

        nClusters=6 #FIXME hardcoded number of clusters to plot

        # colors = plt.cm.Paired(np.linspace(0, 1, nClusters))
        from jaratoolbox import colorpalette
        cp = colorpalette.TangoPalette
        colors = [cp['SkyBlue1'], cp['Chameleon1'], cp['Orange1'],
                  cp['Plum1'], cp['ScarletRed1'], cp['Aluminium4']]

        # colors = ["#cc9d4a",
        #           "#779ae3",
        #           "#7cb851",
        #           "#d27bcd",
        #           "#54bc9f",
        #           "#e76f6f"]

        #This one
        # colors = ["#858bdd",
        #           "#78b34e",
        #           "#d66eb7",
        #           "#52b8a0",
        #           "#dd695a",
        #           "#c59c47"]

        # colors = plt.cm.gist_rainbow(np.linspace(0, 1, nClusters))
        # colors = ['k', 'b', 'g', 'r', 'c', 'm']

        for indt, tetrode in enumerate(tetrodes):
            psth_ax = plt.subplot(gs[indt*2:(indt*2)+2, 6:12])
            for indc, cluster in enumerate(range(1, nClusters+1)):
                clusterColor = colors[indc]
                spikeData= self.loader.get_session_spikes(sessionDir, tetrode, cluster)
                spikeTimestamps = spikeData.timestamps
                timeRange = [-0.2, 1]
                spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
                    spikeTimestamps, eventOnsetTimes, timeRange)


                binEdges = np.linspace(-0.2, 1, 100)
                spikeCountMat = spikesanalysis.spiketimes_to_spikecounts(spikeTimesFromEventOnset,
                                                                         indexLimitsEachTrial,
                                                                         binEdges)
                # import ipdb; ipdb.set_trace()
                smoothWinSize = 3
                winShape = np.concatenate((np.zeros(smoothWinSize),np.ones(smoothWinSize))) # Square (causal)
                winShape = winShape/np.sum(winShape)

                binsStartTime=binEdges[:-1]

                #TODO: This does not suppport diff trial types (for good reason? already complicated enough?)
                binSize = binEdges[1]-binEdges[0]
                thisPSTH = np.mean(spikeCountMat/binSize,axis=0)
                smoothPSTH = np.convolve(thisPSTH,winShape,mode='same')
                downsamplefactor=1
                sSlice = slice(0,len(smoothPSTH),downsamplefactor)
                psth_ax.plot(binsStartTime[sSlice],smoothPSTH[sSlice], color = clusterColor, lw=2)
                psth_ax.hold(1)
                psth_ax.axvline(x=0, color='k')
                psth_ax.set_xlim(timeRange)


                crow = indc/3 + (indt*2)
                ccolStart = (indc%3)*2
                ccolEnd = ccolStart+2
                cluster_ax = plt.subplot(gs[crow, ccolStart:ccolEnd])
                # print 'r{}c{} : Cluster {}, {} spikes'.format(crow, ccolStart, cluster, len(spikeData.timestamps))
                self.plot_colored_waveforms(spikeData.samples, clusterColor, ax=cluster_ax)


    def plot_colored_waveforms(self, waveforms, color='k', ntraces=40, ax=None):
        if ax is None:
            ax = plt.gca()
        (nSpikes,nChannels,nSamplesPerSpike) = waveforms.shape
        if nSpikes>0:
            spikesToPlot = np.random.randint(nSpikes,size=ntraces)
            alignedWaveforms = spikesorting.align_waveforms(waveforms[spikesToPlot,:,:])

            #New stuff for plotting means
            meanWaveforms = np.mean(alignedWaveforms, axis=0)
            waveVariance = np.std(alignedWaveforms, axis=0)
            varUpper = meanWaveforms + waveVariance
            varLower = meanWaveforms - waveVariance

            scalebarSize = abs(meanWaveforms.min())
            # xRange = np.arange(nSamplesPerSpike)
            # for indc in range(nChannels):
            #     newXrange = xRange+indc*(nSamplesPerSpike+2)
            #     wavesToPlot = alignedWaveforms[:,indc,:].T
            #     ax.plot(newXrange,wavesToPlot,color=color,lw=0.4,clip_on=False)
            #     plt.hold(True)

            xRange = np.arange(nSamplesPerSpike)
            for indc in range(nChannels):
                newXrange = xRange+indc*(nSamplesPerSpike+2)
                waveToPlot = meanWaveforms[indc,:].T
                ax.plot(newXrange,waveToPlot,color='w',lw=1,clip_on=False, zorder=1)
                ax.fill_between(newXrange, varLower[indc,:].T, varUpper[indc,:].T, color=color, zorder=0)
                plt.hold(True)

            fontsize=8
            ax.plot(2*[-7],[0,-scalebarSize],color='0.5',lw=2)
            ax.text(-10,-scalebarSize/2,'{0:0.0f}uV'.format(np.round(scalebarSize)),
                    ha='right',va='center',ma='center',fontsize=fontsize)

        plt.axis('off')





