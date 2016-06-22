from jaratoolbox import loadopenephys
from jaratoolbox import spikesorting
from jaratoolbox.test.nick import clustercutting
from matplotlib import pyplot as plt
import os

ephysPath = '/home/nick/data/ephys/pinp013/'

#Data with really only 1 neuron
# ephysFn='2016-05-27_14-08-54'
ephysFn='2016-05-27_14-13-26'
# spikesFn = os.path.join(ephysPath, ephysFn, 'Tetrode2.spikes')
spikesFn = os.path.join(ephysPath, ephysFn, 'Tetrode3.spikes')

#Data with more than one neuron
# ephysFn='2016-05-25_16-02-29'
# spikesFn = os.path.join(ephysPath, ephysFn, 'Tetrode8.spikes')


dataSpikes = loadopenephys.DataSpikes(spikesFn)

GAIN = 5000.0
SAMPLING_RATE=30000.0
dataSpikes.samples = ((dataSpikes.samples - 32768.0) / GAIN) * 1000.0

(numSpikes, numChans, numSamples) = shape(dataSpikes.samples)

allWaves = dataSpikes.samples.reshape(numSpikes, numChans*numSamples)

from sklearn.manifold import TSNE

model = TSNE(n_components=2, method='barnes_hut', verbose=20, n_iter=1000)
Y = model.fit_transform(allWaves)

clf()
plot(Y[:,0], Y[:,1], '.')


#We can cluster the embedded points manually if we want
# cw = clustercutting.ClusterCutter(Y)

# clusterWaves = allWaves[cw.inCluster]
# # clusterWaves = dataSpikes.samples[cw.inCluster, :, :]

# figure()
# for wave in clusterWaves:
#     plot(wave, 'k-', alpha=0.5)
#     hold(1)
# show()



### Use DBSCAN to cluster the embedded points
from sklearn.cluster import DBSCAN

db = DBSCAN(eps=0.3, min_samples=10).fit(Y)
labels = db.labels_
uniqueLabels = np.unique(labels)

colors = plt.cm.Paired(np.linspace(0, 1, len(uniqueLabels)))

#PLot the clusters in the embedded space
clf()
for indLabel, label in enumerate(unique(db.labels_)):
    indsThisLabel = np.flatnonzero(db.labels_==label)
    plot(Y[indsThisLabel, 0], Y[indsThisLabel, 1], '.', color=colors[indLabel])


## Plot the waveforms for all the identified clusters
figure()
clf()
rav = allWaves.ravel()
# maxv = max(allWaves.ravel())
maxv = percentile(rav, 99.95)
minv = percentile(rav, 0.05)
# minv = min(allWaves.ravel())
for indLabel, label in enumerate(uniqueLabels):
    subplot(len(uniqueLabels), 1, indLabel+1)
    clusterWaves = allWaves[labels==label]

    spikesToPlot = np.random.randint(len(clusterWaves),size=50)

    for wave in clusterWaves[spikesToPlot]:
        plot(wave, '-', alpha=0.5, color=colors[indLabel])
        hold(1)
    plot(clusterWaves.mean(0), 'k', lw=2, zorder=10)
    ylim([minv, maxv])
    axvline(x=40, lw=3, color='k')
    axvline(x=80, lw=3, color='k')
    axvline(x=120, lw=3, color='k')



