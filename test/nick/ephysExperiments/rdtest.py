from jaratoolbox.test.nick.ephysExperiments import recordingday as rd
reload(rd)

today = rd.Recording(animalName = 'pinp003',
                     date = '2015-06-24',
                     experimenter = 'nick',
                     paradigm='laser_tuning_curve')

site1 = today.add_site(depth = 3543, goodTetrodes = [6])

s1NB = site1.add_session('15-22-29', None, 'NoiseBurst')
s1NB.set_plot_type('raster', report='main')

s1LP = site1.add_session('15-25-08', None, 'LaserPulse')
s1LP.set_plot_type('raster', report='main')

s1LT = site1.add_session('15-27-37', None, 'LaserTrain')
s1LT.set_plot_type('raster', report='main')

s1TC = site1.add_session('15-31-48', 'a', 'TuningCurve')
s1TC.set_plot_type('tc_heatmap', report='main')

s1BF = site1.add_session('15-45-22', 'b', 'BestFreq')
s1BF.set_plot_type('raster', report='main')

site1.generate_main_report(show=True, save=False, saveClusterReport=False)

cluster1 = site1.add_cluster(clusterNumber=2, tetrode=6, soundResponsive=True, laserPulseResponse=True, followsLaserTrain=True, comments='good cell')
cluster2 = site1.add_cluster(clusterNumber=5, tetrode=6, soundResponsive=True, laserPulseResponse=True, comments='probably synaptic')
cluster3 = site1.add_cluster(clusterNumber=5, tetrode=6, soundResponsive=True, laserPulseResponse=True, comments='probably synaptic') #A repeat cluster


cluster4 = site1.add_cluster(clusterNumber=7, tetrode=6, soundResponsive=True, comments='sound responsive only')


cellDB = rd.JSONCellDB('/tmp/celldb1.json')
cellDB.add_clusters([cluster1, cluster2, cluster3, cluster4])
cellDB.write_database()


