'''
2015-07-31 Nick Ponvert

This file shows how to load a database file, query the database to find certain clusters,
extract the session filenames from the cluster, and use the **DataLoading** object to load the
data.
'''
from jaratoolbox.test.nick.database import dataloader
from jaratoolbox.test.nick.database import cellDB
reload(cellDB)
reload(dataloader)

# ----------------------
##Load the database and find a cluster
# ----------------------

dbfile = '/tmp/allcells.json'
db2 = cellDB.CellDB()
db2.load_from_json(dbfile)

cell1 = db.find_cell_from_site('pinp003', '2015-06-24',  3543, 6, 5)

# -----------------------
##Getting the data from a cluster to make a plot
# -----------------------

#Sessions with no behav data return just the ephys
cell1NoisePhys = cell1.get_data_filenames('noiseBurst')

#Sessions with behav data return the tuple (ephysFilename, behavFilename)
cell1TuningPhys, cell1TuningBehavior = cell1.get_data_filenames('tcHeatmap')
