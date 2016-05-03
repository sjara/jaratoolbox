'''
Estimate spike shape
'''

from pylab import *
from jaratoolbox import ephyscore
from scipy.interpolate import interp1d
import sys

'''
animalName = 'test055'
ephysSession = '20150228a'
tetrode = 3
cluster = 11
'''

# -- Load some spike data --
import allcells_test055 as allcells
cellID = allcells.cellDB.findcell('test055','20150228a',3,11)
oneCell = allcells.cellDB[cellID]

spkData = ephyscore.CellData(oneCell)
waveforms = spkData.spikes.samples
samplingRate = spkData.spikes.samplingRate


# -- Get spike shape --
N_INTERP_SAMPLES = 200
avWaveforms = np.mean(spkData.spikes.samples,0)
avWaveforms = avWaveforms - 2**15 # FIXME: this is specific to OpenEphys
energyEachChannel = np.sum(np.abs(avWaveforms),1)
maxChannel = np.argmax(energyEachChannel)
spikeShape = avWaveforms[maxChannel,:]
sampVals = np.arange(0,len(spikeShape)/samplingRate,1/samplingRate)

interpFun = interp1d(sampVals, spikeShape, kind='cubic')
interpSampVals = np.linspace(0,sampVals[-1],N_INTERP_SAMPLES)
interpSpikeShape = interpFun(interpSampVals)

# NOTE: the peaks of the action potential are: (1) capacitive, (2) Na+, (3) K+
peakNaSample = np.argmin(interpSpikeShape)
peakNaTime = interpSampVals[peakNaSample]
peakCapSample = np.argmax(interpSpikeShape[:peakNaSample])
peakCapTime = interpSampVals[peakCapSample]
peakKSample = np.argmax(interpSpikeShape[peakNaSample:])+peakNaSample
peakKTime = interpSampVals[peakKSample]

clf()
hold(1)
plot(sampVals,spikeShape,'.')
plot(interpSampVals,interpSpikeShape,'g-')
axvline(peakNaTime,ls='--',color='0.75')
axvline(peakCapTime,ls='--',color='0.75')
axvline(peakKTime,ls='--',color='0.75')
hold(0)
show()

