'''
2015-08-01 Nick Ponvert

This module will help with plotting data. Its methods will accept vectors such as spike timestamps and
event onset times, and it will rely on generic plotting functions that it imports to do the actual plotting

There will be another module that will act as a frontend for conducting ephys experiments.
The other module will call the dataloader module to get the data and then pass the data to this
module to do the plotting.

The job of this module is to do the calculations that will be required before passing data to external
plotting functions

Examples of functionality that already exists elsewhere and should not be replicated:

Plotting rasters (extraplots.plot_raster)
Locking spike times to event onset (spikesanalysis.eventlocked_spiketimes)
Finding trials of each type

Functionality I need:

Extract the spikes after event onset for different trial types (for plotting tcs)
Plotting rasters for arrays of tetrodes
Plotting sorted tuning rasters
This module should do things like describe the plot layout for these different plots, but should
leave the actual plotting to outside methods. (I will have to move the method for plotting an array as
a heatmap to an outside method)
 '''

#A method that can make rasters, sorted or not



#This function does not replicate functionality. It allows you to pass spike timestamps and event
#onset times, which are simple to get, as well as an array of any values that can be used to sort the
#raster. This function wraps three other good functions and provides a way to use them easily

#It should have a less ambiguous name though, since there is the function raster_plot in extraplots
from matplotlib import pyplot as plt
import functools
from jaratoolbox import extraplots
from jaratoolbox import spikesanalysis
from jaratoolbox import behavioranalysis

def plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = [], timeRange = [-0.5, 1], ms = 4):
    '''
    Args:
        sortarray (array): an array of parameter values for each trial. output will be sorted by the possible values of the parameter. Must be the same length as the event onset times array

    '''
    if len(sortArray)>0:
        trialseachcond = behavioranalysis.find_trials_each_type(sortArray, np.unique(sortArray))
    else:
        trialsEachCond = []

    spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(spikeTimestamps,eventOnsetTimes,timeRange)

    pRaster,hcond,zline = extraplots.raster_plot(spikeTimesFromEventOnset, indexLimitsEachTrial, timeRange, trialsEachCond = trialsEachCond)
    plt.setp(pRaster,ms=ms)

def two_axis_sorted_raster(spikeTimestamps,
                           eventOnsetTimes,
                           firstSortArray,
                           secondSortArray,
                           firstSortLabels,
                           secondSortLabels,
                           xLabel,
                           plotTitle,
                           flipFirstAxis=False,
                           flipSecondAxis=True, #Useful for making the highest intensity plot on top
                           timeRange=[-0.5, 1],
                           ms=4):

    '''
    This function takes two arrays and uses them to sort spikes into trials by combinaion, and then plots the spikes in raster form.
    The first sort array will be used to sort each raster plot, and there will be a separate raster plot for each possible value of the
    second sort array. This method was developed for plotting frequency-intensity tuning curve data in raster form, in which case the
    frequency each trial is passed as the first sort array, and the intensity each trial is passed as the second sort array.

    Args:
        spikeTimestamps (array): An array of spike timestamps to plot
        eventOnsetTimes (array): An array of event onset times. Spikes will be plotted in raster form relative to these times
        firstSortArray (array): An array of parameter values for each trial. Must be the same length as eventOnsetTimes.
        secondSortArray (array): Another array of paramenter values the same length as eventOnsetTimes. Better if this array has less possible values.
        firstSortLabels (list): A list containing strings to use as labels for the first sort array. Must contain one item for each possible value of the first sort array.
        secondSortLabels (list): Same idea as above, must contain one element for each possible value of the second sort array.
        xLabel (str): A string to use for the x label of the bottom raster plot
        flipFirstAxis (bool): Whether to flip the first sorting axis. Will result in trials with high values for the first sort array appearing on the bottom of each raster.
        flipSecondAxis (bool): Will result in trials with high values for the second sorting array appearing in the top raster plot
        timeRange (list): A list containing the range of times relative to the event onset times that will be plotted
        ms (int): The marker size to use for the raster plots
    '''

    firstPossibleVals = np.unique(firstSortArray)
    secondPossibleVals = np.unique(secondSortArray)

    if flipFirstAxis:
        firstPossibleVals=firstPossibleVals[::-1]
        firstSortLabels=firstSortLabels[::-1]

    if flipSecondAxis:
        secondPossibleVals=secondPossibleVals[::-1]
        secondSortLabels=secondSortLabels[::-1]

    trialsEachCond = behavioranalysis.find_trials_each_combination(firstSortArray, firstPossibleVals, secondSortArray, secondPossibleVals)
    spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(spikeTimestamps,eventOnsetTimes,timeRange)

    fig = plt.gcf()
    plt.clf()

    for ind, secondArrayVal in enumerate(secondPossibleVals):

        if ind == 0:
            fig.add_subplot(len(secondPossibleVals), 1, ind+1)
            plt.title(plotTitle)
        else:
            fig.add_subplot(len(secondPossibleVals), 1, ind+1, sharex=fig.axes[0], sharey=fig.axes[0])

        trialsThisSecondVal = trialsEachCond[:, :, ind]

        pRaster,hcond,zline = extraplots.raster_plot(spikeTimesFromEventOnset, indexLimitsEachTrial, timeRange, trialsEachCond = trialsThisSecondVal, labels = firstSortLabels)
        plt.setp(pRaster,ms=ms)

        plt.ylabel(secondSortLabels[ind])

        if indIntensity == len(possibleIntensity)-1:
            plt.xlabel(xLabel)


def avg_spikes_in_event_locked_timerange_each_cond(self, spikeTimestamps, trialsEachCond, eventOnsetTimes, timeRange):

    if len(eventOnsetTimes)!=np.shape(trialsEachCond)[0]:
        eventOnsetTimes=eventOnsetTimes[:-1]

    spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(spikeTimestamps,
                                                                                                                    eventOnsetTimes,
                                                                                                                    timeRange)
    spikeArray = self.avg_locked_spikes_per_condition(indexLimitsEachTrial, trialsEachCond)

    return spikeArray

def avg_locked_spikes_per_condition(self, indexLimitsEachTrial, trialsEachCond):

    numSpikesInTimeRangeEachTrial = np.squeeze(np.diff(indexLimitsEachTrial, axis=0))
    conditionMatShape = np.shape(trialsEachCond)
    numRepeats = np.product(conditionMatShape[1:])
    nSpikesMat = np.reshape(numSpikesInTimeRangeEachTrial.repeat(numRepeats), conditionMatShape)
    spikesFilteredByTrialType = nSpikesMat*trialsEachCond
    avgSpikesArray = np.sum(spikesFilteredByTrialType, 0)/np.sum(trialsEachCond, 0).astype('float')
    return avgSpikesArray

def plot_TCarray_as_heatmap(self, heatmapArray, xlabels=None, ylabels=None, timeRange = None, flipy=True, flipylabels=True, cmap='Blues'):

    ax = plt.gca()
    ax.set_ylabel('Intensity (dB SPL)')
    ax.set_xlabel('Frequency (kHz)') #FIXME: This should be outside this function and does not appear to work anyway

    if flipy:
        heatmapArray = np.flipud(heatmapArray)

    cax = ax.imshow(heatmapArray, interpolation='none', aspect='auto', cmap=cmap)
    vmin, vmax = cax.get_clim()
    cbar=plt.colorbar(cax, format = '%.1f')

    if timeRange is not None:

        cbar.ax.set_ylabel('Avg spikes in time range: {}'.format(timeRange))

    if xlabels is not None:
        ax.set_xticks(range(len(xlabels)))
        xticks = ["%.1f" % freq for freq in xlabels/1000.0] #FIXME: This should be outside this function
        ax.set_xticklabels(xticks, rotation = 'vertical')

    ax.set_yticks(range(np.shape(heatmapArray)[0]))


    if ylabels is not None:
        if flipylabels:
            ax.set_yticklabels(ylabels[::-1])
        else:
            ax.set_yticklabels(ylabels)

class FlipThroughData(object):

    def __init__(self, plottingFn):
        self.plotter = plottingFn
        #This is supposed to make this a 'well-behaved' decorator,
        #but I am not sure if is is doing its job
        functools.update_wrapper(self, plottingFn)

    def __call__(self, data):

        self.data = data
        self.counter=0
        self.maxDataInd = len(data)-1
        self.fig = plt.gcf()

        self.plotter(self.data[self.counter])

        #Get the user's original plot title
        self.originalPlotTitle = self.fig.axes[0].get_title()
        self.originalXlabel = self.fig.axes[0].get_xlabel()
        self.originalYlabel = self.fig.axes[0].get_ylabel()

        self.title_plot()

        self.kpid = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        #The kpid will now know the size of the data and what to do with it.

    def redraw(self):
        plt.clf()
        self.plotter(self.data[self.counter])
        self.title_plot()

    def on_key_press(self, event):
        '''
        Method to listen for keypresses and change the slice
        '''
        if event.key=='<' or event.key==',' or event.key=='left':
            if self.counter>0:
                self.counter-=1
            else:
                self.counter=self.maxDataInd
            self.redraw()
        elif event.key=='>' or event.key=='.' or event.key=='right':
            if self.counter<self.maxDataInd:
                self.counter+=1
            else:
                self.counter=0
            self.redraw()

    def title_plot(self):
        plt.title("{}/{}: Press < or > to flip through data\n{}".format(self.counter,
                                                                        self.maxDataInd,
                                                                        self.originalPlotTitle))


