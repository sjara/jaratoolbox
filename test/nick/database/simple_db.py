import numpy as np
from jaratoolbox.test.nick.database import cellDB
reload(cellDB)

sessionTypes = {'nb':'noiseBurst',
                'lp':'laserPulse',
                'lt':'laserTrain',
                'tc':'tc_heatmap',
                'bf':'bestFreq',
                '3p':'3mWpulse',
                '1p':'1mWpulse'}

day1 = cellDB.Recording(animalName = 'pinp003', date = '2015-06-24', experimenter = 'nick', paradigm='laser_tuning_curve')

d1site1 = day1.add_site(depth = 3543, goodTetrodes = [6])
d1site1.add_session('15-22-29', None, sessionTypes['nb'])
d1site1.add_session('15-25-08', None, sessionTypes['lp']).set_plot_type('raster')
d1site1.add_session('15-27-37', None, sessionTypes['lt']).set_plot_type('raster')
d1site1.add_session('15-31-48', 'a', sessionTypes['tc']).set_plot_type('tc_heatmap')
d1site1.add_session('15-45-22', 'b', sessionTypes['bf']).set_plot_type('raster')

d1site1.add_clusters({6: [5, 8, 11]})



day2 = cellDB.Experiment(animalName = 'pinp003', date = '2015-07-06', experimenter = 'nick', paradigm='laser_tuning_curve')

d2site1 = day2.add_site(depth = 3509, goodTetrodes = [3, 6])
d2site1.add_session('11-15-56', None, sessionTypes['nb'])
d2site1.add_session('11-18-36', None, sessionTypes['lp'])
d2site1.add_session('11-21-26', None, sessionTypes['lt'])
d2site1.add_session('11-25-58', 'a', sessionTypes['tc'])
d2site1.add_session('11-39-46', None, sessionTypes['bf'])
d2site1.add_session('11-42-37', None, sessionTypes['3p'])
d2site1.add_session('11-45-22', None, sessionTypes['1p'])

d2site1.add_clusters({3: [2, 3, 5], 6:[3, 7]})

db = cellDB.CellDB()
db.add_clusters(d1site1.clusterList)
db.add_clusters(d2site1.clusterList)

# dbfile = '/tmp/allcells.json'
# db.write_to_json(dbfile)


# db2 = cellDB.CellDB()
# db2.load_from_json(dbfile)

##Query functionality

#Find a cell from a specific site
cell1 = db.find_cell_from_site('pinp003', '2015-06-24',  3543, 6, 5)


#Find a cell from a specific ephys session
cell2 = db.find_cell_from_session('pinp003', '2015-06-24_15-22-29', 6, 5)


#Intersectional query - find cells that satisfy certain conditions
hlcells = db.query({
    'animalName': 'pinp003',
    'sessionTypes': '3mWpulse'
})

#There is a bug in the code to set feature values
#Setting the features dict for one cluster appears to set the features for all clusters


#Setting features for all cells
#db.set_features({'coolness': 'very cool'})

#Setting features for just cells with specific inds
#db.set_features({'coolness': 'extra cool'}, [1, 3, 5])

#featureArray = np.array(range(8))
#db.set_features_from_array('number', featureArray)

db[0].features['myfeature'] = 1

print db[1].features
