import os
import unittest
from jaratoolbox import loadopenephys
from jaratoolbox import spikesanalysis
from jaratoolbox import settings
from matplotlib import pyplot as plt
import subprocess
testDataDir = settings.TEST_EPHYS_DATA_PATH

class TestLoadOpenEphys(unittest.TestCase):

    def test_data(self):
        transferCommand = ['rsync', '-av', settings.TEST_DATA_REMOTE, settings.TEST_DATA_LOCAL_ROOT]
        subprocess.call(transferCommand)

    def test_spike_loading(self):
        spikesFn = 'Tetrode2.spikes'
        spikesFile = os.path.join(testDataDir,spikesFn)
        dataSpikes = loadopenephys.DataSpikes(spikesFile)
        plt.plot(dataSpikes.samples[2,:,:].ravel(),'.-')
        # 1/0
        # plt.show()

    def test_event_loading(self):
        eventFn = 'all_channels.events'
        eventFile = os.path.join(testDataDir, eventFn)
        eventData = loadopenephys.Events(eventFile)
        plt.plot(eventData.timestamps, '.')
        # plt.show()

    def test_cont_loading(self):
        contFn = '100_CH11.continuous'
        contFile = os.path.join(testDataDir,contFn)
        contData = loadopenephys.DataCont(contFile)
        plt.plot(contData.samples[:10000],'.-')
        # plt.show()

    def test_event_onsets(self):
        eventFn = 'all_channels.events'
        spikesFn = 'Tetrode2.spikes'
        eventFile = os.path.join(testDataDir,eventFn)
        spikesFile = os.path.join(testDataDir,spikesFn)
        eventData = loadopenephys.Events(eventFile)
        dataSpikes = loadopenephys.DataSpikes(spikesFile)
        spikeTimestamps = dataSpikes.timestamps
        eventOnsetTimes = eventData.get_event_onset_times()

        #convert to seconds
        samplingRate = eventData.samplingRate
        spikeTimestamps = spikeTimestamps/samplingRate
        eventOnsetTimes = eventOnsetTimes/samplingRate
        assert len(eventOnsetTimes)==513

        timeRange = [-0.5, 1.0]
        #Remove events except from frist pulse in laser train
        eventOnsetTimes = spikesanalysis.minimum_event_onset_diff(eventOnsetTimes, 0.5)
        assert len(eventOnsetTimes)==103

        (spikeTimesFromEventOnset,
        trialIndexForEachSpike,
        indexLimitsEachTrial) = spikesanalysis.eventlocked_spiketimes(spikeTimestamps,
                                                                        eventOnsetTimes,
                                                                        timeRange)

        plt.plot(spikeTimesFromEventOnset, trialIndexForEachSpike, '.')
        # plt.show()
