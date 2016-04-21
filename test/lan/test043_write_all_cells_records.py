'''
Script to read all separately written measurements: ISIviolation,maxZsound,maxZmovement,modulationIndex(for reward and movement) and modulationSignificance into one csv file.
'''

import time
import pandas as pd
from jaratoolbox import settings_2 as settings
import sys
import importlib
import os
import codecs

clusNum = 12 #Number of clusters that Klustakwik speparated into
numTetrodes = 8 #Number of tetrodes
cellNumPerSession=clusNum*numTetrodes
all_measures=pd.DataFrame()
#############################################################################
subject = sys.argv[1]
allcellsFileName = 'allcells_'+subject
sys.path.append(settings.ALLCELLS_PATH)
allcells = importlib.import_module(allcellsFileName)
outputDir = '/home/languo/data/ephys/'+subject+'/'
processedDir = os.path.join(outputDir,subject+'_stats')


############################## ISI #########################################
ISIFilename = os.path.join(processedDir,'ISI_Violations_'+subject+'.txt')
ISIFile = open(ISIFilename, 'r')

behavSessionCount=0
#cellIndex=range(cellNumPerSession)
behavSessionList=[]
ISIDict={'ISI':[],'behavSession':[]}
#start1=time.clock()
for line in ISIFile:
    if line.startswith(codecs.BOM_UTF8):
            line = line[3:]
    if (line.split(':')[0] == 'Behavior Session'):
        behavName = line.split(':')[1][:-1] 
        behavSessionList.append(behavName)
        behavSessionCount+=1
        ISIDict['behavSession'].extend([behavName]*cellNumPerSession)
    else:
        ISIDict['ISI'].extend([float(x) for x in line.split(',')[0:-1]])
      
behavSessionNum_ISI=behavSessionCount
ISI=pd.DataFrame(ISIDict)
#print ISI[100:150]
ISI.sort('behavSession',ascending=True,inplace=True)
ISI=ISI.reset_index(drop=True)
#print ISI[100:150]
ISIFile.close()
all_measures['behavSession']=ISI['behavSession']
all_measures['ISI']=ISI['ISI']

#end1=time.clock()
#processTime1=end1-start1
#print processTime1,behavSessionList
print 'read-in ISI: ', behavSessionCount, 'sessions'
############################################################################

#################### maxZ for sound responsiveness #########################
maxZFilename = os.path.join(processedDir,'maxZVal_'+subject+'.txt')
maxZFile = open(maxZFilename, 'r')
maxZsoundDict = {'maxZSoundLeft':[],'maxZSoundRight':[],'behavSession':[]}
behavSessionCount=0
behavSessionList=[]
cellIndex=range(cellNumPerSession)
start=time.clock()
for line in maxZFile:
    if line.startswith(codecs.BOM_UTF8):
        line = line[3:]
    if (line.split(':')[0] == 'Behavior Session'):
        behavName = line.split(':')[1][:-1]  
        behavSessionList.append(behavName)
        behavSessionCount+=1
        maxZsoundDict['behavSession'].extend([behavName]*cellNumPerSession)
    else:
        freq=int(line.split()[0])
        if freq < 9500:
            maxZsoundDict['maxZSoundLeft'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
        elif freq >= 10000: #some sessions have a mid freq, THIS MIGHT BE ANIMAL SPECIFIC
            maxZsoundDict['maxZSoundRight'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])

behavSessionNum_maxZsound=behavSessionCount
maxZsound=pd.DataFrame(maxZsoundDict)
#print maxZsound[100:150]
maxZsound.sort('behavSession',ascending=True,inplace=True)
maxZsound=maxZsound.reset_index(drop=True)

all_measures['maxZSoundLeft']=maxZsound['maxZSoundLeft']
all_measures['maxZSoundRight']=maxZsound['maxZSoundRight']

#print maxZsound[100:150]
#end=time.clock()
maxZFile.close()
print 'read-in sound maxZ: ', behavSessionCount, 'sessions'
#################################################################################

#################### maxZ for movement responsiveness ################
nameOfmovementmaxZFile = 'maxZVal_movement_150to300msAfterSound_'+subject+'.txt'
movementmaxZFilename = os.path.join(processedDir,nameOfmovementmaxZFile)

movementmaxZFile = open(movementmaxZFilename, 'r')
maxZmovementDict = {'maxZMovementLeft':[],'maxZMovementRight':[],'behavSession':[]}
behavSessionCount=0
behavSessionList=[]
cellIndex=range(cellNumPerSession)
#start=time.clock()
for line in movementmaxZFile:
    if line.startswith(codecs.BOM_UTF8):
        line = line[3:]
    if (line.split(':')[0] == 'Behavior Session'):
        behavName = line.split(':')[1][:-1]  
        behavSessionList.append(behavName)
        behavSessionCount+=1
        maxZmovementDict['behavSession'].extend([behavName]*cellNumPerSession)
    else:
        freq=int(line.split()[0])
        if freq < 9500:
            maxZmovementDict['maxZMovementLeft'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
        elif freq >= 10000: #some sessions have a mid freq
            maxZmovementDict['maxZMovementRight'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
behavSessionNum_maxZmovement=behavSessionCount
maxZmovement=pd.DataFrame(maxZmovementDict)

maxZmovement.sort('behavSession',ascending=True,inplace=True)
maxZmovement=maxZmovement.reset_index(drop=True)

all_measures['maxZMovementLeft']=maxZmovement['maxZMovementLeft']
all_measures['maxZMovementRight']=maxZmovement['maxZMovementRight']
#end=time.clock()

movementmaxZFile.close()
#print end-start, behavSessionList
print 'read-in movement maxZ: ', behavSessionCount, 'sessions'
######################################################################

######################### L-R movement Modulation Index ###########################
nameOfmovementmodIFile_1 = 'modIndex_'+'LvsR_movement_0to0.1sec_window_'+subject+'.txt'
movementmodIFilename_1 = os.path.join(processedDir,nameOfmovementmodIFile_1)
nameOfmovementmodIFile_2 = 'modIndex_'+'LvsR_movement_0to0.2sec_window_'+subject+'.txt'
movementmodIFilename_2 = os.path.join(processedDir,nameOfmovementmodIFile_2)

movementmodIFile_1=open(movementmodIFilename_1, 'r')
movementmodIFile_2=open(movementmodIFilename_2, 'r')

#movementmodIDict = {}
movementmodI=pd.DataFrame()
#cellIndex=range(cellNumPerSession)
#start2=time.clock()
movementmodIMeasures={'movementmodI0-0.1':movementmodIFile_1, 'movementmodI0-0.2':movementmodIFile_2}
listOfmovementmodIMeasures=['movementmodI0-0.1','movementmodI0-0.2']
listOfmovementmodIFiles=[movementmodIFile_1,movementmodIFile_2]

for (key,filename) in movementmodIMeasures.items(): #zip(listOfmovementmodIMeasures,listOfmovementmodIFiles):
    behavSessionCount=0
    behavSessionList=[]
    movementmodIDict = {}
    movementmodIDict.update({key:[],'behavSession':[]})
    for line in filename:
        if (line.split(':')[0] == 'Behavior Session'):
            behavName = line.split(':')[1][:-1]  
            behavSessionList.append(behavName)
            behavSessionCount+=1
            movementmodIDict['behavSession'].extend([behavName]*cellNumPerSession)
        else:
            movementmodIDict[key].extend([float(x) for x in line.split(',')[0:-1]])
    movementmodI_current=pd.DataFrame(movementmodIDict)
    movementmodI_current.sort('behavSession',ascending=True,inplace=True)
    movementmodI_current=movementmodI_current.reset_index(drop=True)
    
    all_measures[key]=movementmodI_current[key]
    #behavSessionNum_movementmodI=behavSessionCount
    print 'read in', key, behavSessionCount

movementmodIFile_1.close()
movementmodIFile_2.close()
#end2=time.clock()
#processTime2=end2-start2
#print processTime2, behavSessionList
######################################################################################

######################## L-R movement Modulation Significance ########################

nameOfmovementmodSFile_1 = 'modSig_'+'LvsR_movement_0to0.1sec_window_'+subject+'.txt'
movementmodSFilename_1 = os.path.join(processedDir,nameOfmovementmodSFile_1)
nameOfmovementmodSFile_2 = 'modSig_'+'LvsR_movement_0to0.2sec_window_'+subject+'.txt'
movementmodSFilename_2 = os.path.join(processedDir,nameOfmovementmodSFile_2)
movementmodSFile_1=open(movementmodSFilename_1, 'r')
movementmodSFile_2=open(movementmodSFilename_2, 'r')

movementmodSDict = {}
behavSessionCount=0
behavSessionList=[]
#cellIndex=range(cellNumPerSession)
#start2=time.clock()

movementmodSMeasures={'movementmodS0-0.1':movementmodSFile_1, 'movementmodS0-0.2':movementmodSFile_2}

for (key,filename) in movementmodSMeasures.items(): #zip(listOfmovementmodIMeasures,listOfmovementmodIFiles):
    behavSessionCount=0
    behavSessionList=[]
    movementmodSDict = {}
    movementmodSDict.update({key:[],'behavSession':[]})
    for line in filename:
        if (line.split(':')[0] == 'Behavior Session'):
            behavName = line.split(':')[1][:-1]  
            behavSessionList.append(behavName)
            behavSessionCount+=1
            movementmodSDict['behavSession'].extend([behavName]*cellNumPerSession)
        else:
            movementmodSDict[key].extend([float(x) for x in line.split(',')[0:-1]])
    movementmodS_current=pd.DataFrame(movementmodSDict)
    movementmodS_current.sort('behavSession',ascending=True,inplace=True)
    movementmodS_current=movementmodS_current.reset_index(drop=True)
    
    all_measures[key]=movementmodS_current[key]
    #behavSessionNum_movementmodI=behavSessionCount
    print 'read in', key, behavSessionCount

movementmodSFile_1.close()
movementmodSFile_2.close()

#end2=time.clock()
#processTime2=end2-start2
#print processTime2, behavSessionList
################################################################################


##################### Reward Modulation Index #################################
listOfmodIMeasures = ['sound_0to0.1sec','sound_0to0.15sec','center-out_-0.1to0sec','center-out_0to0.1sec', 'center-out_0to0.2sec','side-in_-0.1to0sec', 'side-in_0to0.1sec', 'side-in_0to0.2sec']
listOfmodIFilenames = ['modIndex_'+i+'_window_'+subject+'.txt' for i in listOfmodIMeasures]
listOfmodIFullFilenames = [os.path.join(processedDir,file) for file in listOfmodIFilenames]
listOfmodIFiles = [open(i, 'r') for i in listOfmodIFullFilenames]

modI=pd.DataFrame()

for (key,filename) in zip(listOfmodIMeasures,listOfmodIFiles):
    behavSessionCount=0
    behavSessionList=[]
    modIDict = {}
    modIDict.update({('modI'+key+'Left'):[],('modI'+key+'Right'):[],'behavSession':[]})
    
    for line in filename:
        if line.startswith(codecs.BOM_UTF8):
            line = line[3:]
        if (line.split(':')[0] == 'Behavior Session'):
            behavName = line.split(':')[1][:-1]  
            behavSessionList.append(behavName)
            behavSessionCount+=1
            modIDict['behavSession'].extend([behavName]*cellNumPerSession)
        else:
            freq=int(line.split()[0])
            if freq < 9500:
                modIDict['modI'+key+'Left'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
            elif freq >= 10000: #some sessions have a mid freq
                modIDict['modI'+key+'Right'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
    modI_current=pd.DataFrame(modIDict)
    modI_current.sort('behavSession',ascending=True,inplace=True) #sort dataframe so that behavSessions are in ascending order
    modI_current=modI_current.reset_index(drop=True) #sort function somehow doesn't change index so have to reset it manually before merging
    
    all_measures['modI'+key+'Left']=modI_current['modI'+key+'Left']
    all_measures['modI'+key+'Right']=modI_current['modI'+key+'Right']
    #behavSessionNum_movementmodI=behavSessionCount
    print 'read in', key, behavSessionCount, behavSessionList

for f in listOfmodIFiles:
    f.close() 
##################################################################################


#################### Reward Modulation Significance #################################
listOfmodSMeasures = ['sound_0to0.1sec','sound_0to0.15sec','center-out_-0.1to0sec','center-out_0to0.1sec', 'center-out_0to0.2sec','side-in_-0.1to0sec', 'side-in_0to0.1sec', 'side-in_0to0.2sec']
listOfmodSFilenames = ['modSig_'+i+'_window_'+subject+'.txt' for i in listOfmodSMeasures]
listOfmodSFullFilenames = [os.path.join(processedDir,file) for file in listOfmodSFilenames]
listOfmodSFiles = [open(i, 'r') for i in listOfmodSFullFilenames]

modS=pd.DataFrame()
for (key,filename) in zip(listOfmodSMeasures,listOfmodSFiles):
    behavSessionCount=0
    behavSessionList=[]
    modSDict = {}
    modSDict.update({('modS'+key+'Left'):[],('modS'+key+'Right'):[],'behavSession':[]})
 
    for line in filename:
        if line.startswith(codecs.BOM_UTF8):
            line = line[3:]
        if (line.split(':')[0] == 'Behavior Session'):
            behavName = line.split(':')[1][:-1]  
            behavSessionList.append(behavName)
            behavSessionCount+=1
            modSDict['behavSession'].extend([behavName]*cellNumPerSession)
        else:
            freq=int(line.split()[0])
            if freq < 9500:
                modSDict['modS'+key+'Left'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
            elif freq >= 10000: #some sessions have a mid freq
                modSDict['modS'+key+'Right'].extend([float(x) for x in line.split()[1].split(',')[0:-1]])
    modS_current=pd.DataFrame(modSDict)
    modS_current.sort(['behavSession'],ascending=True,inplace=True)
    modS_current=modS_current.reset_index(drop=True)
    all_measures['modS'+key+'Left']=modS_current['modS'+key+'Left']
    all_measures['modS'+key+'Right']=modS_current['modS'+key+'Right']
    #behavSessionNum_movementmodI=behavSessionCount
    print 'read in', key, behavSessionCount, behavSessionList

#modS=pd.DataFrame(modSDict)
for f in listOfmodSFiles:
    f.close() 
###################################################################################
all_measuresFilename=processedDir+'/all_measures_'+subject
all_measures.to_csv(all_measuresFilename)


 

   
