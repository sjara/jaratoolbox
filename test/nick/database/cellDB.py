'''
2015-07-24 Nick Ponvert

Beginnings of the electrophysiology recording database for Jaralab. 

'''

class CellDB(list):

    def __init__(self):
        super(CellDB, self).__init__()

    
    def add_clusters(self, clusters):

        for cluster in clusters:
            self.append(cluster)


class Recording(object):


    def __init__(self, animalName, date, experimenter, paradigm): 
        self.animalName = animalName
        self.date = date
        self.experimenter = experimenter
        self.paradigm = paradigm
        self.siteList = []

    def add_site(self, depth, goodTetrodes):
        site = Site(depth,
                    goodTetrodes,
                    animalName=self.animalName,
                    date=self.date,
                    experimenter=self.experimenter,
                    paradigm=self.paradigm)

        self.siteList.append(site)
        return site

    def __repr__(self):
        objStrings = []
        for key,value in sorted(vars(self).iteritems()):
            objStrings.append('%s: %s\n'%(key,str(value)))
        return ''.join(objStrings)
    def __str__(self):
        objStr = '{0} recording on {1} by {2}'.format(self.animalName,
                                                      self.date,
                                                      self.experimenter)
        return objStr
 

class Site(object):

    '''
    Class for holding information about a recording site. 
    Will act as a parent for all of the Session 
    objects that hold information about each individual recording session.
    '''

    def __init__(self, depth, goodTetrodes, animalName, date, experimenter, paradigm):

        self.depth = depth
        self.goodTetrodes = goodTetrodes
        self.animalName = animalName #Provided by Recording
        self.date = date #Provided by Recording
        self.experimenter = experimenter #Provided by Recording
        self.paradigm = paradigm #Provided by Recording
        self.sessionList = []
        self.clusterList = []

    def add_session(self, sessionID, behavFileIdentifier, sessionType):
        session = Session(sessionID, behavFileIdentifier, sessionType, self.date)
        self.sessionList.append(session)
        return session

    def add_cluster(self,
                    clusterNumber,
                    tetrode,
                    soundResponsive=False,
                    laserPulseResponse=False,
                    followsLaserTrain=False,
                    comments=''):

        cluster = Cluster(
            animalName=self.animalName,
            date=self.date,
            depth=self.depth,
            experimenter=self.experimenter,
            paradigm = self.paradigm,
            clusterNumber=clusterNumber,
            tetrode=tetrode,
            ephysSessionList=self.get_session_filenames(),
            behavFileList=self.get_session_behavIDs(),
            sessionTypes=self.get_session_types(),
            soundResponsive=soundResponsive,
            laserPulseResponse=laserPulseResponse,
            followsLaserTrain=followsLaserTrain,
            comments=comments)

        self.clusterList.append(cluster)
        return cluster

    def get_session_filenames(self):
       return [s.session for s in self.sessionList]

    def get_session_behavIDs(self):
        return [s.behavFileIdentifier for s in self.sessionList]

    def get_session_types(self):
        return [s.sessionType for s in self.sessionList]

    def get_session_inds_one_type(self, plotType, report):
        return [index for index, s in enumerate(self.sessionList) if ((s.plotType == plotType) & (s.report == report))]

class Session(object):

    '''
    Class to hold information about a single session.
    Includes the session name, the type of session, and any associated behavior data
    Accepts just the time of the recording (i.e. 11-36-54), and the date, which can
    be passed from the parent when this class is called. This keeps us from
    having to write it over and over again.
    '''

    def __init__(self, sessionID, behavFileIdentifier, sessionType, date):
        self.session = '_'.join([date, sessionID])
        self.behavFileIdentifier = behavFileIdentifier
        self.sessionType = sessionType
        self.plotType = ''
        self.report = ''

    def set_plot_type(self, plotTypeStr, report='main'):
        self.plotType = plotTypeStr
        self.report = report


class Cluster(object):

    def __init__(
            self,
            animalName,
            date,
            depth,
            tetrode,
            experimenter,
            paradigm,
            clusterNumber,
            ephysSessionList,
            behavFileList,
            sessionTypes,
            soundResponsive,
            laserPulseResponse,
            followsLaserTrain,
            comments=''):

        self.animalName = animalName
        self.date = date
        self.cluster = clusterNumber
        self.tetrode = tetrode
        self.clusterNumber = clusterNumber
        self.ephysSessionList = ephysSessionList
        self.behavFileList = behavFileList
        self.sessionTypes = sessionTypes
        self.soundResponsive = soundResponsive
        self.laserPulseResponse = laserPulseResponse
        self.followsLaserTrain = followsLaserTrain
        self.comments = comments

        self.clusterID = '_'.join([animalName,
                                   date,
                                   str(depth),
                                   'TT{}'.format(self.tetrode),
                                   str(clusterNumber)])
    

