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
        plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = sortArray, timeRange=timeRange, ms=ms, colorEachCond=colorEachCond)

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
        plot_psth(spikeTimestamps, eventOnsetTimes, sortArray = sortArray, timeRange=timeRange, lw=lw, colorEachCond=colorEachCond, plotLegend=1)

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

    # DEPRECATED? we never use this
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
            plot_raster(spikeTimestamps, eventOnsetTimes, sortArray=sortArray, ms=ms, timeRange = timeRange)
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
            oneTT.run_clustering(MinClusters=3, MaxClusters=6, MaxPossibleClusters=6)
            oneTT.save_report()

    def cluster_array(self, session, site=-1, experiment=-1):

        sessionObj = self.get_session_obj(session, experiment, site)
        tetrodes=sessionObj.tetrodes
        for tetrode in tetrodes:
            self.cluster_session(session, tetrode, experiment, site)

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

        from jaratoolbox import colorpalette
        cp = colorpalette.TangoPalette
        colors = [cp['SkyBlue1'], cp['Chameleon1'], cp['Orange1'],
                  cp['Plum1'], cp['ScarletRed1'], cp['Aluminium4']]

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
                plot_colored_waveforms(spikeData.samples, clusterColor, ax=cluster_ax)
