from jaratoolbox import loadbehavior
from jaratoolbox import settings
from jaratoolbox import extrafuncs
from jaratoolbox import extraplots
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib.gridspec as gridspec


'''
Lan Guo 2015-08-12
This script includes some extra plots for behavior test results. Can plot running average of intertrial intervals for leftward and rightward trials, and plot choice times for leftward and rightward trial. 
Only takes single-blcok sessions at this point.

FIXME: did not need to use a masked array since already take subsets into a new array.
'''


def plot_ITI_dynamics(bData, winsize=40, fontsize=12):
    '''
    Plot speed of performance (in intertrial intervals) in time for one session. Plots left- and right- rewardSide trials separately. 
    First argument is an object created by loadbehavior.BehaviorData (or subclasses)
    '''
    lineWidth = 2
    trialStarts = bData['timeTrialStart']
    interTrialIntervals = np.hstack((0,np.diff(trialStarts)))

    #Running average of ITI for the left- or right-rewarded trials, including invalid and error trials too 
#    ITIVec = np.ma.masked_array(interTrialIntervals)
    leftTrials = bData['rewardSide']==bData.labels['rewardSide']['left']
    
    leftTrialITIs = np.ma.masked_array(interTrialIntervals[leftTrials])
    movAvITI_left = extrafuncs.moving_average_masked(leftTrialITIs, winsize)
    rightTrialITIs = np.ma.masked_array(interTrialIntervals[~leftTrials])
    movAvITI_right = extrafuncs.moving_average_masked(rightTrialITIs, winsize)
    #plt.plot(range(0,len(leftTrials)),100*movAvChoice_left,
    #             lw=lineWidth,color='g')
    plt.plot(movAvITI_left,lw=lineWidth,color='g')
    plt.hold(1)
    plt.plot(movAvITI_right,lw=lineWidth,color='b')
    plt.hold(1)
    #plt.ylim([0,100])
    #plt.axhline(50,color='0.5',ls='--')
    plt.ylabel('Intertrial Interval(s)',fontsize=fontsize)
    plt.xlabel('Left(g) or Right(b) Trials',fontsize=fontsize)
    ax = plt.gca()
    extraplots.set_ticks_fontsize(ax,fontsize)
    plt.draw()
    plt.show()


def plot_choicetime_dynamics(bData, winsize=40, fontsize=12):
    '''
    This function plots a running average for the choice time based on trial outcomes or which side the animal actually choosed ('choice'). 
    *Invalid trials does not have choice time since timeSideIn is NaN.
    Choice time is defined as the time it took to get to the side ports to retrieve water from the time of leaving center port.
    '''
    lineWidth = 2
#    reactionTime = bData['timeCenterOut']-bData['timeTarget']
    choiceTime = bData['timeSideIn']-bData['timeCenterOut']
    correctTrials = bData['outcome']==bData.labels['outcome']['correct']
    errorTrials = bData['outcome']==bData.labels['outcome']['error']
#    invalidTrials = bData['outcome']==bData.labels['outcome']['invalid']
#Cannot use rewardSide here since some trials will be invalid and contain NaN 'timeSideIn'
    leftTrials = bData['choice']==bData.labels['choice']['left']
#Cannot use ~leftTrials for indexing since will include trials where choice is none and timeSideIn will be NaN
    rightTrials = bData['choice']==bData.labels['choice']['right']

    choiceTCorrect = np.ma.masked_array(choiceTime[correctTrials])
    movAvChoiceTime_correct = extrafuncs.moving_average_masked(choiceTCorrect, winsize)
    choiceTError = np.ma.masked_array(choiceTime[errorTrials])
    movAvChoiceTime_error = extrafuncs.moving_average_masked(choiceTError, winsize)
    choiceTLeft = np.ma.masked_array(choiceTime[leftTrials])
    movAvChoiceTime_left = extrafuncs.moving_average_masked(choiceTLeft, winsize)
    choiceTRight = np.ma.masked_array(choiceTime[rightTrials])
    movAvChoiceTime_right = extrafuncs.moving_average_masked(choiceTRight, winsize)
   
    plt.plot(movAvChoiceTime_correct,lw=lineWidth,color='g',alpha=1)
    plt.hold(1)
    plt.plot(movAvChoiceTime_error,lw=lineWidth,color='b',alpha=1)
    plt.hold(1)
    plt.plot(movAvChoiceTime_left,lw=lineWidth,color='r')
    plt.hold(1)
    plt.plot(movAvChoiceTime_right,lw=lineWidth,color='m')
    plt.hold(1)
    plt.ylim([0,2.5])
    plt.axhline(50,color='0.5',ls='--')
    plt.ylabel('Choice time(s)',fontsize=fontsize)
    plt.xlabel('Correct(g), Error(b), Leftward(r), or Rightward(m) Trials',fontsize=fontsize)
    ax = plt.gca()
    extraplots.set_ticks_fontsize(ax,fontsize)
    plt.draw()
    plt.show()


def plot_reactiontime_dynamics(bData, winsize=40, fontsize=12):
    '''
    This function plots a running average for the reaction time based on trial outcomes or which side the animal actually choosed ('choice'). 
    *Invalid trials does not have choice time since timeSideIn is NaN.
    Reaction time is defined as the time it took from hearing sound stimulus to deciding to act (removing head from center port).
    '''
    lineWidth = 2
    reactionTime = bData['timeCenterOut']-bData['timeTarget']
    correctTrials = bData['outcome']==bData.labels['outcome']['correct']
    errorTrials = bData['outcome']==bData.labels['outcome']['error']
#    invalidTrials = bData['outcome']==bData.labels['outcome']['invalid']
#Cannot use rewardSide here since some trials will be invalid and contain NaN 'timeSideIn'
    leftTrials = bData['choice']==bData.labels['choice']['left']
#Cannot use ~leftTrials for indexing since will include trials where choice is none and timeSideIn will be NaN
    rightTrials = bData['choice']==bData.labels['choice']['right']

    reactionTCorrect = np.ma.masked_array(reactionTime[correctTrials])
    movAvReactionTime_correct = extrafuncs.moving_average_masked(reactionTCorrect, winsize)
    reactionTError = np.ma.masked_array(reactionTime[errorTrials])
    movAvReactionTime_error = extrafuncs.moving_average_masked(reactionTError, winsize)
    reactionTLeft = np.ma.masked_array(reactionTime[leftTrials])
    movAvReactionTime_left = extrafuncs.moving_average_masked(reactionTLeft, winsize)
    reactionTRight = np.ma.masked_array(reactionTime[rightTrials])
    movAvReactionTime_right = extrafuncs.moving_average_masked(reactionTRight, winsize)
   
    plt.plot(movAvReactionTime_correct,lw=lineWidth,color='g',alpha=1)
    plt.hold(1)
    plt.plot(movAvReactionTime_error,lw=lineWidth,color='b',alpha=1)
    plt.hold(1)
    plt.plot(movAvReactionTime_left,lw=lineWidth,color='r')
    plt.hold(1)
    plt.plot(movAvReactionTime_right,lw=lineWidth,color='m')
    plt.hold(1)
    plt.ylim([0,2.5])
    plt.axhline(50,color='0.5',ls='--')
    plt.ylabel('Reaction time(s)',fontsize=fontsize)
    #plt.xlabel('Correct(g), Error(b), Leftward(r), or Rightward(m) Trials',fontsize=fontsize)
    ax = plt.gca()
    extraplots.set_ticks_fontsize(ax,fontsize)
    plt.draw()
    plt.show()


if len(sys.argv)>1:
    sessions = sys.argv[1:]

subject = 'adap009'
EXPERIMENTER = 'santiago'
paradigm = '2afc'
loadingClass = loadbehavior.FlexCategBehaviorData
outputDir = '/home/languo/data/behavior_reports'
settings.BEHAVIOR_PATH = '/home/languo/data/mnt/jarahubdata'
    
nSessions = len(sessions)
gs = gridspec.GridSpec(nSessions, 6)
gs.update(hspace=0.5,wspace=0.4)

for inds, thisSession in enumerate(sessions):
    try:
        behavFile = loadbehavior.path_to_behavior_data(subject,EXPERIMENTER,paradigm,thisSession)
        bData = loadingClass(behavFile,readmode='full')
    except IOError:
        print thisSession+' does not exist'
        continue
    print 'Loaded %s %s'%(subject,thisSession)
    # -- Plot performance speed as intertrial intervals (left or right)--
    ax1=plt.subplot(gs[inds,:-4])
    plot_ITI_dynamics(bData, winsize=40, fontsize=8)
    # -- Plot choice time based on trial outcome and actual choice--
    ax2=plt.subplot(gs[inds,2:4])
    plot_choicetime_dynamics(bData, winsize=40, fontsize=8)
    # -- Plot reactopm time based on trial outcome and actual choice--
    ax3=plt.subplot(gs[inds,-2:])
    plot_reactiontime_dynamics(bData, winsize=40, fontsize=8)

fig_path = outputDir
if not os.path.exists(fig_path):
    os.makedirs(fig_path)
sessionStr = '-'.join(sessions)
fig_name = '{}_{}_behav_extra_graphs.png'.format(subject, sessionStr)
full_fig_path = os.path.join(fig_path, fig_name)
plt.gcf().set_size_inches((10,11))
plt.gcf().savefig(full_fig_path)
plt.close()

