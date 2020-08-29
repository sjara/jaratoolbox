#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Objects and methods for keeping information about isolated cells'''

import numpy as np
import os
import sys
from jaratoolbox import settings
import pandas as pd
import imp
import h5py
import ast  # To parse string representing a list

"""
Cell database version history:
Version 0.0 was when we were still saving using pandas. (For example: 2018thstr project).
Version 1.0 was the first iteration of celldatabase.save_hdf used in python 2.7. (For example: 2018acsup project)
The above versions do not have a saved attribute in the file indicating what the version of the saved db is.

Version 2.0 is the first version of celldb that has an attribute saved to the h5 file that specifies what version of
jaratoolbox.celldatabase was used to save it as 'celldb_version' on line 708.
"""
CELLDB_VERSION = '2.0'


class Experiment(object):
    """
    Experiment is a container of sites.
    One per day.
    Attributes:
        subject(str): Name of the subject
        date (str): The date the experiment was conducted
        brainArea (str): The area of the brain where the recording was conducted
        recordingTrack (str): The location and dye used for a penetration. Ex: anteriorDiD
        sites (list): A list of all recording sites for this experiment
        info (str): Extra info about the experiment
        tetrodes (list): Default tetrodes for this experiment
    TODO: Fail gracefully if the experimenter tries to add sessions without adding a site first
    TODO: Should the info attr be a dictionary?
    """
    def __init__(self, subject, date, brainArea, recordingTrack='', info=''):
        self.subject = subject
        self.date = date
        self.brainArea = brainArea
        self.recordingTrack = recordingTrack
        self.info = info
        self.sites = []
        self.tetrodes = [1, 2, 3, 4, 5, 6, 7, 8]
        self.maxDepth = None
        self.shankEnds = None
        # self.probeGeometryFile = '/tmp/A4x2tet_5mm_150_200_121.py' #TODO: Implement something for probe geometry long-term storage?
        
    def add_site(self, depth, date=None, tetrodes=None):
        """
        Append a new Site object to the list of sites.
        Args:
            depth (int): The depth of the tip of the electrode array for this site
            date (str): The date of recording for this site
            tetrodes (list): Tetrodes to analyze for this site
        Returns:
            site (celldatabase.Site object): Handle to site object
        """
        if date is None:
            date = self.date
        if tetrodes is None:
            tetrodes = self.tetrodes
        site = Site(self.subject, date, self.brainArea, self.recordingTrack, self.info, depth, tetrodes)
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


class Site(object):
    """
    Site is a container of sessions.
    One per group of sessions which contain the same neurons and should be clustered together
    Attributes:
        subject(str): Name of the subject
        date (str): The date the experiment was conducted
        brainArea (str): The area of the brain where the recording was conducted
        info (str): Extra info about the experiment
        depth (int): The depth in microns at which the sessions were recorded
        tetrodes (list): Tetrodes for this site
        sessions (list): A list of all the sessions recorded at this site
        comments (list of str): Comments for this site
        clusterFolder (str): The folder where clustering info will be saved for this site
    """
    def __init__(self, subject, date, brainArea, recordingTrack, info, depth, tetrodes):
        self.subject = subject
        self.date = date
        self.brainArea = brainArea
        self.recordingTrack = recordingTrack
        self.info = info
        self.depth = depth
        self.tetrodes = tetrodes
        self.sessions = []
        self.comments = []
        self.clusterFolder = 'multisession_{}_{}um'.format(self.date, self.depth)
        
    def remove_tetrodes(self, tetrodesToRemove):
        """
        Remove tetrodes from a site's list of tetrodes
        """
        if not isinstance(tetrodesToRemove, list):
            tetrodesToRemove = [tetrodesToRemove]
        for tetrode in tetrodesToRemove:
            self.tetrodes.remove(tetrode)
            
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
        session = Session(self.subject,
                          date,
                          self.brainArea,
                          self.recordingTrack,
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
        """
        Returns a list of the ephys directories for all sessions recorded at this site.
        Returns:
            dirs (list): List of ephys directories for each session in self.sessions
        """
        dirs = [session.ephys_dir() for session in self.sessions]
        return dirs
    # def session_behav_filenames(self):
    #      '''
    #      Returns a list of the behavior filenames for all sessions recorded at this site.
    #      Returns:
    #          fns (list): list of behavior filenames for each session in self.sessions
    #      DEPRECATED (2017-10-30): session function no longer implemented
    #      '''
    #      fns = [session.behav_filename() for session in self.sessions]
    #      return fns
    
    def session_types(self):
        """
        Returns a list of the session type strings for all sessions recorded at this site.
        Returns:
            types (list): List of the sessiontype strings for each session in self.sessions
        DEPRECATED (2017-10-30): We just have the generator in the cluster_info method to be clear
        about what is returned per session and what is a site attr.
        """
        types = [session.sessiontype for session in self.sessions]
        return types
    # def find_session(self, sessiontype):
    #      '''
    #      Return indexes of sessions of type sessiontype.
    #      Args:
    #          sessiontype (str): The sessiontype string to search for.
    #      Returns:
    #          inds (list): List of indices of sessions of type sessiontype.
    #      '''
    #      inds = [i for i, st in enumerate(self.session_types()) if st==sessiontype]
    #      return inds
    
    def cluster_info(self):
        """
        Returns a dictionary with the information needed to identify clusters that come from this site.
        Returns:
            infoDict (dict): dictionary containing info defining clusters that come from this site
        """
        infoDict = {
            'subject': self.subject,
            'date': self.date,
            'brainArea': self.brainArea,
            'recordingTrack': self.recordingTrack,
            'info': self.info,
            'depth': self.depth,
            'ephysTime': [session.timestamp for session in self.sessions],
            'paradigm': [session.paradigm for session in self.sessions],
            'behavSuffix': [session.behavsuffix for session in self.sessions],
            'sessionType': [session.sessiontype for session in self.sessions]
        }
        return infoDict

    def pretty_print(self, sessions=False):
        """
        Print a string with depth, number of sessions, and optional list of sessions by index
        Args:
            sessions (bool): Whether to list all sessions by index
        Returns:
            message (str): A formatted string with the message to print
        """
        message = []
        message.append('Site at {}um with {} sessions\n'.format(self.depth, len(self.sessions)))
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


class Session(object):
    """
    Session is a single recorded ephys file and the associated behavior file.
    Attributes:
        subject(str): Name of the subject
        date (str): The date the experiment was conducted
        depth (int): The depth in microns at which the sessions were recorded
        timestamp (str): The timestamp used by openEphys GUI to name the session
        behavsuffix (str): The suffix of the behavior file
        sessiontype (str): A string describing what kind of session this is.
        paradigm (str): The name of the paradigm used to collect the session
        comments (list): list of strings, comments about the session
    """
    def __init__(self, subject, date, brainArea, recordingTrack, info, depth, tetrodes, timestamp, behavsuffix, sessiontype, paradigm, comments=[]):
        self.subject = subject
        self.date = date
        self.depth = depth
        self.tetrodes = tetrodes
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
        # def behav_filename(self):
        #      '''
        #      Generate the behavior filename from session attributes and the beahvior suffix.
        #      Returns:
        #          fn (str): The full behavior filename
        #      DEPRECATED (2017-10-30) We are going to return the suffix and paradigm, not the full path for each session
        #      '''
        #      fn=None
        #      if self.behavsuffix:
        #           bdate = ''.join(self.date.split('-'))
        #           fn = '{}_{}_{}{}.h5'.format(self.subject,
        #                                    self.paradigm,
        #                                    bdate,
        #                                    self.behavsuffix)
        #      return fn
    
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

# Use the pandas dataframe functions directly
# def save_dataframe_as_HDF5(path, dataframe):
#     '''
#     Saves a dataframe to HDF5 format.

#     Args:
#         path (str): /path/to/file.h5
#         dataframe (pandas.DataFrame): dataframe object
#     '''
#     dataframe.to_hdf(path, 'dataframe')

# def load_dataframe_from_HDF5(path, **kwargs):
#     '''
#     See pandas.read_hdf docs for useful kwargs (loading only certain rows, cols, etc)
#     Args:
#         path (str): /path/to/file.h5
#     '''
#     dataframe = pd.read_hdf(path, key='dataframe', **kwargs)
#     return dataframe


def generate_cell_database(inforecPath):
    """
    Iterates over all sites in an inforec and builds a cell database. This function requires that the data is already clustered.
    Args:
        inforecPath (str): absolute path to the inforec file
    Returns:
        celldb (pandas.DataFrame): the cell database
    """

    # clusterDirFormat = 'multisession_exp{}site{}'
    tetrodeStatsFormat = 'Tetrode{}_stats.npz'
    # inforec = imp.load_source('module.name', inforecPath) # 'module.name' was meant to be an actual name
    inforec = imp.load_source('inforec_module', inforecPath)
    print('\nGenerating database for {}'.format(inforecPath))
    celldb = pd.DataFrame(dtype=object)
    for indExperiment, experiment in enumerate(inforec.experiments):
        # Complain if the maxDepth attr is not set for this experiment
        if experiment.maxDepth is None:
            print("Attribute maxDepth not set for experiment with subject {} on {}".format(experiment.subject, experiment.date))
            # maxDepthThisExp = None
            raise AttributeError('You must set maxDepth for each experiment.')
        else:
            maxDepthThisExp = experiment.maxDepth
        print('Adding experiment from {} on {}'.format(experiment.subject, experiment.date))
        for indSite, site in enumerate(experiment.sites):
            # clusterDir = clusterDirFormat.format(indExperiment, indSite)
            clusterFolder = site.clusterFolder
            for tetrode in site.tetrodes:
                clusterStatsFn = tetrodeStatsFormat.format(tetrode)
                clusterStatsFullPath = os.path.join(settings.EPHYS_PATH,
                                                    inforec.subject,
                                                    clusterFolder,
                                                    clusterStatsFn)
                if not os.path.isfile(clusterStatsFullPath):
                    raise NotClusteredError("Experiment {} Site {} Tetrode {} is not clustered.\nNo file {}".format(indExperiment, indSite, tetrode, clusterStatsFullPath))
                clusterStats = np.load(clusterStatsFullPath)

                for indc, cluster in enumerate(clusterStats['clusters']):
                    # Calculate cluster shape quality
                    clusterPeakAmps = clusterStats['clusterPeakAmplitudes'][indc]
                    clusterSpikeSD = clusterStats['clusterSpikeSD'][indc]
                    clusterShapeQuality = abs(clusterPeakAmps[1]/clusterSpikeSD.mean())
                    clusterDict = {'maxDepth': maxDepthThisExp,
                                   'tetrode': tetrode,
                                   'cluster': cluster,
                                   'nSpikes': clusterStats['nSpikes'][indc],
                                   'isiViolations': clusterStats['isiViolations'][indc],
                                   'spikeShape': clusterStats['clusterSpikeShape'][indc],
                                   'spikeShapeSD': clusterSpikeSD,
                                   'spikePeakAmplitudes': clusterPeakAmps,
                                   'spikePeakTimes': clusterStats['clusterPeakTimes'][indc],
                                   'spikeShapeQuality': clusterShapeQuality}
                    clusterDict.update(site.cluster_info())
                    celldb = celldb.append(clusterDict, ignore_index=True)
    # NOTE: This is an ugly way to force these columns to be int. Will fix in future if possible
    celldb['tetrode'] = celldb['tetrode'].astype(int)
    celldb['cluster'] = celldb['cluster'].astype(int)
    celldb['nSpikes'] = celldb['nSpikes'].astype(int)
    return celldb


def generate_cell_database_from_subjects(subjects, removeBadCells=True, isi=0.05, quality=2):
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
        onedb = generate_cell_database(inforec)
        if removeBadCells:
            onedb = onedb[(onedb['isiViolations'] < isi) & (onedb['spikeShapeQuality'] > quality)]
        fulldb = fulldb.append(onedb, ignore_index=True)
    return fulldb


def find_cell(database, subject, date, depth, tetrode, cluster):
    """
    Find a cell in the database.
    Returns (index, pandasSeries)
    """
    cell = database.query('subject==@subject and date==@date and depth==@depth and tetrode==@tetrode and cluster==@cluster')
    if len(cell) > 1:
        raise AssertionError('This information somehow defines more than 1 cell in the database.')
    elif len(cell) == 0:
        raise AssertionError('No cells fit these search criteria.')
    elif len(cell) == 1:
        return cell.index[0], cell.iloc[0]  # Return the index and the series: once you convert to series the index is lost


def get_cell_info(database, index):
    """
    The index is THE index from the original pandas dataframe. It is not the positional index.
    """
    cell = database.loc[index]
    cellDict = {'subject': cell['subject'],
                'date': cell['date'],
                'depth': cell['depth'],
                'tetrode': cell['tetrode'],
                'cluster': cell['cluster']}
    return cellDict


def save_hdf(dframe, filename):
    """
    Save database as HDF5, in a cleaner format than pandas.DataFrame.to_hdf()
    Use celldatabase.load_hdf() to load these files.

    Args:
        dframe: pandas dataframe containing database.
        filename: full path to output file.

    TODO: save index
    """
    h5file = h5py.File(filename, 'w')
    string_dt = h5py.special_dtype(vlen=str)
    # try:
    if 1:
        dbGroup = h5file.require_group('/')  # database
        dbGroup.attrs['celldb_version'] = CELLDB_VERSION
        for onecol in dframe.columns:
            onevalue = dframe.iloc[0][onecol]
            if isinstance(onevalue, np.ndarray):
                arraydata = np.vstack(dframe[onecol].values)
                dset = dbGroup.create_dataset(onecol, data=arraydata)
            elif isinstance(onevalue, int) or \
                isinstance(onevalue, np.int64) or \
                isinstance(onevalue, float) or \
                isinstance(onevalue, bool) or \
                    isinstance(onevalue, np.bool_):
                arraydata = dframe[onecol].values
                dset = dbGroup.create_dataset(onecol, data=arraydata)
            elif isinstance(onevalue, str):
                # TODO: Add a fix to allow this function to save unicode strings when working in python 2.7
                #   Currently this error can be geenrated by saving cell locations while workin in 2.7
                # We used to save this astype(str) not astype(string_dt)
                arraydata = dframe[onecol].values.astype(string_dt)
                dset = dbGroup.create_dataset(onecol, data=arraydata, dtype=string_dt)
            elif isinstance(onevalue, list):
                # For columns like: behavSuffix, ephysTime, paradigm, sessionType
                arraydata = dframe[onecol].values
                dset = dbGroup.create_dataset(onecol, data=arraydata, dtype=string_dt)
            else:
                raise ValueError('Trying to save items of invalid type')
            # dset.attrs['Description'] = onecol
        h5file.close()
    # except:
    #     h5file.close()
    #     # TODO: We may want to rename the incomplete h5 file
    #     raise


def load_hdf(filename, root='/'):
    """
    Load database into a pandas dataframe from an HDF5 file
    saved by celldatabase.save_hdf()

    Args:
        filename: full path to HDF5 file.
        root: the HDF5 group containing the database.
    """
    dbDict = {}
    try:
        h5file = h5py.File(filename, 'r')
    except IOError:
        print('{0} does not exist or cannot be opened.'.format(filename))
        raise
    for varname, varvalue in h5file[root].items():
        # If an error occurs regarding malformed strings, it is because we used to save as strings not string_dt in save_hdf()
        if varvalue.dtype == np.int or varvalue.dtype == np.float:
            if len(varvalue.shape) == 1:
                dbDict[varname] = varvalue[...]
            else:
                dbDict[varname] = list(varvalue[...])  # If it is an array
        elif varvalue.dtype.kind == 'S':
            dbDict[varname] = varvalue[...]
        elif varvalue.dtype == np.object:
            try:
                dataAsList = [ast.literal_eval("{}".format(v)) for v in varvalue]
            except (ValueError, SyntaxError):
                # ValueError: If a list of strings contains a non-string (like None)
                # Passing something like '2019-01-02' above will result in ast.parse not being able
                # to convert it into a string, and it gives a SyntaxError. ast.parse requires it to be passed as "'2019-01-02'" to work
                dataAsList = [ast.literal_eval('"{}"'.format(v)) for v in varvalue]
            dbDict[varname] = dataAsList
        else:
            #raise ValueError('Data type {} for variable {} is not recognized by celldatabase.'.format(varvalue.dtype,varname))
            print('Warning! Data type "{}" for variable "{}" is not recognized by celldatabase.'.format(varvalue.dtype,varname))
    h5file.close()
    return pd.DataFrame(dbDict)


class NotClusteredError(Exception):
    pass

# def find_cell(db, subject, date, depth, tetrode, cluster):
#     cell = db.query('subject==@subject and date==@date and depth==@depth\
#                        and tetrode==@tetrode and cluster==@cluster')
#     if len(result)!=1:
#         #Does not exist or not unique
#         raise
#     return cell[0]


'''
import h5py
h5file = h5py.File('/tmp/test.h5','w')
dbGroup = h5file.require_group('/')

dset = dbGroup.create_dataset('mykey', data=x)
h5file.close()
'''
