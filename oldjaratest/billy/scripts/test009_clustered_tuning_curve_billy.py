'''
Plot the average firing rate in response to each frequency presented.
'''

#import allcells_noisetest as allcells
from jaratoolbox import ephyscore
from jaratoolbox import loadbehavior
from jaratoolbox import loadopenephys
from jaratoolbox import spikesanalysis
from jaratoolbox import settings
from jaratoolbox import spikesorting_ISI as spikesorting
import numpy as np
from pylab import *
import os
import sys
import importlib

mouseName = str(sys.argv[1]) #the first argument is the mouse name to tell the script which allcells file to use
allcellsFileName = 'allcells_'+mouseName+'_tuning'###########################################
sys.path.append(settings.ALLCELLS_PATH)
allcells = importlib.import_module(allcellsFileName)

SAMPLING_RATE=30000.0
timeRange=[-0.2, 0.3] #In seconds
responseRange = [0.000,0.10] #range of time to count spikes in after event onset in seconds


outputDir = '/home/billywalker/Pictures/tuning/'
#nametrialsToUse = 'tuning_curve'
numOfCells = len(allcells.cellDB) #number of cells that were clustered on all sessions clustered
ephysRootDir = '/home/billywalker/data/ephys/'
behaviorDir='/home/billywalker/data/behavior/billy/'


fulloutputDir = outputDir+mouseName+'/'
if not os.path.exists(fulloutputDir):
    os.makedirs(fulloutputDir)

for cellID in range(0,numOfCells):
    oneCell = allcells.cellDB[cellID]
    
    subject = oneCell.animalName
    behavSession = oneCell.behavSession
    print behavSession
    ephysSession = oneCell.ephysSession
    ephysRoot = ephysRootDir+subject+'/'
    tetrodeID = oneCell.tetrode
    clusterID = oneCell.cluster


    fullbehaviorDir = behaviorDir+subject+'/'
    behavName = subject+'_tuning_curve_'+behavSession+'.h5'
    behavDataFileName=os.path.join(fullbehaviorDir, behavName)


    bdata = loadbehavior.BehaviorData(behavDataFileName,readmode='full')
    freqEachTrial = bdata['currentFreq']
    possibleFreq = np.unique(freqEachTrial)
    numberOfTrials = len(freqEachTrial)

    # -- The old way of sorting (useful for plotting sorted raster) --
    sortedTrials = []
    numTrialsEachFreq = []  #Used to plot lines after each group of sorted trials
    for indf,oneFreq in enumerate(possibleFreq): #indf is index of this freq and oneFreq is the frequency
        indsThisFreq = np.flatnonzero(freqEachTrial==oneFreq) #this gives indices of this frequency
        sortedTrials = np.concatenate((sortedTrials,indsThisFreq)) #adds all indices to a list called sortedTrials
        numTrialsEachFreq.append(len(indsThisFreq)) #finds number of trials each frequency has
    sortingInds = argsort(sortedTrials) #gives array of indices that would sort the sortedTrials

    # -- Load event data and convert event timestamps to ms --
    ephysDir = os.path.join(ephysRoot, ephysSession)
    eventFilename=os.path.join(ephysDir, 'all_channels.events')
    ev=loadopenephys.Events(eventFilename) #load ephys data (like bdata structure)
    eventTimes=np.array(ev.timestamps)/SAMPLING_RATE #get array of timestamps for each event and convert to seconds by dividing by sampling rate (Hz). matches with eventID and 
    evID=np.array(ev.eventID)  #loads the onset times of events (matches up with eventID to say if event 1 went on (1) or off (0)
    eventOnsetTimes=eventTimes[evID==1] #array that is a time stamp for when the chosen event happens.
    #ev.eventChannel woul load array of events like trial start and sound start and finish times (sound event is 0 and trial start is 1 for example). There is only one event though and its sound start
    while (numberOfTrials < len(eventOnsetTimes)):
        eventOnsetTimes = eventOnsetTimes[:-1]




    #raw_input("Press Enter to continue...")

	
    spkData = ephyscore.CellData(oneCell)
    spkTimeStamps = spkData.spikes.timestamps


    '''
    spike_filename=os.path.join(fullephysDir, 'Tetrode{0}.spikes'.format(tetrodeID)) #make a path to ephys spike data of specified tetrode tetrodeID
    sp=loadopenephys.DataSpikes(spike_filename) #load spike data from specified tetrode tetrodeID
    spkTimeStamps=np.array(sp.timestamps)/SAMPLING_RATE #array of timestamps for each spike in seconds (thats why you divide by sampling rate)
    '''


    (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial) = spikesanalysis.eventlocked_spiketimes(spkTimeStamps,eventOnsetTimes,timeRange)
    '''
        Create a vector with the spike timestamps w.r.t. events onset.

        (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial) = 
            eventlocked_spiketimes(timeStamps,eventOnsetTimes,timeRange)

        timeStamps: (np.array) the time of each spike.
        eventOnsetTimes: (np.array) the time of each instance of the event to lock to.
        timeRange: (list or np.array) two-element array specifying time-range to extract around event.

        spikeTimesFromEventOnset: 1D array with time of spikes locked to event.
    o    trialIndexForEachSpike: 1D array with the trial corresponding to each spike.
           The first spike index is 0.
        indexLimitsEachTrial: [2,nTrials] range of spikes for each trial. Note that
           the range is from firstSpike to lastSpike+1 (like in python slices)
        spikeIndices
    '''

    sortedIndexForEachSpike = sortingInds[trialIndexForEachSpike] #Takes values of trialIndexForEachSpike and finds value of sortingInds at that index and makes array. This array gives an array with the sorted index of each trial for each spike


    # -- Calculate tuning --
    nSpikes = spikesanalysis.spiketimes_to_spikecounts(spikeTimesFromEventOnset,indexLimitsEachTrial,responseRange) #array of the number of spikes in range for each trial
    '''Count number of spikes on each trial in a given time range.

           spikeTimesFromEventOnset: vector of spikes timestamps with respect
             to the onset of the event.
           indexLimitsEachTrial: each column contains [firstInd,lastInd+1] of the spikes on a trial.
           timeRange: time range to evaluate. Spike times exactly at the limits are not counted.

           returns nSpikes
    '''
    meanSpikesEachFrequency = np.empty(len(possibleFreq)) #make empty array of same size as possibleFreq

    # -- This part will be replace by something like behavioranalysis.find_trials_each_type --
    trialsEachFreq = []
    for indf,oneFreq in enumerate(possibleFreq):
        trialsEachFreq.append(np.flatnonzero(freqEachTrial==oneFreq)) #finds indices of each frequency. Appends them to get an array of indices of trials sorted by freq

    # -- Calculate average firing for each freq --
    for indf,oneFreq in enumerate(possibleFreq):
        meanSpikesEachFrequency[indf] = np.mean(nSpikes[trialsEachFreq[indf]])

    clf()
    if (len(spkTimeStamps)>0):
        ax1 = plt.subplot2grid((4,4), (3, 0), colspan=1)
        spikesorting.plot_isi_loghist(spkData.spikes.timestamps)
        ax3 = plt.subplot2grid((4,4), (3, 3), colspan=1)
        spikesorting.plot_events_in_time(spkTimeStamps)
        samples = spkData.spikes.samples.astype(float)-2**15
        samples = (1000.0/spkData.spikes.gain[0,0]) *samples
        ax2 = plt.subplot2grid((4,4), (3, 1), colspan=2)
        spikesorting.plot_waveforms(samples)
    ax4 = plt.subplot2grid((4,4), (0, 0), colspan=3,rowspan = 3)
    plot(spikeTimesFromEventOnset, sortedIndexForEachSpike, '.', ms=3)
    axvline(x=0, ymin=0, ymax=1, color='r')

    #The cumulative sum of the list of specific frequency presentations, 
    #used below for plotting the lines across the figure. 
    numTrials = cumsum(numTrialsEachFreq)

    #Plot the lines across the figure in between each group of sorted trials
    for indf, num in enumerate(numTrials):
        ax4.axhline(y = num, xmin = 0, xmax = 1, color = '0.90', zorder = 0)
        #ax2.text(timeRange[0]-0.075, numTrials - mean(numTrialsEachFreq)/2, "%0.2f" % (possibleFreq[indf]/1000), color = 'grey', va = 'center')

    tickPositions = numTrials - mean(numTrialsEachFreq)/2
    tickLabels = ["%0.2f" % (possibleFreq[indf]/1000) for indf in range(len(possibleFreq))]
    ax4.set_yticks(tickPositions)
    ax4.set_yticklabels(tickLabels)
    ylabel('Frequency Presented (kHz), {} total trials'.format(numTrials[-1]))
    title(ephysSession+' T{}c{}'.format(tetrodeID,clusterID))
    xlabel('Time (sec)')


    ax5 = plt.subplot2grid((4,4), (0, 3), colspan=1,rowspan=3)
    ax5.set_xscale('log')
    plot(possibleFreq,meanSpikesEachFrequency,'o-')
    ylabel('Avg spikes in window {0}-{1} sec'.format(*responseRange))
    xlabel('Frequency')

    #show()


    tetrodeClusterName = 'T'+str(tetrodeID)+'c'+str(clusterID)
    plt.gcf().set_size_inches((8.5,11))
    figformat = 'png' #'png' #'pdf' #'svg'
    filename = 'tuning_%s_%s_%s.%s'%(subject,behavSession,tetrodeClusterName,figformat)
    fullFileName = os.path.join(fulloutputDir,filename)
    print 'saving figure to %s'%fullFileName
    plt.gcf().savefig(fullFileName,format=figformat)
