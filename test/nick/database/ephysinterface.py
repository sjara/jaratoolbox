'''
2015-08-01 Nick Ponvert

This module will provide a frontend for plotting data during an ephys experiment

The job of the module will be to take session names, get the data, and then pass the data to the correct plotting function
'''

from jaratoolbox.test.nick.database import dataloader
from jaratoolbox.test.nick.database import dataplotter
reload(dataplotter)
import os
from matplotlib import pyplot as plt
import numpy as np


class EphysInterface(object):

    def __init__(self,
                 animalName,
                 date,
                 experimenter,
                 defaultParadigm=None,
                 serverUser='jarauser',
                 serverName='jarahub',
                 serverBehavPathBase='/data/behavior'
                 ):

        self.animalName = animalName
        self.date = date
        self.experimenter = experimenter
        self.defaultParadigm = defaultParadigm

        self.loader = dataloader.DataLoader('online', animalName, date, experimenter, defaultParadigm)

        self.serverUser = serverUser
        self.serverName = serverName
        self.serverBehavPathBase = serverBehavPathBase
        self.experimenter = experimenter
        self.serverBehavPath = os.path.join(self.serverBehavPathBase, self.experimenter, self.animalName)
        self.remoteBehavLocation = '{0}@{1}:{2}'.format(self.serverUser, self.serverName, self.serverBehavPath)


    #Get the behavior from jarahub
    def get_behavior(self):
        transferCommand = ['rsync', '-a', '--progress', self.remoteBehavLocation, self.localBehavPath]
        print ' '.join(transferCommand)
        subprocess.call(transferCommand)

    def plot_session_raster(self, session, tetrode, cluster = None, sortArray = [], replace=0, ms=4):

        plotTitle = self.loader.get_session_filename(session)
        spikeData= self.loader.get_session_spikes(session, tetrode)
        eventData = self.loader.get_session_events(session)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        spikeTimestamps=spikeData.timestamps

        if cluster:
            spikeTimestamps = spikeTimestamps[spikeData.clusters==cluster]

        if replace:
            plt.cla()
        else:
            plt.figure()

        dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = sortArray, ms=ms)

        plt.show()


    def plot_array_freq_tuning(self, session, behavSuffix, replace=0, tetrodes=[3, 4, 5, 6], timeRange=[0, 0.1]):

        numTetrodes = len(tetrodes)
        eventData = self.loader.get_session_events(session)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        plotTitle = self.loader.get_session_filename(session)
        bdata=self.loader.get_session_behavior(behavSuffix)
        freqEachTrial = bdata['currentFreq']
        freqLabels = ["%.1f"%freq for freq in np.unique(freqEachTrial)/1000]

        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()


        for ind , tetrode in enumerate(tetrodes):

            spikeData = self.loader.get_session_spikes(session, tetrode)

            if ind == 0:
                ax = fig.add_subplot(numTetrodes,1,ind+1)
            else:
                ax = fig.add_subplot(numTetrodes,1,ind+1, sharex = fig.axes[0], sharey = fig.axes[0])

            spikeTimestamps = spikeData.timestamps
            dataplotter.one_axis_tc_or_rlf(spikeTimestamps, eventOnsetTimes, freqEachTrial, timeRange=timeRange)



        plt.show()



    def plot_array_raster(self, session, replace=0, sortArray=[], timeRange = [-0.5, 1], tetrodes=[3,4,5,6], ms=4):
        '''
        This is the much-improved version of a function to plot a raster for each tetrode. All rasters
        will be plotted using standardized plotting code, and we will simply call the functions.
        In this case, we get the event data once, and then loop through the tetrodes, getting the
        spike data and calling the plotting code for each tetrode.
        '''

        numTetrodes = len(tetrodes)
        eventData = self.loader.get_session_events(session)
        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        plotTitle = self.loader.get_session_filename(session)

        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()


        for ind , tetrode in enumerate(tetrodes):

            spikeData = self.loader.get_session_spikes(session, tetrode)

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



    def plot_sorted_tuning_raster(self, session, tetrode, behavSuffix, cluster = None, replace=0, timeRange = [-0.5, 1], ms = 1):
        '''
        '''
        bdata = self.loader.get_session_behavior(behavSuffix)
        plotTitle = self.loader.get_session_filename(session)
        eventData = self.loader.get_session_events(session)
        spikeData = self.loader.get_session_spikes(session, tetrode)

        eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        spikeTimestamps=spikeData.timestamps

        freqEachTrial = bdata['currentFreq']
        intensityEachTrial = bdata['currentIntensity']

        possibleFreq = np.unique(freqEachTrial)
        possibleIntensity = np.unique(intensityEachTrial)
        freqLabels = ['{0:.1f}'.format(freq/1000.0) for freq in possibleFreq]
        intensityLabels = ['{:.0f} dB'.format(intensity) for intensity in possibleIntensity]
        xLabel="Time from sound onset (sec)"

        plt.figure()

        dataplotter.two_axis_sorted_raster(spikeTimestamps,
                                           eventOnsetTimes,
                                           freqEachTrial,
                                           intensityEachTrial,
                                           freqLabels,
                                           intensityLabels,
                                           xLabel,
                                           plotTitle,
                                           flipFirstAxis=False,
                                           flipSecondAxis=True,
                                           timeRange=timeRange,
                                           ms=ms)

        plt.show()


    #Relies on external TC heatmap plotting functions
    def plot_session_tc_heatmap(self, session, tetrode, behavSuffix, replace=True, timeRange=[0, 0.1]):
        bdata = self.loader.get_session_behavior(behavSuffix)
        plotTitle = self.loader.get_session_filename(session)
        eventData = self.loader.get_session_events(session)
        spikeData = self.loader.get_session_spikes(session, tetrode)

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

        dataplotter.two_axis_heatmap(spikeTimestamps,
                                     eventOnsetTimes,
                                     intensityEachTrial,
                                     freqEachTrial,
                                     intenLabels,
                                     freqLabels,
                                     xlabel,
                                     ylabel,
                                     plotTitle,
                                     flipFirstAxis=True,
                                     flipSecondAxis=False,
                                     timeRange=timeRange)

        plt.show()

    def plot_array_heatmap(self, session, behavSuffix, replace=True):
        pass

    #Relies on module for clustering multiple sessions
    #Also relies on methods for plotting rasters and cluster waveforms
    def cluster_sessions_and_plot_rasters_for_each_cluster(self, ):
        pass

    #Relies on methods for interactive plotting (</>, etc)
    def switch_through_plots_interactively(self, ):
        pass
