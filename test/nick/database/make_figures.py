from jaratoolbox.test.nick.database import dataloader
from jaratoolbox.test.nick.database import dataplotter
from jaratoolbox.test.nick.database import cellDB
from jaratoolbox import spikesorting
from matplotlib import pyplot as plt
figdb = cellDB.CellDB()
figdbFn = '/home/nick/Desktop/figure_cells/figure_cells.json' #Change to path on your comp
figdb.load_from_json(figdbFn)

'''
This file will load the cluster database and show methods for getting the data from the clusters and plotting it.
I recommend running the file in parts, since plots will clear the current figure and only the last plot will be shown if the file is run all at once. 



The plots that we need to make are:

B/C/D: The thalamus sound response, laser response, and tuning curve
E: The AM modulation plot
G/H/I: The cortex sound response, laser response, and tuning curve
J: Direct laser activation raster
K: Indirect laser activation raster
L: Waveforms for the laser-responsive units

The figure database has comments explaining what each cell is good for
If you run `print figdb` you will get the following: 


Cell 0
ID: pinp003_2015-06-24_3543_TT6_3
Comments: B/C/D Option -  site 1 T6c3 (Thalamus)

Cell 1
ID: pinp003_2015-06-24_3855_TT6_3
Comments: B/C/D (our favorite so far), also possibly J - site 6 T6c3 (Thalamus)

Cell 2
ID: pinp003_2015-07-06_3654_TT3_10
Comments: J - site4 T3c10 (Thalamus)

Cell 3
ID: pinp003_2015-06-24_3543_TT6_6
Comments: K - site1 T6c6 (Thalamus)

Cell 4
ID: pinp005_2015-08-10_1655_TT5_4
Comments: G/H/I - site4 T5c4 (Cortex)

Cell 5
ID: pinp005_2015-08-10_1655_TT5_9
Comments: K - site4 T5c9 (Cortex)

Cell 6
ID: pinp005_2015-08-10_1655_TT6_2
Comments: J - site4 T6c2 (Cortex)

Cell 7
ID: pinp005_2015-08-10_1491_TT5_7
Comments: Good J example - site2 T5c7 (Cortex)

Cell 8
ID: pinp005_2015-08-10_1491_TT5_8
Comments: K - site2 T5c8 (Cortex)

Cell 9
ID: pinp005_2015-08-13_3970_TT3_3
Comments: Best unit for AM modulation. Also sound/laser responsive thalamus unit for B/C/D

In the directory I gave you there are the .png reports for each of these cells. 

##############

You need the data from the following mice/days:

pinp003: 2014-06-24, 2015-07-06
pinp005: 2015-08-10, 2015-08-13

##############
'''

#You can easily get the data from the clusters by initializing an offline instance of a data loading class.

loader = dataloader.DataLoader('offline', experimenter='nick')

# - If you do not know the string for the session type that you want, it will prompt you:
spikeData, eventData, behavData = loader.get_cluster_data(figdb[0])
# - The dataspikes object will contain only the spikes and samples for this cluster

# - You can also specify the session type:
spikeData, eventData, behavData = loader.get_cluster_data(figdb[0], 'noiseBurst')
# - I tried to keep the session types somewhat consistent but they are not all the same

## ------ Plotting a raster----------

#I usually use plotting functions that live in my dataplotter module.
#These fns take spiketimes and eventOnsetTimes and take care of calling
#spikesanalysis and behavioranalysis methods, and then use extraplots methods to do the plotting

#Lets look at the noise burst response from the first cluster
spikeData, eventData, behavData = loader.get_cluster_data(figdb[0], 'noiseBurst')
spikeTimestamps = spikeData.timestamps
eventOnsetTimes = loader.get_event_onset_times(eventData)

plt.clf()
dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes)
plt.show()

#All rasters in the reports are plotted this way. 

## ------ Plotting a sorted raster ----

#The nice thing about the raster plotting methods is that they can accept an array to sort by
#Lets look at the AM responses from the last cluster (9)

spikeData, eventData, behavData = loader.get_cluster_data(figdb[9], 'AM')

spikeTimestamps = spikeData.timestamps
eventOnsetTimes = loader.get_event_onset_times(eventData)
currentFreq = behavData['currentFreq']

plt.clf()
dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes, sortArray = currentFreq)
plt.show()


## ------ Tuning Curve Heatmaps ----
## Plotting the heatmaps requires a bit more code
## Lets look at the tuning curve from the last cell, since it is a thalamus cell that
## seems directly activated and (I think) it has a nicer tuning than the
## other thalamus cell we were going to use for plots B, C, and D

spikeData, eventData, behavData = loader.get_cluster_data(figdb[9], 'TuningCurve')

spikeTimestamps = spikeData.timestamps
eventOnsetTimes = loader.get_event_onset_times(eventData)
freqEachTrial = behavData['currentFreq']
intensityEachTrial = behavData['currentIntensity']

possibleFreq = np.unique(freqEachTrial)
possibleIntensity = np.unique(intensityEachTrial)

xlabel='Frequency (kHz)'
ylabel='Intensity (dB SPL)'

freqLabels = ["%.1f" % freq for freq in possibleFreq/1000.0]
intenLabels = ["%.1f" % inten for inten in possibleIntensity]

plt.clf()
dataplotter.two_axis_heatmap(spikeTimestamps,
                             eventOnsetTimes,
                             firstSortArray=intensityEachTrial,
                             secondSortArray=freqEachTrial,
                             firstSortLabels=intenLabels,
                             secondSortLabels=freqLabels,
                             timeRange=[0, 0.1])

plt.xlabel(xlabel)
plt.ylabel(ylabel)
plt.show()

### I think that the only other plot you need for the figure that you gave me is the spike waveform plot
##The waveforms for cell 9, the one with the good amp modulation

plt.clf()
spikesorting.plot_waveforms(spikeData.samples)
plt.show()

#The plot_waveforms method currently computes the average over only the 40 selected spikes.
#Spikes are selected and then aligned, and the the aligned ones are used to calculate the average.
#We should think about calculating the average over all the spikes if it isn't too much to align them all. 

