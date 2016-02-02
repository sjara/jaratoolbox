from jaratoolbox.test.nick.database import dataloader
from jaratoolbox.test.nick.database import dataplotter
from jaratoolbox.test.nick.database import cellDB
from jaratoolbox.test.nick.database import clusterfuncs
from jaratoolbox import spikesorting
from matplotlib import pyplot as plt
from jaratoolbox import behavioranalysis
from jaratoolbox import spikesanalysis


reload(cellDB)
reload(clusterfuncs)

figdb = cellDB.CellDB()
figdbFn = '/home/nick/data/database/pinp003_thalamus_cells.json'
figdb.load_from_json(figdbFn)

loader = dataloader.DataLoader('offline', experimenter='nick')

figdb[1].get_session_types()

clusterfuncs.plot_cluster_tuning(figdb[1], 3)

spikeData, eventData, behavData = loader.get_cluster_data(figdb[1], 3)


currentFreq = behavData['currentFreq']
possibleFreq = np.unique(currentFreq)
currentIntensity=behavData['currentIntensity']
possibleIntensity = np.unique(currentIntensity)



spikeTimestamps=spikeData.timestamps
eventOnsetTimes=loader.get_event_onset_times(eventData)
timeRange = [-0.5, 1]

spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
    spikeTimestamps, eventOnsetTimes, timeRange)

plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.')


select= np.flatnonzero((currentIntensity==70) & (currentFreq==possibleFreq[6]))

selectspikes = spikeTimesFromEventOnset[np.in1d(trialIndexForEachSpike, select)]
selectinds = trialIndexForEachSpike[np.in1d(trialIndexForEachSpike, select)]

plot(selectspikes, selectinds, '.')

####This is a good hack to reduce the index vals once they are selected
squeezedinds=array([list(unique(selectinds)).index(x) for x in selectinds])

plot(selectspikes, squeezedinds, '.')


baseline=[-0.5, -0.25]
response=[0, 0.25]



#Count the spikes for each trial that fall into the baseline window
baselineSpikes=[]
for ind in unique(squeezedinds):
    spikesOneTrial = selectspikes[squeezedinds==ind]
    numspikesBaseline = (spikesOneTrial>baseline[0]) & (spikesOneTrial<baseline[1])
    numspikesBaseline=numspikesBaseline.sum()
    baselineSpikes.append(numspikesBaseline)

# count the spike times for each trial that fall within the response time window
responseSpikes=[]
for ind in unique(squeezedinds):
    spikesOneTrial = selectspikes[squeezedinds==ind]
    numspikesResponse = (spikesOneTrial>response[0]) & (spikesOneTrial<response[1])
    numspikesResponse=numspikesResponse.sum()
    responseSpikes.append(numspikesResponse)

maxSpikes=max(responseSpikes)

#Make as an array 
baselineSpikes=array(baselineSpikes)
responseSpikes=array(responseSpikes)


baselineAboveCriterion=[]
responseAboveCriterion=[]
for i in range(0, maxSpikes):
    baselineAboveCriterion.append((baselineSpikes>=i).sum()/float(len(baselineSpikes)))
    responseAboveCriterion.append((responseSpikes>=i).sum()/float(len(baselineSpikes)))

#Compute the area under the ROC curve

#Have to re-order in ascending
auroc=trapz(responseAboveCriterion[::-1], x=baselineAboveCriterion[::-1])


#Re-calculate for different response range

response=[0.25, 0.5]
responseSpikes=[]
for ind in unique(squeezedinds):
    spikesOneTrial = selectspikes[squeezedinds==ind]
    numspikesResponse = (spikesOneTrial>response[0]) & (spikesOneTrial<response[1])
    numspikesResponse=numspikesResponse.sum()
    responseSpikes.append(numspikesResponse)

#Have to reset the response spikes as an array each time
responseSpikes=array(responseSpikes)

baselineAboveCriterion=[]
responseAboveCriterion=[]
for i in range(0, maxSpikes):
    baselineAboveCriterion.append((baselineSpikes>=i).sum()/float(len(baselineSpikes)))
    responseAboveCriterion.append((responseSpikes>=i).sum()/float(len(baselineSpikes)))




###winner winner chicken dinner - much better method


#####Baseline spikes
#The trials you want to look at
select= np.flatnonzero((currentIntensity==70) & (currentFreq==possibleFreq[6]))

#The onset times for those trials
selectedOnsetTimes = eventOnsetTimes[select]

#The timerange you want to look at
timeRange_baseline = [-0.5, -0.25]

spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
    spikeTimestamps, selectedOnsetTimes, timeRange_baseline)

spikesEachTrial_baseline=squeeze(diff(indexLimitsEachTrial, axis=0))/diff(timeRange_baseline)


###Respones spikes
#Generating a bunch of start and stop timeranges
starts = arange(-0.5, 1, 0.1)
stops = arange(-0.4, 1.1, 0.1)


auroc_list=[]
for i in range(len(starts)):
    timeRange = vstack((starts, stops))[:,i]

    spikeTimesFromEventOnset, trialIndexForEachSpike, indexLimitsEachTrial = spikesanalysis.eventlocked_spiketimes(
        spikeTimestamps, selectedOnsetTimes, timeRange)

    spikesEachTrial=squeeze(diff(indexLimitsEachTrial, axis=0))/diff(timeRange)

    baselineAboveCriterion=[]
    responseAboveCriterion=[]
    maxSpikes = max(max(spikesEachTrial_baseline), max(spikesEachTrial))
    for i in linspace(0, maxSpikes, 20):
        baselineAboveCriterion.append((spikesEachTrial_baseline>=i).sum()/float(len(spikesEachTrial_baseline)))
        responseAboveCriterion.append((spikesEachTrial>=i).sum()/float(len(spikesEachTrial)))

    auroc=trapz(responseAboveCriterion[::-1], x=baselineAboveCriterion[::-1])
    auroc_list.append(auroc)


