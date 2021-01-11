import os
import unittest
from jaratoolbox import spikesorting
from jaratoolbox import settings
from matplotlib import pyplot as plt
import subprocess

class TestSpikesorting(unittest.TestCase):

    def test_clustering_single_session(self):
        oneTT = spikesorting.TetrodeToCluster('test', 'testdata', 2)
        oneTT.load_waveforms()
        oneTT.create_fet_files()
        oneTT.run_clustering()
        oneTT.save_report()

    def test_clustering_multiple_sessions(self):
        oneTT = spikesorting.MultipleSessionsToCluster('test', ['testdata', 'testdata2'], 2, 'test')
        oneTT.load_waveforms()
        oneTT.create_fet_files()
        oneTT.run_clustering()
        oneTT.save_single_session_clu_files()
        oneTT.save_report()

