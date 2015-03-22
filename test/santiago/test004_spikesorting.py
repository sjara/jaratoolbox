'''
Example of using spikesorting module (which uses KlustaKwik) for spike sorting
'''

from jaratoolbox import spikesorting
reload(spikesorting)

CASE = 2

if CASE==1:
    animalName = 'test030'
    ephysSession = '2014-06-25_18-33-30_TT6goodGND'
    tetrodes = [6]
if CASE==2:
    animalName = 'pinp001'
    #ephysSession = '2015-03-21_23-56-20'  # sound
    #ephysSession = '2015-03-22_00-02-54'  # laser
    ephysSession = '2015-03-22_00-12-18'  # tuning
    tetrodes = [3,4,6]

for tetrode in tetrodes:
    oneTT = spikesorting.TetrodeToCluster(animalName,ephysSession,tetrode)
    oneTT.create_fet_files()  # This runs oneTT.load_waveforms()
    oneTT.run_clustering()
    oneTT.save_report()
