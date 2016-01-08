'''
List of all isolated units from one animal
'''

from jaratoolbox import celldatabase
eSession = celldatabase.EphysSessionInfo  # Shorter name to simplify code


cellDB = celldatabase.CellDatabase()


oneES = eSession(animalName='test089',
                 ephysSession = '2015-07-27_15-48-06',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150727a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-07-28_13-39-35',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150728a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-07-29_10-02-50',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150729a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-07-30_16-14-33',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150730c')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-07-31_14-27-52',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150731a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-01_13-24-02',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150801a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-03_15-53-28',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150803a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-04_11-10-06',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150804a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-05_16-31-14',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150805a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',#################################################################
                 ephysSession = '2015-08-06_13-04-36 ',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150806a')
cellDB.append_session(oneES)
'''

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-07_15-47-51',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150807a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-10_15-06-35',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150810a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-11_11-04-53',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150811a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',#########################################################################
                 ephysSession = '2015-08-12_23-08-07',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150812a')
cellDB.append_session(oneES)
'''

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-13_16-45-00',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150813a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',#########################################################################
                 ephysSession = '2015-08-14_13-03-20',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150814a')
cellDB.append_session(oneES)
'''

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-17_15-13-03',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150817a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-18_17-20-28',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150818a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-19_12-44-48',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150819a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-20_12-39-56',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150820a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-27_11-47-43',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150827a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-28_11-04-56',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150828a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-08-31_15-59-13',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150831a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-01_13-56-47',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150901a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-02_14-25-18',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150902a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-09_13-19-59',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150901a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',################################################################
                 ephysSession = '2015-09-10_12-24-35 ',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150910a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-11_12-19-19',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150911a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-13_15-49-37',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150913a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-14_17-50-55',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150914a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',#####################################################
                 ephysSession = '2015-09-15_12-19-30 ',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150915a')
cellDB.append_session(oneES)
'''

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-18_12-50-42',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150918a')
cellDB.append_session(oneES)

'''
oneES = eSession(animalName='test089',############################################################
                 ephysSession = '2015-09-21_12-08-09 ',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150921a')
cellDB.append_session(oneES)
'''

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-23_12-32-17',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150923a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-24_13-23-14',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150924a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-09-25_12-30-40',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20150925a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-10-08_13-37-12',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20151008a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-10-09_11-25-21',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20151009a')
cellDB.append_session(oneES)

oneES = eSession(animalName='test089',
                 ephysSession = '2015-10-14_11-00-10',
                 clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                 behavSession = '20151014a')
cellDB.append_session(oneES)
