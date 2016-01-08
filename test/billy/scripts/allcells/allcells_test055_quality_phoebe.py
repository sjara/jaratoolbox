'''
List of all isolated units from one animal
'''

from jaratoolbox import celldatabase_quality as celldatabase
eSession = celldatabase.EphysSessionInfo  # Shorter name to simplify code


cellDB = celldatabase.CellDatabase()

oneES = eSession(animalName='test055',
                 ephysSession = '2015-06-04_15-02-05',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,4,4,3,6,2,3,3,3,6,2,6],2:[3,3,3,7,2,2,2,7,6,6,4,3],3:[3,4,4,1,3,4,3,4,1,3,3,4],4:[3,7,2,2,1,1,1,1,1,3,1,0],5:[3,2,2,4,1,2,3,4,8,3,2,2],6:[2,0,0,0,0,0,0,0,0,0,0,0],7:[3,2,2,2,1,2,1,1,1,3,3,2],8:[3,2,2,3,2,2,1,1,3,3,2,2]},
		 behavSession = '20150604a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-06-02_13-32-18',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,6,2,3,2,4,1,3,1,1,2,1],2:[3,2,3,2,2,3,2,4,2,4,3,2],3:[3,1,1,4,3,1,1,4,3,2,1,1],4:[3,2,2,1,4,1,6,1,4,1,1,3],5:[3,1,2,3,1,2,2,3,2,1,3,2],6:[2,0,0,0,0,0,0,0,0,0,0,0],7:[3,2,2,1,1,2,3,4,1,1,2,3],8:[3,1,1,1,1,2,6,1,1,2,3,1]},
		 behavSession = '20150602a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-06-01_12-51-07',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,1,6,3,2,2,2,4,4,4,4],2:[3,2,6,2,3,2,2,3,4,1,1,2],3:[3,1,4,4,3,4,1,1,2,1,4,4],4:[3,2,2,3,1,2,4,4,1,4,4,3],5:[3,1,1,4,6,2,2,1,2,3,3,0],6:[3,0,0,0,0,0,0,0,0,0,0,0],7:[3,2,1,1,2,2,1,1,1,3,1,4],8:[3,2,2,1,2,1,1,1,1,1,1,2]},
		 behavSession = '20150601a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-30_15-51-45',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,4,1,1,4,3,3,6,4,1,4],2:[3,2,2,3,2,1,2,3,3,2,3,3],3:[3,2,4,1,2,1,4,3,2,1,4,2],4:[3,1,1,3,2,2,2,1,1,4,1,3],5:[3,3,1,1,1,2,3,1,3,2,3,2],6:[3,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,2,1,1,1,1,3,1,1,1,1],8:[3,1,6,6,3,6,2,1,1,1,7,6]},

		 behavSession = '20150530a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-29_14-00-38',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,2,4,1,1,3,3,2,6,1,3],2:[3,2,2,2,2,2,3,2,3,2,3,2],3:[3,1,1,3,1,2,1,2,3,1,3,4],4:[3,1,1,4,1,3,1,2,7,1,1,2],5:[3,1,1,3,2,2,3,2,3,2,2,2],6:[6,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,1,3,4,1,4,1,3,1,4,2],8:[3,1,2,5,2,1,7,3,7,7,2,6]},

		 behavSession = '20150529a')
cellDB.append_session(oneES) 


oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-28_12-49-35',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,1,1,6,2,1,3,3,4,7,2],2:[3,3,3,3,2,1,3,2,3,3,3,2],3:[3,1,4,1,1,3,1,2,1,1,3,3],4:[3,1,2,1,3,1,3,1,2,3,3,2],5:[3,3,2,2,3,1,3,2,6,3,2,2],6:[3,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,3,2,1,2,1,3,3,1,1,3],8:[3,1,4,3,1,3,1,3,2,3,2,2]},

		 behavSession = '20150528a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-27_12-20-52',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,3,3,7,7,3,6,3,2,3,2],2:[3,1,2,3,2,3,1,3,3,1,2,1],3:[3,1,4,1,1,3,1,1,1,3,1,2],4:[3,1,1,1,2,1,1,2,2,3,1,1],5:[3,2,2,2,2,2,1,2,3,3,2,3],6:[3,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,3,1,2,3,1,1,1,1,3,3],8:[3,4,1,3,3,2,2,3,1,2,1,3]},

		 behavSession = '20150527a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-26_13-19-02',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,1,3,1,3,6,3,1,1,1,2],2:[3,1,2,5,1,3,2,2,3,3,1,6],3:[3,2,1,1,3,3,3,2,2,3,1,3],4:[3,2,1,1,1,1,3,1,1,1,5,1],5:[3,3,2,2,2,1,3,2,2,3,3,1],6:[6,0,0,0,0,0,0,0,0,0,0,0],7:[3,2,1,1,1,3,3,1,3,1,1,3],8:[3,2,3,3,2,3,3,2,3,2,2,3]},

		 behavSession = '20150526a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-19_12-54-16',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,4,1,1,1,6,1,1,3,1,4],2:[3,1,3,3,1,2,2,2,1,1,3,3],3:[3,1,3,1,4,1,3,3,2,1,2,0],4:[3,4,2,2,4,4,2,1,1,4,1,3],5:[3,2,2,2,3,3,2,2,5,4,2,0],6:[6,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,1,1,1,1,5,1,3,1,2,1],8:[3,1,1,1,1,6,1,2,2,1,1,3]},

		 behavSession = '20150518a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-18_13-13-02',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,1,1,1,2,6,6,6,1,3,2],2:[3,2,2,1,6,1,2,3,3,2,2,2],3:[3,4,1,1,4,1,3,2,3,1,2,1],4:[3,2,1,1,2,1,3,2,1,3,2,0],5:[3,5,2,2,2,3,5,3,3,2,2,1],6:[3,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,2,2,6,6,1,3,1,1,3,4],8:[3,2,4,1,1,6,1,2,2,1,1,1]},

		 behavSession = '20150518a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-17_18-01-31',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,8,1,1,1,3,1,2,1,3,3],2:[3,1,3,2,1,3,5,3,2,6,1,0],3:[3,2,2,1,3,3,2,3,3,1,1,6],4:[3,1,1,4,2,3,2,2,3,1,3,1],5:[3,2,1,2,2,2,3,2,2,2,3,5],6:[6,0,0,0,0,0,0,0,0,0,0,0],7:[3,1,1,1,5,1,2,1,1,2,1,1],8:[3,1,2,1,1,1,1,3,2,1,1,6]},

		 behavSession = '20150517a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-15_12-05-23',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[

		 behavSession = '2015015a')
cellDB.append_session(oneES) 

oneES = eSession(animalName='test055',
                 ephysSession = '2015-05-15_12-05-23',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[

		 behavSession = '2015015a')
cellDB.append_session(oneES) 













