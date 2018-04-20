#!/usr/bin/env python

'''
Functions and classes for analysis of spikes.
'''


import numpy as np

def eventlocked_spiketimes(timeStamps,eventOnsetTimes,timeRange,spikeindex=False):
    '''Create a vector with the spike timestamps w.r.t. events onset.

    (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial) =
        eventlocked_spiketimes(timeStamps,eventOnsetTimes,timeRange)

    timeStamps: (np.array) the time of each spike.
    eventOnsetTimes: (np.array) the time of each instance of the event to lock to.
    timeRange: (list or np.array) two-element array specifying time-range to extract around event.

    spikeTimesFromEventOnset: 1D array with time of spikes locked to event.
    trialIndexForEachSpike: 1D array with the trial corresponding to each spike.
       The first spike index is 0.
    indexLimitsEachTrial: [2,nTrials] range of spikes for each trial. Note that
       the range is from firstSpike to lastSpike+1 (like in python slices)
    spikeIndices
    '''
    nTrials = len(eventOnsetTimes)
    # FIXME: check if timestamps are sorted. We will use searchsorted() later.

    spikeTimesFromEventOnset = np.empty(0,dtype='float64')
    spikeIndices = np.empty(0,dtype='int')
    trialIndexForEachSpike = np.empty(0,dtype='int')
    indexLimitsEachTrial = np.empty((2,nTrials),dtype='int')
    accumIndexFirstSpike = 0

    for indtrial in np.arange(nTrials):
        thisTrialRange = eventOnsetTimes[indtrial] + timeRange
        firstSpikeInTrial = np.searchsorted(timeStamps,thisTrialRange[0])
        # NOTE: lastSpikeInTrial must not be negative, because slice(0,-1) means from 0 to last.
        lastSpikeInTrialPlusOne = np.searchsorted(timeStamps,thisTrialRange[-1])
        spikesThisTrial = np.arange(firstSpikeInTrial,lastSpikeInTrialPlusOne)
        nSpikesThisTrial = lastSpikeInTrialPlusOne - firstSpikeInTrial

        spikeIndices = np.concatenate((spikeIndices,spikesThisTrial))
        spikeTimesFromEventOnset = np.concatenate((spikeTimesFromEventOnset,
                                        timeStamps[spikesThisTrial]-eventOnsetTimes[indtrial]))
        trialIndexForEachSpike = np.concatenate((trialIndexForEachSpike,
                                            np.repeat(indtrial,nSpikesThisTrial)))
        indexLimitsEachTrial[:,indtrial] = [accumIndexFirstSpike,accumIndexFirstSpike+nSpikesThisTrial]
        accumIndexFirstSpike += nSpikesThisTrial
    if spikeindex:
        return (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial,spikeIndices)
    else:
        return (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial)

def minimum_event_onset_diff(eventOnsetTimes, minEventOnsetDiff):
    '''
    Exclude events that happen too soon after a preceeding event. Useful for plotting
    responses to trains of stimuli (Only consider the first pulse of the train as an event onset)

    Args:
        eventOnsetTimes (array): Array of event onset timestamps
        minEventOnsetDiff (float): Minimum inter-event time for events to be considered
                                   independent.
    Returns:
        eventOnsetTimes (array): Array of event timestamps
    '''

    evdiff = np.r_[1.0, np.diff(eventOnsetTimes)]
    eventOnsetTimes = eventOnsetTimes[evdiff>minEventOnsetDiff]
    return eventOnsetTimes

def spiketimes_to_spikecounts(spikeTimesFromEventOnset,indexLimitsEachTrial,binEdges):
    '''
    Create a matrix with spike counts given the times of the spikes.

    spikeTimesFromEventOnset: vector of spikes timestamps with respect
    to the onset of the event.
    indexLimitsEachTrial: each column contains [firstInd,lastInd+1] of the spikes on a trial
    binEdges: time bin edges (including the left-most and right-most).

    Returns:
    spikeCountMat: each column is one trial. N rows is len(binEdges)-1
    '''
    nTrials = indexLimitsEachTrial.shape[1]
    spikeCountMat = np.empty((nTrials,len(binEdges)-1),dtype=int)
    for indtrial in range(nTrials):
        indsThisTrial = slice(indexLimitsEachTrial[0,indtrial],indexLimitsEachTrial[1,indtrial])
        spkCountThisTrial,binsEdges = np.histogram(spikeTimesFromEventOnset[indsThisTrial],binEdges)
        spikeCountMat[indtrial,:] = spkCountThisTrial
    return spikeCountMat


def response_score(spikeTimesFromEventOnset,indexLimitsEachTrial,baseRange,binEdges):
    '''
    Evaluate the probability of observing changes in firing on time periods given by binEdges
    with respect to the baseline range.

    NOTE: the duration of the the bins should be the same as that of the baseline period.

    TODO:
    - Change the statistic: ranksums is meant for continuous distributions.
                            and it does not handle ties.
    '''
    from scipy import stats
    rangeLength = np.diff(baseRange)
    nBins = len(binEdges)-1
    nspkBase = spiketimes_to_spikecounts(spikeTimesFromEventOnset,indexLimitsEachTrial,baseRange)
    nspkResp = spiketimes_to_spikecounts(spikeTimesFromEventOnset,indexLimitsEachTrial,binEdges)

    zStatsEachRange = np.empty(nBins)
    pValueEachRange = np.empty(nBins)
    for indbin in range(nBins):
        [zStatsEachRange[indbin],pValueEachRange[indbin]] = \
            stats.ranksums(nspkResp[:,indbin],nspkBase[:,0])
    maxZvalue = zStatsEachRange[np.argmax(np.abs(zStatsEachRange))]
    return (zStatsEachRange,pValueEachRange,maxZvalue)


def evaluate_modulation(spikeTimesFromEventOnset,indexLimitsEachTrial,responseRange,trialsEachCond):
    '''
    Evaluate the response for each of two conditions and the probability of observing this
    difference by chance.

    Args:
       trialsEachCond: list of two arrays of indexes (either bool or int)

    Returns:
       (meanSpikes,pValue)
    '''
    from scipy import stats
    nspkResp = []
    for indcond,trialsThisCond in enumerate(trialsEachCond):
        indexLimitsSubset = indexLimitsEachTrial[:,trialsThisCond]
        nspkResp.append(spiketimes_to_spikecounts(spikeTimesFromEventOnset,
                                                  indexLimitsSubset,responseRange).flatten())
    meanSpikes = np.array([np.mean(n) for n in nspkResp])
    [zStat,pValue] = stats.ranksums(nspkResp[0],nspkResp[1])
    return (meanSpikes,pValue)

def avg_num_spikes_each_condition(trialsEachCondition, indexLimitsEachTrial):
    '''
    Returns the average number of spikes (after an event) for each condition.
    Relies on indexLimitsEachTrial from eventlocked_spiketimes() above, so the average
    number of spikes returned is over the time range used in that function.

    This function works with two types of 'trialsEachCondition' arrays. You can either
    use the output of behavioranalysis.find_trials_each_type(), which uses a single
    sorting variable, or you can use the output of behavioranalysis.find_trials_each_combination(),
    which uses a combination of two sorting variables.

    Args:
        trialsEachCondition (array): Array of shape (nTrials, nValues1) OR (nTrials, nValues1, nValues2)
        indexLimitsEachTrial (array): Array of shape (2, nTrials): Range of spike indices for each trial
    Returns:
       avgSpikesArray (array): Array of shape (nValues1,) or (nValues1, nValues2) depending on the shape
           of the trialsEachCondition argument. Contains the average number of spikes in each condition
           (defined by either one of nValues1 or a combination of a value in nValues1 and a value in nValues2).
    '''

    print "WARNING!!! avg_num_spikes_each_condition is deprecated and will be removed in the next version of jaratoolbox."

    numSpikesInTimeRangeEachTrial = np.squeeze(np.diff(indexLimitsEachTrial, axis=0))
    conditionMatShape = np.shape(trialsEachCondition)
    # -- We repeat and reshape the number of spikes each trial so it matches the shape of trialsEachCondition
    numRepeats = np.product(conditionMatShape[1:])
    nSpikesMat = np.reshape(numSpikesInTimeRangeEachTrial.repeat(numRepeats), conditionMatShape)
    # -- Then we filter the repeated array by the boolean trialsEachCondition matrix
    spikesFilteredByTrialType = nSpikesMat * trialsEachCondition
    # -- We can sum the filtered array to get total spikes in each condition, the divide by
    # -- the sum of the numeric representation (1/0) of the boolean array, which is number of trials
    # -- for each condition.
    avgSpikesArray = np.sum(spikesFilteredByTrialType, axis=0) / np.sum(trialsEachCondition, axis=0).astype('float')
    return avgSpikesArray


def response_latency(spikeTimesFromEventOnset, indexLimitsEachTrial, timeRange, threshold=0.5, win=None):
    '''
    Calculate response latency as time point where smooth PSTH crosses some fraction of
    the (baseline subtracted) max response.

    Args: 
        timeRange (list): 2-item list defining time-range of the data.
        threshold (float): fraction of max response (baseline subtracted).
        win (np.ndarray): window to use for smoothing. Default is hanning(7).
    '''
    if win is None:
        win = np.array([0, 0.25, 0.75, 1, 0.75, 0.25, 0]) # scipy.signal.hanning(7)
    win = win/np.sum(win)
    binEdges = np.arange(timeRange[0],timeRange[-1],0.001)
    timeVec = binEdges[1:]  # FIXME: is this the best way to define the time axis?
    spikeCountMat = spiketimes_to_spikecounts(spikeTimesFromEventOnset,indexLimitsEachTrial,binEdges)
    avResp = np.mean(spikeCountMat,axis=0)
    smoothPSTH = np.convolve(avResp,win, mode='same')
    baselineBins = (timeVec<0)
    if not np.any(baselineBins):
        raise ValueError('The data needs to include a period before the stimulus.')
    avBaseline = np.mean(smoothPSTH[baselineBins])
    maxResp = np.max(smoothPSTH)
    thresholdSpikeCount = avBaseline + 0.5*(maxResp-avBaseline)
    respLatencyInd = np.flatnonzero(smoothPSTH>thresholdSpikeCount)[0]
    yDiff = (smoothPSTH[respLatencyInd]-smoothPSTH[respLatencyInd-1])
    yFraction = (thresholdSpikeCount-smoothPSTH[respLatencyInd-1])/ yDiff
    respLatency = timeVec[respLatencyInd-1] + yFraction*(timeVec[respLatencyInd]-timeVec[respLatencyInd-1])
    interim = {'timeVec':timeVec,'avgCount':avResp,'psth':smoothPSTH,'baseline':avBaseline,
               'maxResponse':maxResp,'threshold':thresholdSpikeCount}
    return (respLatency,interim)

    
"""
def calculate_psth(spikeRasterMat,timeVec,windowSize):
    '''Calculate Peri-Stimulus Time Histogram.
    It uses a square window and returns the average spikes per second.
    '''
    nTrials = spikeRasterMat.shape[0]
    deltaTime = timeVec[1]-timeVec[0]
    windowSizeInSamples = int(round(windowSize/deltaTime))

    windowShape = np.ones(windowSizeInSamples,dtype=np.float64)
    windowShape = windowShape/(windowSizeInSamples*deltaTime)
    '''
    PSTHeach = np.empty(spikeRasterMat.shape,dtype=np.float64)
    for indt,trial in enumerate(spikeRasterMat):
        PSTHeach[indt,:] = np.convolve(trial,windowShape,'same')
    PSTH = np.mean(PSTHeach,axis=0)
    '''
    spikeMatMean = np.mean(spikeRasterMat,axis=0)
    PSTH = np.convolve(spikeMatMean,windowShape,'same')
    return PSTH
"""


if __name__ == "__main__":
    CASE = 2
    if CASE==1:
        timeStamps = np.array([4,10,25,27,29])
        eventOnsetTimes = np.array([5,15,25,35])
        timeRange = [-5,10]
        (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial,spikeIndices) = eventlocked_spiketimes(timeStamps,eventOnsetTimes,timeRange,spikeindex=True)
        print spikeTimesFromEventOnset
        print trialIndexForEachSpike
        print indexLimitsEachTrial
        print spikeIndices
        nSpikes = count_spikes_in_range(spikeTimesFromEventOnset,indexLimitsEachTrial,timeRange)
        print nSpikes
    if CASE==2:
        timeStamps = np.array([4,10,25,27,29])
        eventOnsetTimes = np.array([5,15,25,35])
        timeRange = [-5,10]
        (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial,spikeIndices) = eventlocked_spiketimes(timeStamps,eventOnsetTimes,timeRange,spikeindex=True)
        #nSpikes = spiketimes_to_spikecounts(spikeTimesFromEventOnset,indexLimitsEachTrial,timeRange)
        trialsEachCond = [[0,2],[1,3]]
        responseRange = [-3,3]
        (meanSpikes,pValue) = evaluate_modulation(spikeTimesFromEventOnset,indexLimitsEachTrial,responseRange,trialsEachCond)
        print (meanSpikes,pValue)
