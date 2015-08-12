from jaratoolbox.test.nick.database import dataloader
reload(dataloader)

from jaratoolbox.test.nick.database import cellDB
reload(cellDB)

from jaratoolbox.test.nick.database import dataplotter
from jaratoolbox import spikesorting
from jaratoolbox.test.nick import clustercutting

from pylab import *


loader = dataloader.DataLoader('offline', experimenter='nick')

dbFn = '/home/nick/data/database/nick_thalamus_cells.json'
db = cellDB.CellDB()
db.load_from_json(dbFn)


c = db[8]
spikeData, eventData, behavData = loader.get_cluster_data(c, 'laserPulse')

spikeTimes = spikeData.timestamps
eventOnsetTimes = loader.get_event_onset_times(eventData)

# figure()
# spikesorting.plot_waveforms(spikeData.samples)
# title('all spikes')

# figure()
# dataplotter.plot_raster(spikeTimes, eventOnsetTimes)
# show()

# fet = spikesorting.calculate_features(spikeData.samples, ['peak', 'valley', 'energy'])
fet = spikesorting.calculate_features(spikeData.samples, ['peak'])

cw = clustercutting.ClusterCutter(fet)
