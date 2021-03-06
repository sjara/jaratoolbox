'''
List of all isolated units from one animal
'''

from jaratoolbox import celldatabase_quality_depth as celldatabase
eSession = celldatabase.EphysSessionInfo  # Shorter name to simplify code


cellDB = celldatabase.CellDatabase()

#Relative tetrode lengths
#    TT2: 0mm
#    TT1: 140um
#    TT8: 190um
#    TT5: 260um
#    TT3: 320um
#    TT4: 440um
#    TT7: 580um
#    TT6: 640um


oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-27_13-57-32',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[2,2,3,2,4,2,2,2,2,2,2,2],2:[2,2,1,2,2,2,2,2,2,2,2,2],3:[3,2,3,3,3,3,2,3,1,3,3,3],4:[3,0,0,0,0,0,0,0,0,0,0,0],5:[3,3,2,2,2,2,3,2,2,2,4,2],6:[3,1,2,4,3,3,1,3,3,3,1,2],7:[3,3,3,3,3,2,3,2,2,2,0,0],8:[3,2,3,2,1,2,2,2,3,2,4,2]},
                 depth = 3.149,
                 behavSession = '20150727a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-23_17-31-28',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,0,0,0,0,0,0,0,0,0,0,0],2:[3,3,3,3,3,3,4,3,3,3,3,0],3:[1,1,1,1,1,1,1,1,1,1,1,1],4:[3,2,2,2,2,3,3,2,3,3,3,3],5:[3,3,3,3,3,3,2,3,3,2,3,3],6:[3,2,3,2,2,2,2,3,2,4,3,4],7:[3,3,3,3,3,3,3,3,3,3,3,0],8:[3,3,2,3,3,3,3,3,2,3,0,0]},
                 depth = 2.872,
                 behavSession = '20150723a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-22_16-20-38',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,3,3,4,3,2,3,3,3,3],2:[3,2,2,3,3,2,3,3,3,3,3,3],3:[3,1,3,1,3,2,1,1,2,3,3,0],4:[3,3,3,2,3,3,3,3,3,3,3,3],5:[3,2,2,3,3,3,3,2,3,3,3,3],6:[3,3,3,3,3,2,3,2,3,3,2,3],7:[3,0,0,0,0,0,0,0,0,0,0,0],8:[3,3,3,2,3,3,3,3,3,3,3,3]},
                 depth = 2.793,
                 behavSession = '20150722a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-16_14-08-07',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,3,2,3,3,3,2,2,3,3],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,3,3,2,2,3,2,3,2,2,2,3],4:[3,3,3,2,2,2,3,3,3,3,1,1],5:[3,2,2,3,3,3,2,2,2,3,3,3],6:[3,1,2,2,1,2,3,2,3,3,2,2],7:[3,3,3,2,3,3,2,3,3,2,2,2],8:[3,3,4,4,2,3,3,3,3,3,3,3]},
                 depth = 2.634,
                 behavSession = '20150716a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-15_16-09-03',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,4,4,3,2,3,3,3,3,2,2],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,2,3,3,2,3,2,2,2,2,2,2],4:[3,3,3,3,3,3,2,3,3,2,3,3],5:[3,3,3,3,3,3,2,2,3,3,3,3],6:[3,3,3,3,3,2,2,2,2,3,2,2],7:[3,2,2,2,3,3,3,3,3,3,3,0],8:[3,3,3,3,3,3,2,3,1,3,1,4]},
                 depth = 2.594,
                 behavSession = '20150715a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-14_11-36-39',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,3,3,3,2,3,3,3,3,3],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,2,3,2,3,2,2,2,2,2,3,0],4:[3,1,3,2,2,1,3,3,2,3,2,3],5:[3,3,2,3,3,3,3,2,3,2,3,2],6:[3,3,2,3,3,3,3,3,3,2,3,0],7:[3,3,3,2,3,3,2,3,3,3,3,3],8:[3,3,1,3,2,3,3,3,2,3,3,3]},
                 depth = 2.555,
                 behavSession = '20150714a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-13_13-40-41',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,3,3,4,3,3,2,2,2,2,2],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,3,2,2,2,2,2,3,2,3,3,0],4:[3,2,1,2,2,3,3,3,2,3,2,3],5:[3,2,3,2,3,3,3,2,3,3,3,3],6:[3,2,3,3,2,3,3,3,3,3,3,3],7:[3,3,3,3,2,3,3,3,3,3,3,0],8:[3,2,1,3,3,2,3,1,3,3,3,3]},
                 depth = 2.555,
                 behavSession = '20150713a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-10_13-33-33',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,3,3,3,2,3,3,3,3,3],2:[3,3,3,3,3,2,3,2,2,2,3,3],3:[3,2,3,3,3,3,3,2,2,2,2,0],4:[3,3,3,3,3,3,3,3,2,3,2,3],5:[3,3,3,2,3,3,3,2,3,2,3,3],6:[3,3,3,3,3,3,3,3,3,2,3,3],7:[3,0,0,0,0,0,0,0,0,0,0,0],8:[3,1,3,2,3,3,3,3,3,3,3,3]},
                 depth = 2.515,
                 behavSession = '20150710a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-09_17-02-43',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,3,3,3,2,3,3,3,3,3,3],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,3,3,2,2,2,2,2,2,2,2,2],4:[3,3,3,3,3,2,3,2,3,3,3,2],5:[3,3,3,3,4,3,3,3,3,3,2,2],6:[3,3,1,3,1,3,3,3,3,3,3,3],7:[3,3,3,3,2,3,3,3,3,3,3,3],8:[3,3,3,1,3,3,1,3,3,3,3,3]},
                 depth = 2.515,
                 behavSession = '20150709a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-08_13-06-14',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,2,2,2,2,3,2,1,2,2,4],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,2,2,3,3,2,3,3,2,2,2,3],4:[3,2,3,3,2,2,2,2,1,3,1,1],5:[3,3,3,3,3,2,3,2,1,2,1,2],6:[3,3,1,3,1,1,1,3,3,2,3,3],7:[3,2,2,3,3,3,3,3,3,2,2,3],8:[3,3,3,3,1,3,2,2,4,3,3,0]},
                 depth = 2.515,
                 behavSession = '20150708a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-06_11-35-54',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,2,3,1,2,1,2,2,2,2],2:[3,2,2,3,2,3,3,2,3,2,2,2],3:[3,0,0,0,0,0,0,0,0,0,0,0],4:[3,2,3,2,3,1,2,3,2,3,3,3],5:[3,2,2,2,3,3,2,2,2,2,3,0],6:[3,2,2,3,3,3,3,1,2,2,4,1],7:[3,3,2,3,2,3,3,3,3,3,3,2],8:[3,1,3,2,2,1,2,2,2,2,3,3]},
                 depth = 2.476,
                 behavSession = '20150706a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-03_16-50-19',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,1,1,2,2,2,2,3,3,3,2],2:[3,2,2,2,2,3,2,2,2,0,0,0],3:[3,0,0,0,0,0,0,0,0,0,0,0],4:[3,2,3,2,3,2,2,3,3,2,3,3],5:[3,3,2,2,3,2,3,3,3,2,2,2],6:[3,2,3,4,2,3,2,3,2,2,3,3],7:[3,2,3,3,2,2,3,2,2,2,2,0],8:[3,2,3,2,3,3,2,3,3,3,3,0]},
                 depth = 2.476,
                 behavSession = '20150703a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-01_11-17-27',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,3,3,3,2,3,3,3,3,3,3],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,2,2,2,2,2,3,2,2,2,3,3],4:[3,2,3,3,3,3,3,3,3,3,2,3],5:[3,2,2,3,3,2,2,2,2,2,2,3],6:[3,2,2,1,2,3,1,1,3,3,3,0],7:[3,2,1,1,3,3,3,3,3,2,2,2],8:[3,1,1,3,3,1,2,2,3,2,2,1]},
                 depth = 2.476,
                 behavSession = '20150701a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-29_11-30-24',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,3,3,2,3,3,3,3,2,2],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,2,2,2,2,3,2,2,2,2,3,3],4:[3,3,3,2,1,2,3,2,3,3,2,2],5:[3,2,2,2,2,3,3,2,3,3,2,0],6:[3,3,1,1,3,3,2,2,3,3,2,0],7:[3,3,3,3,3,2,3,3,3,2,2,2],8:[3,3,2,2,1,1,1,3,3,1,3,3]},
                 depth = 2.396,
                 behavSession = '20150629a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-25_11-42-24',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,3,3,3,3,3,1,1,1,2,3],2:[3,0,0,0,0,0,0,0,0,0,0,0],3:[3,3,2,3,2,2,2,2,3,2,3,3],4:[3,2,2,2,2,3,1,2,2,2,1,2],5:[3,3,3,2,3,2,2,2,2,2,2,0],6:[3,1,1,2,1,2,2,2,3,2,2,4],7:[3,2,4,1,3,2,3,3,2,2,2,2],8:[3,3,2,3,2,2,2,1,2,2,4,2]},
                 depth = 2.357,
                 behavSession = '20150625a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-22_11-41-15',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,1,3,3,3,3,3,2,3,3,3,2],2:[3,3,3,2,3,3,2,2,3,2,2,3],3:[3,0,0,0,0,0,0,0,0,0,0,0],4:[3,3,1,4,2,2,3,2,3,3,3,2],5:[3,2,3,2,3,3,2,2,2,3,3,3],6:[3,2,1,4,4,2,3,2,3,3,3,3],7:[3,3,3,3,2,2,3,2,2,3,3,0],8:[3,2,2,1,3,1,2,3,2,3,3,3]},
                 depth = 2.357,
                 behavSession = '20150622a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-18_10-34-39',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,3,2,2,3,3,3,2,3,2,2,1],2:[3,2,1,3,3,3,2,2,2,2,2,3],3:[3,2,2,2,2,3,3,3,2,2,3,3],4:[3,0,0,0,0,0,0,0,0,0,0,0],5:[3,2,2,2,2,2,3,2,2,3,2,0],6:[3,1,2,2,2,2,3,3,2,2,2,2],7:[3,3,2,1,1,3,2,2,2,2,2,2],8:[3,3,2,3,2,3,2,3,3,2,3,2]},
                 depth = 2.317,
                 behavSession = '20150618a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-17_10-40-01',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,4,3,4,2,3,2,1,1,3,3,2],2:[3,2,3,3,2,2,2,3,3,3,3,3],3:[3,3,3,2,2,2,3,3,3,3,2,2],4:[3,0,0,0,0,0,0,0,0,0,0,0],5:[3,2,2,3,2,2,3,3,2,3,3,3],6:[3,3,1,2,3,1,2,2,1,2,2,2],7:[3,2,1,2,2,1,3,1,3,3,1,3],8:[3,2,3,3,3,2,2,2,4,4,2,2]},
                 depth = 2.317,
                 behavSession = '20150617a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-15_16-05-58',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,1,1,3,1,3,3,3,3,2,1],2:[3,2,2,2,3,2,2,3,1,3,2,2],3:[3,3,2,2,3,3,2,3,3,2,2,3],4:[3,0,0,0,0,0,0,0,0,0,0,0],5:[3,2,3,3,2,4,2,2,2,3,2,2],6:[3,2,2,2,2,3,2,1,2,3,2,2],7:[3,3,2,2,3,3,3,3,3,3,3,3],8:[3,2,2,2,3,2,3,3,2,3,2,3]},
                 depth = 2.317,
                 behavSession = '20150615a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-10_14-44-24',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 clusterQuality = {1:[3,2,2,1,2,3,2,3,3,2,1,2],2:[3,3,2,2,3,2,1,1,1,2,2,1],3:[3,3,2,2,2,2,3,2,2,2,2,2],4:[3,0,0,0,0,0,0,0,0,0,0,0],5:[3,2,2,2,2,1,2,2,2,2,2,2],6:[3,2,2,2,2,2,2,2,2,2,2,2],7:[3,3,2,2,2,2,3,2,1,2,2,0],8:[3,2,3,2,4,2,2,1,2,3,1,2]},
                 depth = 2.317,
                 behavSession = '20150610a')
cellDB.append_session(oneES)

'''
#The behavior file is missing for this session
oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-24_11-56-39',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150724a')
cellDB.append_session(oneES)

#This session has a skipped trial at trial 574
oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-17_14-39-27',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150717a')
cellDB.append_session(oneES)

#This session has a skipped trial at trial 700
oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-07_17-21-43',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150707a')
cellDB.append_session(oneES)

#This has one skipped trial at 405
oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-26_11-25-16',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150626a')
cellDB.append_session(oneES)

#This has one skipped trial at 1148
oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-19_10-33-57',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150619a')
cellDB.append_session(oneES)

#This has more than one skipped trial
oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-12_18-29-46',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150612a')
cellDB.append_session(oneES)

#This session has a skipped trial at trial 1097
oneES = eSession(animalName='test053',
                 ephysSession = '2015-06-11_15-46-05',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150611a')
cellDB.append_session(oneES)
'''
'''
#This session could not cluster properly for an unknown reason
oneES = eSession(animalName='test053',
                 ephysSession = '2015-07-02_12-12-03',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150702a')
cellDB.append_session(oneES)
'''
