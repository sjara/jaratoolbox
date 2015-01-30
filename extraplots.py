'''
Additional function for modifying plots.
'''


import matplotlib.pyplot as plt
import numpy as np

def boxoff(ax,keep='left',yaxis=True):
    '''
    Hide axis lines, except left and bottom.
    You can specify to keep instead right and bottom with keep='right'
    '''
    ax.spines['top'].set_visible(False)
    if keep=='left':
        ax.spines['right'].set_visible(False)
    else:
        ax.spines['left'].set_visible(False)        
    xtlines = ax.get_xticklines()
    ytlines = ax.get_yticklines()
    for t in xtlines[1::2]+ytlines[1::2]:
        t.set_visible(False)
    if not yaxis:
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ytlines = ax.get_yticklines()
        for t in ytlines:
            t.set_visible(False)

def set_ticks_fontsize(ax,fontSize):
    '''
    Set fontsize of axis tick labels
    '''
    plt.setp(ax.get_xticklabels(),fontsize=fontSize)
    plt.setp(ax.get_yticklabels(),fontsize=fontSize)


def raster_plot(spikeTimesFromEventOnset,indexLimitsEachTrial,timeRange,trialsEachCond=[],
                colorEachCond=None,fillWidth=None,labels=None):
    '''
    Plot spikes raster plot grouped by condition
    Returns (pRaster,hcond)
    First trial is plotted at y=0
    '''
    import matplotlib.pyplot as plt

    if trialsEachCond==[]:
        nCond=1
        trialsEachCond = [np.arange(indexLimitsEachTrial.shape[1])]
    else:
        nCond = len(trialsEachCond)
    nTrialsEachCond = [len(x) for x in trialsEachCond]

    if colorEachCond is None:
        colorEachCond = ['0.5','0.75']*np.ceil(nCond/2.0)

    if fillWidth is None:
        fillWidth = 0.05*np.diff(timeRange)

    nTrials = len(indexLimitsEachTrial[0])
    nSpikesEachTrial = np.diff(indexLimitsEachTrial,axis=0)[0]
    nSpikesEachTrial = nSpikesEachTrial*(nSpikesEachTrial>0) # Some are negative
    trialIndexEachCond = []
    spikeTimesEachCond = []
    for indcond,trialsThisCond in enumerate(trialsEachCond):
        spikeTimesThisCond = np.empty(0,dtype='float64')
        trialIndexThisCond = np.empty(0,dtype='int')
        for indtrial,thisTrial in enumerate(trialsThisCond):
            indsThisTrial = slice(indexLimitsEachTrial[0,thisTrial],
                                  indexLimitsEachTrial[1,thisTrial])
            spikeTimesThisCond = np.concatenate((spikeTimesThisCond,
                                                 spikeTimesFromEventOnset[indsThisTrial]))
            trialIndexThisCond = np.concatenate((trialIndexThisCond,
                                                 np.repeat(indtrial,nSpikesEachTrial[thisTrial])))
        trialIndexEachCond.append(np.copy(trialIndexThisCond))
        spikeTimesEachCond.append(np.copy(spikeTimesThisCond))

    xpos = timeRange[0]+np.array([0,fillWidth,fillWidth,0])
    lastTrialEachCond = np.cumsum(nTrialsEachCond)
    firstTrialEachCond = np.r_[0,lastTrialEachCond[:-1]]

    hcond=[]
    pRaster = []
    ax = plt.gca()
    for indcond in range(nCond):
        pRasterOne, = plt.plot(spikeTimesEachCond[indcond],
                            trialIndexEachCond[indcond]+firstTrialEachCond[indcond],'.k',
                            rasterized=True)
        pRaster.append(pRasterOne)
        plt.hold(True)
        ypos = np.array([firstTrialEachCond[indcond],firstTrialEachCond[indcond],
                         lastTrialEachCond[indcond],lastTrialEachCond[indcond]])-0.5
        hcond.extend(plt.fill(xpos,ypos,ec='none',fc=colorEachCond[indcond]))
        hcond.extend(plt.fill(xpos+np.diff(timeRange)-fillWidth,ypos,ec='none',
                              fc=colorEachCond[indcond]))
    plt.hold(False)
    plt.xlim(timeRange)
    plt.ylim(-0.5,nTrials-0.5)

    if labels:
        labelsPos = (lastTrialEachCond+firstTrialEachCond)/2.0 -0.5
        ax.set_yticks(labelsPos)
        ax.set_yticklabels(labels)

    #axvline(0,color='0.75',zorder=-10)

    return(pRaster,hcond)
