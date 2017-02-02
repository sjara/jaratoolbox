import os
import unittest
from jaratoolbox import spikesorting
from jaratoolbox import settings
from matplotlib import pyplot as plt
import subprocess
testDataDir = settings.TEST_EPHYS_DATA_PATH

class TestLoadOpenEphys(unittest.TestCase):

    def test_data(self):
        transferCommand = ['rsync', '-av', settings.TEST_DATA_REMOTE, settings.TEST_DATA_LOCAL_ROOT]
        subprocess.call(transferCommand)

    def test_clustering_single_session(self):
        oneTT = spikesorting.TetrodeToCluster('test', 'testdata', 2)
        oneTT.load_waveforms()
        oneTT.create_fet_files()
        oneTT.run_clustering()
        oneTT.save_report()

    def test_clustering_multiple_sessions(self):
        oneTT = spikesorting.MultipleSessionsToCluster('test', ['testdata', 'testdata2'], 2, 'test')
        oneTT.load_all_waveforms()
        oneTT.create_multisession_fet_files()
        oneTT.run_clustering()
        oneTT.save_multisession_report()

