'''
Example of using spikesorting module (which uses KlustaKwik) for spike sorting
'''

from jaratoolbox import spikesorting
reload(spikesorting)

CASE = 1

if CASE==1:
    animalName = 'test030'
    ephysSession = '2014-06-25_18-33-30_TT6goodGND'
    tetrode = 6

oneTT = spikesorting.TetrodeToCluster(animalName,ephysSession,tetrode)

#oneTT.load_waveforms() # Note that create_fet_files will run this method again.


oneTT.create_fet_files()

oneTT.run_clustering()

oneTT.save_report()
'''
'''
