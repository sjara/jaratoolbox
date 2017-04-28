from jaratoolbox import celldatabase
import unittest

class TestCellDatabase(unittest.TestCase):

    def setUp(self):
        subject = 'pinp016'
        self.experiments = []
        exp0 = celldatabase.Experiment(subject,
                                    '2017-03-07',
                                    brainarea='rightAC',
                                    info=['medialDiI', 'facingLateral'])
        self.experiments.append(exp0)
        exp0.add_site(2123, tetrodes=range(1, 9))
        exp0.add_session('14-58-17', None, 'noiseburst', 'am_tuning_curve')

    def test_basic_inforec(self):
        assert len(self.experiments) == 1
        assert self.experiments[0].sites[0].depth == 2123

    def test_pretty_printing(self):
        for experiment in self.experiments:
            print experiment.pretty_print(sites=True, sessions=True)

    def test_cluster_folder(self):
        assert self.experiments[0].sites[0].clusterFolder == 'multisession_2017-03-07_2123um'

    def test_midnight_recording(self):
        self.experiments[0].add_session('00-01-00', None, 'laserpulse', 'am_tuning_curve', date='2017-03-08')
        assert self.experiments[0].sites[0].sessions[1].ephys_dir() == '2017-03-08_00-01-00'

    def test_comments(self):
        self.experiments[0].site_comment('Nice site')
        self.experiments[0].session_comment('Good response')
        print ''.join(self.experiments[0].sites[0].comments)
        print ''.join(self.experiments[0].sites[0].sessions[0].comments)

        #Commenting on one site should not affect other sites
        self.experiments[0].add_site(2124, tetrodes=range(1, 9))
        assert self.experiments[0].sites[1].comments == []

    def test_adding_session_with_no_sites(self):
        subject = 'pinp016'
        exp1 = celldatabase.Experiment(subject,
                                    '2017-03-08',
                                    brainarea='rightAC',
                                    info=['medialDiI', 'facingLateral'])
        self.assertRaises(IndexError, lambda: exp1.add_session('14-58-17', None, 'noiseburst', 'am_tuning_curve'))

