'''
List of all isolated units from one animal
'''

from jaratoolbox import celldatabase
reload(celldatabase)
eSession = celldatabase.EphysSessionInfo  # Shorter name to simplify code


cellDB = celldatabase.CellDatabase()


oneES = eSession(animalName='test030',
                 ephysSession = '2014-06-25_18-33-30_TT6goodGND',
                 clustersEachTetrode = {4:[1,3], 6:[3,8,10]},
                 behavSession = '20140625a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test030',
                 ephysSession = '2014-07-30_13-25-28',
                 clustersEachTetrode = {2:[1,3]},
                 behavSession = '')
cellDB.append_session(oneES)


