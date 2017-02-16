#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Objects and methods for keeping information about isolated cells'''

import numpy as np
import os
from jaratoolbox import settings
import pandas as pd
import imp

class EphysSessionInfo(object):
     def __init__(self, animalName, ephysSession, behavSession,
                  clustersEachTetrode={}, trialsToExclude=[]):
         '''
         animalName [string] 'test000'
         ephysSession [string] '2014-06-25_18-33-30'
         behavSession [string] '20111209a'
         clustersEachTetrode [dict] {2:[2,5,6], 6:[3,8,10]}  {tetrodeInd:[cluster1,cluster2], ...}
         trialsToExclude [list of lists] [(2,5,range(100:200)), (6,10,range(600,650))]
            [(tetrodeInd,clusterInd,trialrange), ...]
         '''
         self.animalName = animalName
         self.ephysSession = ephysSession
         self.behavSession = behavSession
         self.clustersEachTetrode = clustersEachTetrode
         self.trialsToExclude = trialsToExclude

class CellInfo(object):
    '''
    Container of information for one cell. 
    '''
    def __init__(self, animalName, ephysSession, behavSession, tetrode, cluster,
                 trialsToExclude=[]):
        # -- Basic info --
        self.animalName = animalName
        self.ephysSession = ephysSession
        self.behavSession = behavSession
        self.tetrode = tetrode
        self.cluster = cluster
        # -- Trial selection --
        self.trialsToExclude = np.array(trialsToExclude,dtype=int)
        # -- Response properties --
        #self.soundResponsive = None
    def get_filename(self):
        ephysDir = settings.EPHYS_PATH
        filenameOnly = 'Tetrode{0}.spikes'.format(self.tetrode)
        fullPath = os.path.join(ephysDir,self.animalName,self.ephysSession,filenameOnly)
        return fullPath
    def __repr__(self):
        objStrings = []
        for key,value in sorted(vars(self).iteritems()):
            objStrings.append('%s: %s\n'%(key,str(value)))
        return ''.join(objStrings)
    def __str__(self):
        objStr = '%s %s T%dc%d'%(self.animalName,self.ephysSession,
                                 self.tetrode,self.cluster)
        return objStr

class MultiUnitInfo(object):
    '''
    Container of information for a multiunit site
    '''
    def __init__(self, animalName, ephysSession,behavSession, tetrode, clusters=[]):
        '''Parameter 'clusters' can be empty (all spikes will be included)'''
        # -- Basic info --
        self.animalName = animalName
        self.ephysSession = ephysSession
        self.behavSession = behavSession
        self.tetrode = tetrode
        self.clusters = clusters
        # -- Response properties --
        #self.soundResponsive = None
    def __repr__(self):
        objStrings = []
        for key,value in sorted(vars(self).iteritems()):
            objStrings.append('%s: %s\n'%(key,str(value)))
        return ''.join(objStrings)
    def __str__(self):
        objStr = '%s %s T%d'%(self.animalName,self.ephysSession,
                              self.tetrode)
        return objStr


class CellDatabase(list):
    '''
    Container of set of cells.
    '''
    def __init__(self):
        super(CellDatabase, self).__init__()
    def append_session(self,sessionInfo):
        '''
        sessionInfo [of type EphysSessionInfo]
        '''
        for tetrode in sorted(sessionInfo.clustersEachTetrode.keys()):
            for cluster in sessionInfo.clustersEachTetrode[tetrode]:
                oneCell = CellInfo(animalName = sessionInfo.animalName,
                                   ephysSession = sessionInfo.ephysSession,
                                   behavSession = sessionInfo.behavSession,
                                   tetrode = tetrode,
                                   cluster = cluster,
                                   trialsToExclude = [])
                for trialset in sessionInfo.trialsToExclude:
                    if trialset[0]==tetrode and trialset[1]==cluster:
                        oneCell.trialsToExclude = trialset[2]
                    else:
                        print "Format of 'trialsToExclude' is not correct ({0})".format(oneCell)
                self.append(oneCell)

        
    def findcell(self,firstParam,behavSession='',tetrode=-1,cluster=-1):
        '''
        Find index of cell. It can be used in two ways:
        >> cellDB.findcell('test000','20001201a',1,11)
        >> cellDB.findcell(onecell)
        '''
        if isinstance(firstParam,str):
            onecell = CellInfo(firstParam,'',behavSession,tetrode,cluster)
        else:
            onecell = firstParam
        cellIndex = None
        for ind,cell in enumerate(self):
            if onecell.animalName==cell.animalName:
                if onecell.behavSession==cell.behavSession:
                    if onecell.tetrode==cell.tetrode:
                        if onecell.cluster==cell.cluster:
                            cellIndex = ind
        return cellIndex
    def set_soundResponsive(self,zScores,threshold=3):
        '''
        Set soundResponsive flag for each cell, given zScores
        zScores: numpy array (nTimeBins,nConditions,nCells)
        threshold: above this or below negative this it is considered responsive
        '''
        for indcell,onecell in enumerate(self):
            onecell.soundResponsive = np.any(abs(zScores[:,:,indcell])>threshold)
    def get_vector(self,varname):
        '''
        EXAMPLE: cellDB.get_vector('tetrode')
        '''
        return np.array([getattr(onecell, varname) for onecell in self])
    def subset(self,indexes):
        subsetDB = CellDatabase()
        if isinstance(indexes,np.ndarray) and indexes.dtype==bool:
            indexes = np.flatnonzero(indexes)
        for ind in indexes:
            subsetDB.append(self[ind])
        return subsetDB
    def __str__(self):
        objStrings = []
        for ind,c in enumerate(self):
            objStrings.append('[%d] %s\n'%(ind,c))
        return ''.join(objStrings)
    def save_locked_spikes(self,outputDir,timeRange=np.array([-0.3,0.9]),lockTo=1):
        sessionanalysis.save_data_each_cell(self,outputDir,timeRange=timeRange,lockTo=lockTo)
    def evaluate_response(self):
        # NOTE IMPLEMENTED
        pass


class MultiUnitDatabase(list):
    '''Container of set of multiunit sites.
    '''
    def __init__(self):
        super(MultiUnitDatabase, self).__init__()
    def __str__(self):
        objStrings = []
        for ind,c in enumerate(self):
            objStrings.append('[%d] %s\n'%(ind,c))
        return ''.join(objStrings)
    def save_locked_spikes(self,outputDir,timeRange=np.array([-0.3,0.9]),lockTo=1):
        sessionanalysis.save_data_each_mu(self,outputDir,timeRange=timeRange,lockTo=1)


# ----------------------- THE NEW (2016) VERSION ------------------------

'''
Design decisions:

- Experiment should add sessions directly to the last site in the list of sites.
  This avoids needing to return a handle to each site during an experiment.
  The experimenter can instead just return handles to each experiment object.
  Pros:
      - No need to return a handle to every site (it gets confusing quickly)
  Cons:
      - Sessions are always added to the last site that was created - the experimenter does not choose the site to add a session to (could be misleading?)

- 'tetrodes' should not be specified when creating individual sites
  Everyone clusters all tetrodes anyway
  (Nick originally included the 'tetrodes' argument to specify which tetrodes had good signals at a specific site,
  but even he just clusters everything now).

  Alternatives for the 'tetrodes' variable:
     * Specify it at the experiment level
       Pros:
            - Having 'tetrodes' as an attribute is really convenient to iterate over when clustering.
       Cons:
            - The numbers rarely change and can be determined from the data (the names of the .spikes files)
            - Sometimes we use single electrodes (very rarely) and might possibly use stereotrodes or
            silicon probes with a linear array of recording sites - neither would be added to openEphys GUI as
            a 'Tetrode' and the .spikes file would show up as something like 'SingleElectrode1.spikes' or
            'Stereotrode1.spikes'. Having an argument for 'tetrode' may not always be applicable to all experiments

      * Do not specify it at all
        Pros:
            - More flexibility (applicable to experiments where we are not recording with tetrodes)
        Cons:
            - When clustering, we will need to read the ephys session files to find out which tetrodes were collected

      * Specify both an electrode name and a range of values ('Tetrode', [1, 2, 3, 4])
        Pros:
            - Applicable to other recording setups (e.g. 'SingleElectrode', range(1, 33) for 32 single electrode recording sites on a linear array)
        Cons:
            - More variables to store, and we don't use other kinds of recording setups now.
      * Have a dict of metadata entries store the tetrode numbers
        Something like:
              experiment.metadata={'electrodeName':  'Tetrode',
                                   'electrodeNums': [1, 2, 3, 4, 5, 6, 7, 8],
                                   'location':       'cortex'}
        Pros:
            - Flexible, can add any metadata that you want about the experiment and can have a set of defaults per animal
        Cons:
            - Need to have the right key names to be able to use the values in scripts later

* Should sessions convert the and date into the ephys session folder and store that?
  Also convert the behav suffix and paradigm into the behav filename?

  Pros:
      The relevant information for clustering and plotting reports will be easy to add
      to a pandas dataframe because we can do vars(session) and this returns a dict, 
      which we can add to a pandas dataframe directly. Later, we can simply use this 
      column instead of having to get multiple columns and create the correct 
  Cons:
      This is redundant if we are also storing the date, timestamp, paradigm, etc. 

---

class InfoRecording(object):
     InfoRecordings is a container of experiments.
     One per subject
     Attributes:
         subject (str): The name of the subject
         experiments (list): A list of all the experiments conducted with this subject
     Methods:
         add_experiment: Add a new experiment for this subject



'''



class Experiment(object):
     '''
     #TODO: default tetrodes, sites and sessions can redefine them though
     Experiment is a container of sites.
     One per day.
     Attributes:
         subject(str): Name of the subject
         date (str): The date the experiment was conducted
         sites (list): A list of all recording sites for this experiment
     Methods:
         new_site(depth): Add a new site when you move the electrodes to a new depth
         add_session(timestamp, behavsuffix, sessiontype, paradigm): Add a recording session to the current site
     TODO: Fail gracefully if the experimenter tries to add sessions without adding a site first
     '''
     def __init__(self, subject, date, brainarea, info=''):
          self.subject=subject
          self.date=date
          self.brainarea=brainarea
          self.info=info
          self.sites=[]
          self.tetrodes = [1,2,3,4,5,6,7,8]
     def add_site(self, depth, tetrodes = None):
          #TODO: default tetrode are self.tetrodes, can redefine per site if needed
          if not tetrodes:
              tetrodes = self.tetrodes
          site=Site(self.subject, self.date, self.brainarea, self.info, depth, tetrodes)
          self.sites.append(site)
          return site
     def add_session(self, timestamp, behavsuffix, sessiontype, paradigm, date=None):
          '''
          Add a session to the most recent site
          '''
          activeSite = self.sites[-1] #Use the most recent site for this experiment
          session = activeSite.add_session(timestamp,
                                           behavsuffix,
                                           sessiontype,
                                           paradigm,
                                           date)
          return session
     def pretty_print(self, sites=True, sessions=False):
          message = []
          message.append('Experiment on {} in {}\n'.format(self.date, self.brainarea))
          if sites:
               for indSite, site in enumerate(self.sites):
                    message.append('    [{}]: {}'.format(indSite, site.pretty_print(sessions=sessions)))
          return ''.join(message)

class Site(object):
     '''
     #TODO: Attribute for reference (does not inherit from top)
     #TODO: reference (example 'T1ch1' or 'GND')
     #NOTE: Channels from 1 (not 0) because this is the way it is in openephys GUI
     #TODO: Explicitly define ref if it is ground
     #TODO: Force ref definition when creating a new site
     Site is a container of sessions.
     One per group of sessions which contain the same neurons and should be clustered together
     Attributes:
         subject(str): Name of the subject
         date (str): The date the experiment was conducted
         depth (int): The depth in microns at which the sessions were recorded
         sessions (list): A list of all the sessions recorded at this site
     '''
     def __init__(self, subject, date, brainarea, info, depth, tetrodes):
          self.subject=subject
          self.date=date
          self.brainarea=brainarea
          self.info=info
          self.depth=depth
          self.tetrodes = tetrodes
          self.sessions=[]
     def add_session(self, timestamp, behavsuffix, sessiontype, paradigm, date=None):
          if not date:
               date=self.date
          session = Session(self.subject,
                            date,
                            self.brainarea,
                            self.info,
                            self.depth,
                            self.tetrodes,
                            timestamp,
                            behavsuffix,
                            sessiontype,
                            paradigm)
          self.sessions.append(session)
          return session
     def session_ephys_dirs(self):
          dirs = [session.ephys_dir() for session in self.sessions]
          return dirs
     def session_behav_filenames(self):
          fns = [session.behav_filename() for session in self.sessions]
          return fns
     def session_types(self):
          types=[session.sessiontype for session in self.sessions]
          return types
     def cluster_info(self):
          infoDict = {
               'subject':self.subject,
               'date':self.date,
               'brainarea': self.brainarea,
               'info': self.info,
               'depth':self.depth,
               'ephys':self.session_ephys_dirs(),
               'behavior':self.session_behav_filenames(),
               'sessiontype':self.session_types()
          }
          return infoDict

     def pretty_print(self, sessions=False):
          message=[]
          message.append('Site at {}um with {} sessions\n'.format(self.depth, len(self.sessions)))
          if sessions:
               for session in self.sessions:
                    message.append('        {}\n'.format(session.pretty_print()))
          return ''.join(message)

class Session(object):
     '''
     Session is a single recorded ephys file and the associated behavior file.
     Attributes:
         subject(str): Name of the subject
         date (str): The date the experiment was conducted
         depth (int): The depth in microns at which the sessions were recorded
         timestamp (str): The timestamp used by openEphys GUI to name the session
         behavsuffix (str): The suffix of the behavior file
         sessiontype (str): A string describing what kind of session this is.
         paradigm (str): The name of the paradigm used to collect the session
     '''
     def __init__(self, subject, date, brainarea, info, depth, tetrodes, timestamp, behavsuffix, sessiontype, paradigm):
          self.subject=subject
          self.date=date
          self.depth=depth
          self.tetrodes=tetrodes
          self.timestamp=timestamp
          self.behavsuffix=behavsuffix
          self.sessiontype=sessiontype
          self.paradigm=paradigm
     def ephys_dir(self):
          path = os.path.join('{}_{}'.format(self.date, self.timestamp))
          return path
     def behav_filename(self):
          fn=None
          if self.behavsuffix:
               #TODO: check if date is a module, don't use that var name
               date = ''.join(self.date.split('-'))
               fn = '{}_{}_{}{}.h5'.format(self.subject,
                                        self.paradigm,
                                        date,
                                        self.behavsuffix)
          return fn
     def pretty_print(self):
          return "{}: {}".format(self.timestamp, self.sessiontype)

def save_dataframe_as_HDF5(path, dataframe):
    '''
    Saves a dataframe to HDF5 format.

    Args:
        path (str): /path/to/file.h5
        dataframe (pandas.DataFrame): dataframe object
    '''
    dataframe.to_hdf(path, 'dataframe')

def load_dataframe_from_HDF5(path, **kwargs):
    '''
    See pandas.read_hdf docs for useful kwargs (loading only certain rows, cols, etc)
    Args:
        path (str): /path/to/file.h5
    '''
    dataframe = pd.read_hdf(path, key='dataframe', **kwargs)
    return dataframe

def generate_cell_database(inforecPath):
    '''
    Iterates over all sites in an inforec and builds a cell database
    Args:
        inforecPath (str): absolute path to the inforec file
    Returns:
        db (pandas.DataFrame): the cell database
    '''

    inforec = imp.load_source('module.name', inforecPath)
    db = pd.DataFrame()
    for indExperiment, experiment in enumerate(inforec.experiments):
        for indSite, site in enumerate(experiment.sites):
            clusterDir = 'multisession_exp{}site{}'.format(indExperiment, indSite)
            for tetrode in site.tetrodes:
                clusterStatsFn = 'Tetrode{}_stats.npz'.format(tetrode)
                clusterStatsFullPath = os.path.join(settings.EPHYS_PATH,
                                                    inforec.subject,
                                                    clusterDir,
                                                    clusterStatsFn)
                if not os.path.isfile(clusterStatsFullPath):
                    raise NotClusteredYetError("Experiment {} Site {} Tetrode {} is not clustered".format(indExperiment, indSite, tetrode))
                clusterStats = np.load(clusterStatsFullPath)

                for indc, cluster in enumerate(clusterStats['clusters']):
                    clusterDict = {'tetrode':tetrode,
                                   'cluster':cluster,
                                   'indExperiment':indExperiment,
                                   'indSite':indSite,
                                   'inforecPath':inforecPath,
                                   'nSpikes':clusterStats['nSpikes'][indc],
                                   'isiViolations':clusterStats['isiViolations'][indc]}
                    clusterDict.update(site.cluster_info())
                    db = db.append(clusterDict, ignore_index=True)
    return db

class NotClusteredYetError(Exception):
    pass

if __name__=="__main__":
     CASE=0
     if CASE==0: #Verify that saving to and loading from h5 preserves cell dtype
        d = {'a': [1, 2], 'b': [['a', 'b'], ['b', 'c']]}
        df = pd.DataFrame(d)
        save_dataframe_as_HDF5('/tmp/df_test.h5', df)
        df2 = load_dataframe_from_HDF5('/tmp/df_test.h5')
        print type(df2['b'][0])

# '''

# class InfoRecording(object):
#      '''
#      DEPRECATED: Use Experiment objects instead
#      InfoRecordings is a container of experiments. One per subject.
#      '''
#      def __init__(self, subject):
#           '''
#           Args:
#               subject (str): subject's name
#           '''
#           self.subject = subject
#           self.experiments = []
#      def add_experiment(self, date):
#           '''
#           Adds an Experiment object to the list.
#           Args:
#               date (str): date in format YYYY-MM-DD
#           '''
#           experiment=Experiment(self.subject,
#                                 date)
#           self.experiments.append(experiment)
# 	  return experiment
#      def add_site(self, depth, tetrodes = [1,2,3,4,5,6,7,8]):
#           '''
#           Add a site to the last experiment
#           '''
#           activeExperiment = self.experiments[-1]
#           site = activeExperiment.add_site(depth, tetrodes)
#           return site
#      def add_session(self, timestamp, behavsuffix, sessiontype, paradigm):
#           activeExperiment = self.experiments[-1] #Use the most recent experiment
#           session = activeExperiment.add_session(timestamp,
#                                  behavsuffix,
#                                  sessiontype,
#                                  paradigm)
#           return session
#      def __str__(self):
#           message = []
#           message.append('Subject: {}'.format(self.subject))
#           message.append('{} Experiments:'.format(len(self.experiments)))
#           for indExp, experiment in enumerate(self.experiments):
#                date = experiment.date
#                numSites = len(experiment.sites)
#                numSessions = 0
#                #count total number of sessions
#                for site in experiment.sites:
#                     for session in site.sessions:
#                          numSessions += 1
#                message.append('Experiment {} on {}: {} Sites, {} Total sessions'.format(indExp,
#                                                                                         date,
#                                                                                         numSites,
#                                                                                         numSessions))
#           return '\n'.join(message)
# '''
