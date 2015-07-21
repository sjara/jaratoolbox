from jaratoolbox.test.nick.ephysExperiments import recordingday as rd
reload(rd)

today = rd.RecordingDay(animalName = 'pinp003', date = '2015-06-24', experimenter = 'nick')

site1 = today.add_site(depth = 3543, goodTetrodes = [6])

s1NB = site1.add_session('15-22-29', None, 'NoiseBurst')
s1LP = site1.add_session('15-25-08', None, 'LaserPulse')
s1LT = site1.add_session('15-27-37', None, 'LaserTrain')
s1TC = site1.add_session('15-31-48', 'a', 'TuningCurve')
s1BF = site1.add_session('15-45-22', 'b', 'BestFreq')

cluster1 = site1.add_cluster(2, soundResponsive=True, laserPulseResponse=True, followsLaserTrain=True, comments='good cell')
cluster2 = site1.add_cluster(5, soundResponsive=True, laserPulseResponse=True, comments='probably synaptic')
cluster3 = site1.add_cluster(5, soundResponsive=True, laserPulseResponse=True, comments='probably synaptic') #A repeat cluster

site1.write_database('/tmp/celldb7.json')

cellDB = rd.load_cluster_database('/tmp/celldb7.json')
