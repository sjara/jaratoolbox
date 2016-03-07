'''
calculates max Z value for laser burst test for all cells with good quality (score of 1 or 6).
Lan Guo 2016-02-18
'''

from jaratoolbox import loadbehavior
from jaratoolbox import settings_2 as settings
reload (settings)
from jaratoolbox import ephyscore
import os
import numpy as np
from jaratoolbox import loadopenephys
from jaratoolbox import spikesanalysis
from jaratoolbox import extraplots
from jaratoolbox import celldatabase as cellDB
import matplotlib.pyplot as plt
import sys
import importlib
import re

mouseName = str(sys.argv[1]) #the first argument is the mouse name to tell the script which allcells file to use
allcellsFileName = 'allcells_'+mouseName
sys.path.append(settings.ALLCELLS_PATH)
allcells = importlib.import_module(allcellsFileName)

SAMPLING_RATE=30000.0

outputDir = '/home/languo/data/ephys/'+mouseName
nameOfFile = 'maxZVal_laser_'+mouseName
finalOutputDir = outputDir+'/'+mouseName+'_stats'
if not os.path.exists(finalOutputDir):
    os.mkdir(finalOutputDir)

laserTriggerChannel = 0 # channel 0 is the sound presentation, 1 is the trial
binWidth = 0.010 # Size of each bin in histogram in seconds

timeRange = [-0.3,0.7] # In seconds. Time range for rastor plot to plot spikes (around some event onset as 0)

clusNum = 12 #Number of clusters that Klustakwik speparated into
numTetrodes = 8 #Number of tetrodes

ephysRootDir = settings.EPHYS_PATH

experimenter = 'lan'
paradigm = '2afc'

Zthreshold = 3

numOfCells = len(allcells.cellDB) #number of cells that were clustered on all sessions clustered
subject = allcells.cellDB[0].animalName
behavSession = ''
laserSession = ''
tetrodeID = ''

################################################################################################
baseRange = [-0.050,-0.025]              # Baseline range (in seconds)
binTime = baseRange[1]-baseRange[0]         # Time-bin size
#responseTimeRange = [-0.1,0.1]      
#responseTime = responseTimeRange[1]-responseTimeRange[0]
binEdges = np.arange(0,5)*binTime  # Edges of bins to calculate response (in seconds)
################################################################################################

class nestedDict(dict):#This is to create maxZDict
    def __getitem__(self, item):
        try:
            return super(nestedDict, self).__getitem__(item)
        except KeyError:
            value = self[item] = type(self)()
            return value


maxZDict = nestedDict()
#ZscoreArray = np.array([])
maxZList = [] #List of behavior sessions that already have maxZ values calculated

try:
    text_file = open("%s/%s.txt" % (finalOutputDir,nameOfFile), 'r+') #open a text file to read and write in
    text_file.readline()
    behavName = ''
    for line in text_file:
        behavLine = line.split(':')
        freqLine = line.split()
        if (behavLine[0] == 'Behavior Session'):
            behavName = behavLine[1][:-1]
            maxZList.append(behavName)
            

except:
    text_file = open("%s/%s.txt" % (finalOutputDir,nameOfFile), 'w') #open a text file to read and write in

badSessionList = []#Makes sure sessions that crash don't get ZValues printed

for cellID in range(0,numOfCells):
    oneCell = allcells.cellDB[cellID]
    tetrode = oneCell.tetrode
    cluster = oneCell.cluster
    quality = oneCell.quality

    if (oneCell.behavSession in maxZList): #checks to make sure the maxZ value is not recalculated
        continue
    if quality ==1 or quality ==6:
        try:
            if (behavSession != oneCell.behavSession):

                subject = oneCell.animalName
                behavSession = oneCell.behavSession
                laserSession = oneCell.laserSession
                ephysRoot = os.path.join(ephysRootDir,subject)

                print oneCell.behavSession
                
                # -- Load event data and convert event timestamps to ms --
                ephysDir = os.path.join(ephysRoot, laserSession)
                eventFilename=os.path.join(ephysDir, 'all_channels.events')
                eventData = loadopenephys.Events(eventFilename) # Load events data
                eventTimes=np.array(eventData.timestamps)/SAMPLING_RATE #get array of timestamps for each event and convert to seconds by dividing by sampling rate (Hz). matches with eventID and 
                #####20160218 Need laser onset trigger
                laserOnsetEvents = (eventData.eventID==1) & (eventData.eventChannel==laserTriggerChannel)
                eventOnsetTimes = eventTimes[laserOnsetEvents]
                print "number of ephys trials ",len(eventOnsetTimes)

                #######20160218 Don't need to iterate through freqs, need [behavsession]as key in maxZdict?? maybe just to associate with behav recording session
                maxZDict[behavSession] = np.zeros([clusNum*numTetrodes]) #initialize a list for storing maxZ with max length, only good clusters will be filled in so the rest of the entries will be zeros.
                #maxZArray = np.empty([clusNum*numTetrodes])

                # -- Load Spike Data From Certain Cluster --
                spkData = ephyscore.CellData(oneCell)
                spkTimeStamps = spkData.spikes.timestamps

                (spikeTimesFromEventOnset,trialIndexForEachSpike,indexLimitsEachTrial) = \
                    spikesanalysis.eventlocked_spiketimes(spkTimeStamps,eventOnsetTimes,timeRange)


                [zStat,pValue,maxZ] = spikesanalysis.response_score(spikeTimesFromEventOnset,indexLimitsEachTrial,baseRange,binEdges) #computes z score for each bin. zStat is array of z scores. maxZ is maximum value of z in timeRange

                clusterNumber = (tetrode-1)*clusNum+(cluster-1)
                maxZDict[behavSession][clusterNumber] = maxZ
                #if abs(maxZ)=<Zthreshold & onecell.soundResponsive!=True:
                    #oneCell.soundResponsive=False
                #elif abs(maxZ)>Zthreshold:
                    #oneCell.soundResponsive=True

                #ZscoreArray[:,Frequency,cellID] = zStat
        except:
            #print "error with session "+oneCell.behavSession
            if (oneCell.behavSession not in badSessionList):
                badSessionList.append(oneCell.behavSession)

    else:
        continue

bSessionList = []
for bSession in maxZDict:
    if (bSession not in badSessionList):
        bSessionList.append(bSession)

bSessionList.sort()
for bSession in bSessionList:
    text_file.write("Behavior Session:%s" % bSession)
    text_file.write("\n")
    for ZVal in maxZDict[bSession]:
        text_file.write("%s," % ZVal)
    text_file.write("\n")

text_file.close()
print 'error with sessions: '
for badSes in badSessionList:
    print badSes
print 'finished laser response max Z value check'
