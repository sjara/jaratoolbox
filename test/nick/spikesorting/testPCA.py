from jaratoolbox import loadopenephys
from jaratoolbox import spikesorting
from jaratoolbox.test.nick import clustercutting
import os

ephysPath = '/home/nick/data/ephys/pinp013/'
ephysFn='2016-05-27_14-08-54'
spikesFn = os.path.join(ephysPath, ephysFn, 'Tetrode2.spikes')

dataSpikes = loadopenephys.DataSpikes(spikesFn)

GAIN = 5000.0
SAMPLING_RATE=30000.0
dataSpikes.samples = ((dataSpikes.samples - 32768.0) / GAIN) * 1000.0

# alignedSamples=spikesorting.align_waveforms(dataSpikes.samples)

(numSpikes, numChans, numSamples) = shape(dataSpikes.samples)

allWaves = dataSpikes.samples.reshape(numSpikes, numChans*numSamples)
# allWaves = alignedSamples.reshape(numSpikes, numChans*numSamples)

from matplotlib.mlab import PCA

results = PCA(allWaves)

figure()
for weightVector in results.Wt:
    clf()
    plot(weightVector)
    axvline(x=40, color='r')
    axvline(x=80, color='r')
    axvline(x=120, color='r')
    waitforbuttonpress()

cw = clustercutting.ClusterCutter(results.Y[:, 0:4])

clusterWaves = allWaves[cw.inCluster]
# clusterWaves = dataSpikes.samples[cw.inCluster, :, :]

figure()
for wave in clusterWaves:
    plot(wave, 'k-')
    hold(1)
show()

