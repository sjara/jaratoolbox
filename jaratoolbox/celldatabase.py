"""
Objects and methods for keeping information about isolated cells.

Cell database version history:
- v5.0 saves arrays of lists of string flatten as JSON. This make loading a
  database about 10 times faster.
- v4.0 uses name egroup instead of tetrode (so it works with any probe) and 
  changed depth to pdepth (since this is the depth of the probe, not the cell)
  This version should work with both NeuroNexus and Neuropixels.
- v3.0 we now save the index of the dataframe, so we can keep track of the
  cells as we save subsets of the database.
- v2.0 is the first version of celldb that has an attribute saved to the
  h5 file that specifies what version of jaratoolbox.celldatabase was used to
  save it as 'celldb_version'.
- v1.0 was the first iteration of celldatabase.save_hdf used in python 2.7.
  (For example: 2018acsup project) The above versions do not have a saved
  attribute in the file indicating what the version of the saved db is.
- v0.0 was when we were still saving using pandas (e.g., for 2018thstr project).
"""

import numpy as np
import os
import sys
from jaratoolbox import settings
import pandas as pd
import importlib
import h5py
import ast  # To parse string representing a list
import json # To save lists of strings
import pickle # To save lists of strings

CELLDB_VERSION = '5.0'

def pandas_version_at_least(newVersion):
    """
    Return True is pandas version is equal or higher than newVersion.
    Args:
        newVersion (str): such as '1.4'
    """
    pandasVersion = pd.__version__
    pandasVersionFloat = float('.'.join(pandasVersion.split('.')[:2]))
    newVersionFloat = float('.'.join(newVersion.split('.')[:2]))
    isEqualOrHigher = pandasVersionFloat >= newVersionFloat
    return isEqualOrHigher

class Experiment():
    """
    Experiment is a container of sites.
    """
    # TODO: Fail gracefully if the experimenter tries to add sessions without adding a site first
    # TODO: Should the info attr be a dictionary?
    def __init__(self, subject, date, brainArea, recordingTrack='', egroups=None, probe=None, info=''):
        """
        Args:
            subject(str): Name of the subject.
            date (str): The date the experiment was conducted.
            brainArea (str): The area of the brain where the recording was conducted.
            recordingTrack (str): The location and dye used for a penetration. Ex: anteriorDiD.
            egroups (list): Default list of electrode groups (e.g., tetrodes) clustered separately.
            probe (str): Type of probe and probe ID. Ex: NPv1-1234.
            info (str): Additional information about the experiment.
        """
        self.subject = subject
        self.date = date
        self.brainArea = brainArea
        self.recordingTrack = recordingTrack
        self.info = info
        self.sites = []
        self.maxDepth = None
        self.probe = probe
        if egroups is None:
            if self.probe == 'A4x2-tet':
                self.egroups = [1, 2, 3, 4, 5, 6, 7, 8]
            elif self.probe[:2] == 'NP':
                self.egroups = [0]
            else:
                self.egroups = [1, 2, 3, 4, 5, 6, 7, 8]  # Assume tetrodes
        else:
            self.egroups = egroups
        # self.probeGeometryFile = '/tmp/A4x2tet_5mm_150_200_121.py'
        #TODO: Implement something for probe geometry long-term storage?
    
    def add_site(self, pdepth, date=None, egroups=None):
        """
        Append a new Site object to the list of sites.
        Args:
            pdepth (int): The depth of the tip of the electrode array for this site
            date (str): The date of recording for this site
            egroups (list): Groups of electrodes to analyze for this site
        Returns:
            site (celldatabase.Site object): Handle to site object
        """
        if date is None:
            date = self.date
        if egroups is None:
            egroups = self.egroups
        site = Site(self.subject, date, self.brainArea, self.recordingTrack,
                    egroups, self.probe, self.info, pdepth)
        self.sites.append(site)
        return site
    
    def add_session(self, timestamp, behavsuffix, sessiontype, paradigm, date=None):
        """
        Add a new Session object to the list of sessions belonging to the most recent Site
        Args:
            timestamp (str): The timestamp used by openEphys GUI to name the session
            behavsuffix (str): The suffix of the behavior file
            sessiontype (str): A string describing what kind of session this is.
            paradigm (str): The name of the paradigm used to collect the session
            date (str): The recording date. Only needed if the date of the session is different
                        from the date of the Experiment/Site (if you record past midnight)
        """
        try:
            activeSite = self.sites[-1]  # Use the most recent site for this experiment
        except IndexError:
            raise IndexError('There are no sites to add sessions to')
        session = activeSite.add_session(timestamp,
                                         behavsuffix,
                                         sessiontype,
                                         paradigm,
                                         date)
        return session

    def __str__(self):
        return self.pretty_print()
    
    def pretty_print(self, sites=True, sessions=False):
        """
        Print a string with date, brainArea, and optional list of sites/sessions by index
        Args:
            sites (bool): Whether to list all sites in the experiment by index
            sessions (bool): Whether to list all sessions in each site by index
        Returns:
            message (str): A formatted string with the message to print
        """
        message = []
        message.append('Experiment on {} in {}\n'.format(self.date, self.brainArea))
        if sites:
            for indSite, site in enumerate(self.sites):
                # Append the ouput of the pretty_print() func for each site
                message.append('    [{}]: {}'.format(indSite,
                                                     site.pretty_print(sessions=sessions)))
        return ''.join(message)
    
    def site_comment(self, message):
        """
        Add a comment string to the list of comments for the most recent Site.
        This method allows commenting on Site objects without returning handles to them.
        Args:
            message (str): The message string to append to the list of comments for the Site
        """

        activeSite = self.sites[-1]  # Use the most recent site for this experiment
        activeSite.comment(message)
        
    def session_comment(self, message):
        """
        Add a comment string to the list of comments for the most recent Session.
        This method allows commenting on Session objects without returning handles to them.
        Args:
            message (str): The message string to append to the list of comments for the Session
        """
        activeSite = self.sites[-1]  # Use the most recent Site for this Experiment
        activeSession = activeSite.sessions[-1]  # Use the most recent Session for this Site
        activeSession.comment(message)


class Site():
    """
    Site is a container of sessions.
    Spike sorting (clustering) should be done together for all sessions in a site.
    """
    def __init__(self, subject, date, brainArea, recordingTrack, egroups, probe, info, pdepth):
        """
        Args:
            subject(str): Name of the subject.
            date (str): The date the experiment was conducted.
            brainArea (str): The area of the brain where the recording was conducted.
            recordingTrack (str): The location and dye used for a penetration. Ex: anteriorDiD.
            egroups (list): Default list of electrode groups (e.g., tetrodes) clustered separately.
            probe (str): Type of probe and probe ID. Ex: NPv1-1234.
            info (str): Additional information about the experiment.
            pdepth (int): The depth of the probe (in microns) at which the sessions were recorded
        """
        self.subject = subject
        self.date = date
        self.brainArea = brainArea
        self.recordingTrack = recordingTrack
        self.egroups = egroups
        self.probe = probe
        self.info = info
        self.pdepth = pdepth
        self.sessions = []
        self.comments = []
        if probe=='A4x2-tet':
            self.clusterFolder = 'multisession_{}_{}um'.format(self.date, self.pdepth)
        else:
            self.clusterFolder = 'multisession_{}_{}um_processed'.format(self.date, self.pdepth)
        
    def remove_egroups(self, egroupsToRemove):
        """
        Remove egroups from a site's list of egroups
        """
        if not isinstance(egroupsToRemove, list):
            egroupsToRemove = [egroupsToRemove]
        for egroup in egroupsToRemove:
            self.egroups.remove(egroup)
            
    def add_session(self, timestamp, behavsuffix, sessiontype, paradigm, date=None):
        """
        Add a session to the list of sessions.
        Args:
            timestamp (str): The timestamp used by openEphys GUI to name the session
            behavsuffix (str): The suffix of the behavior file
            sessiontype (str): A string describing what kind of session this is.
            paradigm (str): The name of the paradigm used to collect the session
            date (str): The recording date. Only needed if the date of the session is different
                        from the date of the Experiment/Site (if you record past midnight)
        """
        if date is None:
            date = self.date
        session = Session(self.subject, date, self.brainArea, self.recordingTrack,
                          self.egroups, self.probe, self.info, self.pdepth,
                          timestamp, behavsuffix, sessiontype, paradigm)
        self.sessions.append(session)
        return session
    
    def session_ephys_dirs(self):
        """
        Returns a list of the ephys directories for all sessions recorded at this site.
        Returns:
            dirs (list): List of ephys directories for each session in self.sessions
        """
        dirs = [session.ephys_dir() for session in self.sessions]
        return dirs
    
    def get_info(self):
        """
        Returns a dictionary with the information needed to identify clusters that
        come from this site.

        Returns:
            infoDict (dict): dictionary that defines clusters that come from this site.
        """
        infoDict = {
            'subject': self.subject,
            'date': self.date,
            'brainArea': self.brainArea,
            'recordingTrack': self.recordingTrack,
            #'egroups': self.egroups,  # Ignore list of egroups
            'probe': self.probe,
            'info': self.info,
            'pdepth': self.pdepth,
            'ephysTime': [session.timestamp for session in self.sessions],
            'paradigm': [session.paradigm for session in self.sessions],
            'behavSuffix': [session.behavsuffix for session in self.sessions],
            'sessionType': [session.sessiontype for session in self.sessions]
        }
        return infoDict

    def get_session_index(self, sessiontype):
        """
        Returns the index of the last sessions of a particular type.
        """
        sessionsDict = {oneSession.sessiontype:ind for ind,oneSession in enumerate(self.sessions)}
        return sessionsDict[sessiontype]

    def __str__(self):
        return self.pretty_print(sessions=True)
        
    def pretty_print(self, sessions=False):
        """
        Print a string with depth, number of sessions, and optional list of sessions by index.

        Args:
            sessions (bool): Whether to list all sessions by index
        Returns:
            message (str): A formatted string with the message to print
        """
        message = []
        message.append('Site at {}um with {} sessions\n'.format(self.pdepth, len(self.sessions)))
        if sessions:
            for session in self.sessions:
                message.append('        {}\n'.format(session.pretty_print()))
        return ''.join(message)
    
    def comment(self, message):
        """
        Add a comment to self.comments
        Args:
            message (str): The message string to append to self.comments
        """
        self.comments.append(message)


class Session():
    """
    Session is a single recorded ephys file and the associated behavior file.
    """
    def __init__(self, subject, date, brainArea, recordingTrack, egroups, probe, info, pdepth, 
                 timestamp, behavsuffix, sessiontype, paradigm, comments=[]):
        """
        Args:
            subject(str): Name of the subject.
            date (str): The date the experiment was conducted.
            brainArea (str): The area of the brain where the recording was conducted.
            recordingTrack (str): The location and dye used for a penetration. Ex: anteriorDiD.
            egroups (list): Default list of electrode groups (e.g., tetrodes) clustered separately.
            probe (str): Type of probe and probe ID. Ex: NPv1-1234.
            info (str): Additional information about the experiment.
            pdepth (int): The depth of the probe (in microns) at which the sessions were recorded
            timestamp (str): The timestamp used by openEphys GUI to name the session
            behavsuffix (str): The suffix of the behavior file
            sessiontype (str): A string describing what kind of session this is.
            paradigm (str): The name of the paradigm used to collect the session
            comments (list): list of strings, comments about the session
        """
        self.subject = subject
        self.date = date
        self.pdepth = pdepth
        self.egroups = egroups
        self.timestamp = timestamp
        self.behavsuffix = behavsuffix
        self.sessiontype = sessiontype
        self.paradigm = paradigm
        self.comments = comments
        
    def ephys_dir(self):
        """
        Join the date and the session timestamp to generate the actual directory used store the ephys data
        Returns:
          path (str): The full folder name used by OpenEphys to save the ephys data
        DEPRECATED (2017-10-30): We are going to return just the timestamp, not with the date attached
        """
        path = os.path.join('{}_{}'.format(self.date, self.timestamp))
        return path
    
    def pretty_print(self):
        """
        Print a string containing the timestamp and sessiontype string
        """
        return "{}: {}".format(self.timestamp, self.sessiontype)
    
    def __str__(self):
        """
        Use self.pretty_print() if someone tries to print a session
        """
        return self.pretty_print()
    
    def comment(self, message):
        """
        Add a message to the list of comments
        Args:
          message (str): The message string to append
        """
        self.comments.append(message)


def make_db_neuronexus_tetrodes(experiment):
    """
    Create a database of cells given an Experiment object associated with
    recordings using NeuroNexus probes with tetrodes.

    Args:
        experiment (celldatabase.Experiment): object defining experiment and sites.
    Returns:
        celldb (pandas.DataFrame): the cell database
    """
    egroupStatsFormat = 'Tetrode{}_stats.npz'
    celldb = pd.DataFrame()
    for indSite, site in enumerate(experiment.sites):
        # -- Add site info to database
        siteInfoDict = site.get_info()
        for egroup in site.egroups:
            tempdb = pd.DataFrame()
            clusterStatsFn = egroupStatsFormat.format(egroup)
            clusterStatsFullPath = os.path.join(settings.EPHYS_PATH,
                                                experiment.subject,
                                                site.clusterFolder,
                                                clusterStatsFn)
            if not os.path.isfile(clusterStatsFullPath):
                raise NotClusteredError(f'Experiment {site.subject} {site.date} ' +
                                        f'T{egroup} {site.pdepth}um is not clustered.\n' +
                                        f'No file {clusterStatsFullPath}')
            clusterStats = np.load(clusterStatsFullPath)
            nClusters, nTimePoints = clusterStats['clusterSpikeShape'].shape
            dtypeSpikeShape = clusterStats['clusterSpikeShape'].dtype
            tempdb['probe'] = np.tile(experiment.probe, nClusters)
            tempdb['maxDepth'] = np.tile(experiment.maxDepth, nClusters)
            tempdb['egroup'] = np.tile(egroup, nClusters)
            tempdb['cluster'] = clusterStats['clusters']
            tempdb['nSpikes'] = clusterStats['nSpikes']
            tempdb['isiViolations'] = clusterStats['isiViolations']
            tempdb['spikeShape'] = list(clusterStats['clusterSpikeShape'])
            tempdb['spikeShapeSD'] = list(clusterStats['clusterSpikeSD'])
            tempdb['spikePeakAmplitudes'] = list(clusterStats['clusterPeakAmplitudes'])
            tempdb['spikePeakTimes'] = list(clusterStats['clusterPeakTimes'])
            mainPeak = clusterStats['clusterPeakAmplitudes'][:,1]
            avgSD = clusterStats['clusterSpikeSD'].mean(axis=1)
            clustersWithOneSpike = clusterStats['nSpikes']==1
            # NOTE: We make spikeQuality zero if nSpikes is only 1
            mainPeak[clustersWithOneSpike] = 0  # Zero out peak value if nSpikes==1
            avgSD[clustersWithOneSpike] = 1     # Make value non-zero if nSpikes==1
            tempdb['spikeShapeQuality'] = abs(mainPeak/avgSD)
            for key, val in siteInfoDict.items():
                tempdb[key] = len(tempdb)*[val]
            #celldb = pd.concat((celldb, tempdb), axis=0, ignore_index=True)
            celldb = celldb.append(tempdb, ignore_index=True)
    return celldb


def OLD_make_db_neuropixels_v1(experiment, singleSession=None):
    """
    Create a database of cells given an Experiment object associated with
    recordings using Neuropixels probes version 1.

    Args:
        experiment (celldatabase.Experiment): object defining experiment and sites.
        singleSession (dict): specifies a single session to process, with format:
            {'date': YYYY-MM-DD, 'pdepth': int, 'sessiontype': str}
    Returns:
        celldb (pandas.DataFrame): the cell database
    """
    singleSuffix='_processed_single'
    celldb = pd.DataFrame()
    for indSite, site in enumerate(experiment.sites):
        for indEletrodeGroup, egroup in enumerate(experiment.egroups):
            # FIXME: how to define the clustered data for different egroups?
            if singleSession is None:
                clusterFolder = os.path.join(settings.EPHYS_NEUROPIX_PATH,
                                             experiment.subject, site.clusterFolder)
            else:
                if site.date==singleSession['date'] and site.pdepth==singleSession['pdepth']:
                    sessionIndex = site.get_session_index(singleSession['sessiontype'])
                    ephysTime = site.sessions[sessionIndex].timestamp
                    oneSessionFolder = f'{site.date}_{ephysTime}' + singleSuffix
                    clusterFolder = os.path.join(settings.EPHYS_NEUROPIX_PATH,
                                                 experiment.subject, oneSessionFolder)
                else:
                    break
            spikeClustersFile = os.path.join(clusterFolder, 'spike_clusters.npy')
            clusterGroupFile = os.path.join(clusterFolder, 'cluster_group.tsv')
            spikeClusters = np.load(spikeClustersFile).squeeze()
            clusterGroup = pd.read_csv(clusterGroupFile, sep='\t')

            tempdb = clusterGroup.query("KSLabel=='good'").reset_index(drop=True)
            templates = np.load(os.path.join(clusterFolder,'templates.npy'))
            (nOrigClusters, nTimePoints, nChannels) = templates.shape
            nGoodClusters = len(tempdb)

            # -- Get nspikes, best channel, spikeshape, etc --
            spikeShapes = np.empty([nGoodClusters, nTimePoints], dtype=templates.dtype)
            nSpikes = np.empty(nGoodClusters, dtype=int)
            bestChannel = np.empty(nGoodClusters, dtype=int)
            for indc, clusterID in enumerate(tempdb['cluster_id']):
                oneTemplate = templates[clusterID]
                indMax = np.argmax(np.abs(oneTemplate))
                (rowMax, colMax) = np.unravel_index(indMax, oneTemplate.shape)
                spikeShapes[indc,:] = oneTemplate[:,colMax]
                bestChannel[indc] = colMax
                nSpikes[indc] = np.count_nonzero(spikeClusters==clusterID)
            # -- Add site info to database
            siteInfoDict = site.get_info()
            for key, val in siteInfoDict.items():
                tempdb[key] = len(tempdb)*[val]
            # -- Add cluster-specific info --
            tempdb['nSpikes'] = nSpikes
            tempdb['bestChannel'] = bestChannel
            tempdb['maxDepth'] = experiment.maxDepth
            tempdb['egroup'] = egroup
            #tempdb['probe'] = np.tile(experiment.probe, nClusters)
            tempdb['spikeShape'] = list(spikeShapes)
            tempdb.rename(columns={'cluster_id': 'cluster'}, inplace=True)
            celldb = celldb.append(tempdb, ignore_index=True)
    return celldb


def make_db_neuropixels_v1(experiment, singleSession=None, onlyGood=True, minimal=False,
                           trimSpikeShapes=True, ignoreMissing=False):
    """
    Create a database of cells given an Experiment object associated with
    recordings using Neuropixels probes version 1.
    This function reads data from multisession folders defined by site.clusterFolder,
    usually named something like "multisession_2021-11-19_3320um_processed".

    Args:
        experiment (celldatabase.Experiment): object defining experiment and sites.
        singleSession (dict): specifies a single session to process, with format:
            {'date': YYYY-MM-DD, 'pdepth': int, 'sessiontype': str}
        onlyGood (bool): include only clusters labeled "good" by Kilosort/Phy.
        trimSpikeShapes (bool): remove padding (zero) elements from spike shapes.
        minimal (bool): create a minimal database that does not include spike shapes.
        ignoreMissing (bool): do not raise an error if the data for a site is missing.
    Returns:
        celldb (pandas.DataFrame): the cell database
    """
    #singleSuffix='_processed_single'
    singleSuffix='_processed_multi'
    celldb = pd.DataFrame()
    for indSite, site in enumerate(experiment.sites):
        for indEletrodeGroup, egroup in enumerate(experiment.egroups):
            # FIXME: how to define the clustered data for different egroups?
            if singleSession is None:
                clusterFolder = os.path.join(settings.EPHYS_NEUROPIX_PATH,
                                             experiment.subject, site.clusterFolder)
                if not os.path.isdir(clusterFolder):
                    print(f'WARNING: Experiment {site.subject} {site.date} ' +
                          f'{site.pdepth}um is not spike-sorted.')
                    if ignoreMissing:
                        continue
            else:
                if site.date==singleSession['date'] and site.pdepth==singleSession['pdepth']:
                    sessionIndex = site.get_session_index(singleSession['sessiontype'])
                    ephysTime = site.sessions[sessionIndex].timestamp
                    oneSessionFolder = f'{site.date}_{ephysTime}' + singleSuffix
                    clusterFolder = os.path.join(settings.EPHYS_NEUROPIX_PATH,
                                                 experiment.subject, oneSessionFolder)
                else:
                    break
            clusterGroup = pd.read_csv(os.path.join(clusterFolder, 'cluster_group.tsv'), sep='\t')
            # -- Force the names of columns (since Kilosort and Phy use different names)--
            clusterGroup.columns=['cluster', 'cluster_label']
            if not minimal:
                bestChannel = np.load(os.path.join(clusterFolder, 'cluster_bestChannel.npy'))
                spikeShapesFile = os.path.join(clusterFolder, 'cluster_waveform.npy')
                if not os.path.isfile(spikeShapesFile):
                    spikeShapesFile = os.path.join(clusterFolder, 'spikes_shapes.npy') # pre 2024-07-30
                spikeShapes = np.load(os.path.join(clusterFolder, spikeShapesFile))
                if trimSpikeShapes:
                    firstValidSample = np.flatnonzero(np.nansum(spikeShapes, axis=0))[0]
                    spikeShapes = spikeShapes[:, firstValidSample:]
            if onlyGood:
                tempdb = clusterGroup.query("cluster_label=='good'").reset_index(drop=True)
            else:
                tempdb = clusterGroup
            # -- Add site info to database
            siteInfoDict = site.get_info()
            for key, val in siteInfoDict.items():
                tempdb[key] = len(tempdb)*[val]
            # -- Add cluster-specific info --
            tempdb['maxDepth'] = experiment.maxDepth
            tempdb['egroup'] = egroup
            if not minimal:
                tempdb['bestChannel'] = bestChannel[tempdb.cluster]
                tempdb['spikeShape'] = list(spikeShapes[tempdb.cluster,:])
            #celldb = celldb.append(tempdb, ignore_index=True)
            celldb = pd.concat((celldb, tempdb), axis=0, ignore_index=True)
    return celldb


def generate_cell_database(inforecFile, singleSession=None, onlyGood=True, minimal=False,
                           ignoreMissing=False):
    """
    Iterates over all experiments in an inforec and builds a cell database.
    This function requires that the data is already clustered.

    Args:
        inforecFile (str): full path to the inforec file
        singleSession (dict): specifies a single session to process, with format:
            {'date': YYYY-MM-DD, 'pdepth': int, 'sessiontype': str}
        onlyGood (bool): include only clusters labeled "good" by Kilosort/Phy.
        ignoreMissing (bool): do not raise an error if the data for a site is missing.
    Returns:
        celldb (pandas.DataFrame): the cell database
    """
    inforec = read_inforec(inforecFile)
    
    print('\nGenerating database for {}'.format(inforecFile))
    celldb = pd.DataFrame() #dtype=object
    for indExperiment, experiment in enumerate(inforec.experiments):
        if experiment.maxDepth is None:
            print(f'Attribute maxDepth not set for experiment with subject '+
                  f'{experiment.subject} on {experiment.date}')
            raise AttributeError('You must set maxDepth for each experiment.')
        print(f'Adding experiment from {experiment.subject} on {experiment.date}')
        if (experiment.probe == 'A4x2-tet'):
            extraRows = make_db_neuronexus_tetrodes(experiment)
            if onlyGood and len(extraRows)>0:
                isi = 0.05
                quality = 2
                extraRows = extraRows[(extraRows['isiViolations'] < isi) & \
                                      (extraRows['spikeShapeQuality'] > quality)]
            celldb = pd.concat((celldb, extraRows), ignore_index=False)
            # FIXME: It is really appropriate to ignore_index?
            #        The reason is to preserve index of clusters when removing bad cells
        elif experiment.probe[:2] == 'NP':
            extraRows = make_db_neuropixels_v1(experiment, singleSession, onlyGood,
                                               minimal=minimal, ignoreMissing=ignoreMissing)
            celldb = pd.concat((celldb, extraRows), ignore_index=True)
        elif experiment.probe is None:
            raise TypeError(f'Inforec problem: An experiment of {experiment.subject} ' +
                            'did not specify the probe.')
    return celldb


def read_inforec(inforecFile):
    spec = importlib.util.spec_from_file_location('inforec_module', inforecFile)
    inforec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inforec)
    return inforec


def generate_cell_database_from_subjects(subjects, onlyGood=True):
    """
    This function generates a database for multiple subjects.

    Args:
        subjects (list): List of strings containing names of subjects

    Returns:
        fulldb (pandas.DataFrame): Database with cells from all subjects.
    """
    fulldb = pd.DataFrame()
    for subject in subjects:
        inforec = os.path.join(settings.INFOREC_PATH, '{0}_inforec.py'.format(subject))
        onedb = generate_cell_database(inforec, onlyGood=onlyGood)
        fulldb = fulldb.append(onedb, ignore_index=True)
    return fulldb


def find_cell(database, subject, date, pdepth, egroup, cluster):
    """
    Find a cell in the database.
    Returns (index, pandasSeries)
    """
    cell = database.query('subject==@subject and date==@date and pdepth==@pdepth and ' +
                          'egroup==@egroup and cluster==@cluster')
    if len(cell) > 1:
        raise AssertionError('This information somehow defines more than 1 cell in the database.')
    elif len(cell) == 0:
        raise AssertionError('No cells fit these search criteria.')
    elif len(cell) == 1:
        # Return the index and the series: once you convert to series the index is lost
        return cell.index[0], cell.iloc[0]


def get_cell_info(database, index):
    """
    The index is THE index from the original pandas dataframe. It is not the positional index.
    """
    cell = database.loc[index]
    cellDict = {'subject': cell['subject'],
                'date': cell['date'],
                'pdepth': cell['pdepth'],
                'egroup': cell['egroup'],
                'cluster': cell['cluster']}
    return cellDict


def save_hdf(dframe, filename, verbose=True):
    """
    Save database as HDF5, in a cleaner format than pandas.DataFrame.to_hdf()
    Use celldatabase.load_hdf() to load these files.

    Args:
        dframe: pandas dataframe containing database.
        filename: full path to output file.

    Note: the name 'index' is reserved to store the cell index, so your dataframe
          should not have a column named 'index'.
    """
    h5file = h5py.File(filename, 'w')
    #string_dt = h5py.special_dtype(vlen=str)  # OLD
    listOfStr_dt =  h5py.special_dtype(vlen=str) #h5py.string_dtype(encoding='utf-8', length=None) 
    try:
        dbGroup = h5file.require_group('/')  # database
        dbGroup.attrs['celldb_version'] = CELLDB_VERSION
        # -- Save index --
        dset = dbGroup.create_dataset('index', data=dframe.index)
        # -- Save each column --
        for onecol in dframe.columns:
            onevalue = dframe.iloc[0][onecol]
            if isinstance(onevalue, np.ndarray):
                arraydata = np.vstack(dframe[onecol].values)
                dset = dbGroup.create_dataset(onecol, data=arraydata)
            elif isinstance(onevalue, int) or \
                isinstance(onevalue, np.int64) or \
                isinstance(onevalue, np.int32) or \
                isinstance(onevalue, float) or \
                isinstance(onevalue, bool) or \
                    isinstance(onevalue, np.bool_):
                arraydata = dframe[onecol].values
                dset = dbGroup.create_dataset(onecol, data=arraydata)
            elif isinstance(onevalue, str):
                #arraydata = dframe[onecol].values.astype(string_dt)
                #dset = dbGroup.create_dataset(onecol, data=arraydata, dtype=string_dt)
                arraydata = dframe[onecol].values.astype('S')
                dset = dbGroup.create_dataset(onecol, data=arraydata)
            elif isinstance(onevalue, list):
                # For columns like: behavSuffix, ephysTime, paradigm, sessionType
                '''
                arraydata = dframe[onecol].values
                dset = dbGroup.create_dataset(onecol, data=arraydata, dtype=listOfStr_dt)
                '''
                arraydata = dframe[onecol].to_json(orient='split')
                dset = dbGroup.create_dataset(onecol, data=arraydata, dtype=listOfStr_dt)
                #dbGroup.attrs[onecol] = np.void(pickle.dumps(arraydata))
                #dset = dbGroup.create_dataset(onecol, data=json.dumps(arraydata), dtype=listOfStr_dt)
            else:
                raise ValueError('Trying to save items of invalid type')
            # dset.attrs['Description'] = onecol
        h5file.close()
        if verbose:
            print(f'Saved {filename}')
    except OSError:
        h5file.close()
        raise


def load_hdf(filename, columns=[], root='/'):
    """
    Load database into a pandas dataframe from an HDF5 file
    saved by celldatabase.save_hdf()

    Args:
        filename: full path to HDF5 file.
        columns: list of columns to load. Default: loads all columns.
                 You need to include 'index' to load the original indices.
        root: the HDF5 group containing the database.
    """
    dbDict = {}
    indexArray = None
    try:
        h5file = h5py.File(filename, 'r')
    except IOError:
        print('{0} does not exist or cannot be opened.'.format(filename))
        raise
    for varname, varvalue in h5file[root].items():
        # If an error occurs regarding malformed strings, it is because we used
        # to save as strings not string_dt in save_hdf()
        # NOTE: It looks liek in Windows int64 is not recognized as int,
        #       so we need to check it here.
        if columns:
            # Check if argument columns is specified and skip variables not listed
            if varname not in columns:
                continue
        if varname=='index':
            indexArray = varvalue[...]
        elif np.issubdtype(varvalue, np.integer) or np.issubdtype(varvalue, np.floating):
            if len(varvalue.shape) == 1:
                dbDict[varname] = varvalue[...]
            else:
                dbDict[varname] = list(varvalue[...])  # If it is an array
        elif varvalue.dtype.kind == 'S':
            dbDict[varname] = varvalue[...].astype(str)
        elif varvalue.dtype == np.object:
            '''
            try:
                #dataAsList = [ast.literal_eval("{}".format(v)) for v in varvalue]
                dataAsList = [ast.literal_eval("{}".format(v)) for v in varvalue]
            except (ValueError, SyntaxError):
                # ValueError: If a list of strings contains a non-string (like None)
                # Passing something like '2019-01-02' above will result in ast.parse not
                # being able to convert it into a string, and it gives a SyntaxError.
                # ast.parse requires it to be passed as "'2019-01-02'" to work.
                dataAsList = [ast.literal_eval('"{}"'.format(v)) for v in varvalue]
            dbDict[varname] = dataAsList
            '''
            if pandas_version_at_least('1.4'):
                dbDict[varname] = pd.read_json(varvalue[()].decode()).data
            else:
                dbDict[varname] = pd.read_json(varvalue[()]).data
        else:
            raise ValueError('Data type {} for variable {} is not recognized '+\
                             'by celldatabase.'.format(varvalue.dtype,varname))
            #print('Warning! Data type "{}" for variable "{}" is not recognized '+\
            #      'by celldatabase.'.format(varvalue.dtype,varname))
    h5file.close()
    dframe = pd.DataFrame(dbDict)
    if indexArray is not None:
        dframe.index = indexArray
    else:
        print('Warning! the database file did not contain an index array. Indices have been reset.')
    return dframe


class NotClusteredError(Exception):
    pass

