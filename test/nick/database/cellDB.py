'''
2015-07-24 Nick Ponvert

Beginnings of the electrophysiology recording database for Jaralab.

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

    def query(self, lookup_dict, startingList=self, verbose=True):
        '''
        The lookup dict will be like this: {'animalName': 'test000', 'date': '2014-06-24'}
        You can also do: {'animalName': ['test000', 'test001']}
        THIS WILL BREAK or at least not do useful things when we try to look at attributes that
        are lists, such as the sessions or sessionTypes. The function below tries to remedy this
        '''
        queryResults = startingList
        for attrName, attrVal in lookup_dict.iteritems():
            if isinstance(attrVal, list): #If a list of possible values is supplied, test whether each cluster value is in the list
                queryResults = [clu for clu in queryResults if getattr(clu, attrName) in attrVal]
            else: #If a single value is supplied, just check if each cluster's attribute value is equal to it.
                queryResults = [clu for clu in queryResults if getattr(clu, attrName)==attrVal]

        if verbose:
            print "{} clusters satisfying these conditions".format(len(queryResults))
        return queryResults

    def query_improved(self, lookup_dict, startingList=self, verbose=True):
        '''
        The lookup dict will be like this: {'animalName': 'test000', 'date': '2014-06-24'}
        You can also do: {'animalName': ['test000', 'test001']}
        We need to figure out what to do when looking for cells that have a 'BestFreq' session,
        when looking for cells with a particular ephys session, etc since these attributes are lists
        '''
        #Start with either the entire DB or some pre-defined subset of it.
        queryResults = startingList

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
        return cell[0]

    def query_features(self, features_dict, startingList=self, verbose=True):
        '''
        The features dictionary is annoying to query with the regular query function because you
        have to write a dictionary inside the query dict. This method will search the features attr only.
        '''
        queryResults = startingList
        for featureName, featureVal in features_dict.iteritems():
            if isinstance(featureVal, list):
                queryResults = [c for c in queryResults if c.features[featureName] in featureVal]
            else:
                queryResults = [c for c in queryResults if c.features[featureName] == featureVal]
        if verbose:
            print "{} clusters satisfying these conditions".format(len(queryResults))
        return queryResults

    def query_features_custom_op(self, features_dict, op=operator.eq, startingList=self, verbose=True):
        '''
        This method allows you to query using a custom comparison opeartor, like operator.gt()
        '''
        queryResults = startingList
        for featureName, featureVal in features_dict.iteritems():
                queryResults = [c for c in queryResults if op(c.features[featureName], featureVal)]
        if verbose:
            print "{} clusters satisfying these conditions".format(len(queryResults))
        return queryResults

    def set_features(self, features_dict, inds_to_set=range(len(self))):
        '''
        Do we ever want to specify a range of inds to this function?
        '''
        for featureName, featureVal in features_dict.iteritems():
            for ind in inds_to_set:
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

    def write_to_json(self, filename):
        '''CAUTION: This will currently overwrite the json file. You should always load the most current
        database work with it, and then write the updated version when you are done.'''

        confirmation = raw_input("This will overwrite the .json file. Proceed? [yes/no] ")

        if confirmation=='yes':
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
                    features = {},
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
            features=features,
            comments=comments)

        self.clusterList.append(cluster)
        return cluster

    def add_clusters(self, clusterDict):
        '''
        Add clusters from many tetrodes at once by passing a dictionary
        e.g. add_clusters({ 3: [2, 3, 5], 5: [3, 7]})
        '''
        for tetrode, clusters in clusterDict.iteritems():
            for cluster in clusters:
                self.add_cluster(cluster, tetrode)


    def get_session_filenames(self):
       return [s.session for s in self.sessionList]

    def get_session_behavIDs(self):
        return [s.behavFileIdentifier for s in self.sessionList]

    def get_session_types(self):
        return [s.sessionType for s in self.sessionList]

    def get_session_inds_one_type(self, plotType, report):
        return [index for index, s in enumerate(self.sessionList) if ((s.plotType == plotType) & (s.report == report))]


    def __repr__(self):
        return "Site at {}um".format(self.depth)

    def __str__(self):
        return "Site at {}um".format(self.depth)

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

    def __repr__(self):
        return "{0} - {1}".format(self.session, self.sessionType)

    def __str__(self):
        return "{0} - {1}".format(self.session, self.sessionType)


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
            features,
            comments=''):

        self.animalName = animalName
        self.date = date
        self.depth = depth
        self.tetrode = tetrode
        self.experimenter = experimenter
        self.paradigm = paradigm
        self.cluster = clusterNumber
        self.ephysSessionList = ephysSessionList
        self.behavFileList = behavFileList
        self.sessionTypes = sessionTypes
        self.features = features
        self.comments = comments
        self.clusterID = '_'.join([animalName,
                                   date,
                                   str(depth),
                                   'TT{}'.format(self.tetrode),
                                   str(clusterNumber)])

    def __repr__(self):
        return self.clusterID

    def __str__(self):
        return self.clusterID

class LoadedCluster(Cluster):

    # def __init__(self, decodedDict):
    #     for key in decodedDict:
    #         if key not in [
    #                 '__class__',
    #                 '__module__']:  # FIXME: get rid of this, it does not seem useful
    #             setattr(self, key, decodedDict[key])
    def __init__(self, decodedDict):
        for key in decodedDict:
            setattr(self, key, decodedDict[key])
