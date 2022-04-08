'''
2016-08-29 Nick Ponvert and Anna Lakunina

This module will provide a frontend for plotting data during an ephys experiment

The job of the module will be to take session names, get the data, and then pass the data to the correct plotting function
'''

import os
import imp
# from jaratest.nick.database import dataloader_v2 as dataloader
# from jaratest.nick.database import dataplotter #TODO: We need to get rid of dataplotter functions (see color psth)
from jaratoolbox import ephyscore
# reload(dataplotter)
# reload(dataloader)
import numpy as np
from matplotlib import pyplot as plt
import functools
from jaratoolbox import extraplots
from jaratoolbox import spikesanalysis
from jaratoolbox import spikesorting
from jaratoolbox import behavioranalysis
from jaratoolbox import loadbehavior

def plot_raster(spikeTimestamps,
                eventOnsetTimes,
                sortArray=[],
                timeRange=[-0.5, 1],
                ms=4,
                labels=None,
                *args,
                **kwargs):
    '''
    Function to accept spike timestamps, event onset times, and an optional sorting array and plot a
    raster plot (sorted if the sorting array is passed)

    This function does not replicate functionality. It allows you to pass spike timestamps and event
    onset times, which are simple to get, as well as an array of any values that can be used to sort the
    raster. This function wraps three other good functions and provides a way to use them easily

    Args:
        sortarray (array): An array of parameter values for each trial.
                           Output will be sorted by the possible values of the parameter.
                           Must be the same length as the event onset times array

    '''
    # If a sort array is supplied, find the trials that correspond to each value of the array
    if len(sortArray) > 0:
        trialsEachCond = behavioranalysis.find_trials_each_type(
            sortArray, np.unique(sortArray))
        if not labels:
            labels = ['%.1f' % f for f in np.unique(sortArray)]
    else:
        trialsEachCond = []
    # Align spiketimestamps to the event onset times for plotting
    spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
        spikeTimestamps, eventOnsetTimes, timeRange)
    #Plot the raster, which will sort if trialsEachCond is supplied
    pRaster, hcond, zline = extraplots.raster_plot(
        spikeTimesFromEventOnset,
        indexLimitsEachTrial,
        timeRange,
        trialsEachCond=trialsEachCond,
        labels=labels, *args, **kwargs)
    #Set the marker size for better viewing
    plt.setp(pRaster, ms=ms)

def plot_psth(spikeTimestamps, eventOnsetTimes, sortArray=[], timeRange=[-0.5,1], binsize = 50, lw=2, plotLegend=0, *args, **kwargs):
    '''
    Function to accept spike timestamps, event onset times, and an optional sorting array and plot a
    PSTH (sorted if the sorting array is passed)

    This function does not replicate functionality. It allows you to pass spike timestamps and event
    onset times, which are simple to get.

    Args:
        binsize (float) = size of bins for PSTH in ms
    '''
    binsize = binsize/1000.0
    # If a sort array is supplied, find the trials that correspond to each value of the array
    if len(sortArray) > 0:
        trialsEachCond = behavioranalysis.find_trials_each_type(
            sortArray, np.unique(sortArray))
    else:
        trialsEachCond = []
    # Align spiketimestamps to the event onset times for plotting
    spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
        spikeTimestamps, eventOnsetTimes, [timeRange[0]-binsize, timeRange[1]])
    binEdges = np.around(np.arange(timeRange[0]-binsize, timeRange[1]+2*binsize, binsize), decimals=2)
    spikeCountMat = spikesanalysis.spiketimes_to_spikecounts(spikeTimesFromEventOnset, indexLimitsEachTrial, binEdges)
    pPSTH = extraplots.plot_psth(spikeCountMat/binsize, 1, binEdges[:-1], trialsEachCond, *args, **kwargs)
    plt.setp(pPSTH, lw=lw)
    plt.hold(True)
    zline = plt.axvline(0,color='0.75',zorder=-10)
    plt.xlim(timeRange)

    if plotLegend:
        if len(sortArray)>0:
            sortElems = np.unique(sortArray)
            for ind, pln in enumerate(pPSTH):
                pln.set_label(sortElems[ind])
            # ax = plt.gca()
            # plt.legend(mode='expand', ncol=3, loc='best')
            plt.legend(ncol=3, loc='best')

def plot_colored_waveforms(waveforms, color='k', ntraces=40, ax=None):
    '''
    Plot mean waveform and variance as a colored area.
    Args:
        waveforms (array): waveform array of shape (nChannels,nSamplesPerSpike,nSpikes)
        color (str): matplotlib color
        ntraces (int): Number of randomly-selected traces to use
        ax (matplotlib Axes object): The axis to plot on
    '''
    if ax is None:
        ax = plt.gca()
    (nSpikes,nChannels,nSamplesPerSpike) = waveforms.shape
    if nSpikes>0:
        spikesToPlot = np.random.randint(nSpikes,size=ntraces)
        alignedWaveforms = spikesorting.align_waveforms(waveforms[spikesToPlot,:,:])
        meanWaveforms = np.mean(alignedWaveforms, axis=0)
        waveVariance = np.std(alignedWaveforms, axis=0)
        varUpper = meanWaveforms + waveVariance
        varLower = meanWaveforms - waveVariance
        scalebarSize = abs(meanWaveforms.min())
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

class EphysInterface(object):

    def __init__(self, filepath):
        '''
        Args:
           filepath (str): Absolute path to the inforec file.
        '''
        if not os.path.isfile(filepath):
            raise AttributeError("The path provided does not point to an inforec file.")
        self.filepath = filepath
        self.inforec = self.load_inforec()
        # self.loader = dataloader.DataLoader(self.inforec.subject)

    def load_inforec(self):
        inforec = imp.load_source('module.name', self.filepath)
        return inforec

    def get_colours(self, ncolours):
        '''
        Returns n colors from the matplotlib rainbow colormap.
        '''
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
        Returns:
            sessionObj (jaratoolbox.celldatabase.Session)

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
            print("Unrecognized session format")
            pass
        sessionObj = sessions[sessionIndex] #Get the right session object
        return sessionObj

    def get_site_obj(self, experiment, site):
        '''
        Get the site object given experiment and site indices.
        Args:
            experiment (index): The index of the experiment to get the site from.
            site (index): The index of the site in the experiment.
        Returns:
            siteObj (jaratoolbox.celldatabase.Site): The site object.
        '''

        self.inforec = self.load_inforec()
        #List of session objects and session ephys names for the specified experiment and site

        sites = self.inforec.experiments[experiment].sites

        if isinstance(site, int):
            siteIndex = site #Use site as an index directly
        siteObj = sites[siteIndex] #Get the right session object
        return siteObj

    def load_session_data(self, session, experiment, site, tetrode, cluster=None, behavClass=None):
        '''
        Return ephys and behavior data for a particular session.
        Args
            session (int or str): Can be an integer index, to be used
                                  on the list of sessions for this site/experiment,
                                  or a string with the timestamp of the session.
            experiment (int): The index of the experiment to use
            site (int): The index of the site to use
            tetrode (int): Tetrode number to load
            cluster (int): Cluster number to load (set to None to load all clusters)
            behavClass (str): name of jaratoolbox.loadbehavior class to use for loading behavior
        Returns
            ephysData (dict): dictionary of ephys data returned by jaratoolbox.ephyscore.load_ephys()
            bdata (dict): jaratoolbox.loadbehavior.BehaviorData (or subclass, depending on behavClass arg)
        '''
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()

        #Some info to return about the session. TODO: Is this necessary??
        info = {'sessionDir':sessionDir}

        if behavClass == None:
            behavClass = loadbehavior.BehaviorData
        if sessionObj.behavsuffix is not None:
            dateStr = ''.join(sessionObj.date.split('-'))
            fullSessionStr = '{}{}'.format(dateStr, sessionObj.behavsuffix)
            behavDataFilePath = loadbehavior.path_to_behavior_data(sessionObj.subject,
                                                                sessionObj.paradigm,
                                                                fullSessionStr)
            bdata = behavClass(behavDataFilePath)
        else:
            bdata = None
        ephysData = ephyscore.load_ephys(sessionObj.subject, sessionObj.paradigm, sessionDir, tetrode, cluster)
        return ephysData, bdata, info

    def plot_session_raster(self, session, tetrode, experiment=-1, site=-1, cluster=None, sortArray='currentFreq', timeRange=[-0.5, 1], replace=0, ms=4, colorEachCond=None):
        #Load the behavior data if it exists and set the array that will be used to sort the raster trials.
        ephysData, bdata, info = self.load_session_data(session, experiment, site, tetrode, cluster)
        eventOnsetTimes = ephysData['events']['stimOn']
        spikeTimestamps = ephysData['spikeTimes']
        if bdata is not None:
            sortArray = bdata[sortArray]
        else:
            sortArray = []
        plotTitle = info['sessionDir']
        ##  ---  ##
        if replace:
            plt.cla()
        else:
            plt.figure()
        plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = sortArray,
                    timeRange=timeRange, ms=ms, colorEachCond=colorEachCond)
        plt.show()

    def plot_session_PSTH(self, session, tetrode, experiment=-1, site=-1, cluster = None, sortArray='currentFreq', timeRange = [-0.5, 1], replace=0, lw=3, colorEachCond=None):
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()

        ephysData, bdata, info = self.load_session_data(session, experiment, site, tetrode, cluster)
        eventOnsetTimes = ephysData['events']['stimOn']
        spikeTimestamps = ephysData['spikeTimes']
        if bdata is not None:
            sortArray = bdata[sortArray]
            if colorEachCond is None:
                colorEachCond = self.get_colours(len(np.unique(sortArray)))
        else:
            sortArray = []
        plotTitle = info['sessionDir']

        ephysData = ephyscore.load_ephys(sessionObj.subject, sessionObj.paradigm, sessionDir, tetrode, cluster)
        eventOnsetTimes = ephysData['events']['stimOn']
        spikeTimestamps = ephysData['spikeTimes']

        if replace==1:
            plt.cla()
        elif replace==2:
            plt.sca(ax)
        else:
            plt.figure()
        plot_psth(spikeTimestamps, eventOnsetTimes, sortArray = sortArray, timeRange=timeRange, lw=lw, colorEachCond=colorEachCond, plotLegend=0)

    def plot_am_freq_tuning(self, freqsession, amsession, tetrode, cluster = None,experiment=-1, site=-1, freqTimeRange = [-0.1, 0.3], amTimeRange = [-0.2, 0.8], colorEachCond=None, replace=1, ms=1, lw=3):
        if replace:
            plt.clf()
        else:
            plt.figure()
        #FIXME: currently hardcoded for number of am rates Anna uses
        if colorEachCond is None:
            colorEachCond = self.get_colours(5)
        axAMRaster = plt.subplot(221)
	#plt.waitforbuttonpress()
        #self.plot_session_raster(amsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=amTimeRange, ms=ms, colorEachCond=colorEachCond, ax=axAMRaster)
        self.plot_session_raster(amsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=amTimeRange, ms=ms, colorEachCond=colorEachCond)
        plt.xlabel('Time from event onset (sec)')
        plt.ylabel('Modulation rate (Hz)')
        axAMPSTH = plt.subplot(223)
        #self.plot_session_PSTH(amsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=amTimeRange, lw=lw, colorEachCond=colorEachCond, ax=axAMPSTH)
        self.plot_session_PSTH(amsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=amTimeRange, lw=lw, colorEachCond=colorEachCond)
        plt.xlabel('Time from event onset (sec)')
        plt.ylabel('Firing rate (Hz)')
        axFreqRaster = plt.subplot(222)
        #self.plot_session_raster(freqsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=freqTimeRange, ms=ms, ax=axFreqRaster)
        self.plot_session_raster(freqsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=freqTimeRange, ms=ms)
        plt.xlabel('Time from event onset (sec)')
        plt.ylabel('Frequency (Hz)')
        axFreqTuning = plt.subplot(224)
        #self.plot_session_freq_tuning(freqsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=[0, 0.1], ax=axFreqTuning)
        self.plot_session_freq_tuning(freqsession, tetrode, experiment, site, cluster=cluster, replace=1, timeRange=[0, 0.1])
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('Average number of spikes in range [0, 0.1]')
        plt.suptitle('TT{}'.format(tetrode))

    def one_axis_tc_or_rlf(self, spikeTimestamps, eventOnsetTimes, sortArray, timeRange=[0, 0.1], labels = None):
        trialsEachCond = behavioranalysis.find_trials_each_type(
            sortArray, np.unique(sortArray))
        spikeArray = self.avg_spikes_in_event_locked_timerange_each_cond(
            spikeTimestamps, trialsEachCond, eventOnsetTimes, timeRange)
        plt.plot(spikeArray, ls='-', lw=2, c='0.25')

    def avg_spikes_in_event_locked_timerange_each_cond(self, spikeTimestamps, trialsEachCond, eventOnsetTimes, timeRange):
        if len(eventOnsetTimes) != np.shape(trialsEachCond)[0]:
            eventOnsetTimes = eventOnsetTimes[:-1]
            print("Removing last event onset time to align with behavior data")
        spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
            spikeTimestamps, eventOnsetTimes, timeRange)
        spikeArray = self.avg_locked_spikes_per_condition(indexLimitsEachTrial,
                                                    trialsEachCond)
        return spikeArray

    def avg_locked_spikes_per_condition(self, indexLimitsEachTrial, trialsEachCond):
        numSpikesInTimeRangeEachTrial = np.squeeze(np.diff(indexLimitsEachTrial,
                                                        axis=0))
        conditionMatShape = np.shape(trialsEachCond)
        numRepeats = np.product(conditionMatShape[1:])
        nSpikesMat = np.reshape(
            numSpikesInTimeRangeEachTrial.repeat(numRepeats), conditionMatShape)
        spikesFilteredByTrialType = nSpikesMat * trialsEachCond
        avgSpikesArray = np.sum(spikesFilteredByTrialType, 0) / np.sum(
            trialsEachCond, 0).astype('float')
        return avgSpikesArray

    def plot_session_freq_tuning(self, session, tetrode, experiment = -1, site = -1, cluster = None, sortArray='currentFreq', replace=0, timeRange=[0,0.1]):
        if replace:
            plt.cla()
        else:
            plt.figure()
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()

        ephysData, bdata, info = self.load_session_data(session, experiment, site, tetrode, cluster)
        freqEachTrial = bdata[sortArray]

        # eventData = self.loader.get_session_events(sessionDir)
        # eventOnsetTimes = self.loader.get_event_onset_times(eventData)
        # spikeData = self.loader.get_session_spikes(sessionDir, tetrode, cluster)
        # spikeTimestamps = spikeData.timestamps
        eventOnsetTimes = ephysData['events']['stimOn']
        spikeTimestamps = ephysData['spikeTimes']


        plotTitle = sessionDir
        freqLabels = ["%.1f"%freq for freq in np.unique(freqEachTrial)/1000]
        self.one_axis_tc_or_rlf(spikeTimestamps, eventOnsetTimes, freqEachTrial, timeRange=timeRange)
        ax = plt.gca()
        ax.set_xticks(range(len(freqLabels)))
        ax.set_xticklabels(freqLabels, rotation='vertical')

    # TODO: This seems like it would be good to get working, even though people don't really use it.
    # def plot_array_freq_tuning(self, session, experiment=-1, site=-1, tetrodes=None, replace=0, timeRange=[0, 0.1]):

    #     sessionObj = self.get_session_obj(session, experiment, site)
    #     sessionDir = sessionObj.ephys_dir()
    #     behavFile = sessionObj.behav_filename()
    #     if not tetrodes:
    #         tetrodes=sessionObj.tetrodes
    #     numTetrodes = len(tetrodes)
    #     eventData = self.loader.get_session_events(sessionDir)
    #     eventOnsetTimes = self.loader.get_event_onset_times(eventData)
    #     plotTitle = sessionDir
    #     bdata=self.loader.get_session_behavior(behavFile)
    #     freqEachTrial = bdata['currentFreq']
    #     freqLabels = ["%.1f"%freq for freq in np.unique(freqEachTrial)/1000]

    #     if replace:
    #         fig = plt.gcf()
    #         plt.clf()
    #     else:
    #         fig = plt.figure()

    #     for ind , tetrode in enumerate(tetrodes):

    #         spikeData = self.loader.get_session_spikes(sessionDir, tetrode)

    #         if ind == 0:
    #             ax = fig.add_subplot(numTetrodes,1,ind+1)
    #         else:
    #             ax = fig.add_subplot(numTetrodes,1,ind+1, sharex = fig.axes[0], sharey = fig.axes[0])

    #         spikeTimestamps = spikeData.timestamps
    #         dataplotter.one_axis_tc_or_rlf(spikeTimestamps, eventOnsetTimes, freqEachTrial, timeRange=timeRange)

    #         ax.set_xticks(range(len(freqLabels)))

    #         if ind == numTetrodes-1:
    #             ax.set_xticklabels(freqLabels, rotation='vertical')
    #             plt.xlabel('Frequency (kHz)')
    #         else:
    #             plt.setp(ax.get_xticklabels(), visible=False)


    #         plt.ylabel('TT {}'.format(tetrode))


    #     plt.figtext(0.05, 0.5, 'Average number of spikes in range {}'.format(timeRange), rotation='vertical', va='center', ha='center')
    #     plt.show()

    def plot_array_raster(self, session, experiment=-1, site=-1, tetrodes=None, replace=0, sortArray='currentFreq', timeRange = [-0.5, 1], ms=4, electrodeName='Tetrode'):
        '''
        Plot rasters for each tetrode, for a single recording session.
        Args:
            session (index): The index of the session to cluster.
            experiment (index): The index of the experiment to get the site from.
            site (index): The index of the site to pull sessions from.
            tetrodes (list of int): The tetrodes to plot. Defaults to all siteObj.tetrodes
            replace (bool): True clears and uses the current figure. False makes a new figure.
            sortArray (string): Label of the bdata array used to sort the trials.
            timeRange (list): Time range around each event to align spikes.
            ms (float): matplotlib marker size for raster plots
            electrodeName (string): Name of spikes file should be {electrodeName}{electrodeNumber}.spikes
        Returns nothing - draws a figure.
        '''
        sessionObj = self.get_session_obj(session, experiment, site)
        sessionDir = sessionObj.ephys_dir()

        # behavFile = sessionObj.behav_filename()
        # if not behavFile:
        #     sortArray = []
        # else:
        #     bdata = self.loader.get_session_behavior(behavFile)
        #     sortArray = bdata[sortArray]

        behavClass = None #TODO: This should be an option somewhere.
        if behavClass == None:
            behavClass = loadbehavior.BehaviorData
        if sessionObj.behavsuffix is not None:
            dateStr = ''.join(sessionObj.date.split('-'))
            fullSessionStr = '{}{}'.format(dateStr, sessionObj.behavsuffix)
            behavDataFilePath = loadbehavior.path_to_behavior_data(sessionObj.subject,
                                                                sessionObj.paradigm,
                                                                fullSessionStr)
            bdata = behavClass(behavDataFilePath)
            sortArray = bdata[sortArray]
        else:
            sortArray = []

        if not tetrodes:
            tetrodes=sessionObj.tetrodes
        numTetrodes = len(tetrodes)

        # eventData = self.loader.get_session_events(sessionDir)
        # eventOnsetTimes = self.loader.get_event_onset_times(eventData)

        plotTitle = sessionDir
        if replace:
            fig = plt.gcf()
            plt.clf()
        else:
            fig = plt.figure()
        for ind , tetrode in enumerate(tetrodes):
            # spikeData = self.loader.get_session_spikes(sessionDir, tetrode)
            ephysData = ephyscore.load_ephys(sessionObj.subject, sessionObj.paradigm, sessionDir, tetrode)
            eventOnsetTimes = ephysData['events']['stimOn']
            spikeTimestamps = ephysData['spikeTimes']

            if ind == 0:
                ax = fig.add_subplot(numTetrodes,1,ind+1)
            else:
                ax = fig.add_subplot(numTetrodes,1,ind+1, sharex = fig.axes[0], sharey = fig.axes[0])
            # spikeTimestamps = spikeData.timestamps
            plot_raster(spikeTimestamps, eventOnsetTimes, sortArray=sortArray, ms=ms, timeRange = timeRange)
            if ind == 0:
                plt.title(plotTitle)
            plt.ylabel('TT {}'.format(tetrode))
        plt.xlabel('time (sec)')
        plt.show()

    # FIXME: This function won't load data correctly
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

        # dataplotter.two_axis_sorted_raster(spikeTimestamps,
        #                                    eventOnsetTimes,
        #                                    firstSortArray,
        #                                    secondSortArray,
        #                                    firstLabels,
        #                                    secondLabels,
        #                                    xLabel,
        #                                    yLabel,
        #                                    plotTitle,
        #                                    flipFirstAxis=False,
        #                                    flipSecondAxis=True,
        #                                    timeRange=timeRange,
        #                                    ms=ms)

        # We flip the second axis so that high intensities appear at the top
        flipFirstAxis=False
        flipSecondAxis=True

        if not firstSortLabels:
            firstSortLabels = []
        if not secondSortLabels:
            secondSortLabels = []
        if not xLabel:
            xlabel = ''
        if not yLabel:
            ylabel = ''
        if not plotTitle:
            plotTitle = ''
        #Set first and second possible val arrays and invert them if desired for plotting
        firstPossibleVals = np.unique(firstSortArray)
        secondPossibleVals = np.unique(secondSortArray)
        if flipFirstAxis:
            firstPossibleVals = firstPossibleVals[::-1]
            firstSortLabels = firstSortLabels[::-1]
        if flipSecondAxis:
            secondPossibleVals = secondPossibleVals[::-1]
            secondSortLabels = secondSortLabels[::-1]
        #Find the trials that correspond to each pair of sorting values
        trialsEachCond = behavioranalysis.find_trials_each_combination(
            firstSortArray, firstPossibleVals, secondSortArray, secondPossibleVals)
        #Calculate the spike times relative to event onset times
        spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
            spikeTimestamps, eventOnsetTimes, timeRange)
        #Grab the current figure and clear it for plotting
        fig = plt.gcf()
        plt.clf()
        plt.suptitle(plotTitle)

        #Make a new plot for each unique value of the second sort array, and then plot a raster on that plot sorted by this second array
        for ind, secondArrayVal in enumerate(secondPossibleVals):
            if ind == 0:
                fig.add_subplot(len(secondPossibleVals), 1, ind + 1)
                plt.title(plotTitle)
            else:
                fig.add_subplot(
                    len(secondPossibleVals),
                    1,
                    ind + 1,
                    sharex=fig.axes[0],
                    sharey=fig.axes[0])
            trialsThisSecondVal = trialsEachCond[:, :, ind]
            pRaster, hcond, zline = extraplots.raster_plot(
                spikeTimesFromEventOnset,
                indexLimitsEachTrial,
                timeRange,
                trialsEachCond=trialsThisSecondVal,
                labels=firstSortLabels)
            plt.setp(pRaster, ms=ms)
            if secondSortLabels:
                # plt.ylabel(secondSortLabels[ind])
                plt.title(secondSortLabels[ind])
            if ind == len(secondPossibleVals) - 1:
                plt.xlabel(xLabel)
            if yLabel:
                plt.ylabel(yLabel)

        plt.show()

    def cluster_session(self, session, tetrode, experiment=-1, site=-1):
        '''
        Cluster a single tetrode for a recording session.
        Args:
            session (index): The index of the session to cluster.
            tetrode (int): The tetrode number to cluster.
            site (index): The index of the site to pull sessions from.
            experiment (index): The index of the experiment to get the site from.
        Returns nothing, but .clu files and multisession cluster reports will be created.
        '''
        from jaratoolbox import spikesorting

        print('Clustering tetrode {}'.format(tetrode))
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
            oneTT.run_clustering(MinClusters=3, MaxClusters=6, MaxPossibleClusters=6)
            oneTT.save_report(dirname='online_reports_clusters')

    def cluster_array(self, session, site=-1, experiment=-1):
        '''
        Cluster every tetrode for a recording session.
        Args:
            session (index): The index of the session to cluster.
            site (index): The index of the site to pull sessions from.
            experiment (index): The index of the experiment to get the site from.
        Returns nothing, but .clu files and multisession cluster reports will be created.
        '''

        sessionObj = self.get_session_obj(session, experiment, site)
        tetrodes=sessionObj.tetrodes
        for tetrode in tetrodes:
            self.cluster_session(session, tetrode, experiment, site)


    def cluster_array_multisession(self, sessionList, site=-1, experiment=-1):
        '''
        Run multisession clustering on all tetrodes for a number of recording sessions.
        Args:
            sessionList (list of indices): A list of the indices of the sessions you want to cluster together.
            site (index): The index of the site to pull sessions from.
            experiment (index): The index of the experiment to get the site from.
        Returns nothing, but .clu files and multisession cluster reports will be created.
        '''

        from jaratoolbox import spikesorting

        siteObj = self.get_site_obj(site=site, experiment=experiment)
        sessionsToCluster = [siteObj.session_ephys_dirs()[ind] for ind in sessionList]
        subject = self.inforec.subject
        idString = 'online_multisession_{}'.format('-'.join(sessionsToCluster))

        for tetrode in siteObj.tetrodes:
            spikesorting.cluster_many_sessions(subject,
                    sessionsToCluster,
                    tetrode,
                    idString,
                    minClusters=3,
                    maxClusters=6,
                    maxPossibleClusters=6)

    def cluster_color_psth(self, sessionList, plotType=None, site=-1, experiment=-1, tuningTimeRange = [0.0,0.1]):
        '''
        Display cluster waveforms and a PSTH or tuning curve for each cluster.
        Performs multisession clustering for each tetrode recorded at the site.
        Args:
            sessionList (list of indices): The indices of the sessions to be included in the multisession clustering.
            plotType (list of str): A list the same length as sessionList, containing the type of plot for that session.
                                    Current valid plotTypes are: 'psth', 'tuning'
            site (index): The index of the site to pull sessions from.
            experiment (index): The index of the experiment to get the site from.
            tuningTimeRange (list of float): List containing [start, stop] times relative to event onset over which to
                                             average spikes for tuning curve.
        Returns nothing, but .clu files and multisession cluster reports will be created.
        '''

        if not isinstance(sessionList, list):
            sessionList = list(sessionList)
        if plotType is None:
            plotType = ['psth']*len(sessionList)

        #Cluster the site, all tetrodes
        #TODO: Make sure this function is using nice new cms with numclusters=6
        self.cluster_array_multisession(sessionList, site=site, experiment=experiment)


        allSessionObj = [self.get_session_obj(session, experiment, site) for session in sessionList]
        allTetrodes=[so.tetrodes for so in allSessionObj]

        # allEventOnsetTimes = [self.loader.get_event_onset_times(ed) for ed in allEventData]

        siteObj = self.get_site_obj(site=site, experiment=experiment)
        allSessionType = [siteObj.session_types()[ind] for ind in sessionList]

        self.fig = plt.gcf()
        self.fig.clf()
        self.fig.set_facecolor('w')

        from matplotlib import gridspec
        gs = gridspec.GridSpec(2*len(allTetrodes[0]), 6+6*len(sessionList))
        gs.update(wspace=0.5, hspace=0.5)

        nClusters=6 #FIXME hardcoded number of clusters to plot

        from jaratoolbox import colorpalette
        cp = colorpalette.TangoPalette
        colors = [cp['SkyBlue1'], cp['Chameleon1'], cp['Orange1'],
                  cp['Plum1'], cp['ScarletRed1'], cp['Aluminium4']]

        for indSession, sessionObj in enumerate(allSessionObj):

            # sessionObj = allSessionObj[indSession]
            # sessionDir = allSessionDir[indSession]
            sessionDir = sessionObj.ephys_dir()

            # eventData = allEventData[indSession]
            # eventOnsetTimes = allEventOnsetTimes[indSession]

            tetrodes = allTetrodes[indSession]

            if plotType[indSession] == 'tuning':

                if sessionObj.behavsuffix is None:
                    raise AttributeError('There is no behavior suffix recorded for this session') #TODO: add session info
                behavClass = loadbehavior.BehaviorData
                dateStr = ''.join(sessionObj.date.split('-'))
                fullSessionStr = '{}{}'.format(dateStr, sessionObj.behavsuffix)
                behavDataFilePath = loadbehavior.path_to_behavior_data(sessionObj.subject,
                                                                    sessionObj.paradigm,
                                                                    fullSessionStr)
                bdata = behavClass(behavDataFilePath)
                #FIXME: Hardcoded variable name to sort by for tuning
                freqEachTrial = bdata['currentFreq']
                freqLabels = ["%.1f"%freq for freq in np.unique(freqEachTrial)/1000]

            for indt, tetrode in enumerate(tetrodes):

                colStart = 6+(6*indSession)
                colEnd = colStart+6
                psth_ax = plt.subplot(gs[indt*2:(indt*2)+2, colStart:colEnd])

                for indc, cluster in enumerate(range(1, nClusters+1)):

                    ephysData = ephyscore.load_ephys(sessionObj.subject, sessionObj.paradigm, sessionDir, tetrode, cluster)
                    spikeTimestamps = ephysData['spikeTimes']
                    eventOnsetTimes = ephysData['events']['stimOn']

                    clusterColor = colors[indc]
                    # spikeData= self.loader.get_session_spikes(sessionDir, tetrode, cluster)
                    # spikeTimestamps = spikeData.timestamps
                    timeRange = [-0.2, 1]
                    spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
                        spikeTimestamps, eventOnsetTimes, timeRange)


                    if plotType[indSession] == 'psth':
                        binEdges = np.linspace(-0.2, 1, 100)
                        spikeCountMat = spikesanalysis.spiketimes_to_spikecounts(spikeTimesFromEventOnset,
                                                                                 indexLimitsEachTrial,
                                                                                 binEdges)
                        # import ipdb; ipdb.set_trace()
                        smoothWinSize = 3
                        winShape = np.concatenate((np.zeros(smoothWinSize),np.ones(smoothWinSize))) # Square (causal)
                        winShape = winShape/np.sum(winShape)

                        binsStartTime=binEdges[:-1]

                        binSize = binEdges[1]-binEdges[0]
                        thisPSTH = np.mean(spikeCountMat/binSize,axis=0)
                        smoothPSTH = np.convolve(thisPSTH,winShape,mode='same')
                        downsamplefactor=1
                        sSlice = slice(0,len(smoothPSTH),downsamplefactor)
                        psth_ax.plot(binsStartTime[sSlice],smoothPSTH[sSlice], color = clusterColor, lw=2)
                        psth_ax.set_xlim(timeRange)
                    elif plotType[indSession] == 'tuning':
                        trialsEachCond = behavioranalysis.find_trials_each_type(freqEachTrial, np.unique(freqEachTrial))
                        # spikeArray = dataplotter.avg_spikes_in_event_locked_timerange_each_cond(spikeTimestamps, trialsEachCond, eventOnsetTimes, timeRange=tuningTimeRange)
                        spikeArray = self.avg_spikes_in_event_locked_timerange_each_cond(spikeTimestamps, trialsEachCond, eventOnsetTimes, timeRange=tuningTimeRange)
                        psth_ax.plot(spikeArray, ls='-', lw=2, color = clusterColor)
                        psth_ax.set_xticks(range(len(np.unique(freqEachTrial))))
                        psth_ax.set_xticklabels(freqLabels,fontsize=8)
                    psth_ax.hold(1)
                    psth_ax.axvline(x=0, color='k')
                    if indt==0:
                        psth_ax.set_title(allSessionType[indSession])

                    crow = indc/3 + (indt*2)
                    ccolStart = (indc%3)*2
                    ccolEnd = ccolStart+2

                    if indSession==0:
                        cluster_ax = plt.subplot(gs[crow, ccolStart:ccolEnd])
                        # print 'r{}c{} : Cluster {}, {} spikes'.format(crow, ccolStart, cluster, len(spikeData.timestamps))
                        plot_colored_waveforms(ephysData['samples'], clusterColor, ax=cluster_ax)

        plt.show()
