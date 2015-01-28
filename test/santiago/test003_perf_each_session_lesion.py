'''
Plot the average performance for each session before and after a lesion.
'''

from jaratoolbox import behavioranalysis
from jaratoolbox import loadbehavior
import numpy as np
from pylab import *
from jaratoolbox import settings 

experimenter = 'santiago'
animalName = 'test012'
animalName = 'test020'

sessionsPre = ['20150106a','20150108a','20150109a','20150110a'] # Pre-lesion
sessionsPost = ['20150115a','20150116a','20150117a','20150118a'] # Post-lesion
sessionsVisual = ['20150120a','20150121a','20150122a','20150123a','20150124a','20150125a'] # Visual
sessionsMorePost = ['20150126a','20150127a']

typeEachSessionLabels = ['pre','post','visual','morepost']
typeEachSession = len(sessionsPre)*[0] + len(sessionsPost)*[1] + len(sessionsVisual)*[2] + len(sessionsMorePost)*[3]
allSessions = sessionsPre+sessionsPost+sessionsVisual+sessionsMorePost
nSessions = len(allSessions)

nCorrectEachSession = np.empty(nSessions)
nValidEachSession = np.empty(nSessions)
#avPerfEachSession = []
#ciEachSession = []

for inds,oneSession in enumerate(allSessions):
    typeThisSession = typeEachSessionLabels[typeEachSession[inds]]
    if (typeThisSession=='pre') | (typeThisSession=='post')| (typeThisSession=='morepost'):
        paradigm = '2afc'
    elif typeThisSession=='visual':
        paradigm = 'lightDiscrim'
    else:
        raise TypeError('This session type is not defined')

    try:
        fname = loadbehavior.path_to_behavior_data(animalName,experimenter,paradigm,oneSession)
        bdata=loadbehavior.BehaviorData(fname)
    except IOError:
        print 'It could not load {0}'.format(fname)
        continue

    '''
    print '-----------------------------'
    print bdata['nRewarded'][-1]
    print bdata['nValid'][-1]
    '''
    nCorrectEachSession[inds] = bdata['nRewarded'][-1]
    nValidEachSession[inds] = bdata['nValid'][-1]

avPerfEachSession = nCorrectEachSession/nValidEachSession

clf()
colorEachType = ['k','k','m','k']
markerFaceEachType = ['k','w','w','w']
fontSize = 12

ax = gca()
xValues = np.arange(nSessions)+1
plot(xValues,100*avPerfEachSession,'-',color='0.5')
axhline(100*0.5,color='0.75',ls='--')
axhline(100*0.75,color='0.75',ls='--')
for inds,perfOneSession in enumerate(avPerfEachSession):
    hold(True)
    thisColor = colorEachType[typeEachSession[inds]]
    thisFace = markerFaceEachType[typeEachSession[inds]]
    plot(xValues[inds],100*perfOneSession,'o',ms=8,mew=2,mec=thisColor,mfc=thisFace)
ylim(100*np.array([0.4,1]))

ax.set_ylabel('Trials correct (%)',fontsize=fontSize)
xlabel('Session',fontsize=fontSize)

title(animalName)


draw()
show()

'''
# -- Save figure --
outputDir = figparams.figuresDir
if PRINT_FIGURE:
    plt.gcf().set_size_inches((5,3)) # for paper
    figName = 'perf_prepostvis_{0}.{1}'.format(animalName,figFormat)
    fullName = os.path.join(outputDir,figName)
    print 'Saving figure to %s'%fullName
    plt.gcf().set_frameon(False)
    plt.savefig(fullName,format=figFormat,facecolor=figparams.colBG)
    plt.gcf().set_frameon(True)
    print '... figure saved.'
    pass
'''
