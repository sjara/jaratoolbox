
from jaratoolbox import behavioranalysis
from jaratoolbox import loadbehavior
import numpy as np
from pylab import *
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint #Used to compute confidence interval for the error bars. 

#subjects = ['test065','test067','test068','test070']
#subjects = ['test064']
session = '20141116a' #20141116-20141119
#session = '20141117a' #20141116-20141119
animalNames = ['test064']
sessions = ['20141116a','20141117a','20141118a','20141119a']

#clf()
for ind, subject in enumerate(animalNames):#enumerate(subjects):
    #fname=loadbehavior.path_to_behavior_data(subject,'santiago','2afc',session)

    try:
        #bdata=loadbehavior.BehaviorData(fname)
        bdata = behavioranalysis.load_many_sessions(animalNames,sessions)
    except IOError:
        continue
    from jaratoolbox import settings 

    targetFrequency=bdata['targetFrequency']
    valid=bdata['valid']
    choice=bdata['choice']
    intensities=bdata['targetIntensity']
    choiceRight = choice==bdata.labels['choice']['right'] ########## FIX ME : HARDCODED!


    possibleFreq = np.unique(targetFrequency)
    nFreq = len(possibleFreq) 
    fractionRightEachFreq=np.zeros(nFreq)
    confLimitsEachFreq=np.zeros([2, nFreq]) #Upper and lower confidence limitsi
    trialsEachFreq = behavioranalysis.find_trials_each_type(targetFrequency,possibleFreq)

    #positions=[(0,0), (0,1), (1,0), (1,1), (2,0)]
    #ax1=plt.subplot2grid((3,2), positions[ind])

    nTrialsEachFreq = np.empty(nFreq)
    nRightwardEachFreq = np.empty(nFreq)
    for indf,thisFreq in enumerate(possibleFreq):

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
suptitle(session)    
show()


'''
    fractionRightEachFreq = nRightwardEachFreq/nTrialsEachFreq.astype(float)

    #plot(possibleFreq,fractionRightEachFreq,'-o')
    #gca().set_xscale('log')
    positions=[(0,0), (0,1), (1,0), (1,1), (2,0)]
    ax1=plt.subplot2grid((3,2), positions[ind])
    ax1.plot(fractionRightEachFreq,'-o')
    title(subject)
    ylim([0,1])
show()
'''
