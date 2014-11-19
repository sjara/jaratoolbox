
from jaratoolbox import behavioranalysis
from jaratoolbox import loadbehavior
import numpy as np
from pylab import *
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint #Used to compute confidence interval for the error bars. 

subjects = ['hm4d004', 'hm4d005', 'hm4d006']
session = '20140826a'

for ind, subject in enumerate(subjects):
    fname=loadbehavior.path_to_behavior_data(subject,'nick','2afc',session)


    try:
        bdata=loadbehavior.BehaviorData(fname)
    except IOError:
        pass
    from jaratoolbox import settings 

    targetFrequency=bdata['targetFrequency']
    valid=bdata['valid']
    choice=bdata['choice']
    intensities=bdata['targetIntensity']
    choiceRight = choice==bdata.labels['choice']['right']


    possibleFreq = np.unique(targetFrequency)
    nFreq = len(possibleFreq) 
    fractionRightEachFreq=np.zeros(nFreq)
    confLimitsEachFreq=np.zeros([2, nFreq]) #Upper and lower confidence limits
    trialsEachFreq = behavioranalysis.find_trials_each_type(targetFrequency,possibleFreq)

    positions=[(0,0), (0,1), (1,0), (1,1)] #FIXME: can only place 4 mice for now
    ax1=plt.subplot2grid((2,2), positions[ind])

    nTrialsEachFreq = np.empty(nFreq)
    nRightwardEachFreq = np.empty(nFreq)
    for indf,thisFreq in enumerate(possibleFreq): #Compute the %right and c.i for each freq.


        nTrialsThisFreq = sum(valid & trialsEachFreq[:,indf])
        nRightwardThisFreq =  sum(valid & choiceRight & trialsEachFreq[:,indf])
        conf = np.array(proportion_confint(nRightwardThisFreq, nTrialsThisFreq, method = 'wilson'))
        
        nTrialsEachFreq[indf] = nTrialsThisFreq
        nRightwardEachFreq[indf] = nRightwardThisFreq
        confLimitsEachFreq[0, indf] = conf[0] # Lower ci
        confLimitsEachFreq[1, indf] = conf[1] # Upper ci

    fractionRightEachFreq = nRightwardEachFreq/nTrialsEachFreq.astype(float)

    #plot(possibleFreq,fractionRightEachFreq,'-o')
    #gca().set_xscale('log')
    upperWhisker = confLimitsEachFreq[1, :] - fractionRightEachFreq #Find lengths of whiskers for plotting function
    lowerWhisker = fractionRightEachFreq - confLimitsEachFreq[0,:]
    x = range(nFreq)
    errorbar(x, fractionRightEachFreq, yerr = [lowerWhisker, upperWhisker])
    axhline(y=0.5, color = 'red')
    title(subject)
    ylim([0,1])
show()


'''
    fractionRightEachFreq = nRightwardEachFreq/nTrialsEachFreq.astype(float)

    #plot(possibleFreq,fractionRightEachFreq,'-o')
    #gca().set_xscale('log')
    positions=[(0,0), (0,1), (1,0), (1,1)]
    ax1=plt.subplot2grid((2,2), positions[ind])
    ax1.plot(fractionRightEachFreq,'-o')
    title(subject)
    ylim([0,1])
show()
'''
