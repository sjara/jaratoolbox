'''
2015-07-24 Nick Ponvert

Beginnings of the electrophysiology recording database for Jaralab.

TODO:

- What to do when sessions from the same site occur on different days?
TESTED, DONT THINK SO- If we change the experimenter for an Experiment, will it change for all of
the clusters because they are all pointing at the same place in memory?
DONE -  Change tetrodes to just tetrodes
DONE - Change behavFileIdentifier to something like behavSuffix
DONE - Sessions need to know about the paradigm that was used
DONE (I think)- Repeated arguments should be in the same order ('animalName', etc)

animalName, date, ephysSessionList, behavFileList, experimenter, paradigm,

- We should be able to cluster just a single session and get clusters from it
- We need to have a database of sites in addition to a database of clusters
DONE - Sessions need to hold the whole behavior file name, not just the suffix. We will still create them by specifying the suffix

- Consider not separating the behav files by animal

- the database will ultimately give us back strings for the filenames of the ephys and behavior session, also cluster objects.
- Cluster may need to have methods for returning ephys and behav filenames


- For next time: how do we send an email with what clusters to plot and then plot them very easily?
'''

import json
import operator
import os

class CellDB(list):

    def __init__(self):
        super(CellDB, self).__init__()


    def add_clusters(self, clusters):
        '''
        The safe way to append clusters. Will not add a cluster if it already exists in the database.
        '''

        for cluster in clusters:
            if cluster.clusterID not in self.get_cluster_ids():
                self.append(cluster)
            else:
                print "Attemted to add duplicate cluster {}".format(cluster.clusterID)

    def get_cluster_ids(self):
        return [c.clusterID for c in self]

    # def query(self, lookup_dict, verbose=True):
    #     '''
    #     The lookup dict will be like this: {'animalName': 'test000', 'date': '2014-06-24'}
    #     You can also do: {'animalName': ['test000', 'test001']}
    #     THIS WILL BREAK or at least not do useful things when we try to look at attributes that
    #     are lists, such as the sessions or sessionTypes. The function below tries to remedy this
    #     '''
    #     queryResults = self
    #     for attrName, attrVal in lookup_dict.iteritems():
    #         if isinstance(attrVal, list): #If a list of possible values is supplied, test whether each cluster value is in the list
    #             queryResults = [clu for clu in queryResults if getattr(clu, attrName) in attrVal]
    #         else: #If a single value is supplied, just check if each cluster's attribute value is equal to it.
    #             queryResults = [clu for clu in queryResults if getattr(clu, attrName)==attrVal]

    #     if verbose:
    #         print "{} clusters satisfying these conditions".format(len(queryResults))
    #     return queryResults

    def query(self, lookup_dict, verbose=True):
        '''
        The lookup dict will be like this: {'animalName': 'test000', 'date': '2014-06-24'}
        You can also do: {'animalName': ['test000', 'test001']}
        We need to figure out what to do when looking for cells that have a 'BestFreq' session,
        when looking for cells with a particular ephys session, etc since these attributes are lists
        '''
        #Start with either the entire DB or some pre-defined subset of it.
        queryResults = self

        #Iterate through the values in the query dictionary, narrowing the results each time.
        for attrName, attrVal in lookup_dict.iteritems():
            passing_clusters_this_attr = []
            for clu in queryResults:
                #Get the value of the attribute for this cluster
                clusterAttrVal = getattr(clu, attrName)

                #Some attributes, like sessions, sessionTypes, and behavFileIDs,
                #are lists. We should check each entry
                if isinstance(clusterAttrVal, list):

                    #Now we need to handle things differently depending on whether
                    #the supplied attribute value in the query was a list of possible
                    #values or a single value

                    #Compare the list of cluster attribute vals to a list
                    if isinstance(attrVal, list):
                        #This should pass if they share any items
                        if set(clusterAttrVal) & set(attrVal):
                            passing_clusters_this_attr.append(clu)
                            pass
                    else:
                        #Test whether the supplied value is in the cluster attribute
                        if attrVal in clusterAttrVal:
                            passing_clusters_this_attr.append(clu)
                            pass
                #If the cluster attribute val is not a list
                else:
                    #Compare a single cluster attribute to a list of possibilities
                    if isinstance(attrVal, list):
                        if clusterAttrVal in attrVal:
                            passing_clusters_this_attr.append(clu)
                            pass
                    #Compare a single cluster attribute to a single value
                    else:
                        if clusterAttrVal==attrVal:
                            passing_clusters_this_attr.append(clu)
                            pass


            queryResults = passing_clusters_this_attr
        if verbose:
            print "{} clusters satisfying these conditions".format(len(queryResults))
        return queryResults

    def find_cell_from_site(self, animalName, date, depth, tetrode, cluster):
        '''
        This method will return only a single cell
        '''

        cell = self.query({'animalName': animalName,
                           'date': date,
                           'depth': depth,
                           'tetrode': tetrode,
                           'cluster': cluster}, verbose=False)
        if cell:
            return cell[0]
        else:
            print "No clusters found"

    def find_cell_from_session(self, animalName, ephysSession, tetrode, cluster):

        cell = self.query({
            'animalName': animalName,
            'ephysSessionList': ephysSession,
            'tetrode': tetrode,
            'cluster': cluster}, verbose=False)

        if cell:
            return cell[0]
        else:
            print "No clusters found"

    def query_features(self, features_dict, verbose=True):
        '''
        The features dictionary is annoying to query with the regular query function because you
        have to write a dictionary inside the query dict. This method will search the features attr only.
        This method will only work if features have ONE value. It is not yet implemented for features that
        contain lists of values.
        '''
        queryResults = self
        for featureName, featureVal in features_dict.iteritems():
            if isinstance(featureVal, list):
                queryResults = [c for c in queryResults if c.features[featureName] in featureVal]
            else:
                queryResults = [c for c in queryResults if c.features[featureName] == featureVal]
        if verbose:
            print "{} clusters satisfying these conditions".format(len(queryResults))
        return queryResults

    def query_features_custom_op(self, features_dict, op=operator.eq, verbose=True):
        '''
        This method allows you to query using a custom comparison opeartor, like operator.gt()
        The operator function must compare the feature val of a cluster with the val you supply and
        return True or False.

        This method only works if you supply a single value as a feature val.
        Other constraints apply depending on the choice of opeartor function. When using
        functions from the opeartor module, this will probably only work well with numeric features
        '''
        queryResults = self
        for featureName, featureVal in features_dict.iteritems():
                queryResults = [c for c in queryResults if op(c.features[featureName], featureVal)]
        if verbose:
            print "{} clusters satisfying these conditions".format(len(queryResults))
        return queryResults

    def set_features(self, features_dict, indsToSet=[]):
        '''
        Do we ever want to specify a range of inds to this function?
        '''
        if not indsToSet:
            indsToSet = range(len(self))
        for featureName, featureVal in features_dict.iteritems():
            for ind in indsToSet:
                self[ind].features[featureName]=featureVal

    def set_features_from_array(self, featureName, featureArray):
        '''
        The feature array has to be the same length as the database
        '''
        if len(featureArray)!=len(self):
            print "The feature array has to be the same length as the database"
            pass

        for indClust, featureVal in enumerate(featureArray):
            self[indClust].features[featureName]=featureVal

    def write_to_json(self, filename, force=False):
        '''CAUTION: This will currently overwrite the json file. You should always load the most current
        database work with it, and then write the updated version when you are done.'''

        confirmation=''
        if not force:
            confirmation = raw_input("This will overwrite the .json file. Proceed? [yes/no] ")

        if (confirmation=='yes' or force):
            with open(filename, 'w') as f:
                f.write('[\n')
                for indClust, cluster in enumerate(self):
                    f.write(
                        json.dumps(
                            cluster.__dict__,
                            indent=4,
                            sort_keys=True))
                    if indClust < len(self) - 1:
                        f.write(',\n')
                f.write('\n]')
        elif confirmation=='no':
            print "Aborting"
        else:
            print "Please enter 'yes' or 'no'"



    def load_from_json(self, filename):
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                jsonDict = json.load(f)

            self.add_clusters([LoadedCluster(d) for d in jsonDict])

        else:
            print "No database file found"

class Experiment(object):
    '''
    Experiment is a container of Sites.
    '''


    def __init__(self, animalName, date, experimenter, defaultParadigm=''):
        self.animalName = animalName
        self.date = date
        self.experimenter = experimenter
        self.defaultParadigm = defaultParadigm
        self.siteList = []
    def add_site(self, depth, tetrodes):

        '''
        Args:

        depth (int): The depth of the site in microns
        tetrodes (list): A list of the tetrode numbers that have good signals
        '''

        site = Site(animalName=self.animalName,
                    date=self.date,
                    experimenter=self.experimenter,
                    defaultParadigm=self.defaultParadigm,
                    tetrodes=tetrodes,
                    depth=depth)

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

    Will act as a parent for all of the Session objects that hold
    information about each individual recording session.
    '''

    def __init__(self, animalName, date, experimenter, defaultParadigm, tetrodes, depth=0):

        '''
        Args:

        depth (int): The site depth in microns
        tetrodes (list): A list of the tetrodes with good signals for this site
        '''

        self.depth = depth
        self.tetrodes = tetrodes
        self.animalName = animalName #Provided by Recording
        self.date = date #Provided by Recording
        self.experimenter = experimenter #Provided by Recording
        self.defaultParadigm = defaultParadigm #Provided by Recording
        self.sessionList = []
        self.clusterList = []

    def add_session(self, sessionTimestamp, behavFileSuffix, sessionType, paradigm=None):
        '''
        Args:
            sessionTimestamp (str): The timestamp for the ephys file (e.g. '11-22-33')
            behavFileSuffix (str): The suffix on the behavior file
            sessionType (str): An arbitrary string describing the session. Useful if standardized for a particular experiment (e.g. 'NoiseBurst')
            paradigm (str): The name of the paradigm that was used to collect the session. Defaults to the default paradigm for this site.
        '''

        if not paradigm:
            paradigm = self.defaultParadigm

        if behavFileSuffix:
            datestr = ''.join(self.date.split('-'))
            behavFileNameBaseName = '_'.join([self.animalName, paradigm, datestr])
            fullBehavFileName = '{}{}.h5'.format(behavFileNameBaseName, behavFileSuffix)
        else:
            fullBehavFileName=None

        fullSessionFilename = '_'.join([self.date, sessionTimestamp])

        session = Session(fullSessionFilename, fullBehavFileName, sessionType)
        self.sessionList.append(session)
        return session

    def add_cluster(self,
                    tetrode,
                    cluster,
                    **kwargs):

        cluster = Cluster(
            animalName=self.animalName,
            date=self.date,
            depth=self.depth,
            tetrode=tetrode,
            cluster=cluster,
            ephysSessionList=self.get_session_ephys_filenames(),
            behavFileList=self.get_session_behav_filenames(),
            sessionTypes=self.get_session_types(),
            **kwargs)

        self.clusterList.append(cluster)
        return cluster

    def add_clusters(self, clusterDict):
        '''
        Add clusters from many tetrodes at once by passing a dictionary.

        Args:
            clusterDict (dict): A dictionary in the form: {tetrodeNumber: [clusterNumbers]}
        '''
        for tetrode, clusters in clusterDict.iteritems():
            for cluster in clusters:
                self.add_cluster(tetrode, cluster)


    def get_session_ephys_filenames(self):
        '''
        Returns a list of the ephys filenames for each session in the sessionList
        '''
        return [s.ephysFilename for s in self.sessionList]

    def get_session_behav_filenames(self):
        '''
        Returns a list of the behavior filenames for each session in the sessionList
        '''
        return [s.behavFilename for s in self.sessionList]

    def get_session_types(self):
        '''
        Returns a list of the session types for each session in the sessionList
        '''
        return [s.sessionType for s in self.sessionList]

    def __repr__(self):
        return "Site at {}um".format(self.depth)

    def __str__(self):
        return "Site at {}um".format(self.depth)

class Session(object):

    '''
    Class to hold information about a single session.
    '''

    def __init__(self, fullSessionFilename, fullBehavFilename, sessionType):
        self.ephysFilename = fullSessionFilename
        self.behavFilename = fullBehavFilename
        self.sessionType = sessionType

    def __repr__(self):
        return "{0} - {1}".format(self.session, self.sessionType)

    def __str__(self):
        return "{0} - {1}".format(self.session, self.sessionType)


class Cluster(object):
    '''
    The init method currently sets the features attr to a copy of the features argument
    If we dont do this, all clusters will point to the same dictionary and we dont know why
    '''

    def __init__(
            self,
            animalName,
            date,
            depth,
            tetrode,
            cluster,
            ephysSessionList,
            behavFileList,
            sessionTypes,
            features={},
            comments=''):

        self.animalName = animalName
        self.date = date
        self.depth = depth
        self.tetrode = tetrode
        self.cluster = cluster
        self.ephysSessionList = ephysSessionList
        self.behavFileList = behavFileList
        self.sessionTypes = sessionTypes
        self.features = features.copy()
        self.comments = comments
        self.clusterID = '_'.join([animalName,
                                   date,
                                   str(depth),
                                   'TT{}'.format(self.tetrode),
                                   str(cluster)])

    def get_data_filenames(self, sessionType, includeMouse=True):
        '''
        Returns the ephys session folder name, or a tuple containing both the ephys filename
        and the behavior file name

        Args:
            sessionType (str): The string used to define the session when it was created
            includeMouse (bool): Whether to return the full filename joined to the mouse folder
        Returns:
            ephysFilename (str): The full name of the ephys session folder
            behavFilename (str): Also returned if the session has behavior data
        '''
        sessionIndex = self.sessionTypes.index(sessionType)
        ephysFile = None
        behavFile = None

        #I think we will usually want to include the mouse directory in the output.
        #This will help when doing offline plotting of cells from many mice.
        #We will not have to have seperate DataLoader objects for each mouse that we deal with
        if includeMouse:
            ephysFile = os.path.join(self.animalName, self.ephysSessionList[sessionIndex])
            if self.behavFileList[sessionIndex]:
                behavFile = os.path.join(self.animalName, self.behavFileList[sessionIndex]) #We can't do the join if the behav file is None

        else:
            ephysFile = self.ephysSessionList[sessionIndex]
            behavFile = self.behavFileList[sessionIndex]

        if behavFile:
            return ephysFile, behavFile
        else:
            return ephysFile

    def __repr__(self):
        return self.clusterID

    def __str__(self):
        return self.clusterID

class LoadedCluster(Cluster):

    def __init__(self, decodedDict):
        for key in decodedDict:
            setattr(self, key, decodedDict[key])
