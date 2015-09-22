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

"""
def count_spikes_in_range(spikeTimesFromEventOnset,indexLimitsEachTrial,timeRange):
    '''
    OBSOLETE: use spiketimes_to_spikecounts() instead

    Count number of spikes on each trial in a given time range.

       spikeTimesFromEventOnset: vector of spikes timestamps with respect
         to the onset of the event.
       indexLimitsEachTrial: each column contains [firstInd,lastInd+1] of the spikes on a trial.
       timeRange: time range to evaluate. Spike times exactly at the limits are not counted.

       returns nSpikes
    '''
    nTrials = indexLimitsEachTrial.shape[1]
    nSpikes = np.empty(nTrials,dtype=int)
    for indtrial in range(nTrials):
        indsThisTrial = slice(indexLimitsEachTrial[0,indtrial],indexLimitsEachTrial[1,indtrial])
        spikeTimesThisTrial = spikeTimesFromEventOnset[indsThisTrial]
        nSpikes[indtrial] = sum((spikeTimesThisTrial>timeRange[0]) & (spikeTimesThisTrial<timeRange[-1]))
    return nSpikes
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
