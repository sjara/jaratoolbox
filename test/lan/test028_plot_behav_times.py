from jaratoolbox import loadbehavior
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

animal = 'adap012'
experimenter = 'lan'

if len(sys.argv)>1:
    sessions = sys.argv[1:]

for session in sessions:
    behavFilename=animal+'_2afc_'+session+'.h5' 
    
    behavPath = '/home/languo/data/behavior/'+experimenter+'/'+animal+'/'+behavFilename

    bdata = loadbehavior.BehaviorData(behavPath)
    ###Get event times, only looking at valid trials###
    valid=bdata['valid']& (bdata['choice']!=bdata.labels['choice']['none'])
    timeCenterIn = bdata['timeCenterIn']
    timeTone = bdata['timeTarget']
    timeCenterOut = bdata['timeCenterOut']
    timeSideIn = bdata['timeSideIn'] #invalid trials does not have side in time recorded
    
    phase1Length=(timeTone-timeCenterIn)[valid] #initiates trial before soundonset
    phase2Length=(timeCenterOut-timeTone)[valid] #presentation of tone before withdrawal from center port
    phase3Length=(timeSideIn-timeCenterOut)[valid] #executes movement to side port
    phase4Length=timeCenterIn[1:]-timeSideIn[:-1]
    phase4Length=np.insert(phase4Length,0,0)
    phase4Length=phase4Length[valid]
    print len(phase4Length)
    correctTrials = bdata['outcome']==bdata.labels['outcome']['correct']
    errorTrials = bdata['outcome']==bdata.labels['outcome']['error']
    invalidTrials = bdata['outcome']==bdata.labels['outcome']['invalid']

    
    plt.figure()

    line1, = plt.plot(phase1Length,'.g',label='Phase1')
    line2, = plt.plot(phase2Length,'.b',label='Phase2')
    
    line3, = plt.plot(phase3Length, '.r',label='Phase3')
    
    line4, = plt.plot(phase4Length, '.y',label='Phase4')
    
    plt.legend([line1,line2,line3,line4],loc=2)
    
    plt.title(behavFilename)

    plt.show()
    
