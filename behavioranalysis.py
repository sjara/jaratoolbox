'''
Tools for analyzing behavioral data.
'''

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from jaratoolbox import extrafuncs
from jaratoolbox import extraplots
from jaratoolbox import loadbehavior
from jaratoolbox import settings
from jaratoolbox import colorpalette

EXPERIMENTER = settings.DEFAULT_EXPERIMENTER
FREQCOLORS = [colorpalette.TangoPalette['Chameleon3'],
              colorpalette.TangoPalette['ScarletRed1'],
              colorpalette.TangoPalette['SkyBlue2'] ]
#colorpalette.TangoPalette['Orange2']

def find_trials_each_type(parameter,parameterPossibleValues):
    nTrials = len(parameter)
    nValues = len(parameterPossibleValues)
    trialsEachType = np.zeros((nTrials,nValues),dtype=bool)
    for indval,paramValue in enumerate(parameterPossibleValues):
        trialsEachType[:,indval] = (parameter==paramValue)
    return trialsEachType

'''    
,validTrials=[]
    if(not len(validTrials)):
        validTrials = np.ones(nTrials,dtype=bool)
        trialsEachType[:,indval] = trialsThisValue & validTrials
'''

def find_trials_each_type_each_block(psyCurveParameter,psyCurveParameterPossibleValues,\
                                     currentBlock,currentBlockPossibleValues,validTrials=[]):
    '''
    Parameters
    ----------
    psyCurveParameter
    psyCurveParameterPossibleValues
    currentBlock
    currentBlockPossibleValues
    validTrials

    Returns
    -------
    trialsEachType: [nTrials,nParamValues,nBlockTypes] (boolean)

    See also:
    extracellpy.sessionanalysis.trials_by_condition()
    '''
    nTrials = len(psyCurveParameter)
    nValues = len(psyCurveParameterPossibleValues)
    nBlockTypes = len(currentBlockPossibleValues)
    if(not len(validTrials)):
        validTrials = np.ones(nTrials,dtype=bool)

    trialsEachBlock = np.zeros((nTrials,nBlockTypes),dtype=bool)
    for indb,blockID in enumerate(currentBlockPossibleValues):
        trialsEachBlock[:,indb] = (currentBlock==blockID)
    trialsEachType = np.zeros((nTrials,nValues,nBlockTypes),dtype=bool)
    for indval,paramValue in enumerate(psyCurveParameterPossibleValues):
        trialsThisValue = (psyCurveParameter==paramValue)
        for indb in range(nBlockTypes):
            trialsEachType[:,indval,indb] = trialsThisValue & \
                                            trialsEachBlock[:,indb] & validTrials
        
    return trialsEachType



def behavior_summary(subjects,sessions,trialslim=[],outputDir='',paradigm=None,soundfreq=None):
    '''
    subjects: an array of animals to analyze (it can also be a string for a single animal)
    sessions: an array of sessions to analyze (it can also be a string for a single session)
    trialslim: array to set xlim() of dynamics' plot
    outputDir: where to save the figure (if not specified, nothing will be saved)
    paradigm: load data from a different paradigm. Warning: data should be loaded with
              loadbehavior.ReversalBehaviorData().
    '''
    if isinstance(subjects,str):
        subjects = [subjects]
    if isinstance(sessions,str):
        sessions = [sessions]
    nSessions = len(sessions)
    nAnimals = len(subjects)

    loadingClass = loadbehavior.FlexCategBehaviorData
    paradigm = '2afc'

    gs = gridspec.GridSpec(nSessions*nAnimals, 3)
    gs.update(hspace=0.5,wspace=0.4)
    plt.clf()
    for inds,thisSession in enumerate(sessions):
        for inda,animalName in enumerate(subjects):
            try:
                behavFile = loadbehavior.path_to_behavior_data(animalName,EXPERIMENTER,paradigm,thisSession)
                behavData = loadingClass(behavFile,readmode='full')
            except IOError:
                print thisSession+' does not exist'
                continue
            print 'Loaded %s %s'%(animalName,thisSession)
            behavData.find_trials_each_block()
            thisAnimalPos = 3*inda*nSessions
            thisPlotPos = thisAnimalPos+3*inds
            ax1=plt.subplot(gs[thisPlotPos])
            plot_summary(behavData,fontsize=8)
            ax2=plt.subplot(gs[thisPlotPos+1:thisPlotPos+3])
            plot_dynamics(behavData,winsize=40,fontsize=8,soundfreq=soundfreq)
            plt.setp(ax1.get_xticklabels(),visible=False)
            ax1xlabel = ax1.get_xlabel()
            ax2xlabel = ax2.get_xlabel()
            ax1.set_xlabel('')
            ax2.set_xlabel('')
            if trialslim:
                plt.xlim(trialslim)
            plt.draw()
            plt.show()
    plt.setp(ax1.get_xticklabels(),visible=True)
    plt.setp(ax2.get_xticklabels(),visible=True)
    ax1.set_xlabel(ax1xlabel)
    ax2.set_xlabel(ax2xlabel)
    #plt.draw()
    #plt.show()
                      
    if len(outputDir):
        animalStr = '-'.join(subjects)
        sessionStr = '-'.join(sessions)
        plt.gcf().set_size_inches((8.5,11))
        figformat = 'png' #'png' #'pdf' #'svg'
        filename = 'behavior_%s_%s.%s'%(animalStr,sessionStr,figformat)
        fullFileName = os.path.join(outputDir,filename)
        print 'saving figure to %s'%fullFileName
        plt.gcf().savefig(fullFileName,format=figformat)



def plot_summary(behavData,fontsize=12):
    '''Show summary of performance.
    First argument is an object created by loadbehavior.BehaviorData (or subclasses)
    '''
    correct = behavData['outcome']==behavData.labels['outcome']['correct']
    early = behavData['outcome']==behavData.labels['outcome']['invalid']
    possibleFreq = np.unique(behavData['targetFrequency'])
    possibleBlockID = np.unique(behavData['currentBlock'])
    trialsEachType = find_trials_each_type_each_block(behavData['targetFrequency'],possibleFreq,
                                                      behavData['currentBlock'],possibleBlockID)
    validTrialsEachType = trialsEachType & behavData['valid'][:,np.newaxis,np.newaxis].astype(bool)
    correctTrialsEachType = validTrialsEachType & correct[:,np.newaxis,np.newaxis]
    nCorrectEachType = np.sum(correctTrialsEachType,axis=0)
    nValidEachType = np.sum(validTrialsEachType,axis=0)

    #perfEachType = np.where(nValidEachType>0, nCorrectEachType/nValidEachType.astype(float), np.nan)
    perfEachType = nCorrectEachType/nValidEachType.astype(float)

    # --- Plot results ---
    itemsToPlot = nValidEachType.flatten()>0  #~np.isnan(perfEachType.flatten())
    perfToPlot = perfEachType.flatten()[itemsToPlot] # Show only 2 freq for each block type
    freqLabels = np.repeat(possibleFreq,len(possibleBlockID))[itemsToPlot]
    nValidCounts = nValidEachType.flatten()[itemsToPlot]
    xPos = [0,1,3,4][:len(perfToPlot)]
    ax = plt.gca()
    ax.set_xlim([-1,5])
    ax.set_ylim([0,100])
    plt.hold(True)
    hline50 = plt.axhline(50,linestyle=':',color='k',zorder=-1)
    hline75 = plt.axhline(75,linestyle=':',color='k',zorder=-1)
    hbars = plt.bar(xPos,100*perfToPlot,align='center',fc=[0.8,0.8,0.8],ec='k')
    for thispos,thistext in zip(xPos,nValidCounts):
        plt.text(thispos,10,str(thistext),ha='center',fontsize=fontsize)
    ax.set_ylabel('% correct',fontsize=fontsize)
    ax.set_xticks(xPos)
    ax.set_xticklabels(freqLabels/1000)

    titleStr = '{0} [{1}] {2}\n'.format(behavData.session['subject'],behavData.session['date'],
                                        behavData.session['hostname'])
    titleStr += '{0} valid, {1:.0%} early'.format(sum(nValidCounts),np.mean(early))
    ax.set_title(titleStr,fontweight='bold',fontsize=fontsize,y=0.95)
    ax.set_xlabel('Frequency (kHz)',fontsize=fontsize)
    extraplots.set_ticks_fontsize(ax,fontsize)
    plt.draw()
    plt.show()





def plot_dynamics(behavData,winsize=40,fontsize=12,soundfreq=None):
    '''
    Plot performance in time for one session.
    First argument is an object created by loadbehavior.BehaviorData (or subclasses)
    '''
    ax = plt.gca()
    ax.cla()
    lineWidth = 2
    if not soundfreq:
        possibleFreq = np.unique(behavData['targetFrequency'])
    else:
        possibleFreq = soundfreq
    possibleColors = FREQCOLORS + ['k','m','c', 'b','r','g']
    colorEachFreq = dict(zip(possibleFreq,possibleColors))

    behavData.find_trials_each_block()

    nBlocks = behavData.blocks['nBlocks']
    trialsEachBlock = behavData.blocks['trialsEachBlock']
    validEachBlock = trialsEachBlock & (behavData['valid'][:,np.newaxis].astype(bool))
    nValidEachBlock = np.sum(validEachBlock,axis=0)
    lastValidEachBlock = np.cumsum(nValidEachBlock) # Actually, these values correspond to lastIndex+1
    firstValidEachBlock = np.concatenate(([0],lastValidEachBlock[:-1]))
    rightChoice = behavData['choice']==behavData.labels['choice']['right']

    for indb in range(nBlocks):
        trialsThisBlock = trialsEachBlock[:,indb]
        validThisBlock = validEachBlock[:,indb]
        for indf,thisFreq in enumerate(possibleFreq):
            thisColor = colorEachFreq[thisFreq]
            trialsThisFreq = (behavData['targetFrequency']==thisFreq)
            choiceVecThisFreq = np.ma.masked_array(rightChoice[validThisBlock])
            choiceVecThisFreq.mask = ~trialsThisFreq[validThisBlock]
            movAvChoice = extrafuncs.moving_average_masked(choiceVecThisFreq,winsize)
            plt.plot(range(firstValidEachBlock[indb],lastValidEachBlock[indb]),100*movAvChoice,
                 lw=lineWidth,color=thisColor)
            plt.hold(True)
    plt.ylim([-5,105])
    plt.axhline(50,color='0.5',ls='--')
    plt.ylabel('% rightward',fontsize=fontsize)
    plt.xlabel('Trial',fontsize=fontsize)
    extraplots.set_ticks_fontsize(ax,fontsize)
    plt.draw()
    plt.show()


if __name__ == "__main__":

    CASE=2
    if CASE==1:
        from jaratoolbox import loadbehavior
        import numpy as np
        experimenter = 'santiago'
        paradigm = '2afc'
        subject = 'test020'
        session = '20140421a'

        behavFile = loadbehavior.path_to_behavior_data(subject,experimenter,paradigm,session)
        behavData = loadbehavior.FlexCategBehaviorData(behavFile,readmode='full')
        behavData.find_trials_each_block()
 
        #trialsEachBlock = behavData.blocks['trialsEachBlock']
        #nValidEachBlock = np.sum(trialsEachBlock & (~behavData['valid'][:,np.newaxis]),axis=0)
        #validEachBlock = trialsEachBlock & behavData['valid'][:,np.newaxis].astype(bool)

        #plot_dynamics(behavData,winsize=100)
        plot_summary(behavData)
        #tet = find_trials_each_type(behavData['targetFrequency'],np.unique(behavData['targetFrequency']),
        #                            behavData['currentBlock'],np.unique(behavData['currentBlock']))

    elif CASE==2:
        if 1:
            subjects = ['test011','test012','test013','test014','test015',
                        'test016','test017','test018','test019','test020']
        else:
            subjects = ['test050','test051','test052','test053','test054',
                        'test055','test056','test057','test058','test059']
        #subjects = ['test019','test020']
        #sessions = '20140321a' # No currentBlock
        sessions = '20140616a'
        behavior_summary(subjects,sessions,trialslim=[0,1200],outputDir='/tmp/')

    elif CASE==3:
        pass
