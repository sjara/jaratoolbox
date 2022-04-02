#!/usr/bin/env python

'''
Read behavior data from files (saved by taskontrol).
'''

from jaratoolbox import settings
import os
import numpy as np
import h5py


def dict_from_HDF5(dictGroup):
    '''
    Create bidirectional dict from data saved in file.
    Used for loading labels for menus and categorical variables.
    Args:
        dictGroup: HDF5 node. As in h5file['/resultsLabels/outcomeMode']
                   where h5file is an open HDF5.
    '''
    newDict={}
    for k,v in dictGroup.items():
        newDict[k]=v[()]
        newDict[v[()]]=k
    return newDict


def path_to_behavior_data(subject,paradigm,sessionstr,experimenter=''):
    '''
    Return full path to data file. It assumes that data is in:
    BEHAVIOR_PATH/experimenter/subject/

    Args:
        subject: string
        experimenter: string
        paradigm: string
        sessionstr: string. Usually of the form YYYYMMDDa (as in '20140401a')
    '''
    dataFileFormat = '{0}_{1}_{2}.h5'
    behavFileName = dataFileFormat.format(subject,paradigm,sessionstr)
    behavFile = os.path.join(settings.BEHAVIOR_PATH,experimenter,subject,behavFileName)
    return behavFile



class BehaviorData(dict):
    '''
    Access to behavior data in HDF5 format saved by taskontrol.savedata

    TODO:
    - Check version/format

    '''
    def __init__(self, filename, varlist=[]):
        """
        Args:
            filename (str): full path to data file.
            varlist (list): list of strings specifying variables to read. If empty, read everything.
                            If not empty, it will read the corresponding labels too.
        """
        self.filename = filename
        self.labels = {}
        self.stateMatrix = {}
        self.events = {}
        self.session = {}
        try:
            self.h5file = h5py.File(self.filename,'r')
        except IOError:
            print('{0} does not exist or cannot be opened.'.format(self.filename))
            raise
        try:
            if len(varlist) > 0:
                self.read_subset(varlist)
            else:
                self.read_full()
            '''
            if readmode=='summary':
                self.read_summary()
            elif readmode=='full':
                self.read_full()
            elif readmode=='subset':
                self.read_subset(varlist)
            '''
        except IOError:
            print('Some error occurred while reading data.')
            self.h5file.close()
            raise
        self.h5file.close()
    def read_full(self):
        '''
        Read all variables from file.
        '''
        for varname,varvalue in self.h5file['/resultsData'].items():
            self[varname] = varvalue[...]
        for varname,varvalue in self.h5file['/resultsLabels'].items():
            self.labels[varname] = dict_from_HDF5(varvalue)
        for varname,varvalue in self.h5file['/stateMatrix'].items():
            self.stateMatrix[varname] = dict_from_HDF5(varvalue)
        for varname,varvalue in self.h5file['/events'].items():
            self.events[varname] = varvalue[...]
        for varname,varvalue in self.h5file['/sessionData'].items():
            self.session[varname] = str(varvalue[...])
    def OBSOLETE_read_summary(self):
        '''
        Read only results to calculate average performance.
        '''
        #self['nValid'] = self.h5file['/resultsData/nValid'][-1]
        #self['nRewarded'] = self.h5file['/resultsData/nRewarded'][-1]
        self['nTrials'] = len(self.h5file['/resultsData/nValid'][...])
        paramsNoHistory = ['nValid','nRewarded','outcomeMode','antibiasMode']
        for indp,thisparam in enumerate(paramsNoHistory):
            try:
                self[thisparam] = self.h5file['/resultsData/'+thisparam][-1]
            except KeyError:
                print("{0} has no key '{1}'".format(self.filename,thisparam))
                self[thisparam] = 0
    
    def read_subset(self,varlist):
        '''
        Read a subset of variables.
        '''
        #self['nTrials'] = len(self.h5file['/resultsData/nValid'][...])
        #self['nValid'] = self.h5file['/resultsData/nValid'][-1]
        for indp,thisparam in enumerate(varlist):
            try:
                self[thisparam] = self.h5file['/resultsData/'+thisparam][...]
                if '/resultsLabels/'+thisparam in self.h5file:
                    self.labels[thisparam] = dict_from_HDF5(self.h5file['/resultsLabels/'+thisparam])
            except KeyError:
                print("{0} has no key '{1}'".format(self.filename,thisparam))
                self[thisparam] = 0
    
    def remove_trials(self,trialslist):
        '''
        Delete a subset of trials.
        Note that self.events is not modified. This is trickier, and maybe changing
        only events['indexLastEventEachTrial'] would work.
        '''
        for varname in self.iterkeys():
            self[varname] = np.delete(self[varname],trialslist)

    def __str__(self):
        objStrings = []
        for key,value in sorted(self.iteritems()):
            if isinstance(value,np.ndarray):
                objStrings.append('%s : %s\n'%(key,str(value.shape)))
            elif isinstance(value,int):
                objStrings.append('%s : %d\n'%(key,value))
            elif isinstance(value,str):
                objStrings.append('%s : %s\n'%(key,value))
            else:
                objStrings.append('%s : %s\n'%(key,str(type(value))))
        return ''.join(objStrings)
    def __deepcopy__(self, memo):
        return self


class FlexCategBehaviorData(BehaviorData):
    '''This class adds methods specific to the flexible categorization paradigm.'''
    def __init__(self,behavFileName,readmode='full',varlist=[]):
        BehaviorData.__init__(self,behavFileName,readmode,varlist)
        # FIXME: Not sure nTrials should be defined here. What is trials are removed?
        self.nTrials = len(self['currentBlock'])
        self.blocks = {}
    def find_boundaries_each_block(self):
        #print len(self['currentBlock']) ### DEBUG
        blockBoundaries = np.flatnonzero(np.diff(self['currentBlock']))
        lastTrialEachBlock = np.hstack((blockBoundaries,self.nTrials))
        firstTrialEachBlock = np.hstack((0,lastTrialEachBlock[:-1]+1))
        self.blocks['eachBlockType'] = self['currentBlock'][firstTrialEachBlock]
        self.blocks['nBlocks'] = len(lastTrialEachBlock)
        self.blocks['lastTrialEachBlock'] = lastTrialEachBlock
        self.blocks['firstTrialEachBlock'] = firstTrialEachBlock
    def find_trials_each_block(self):
        self.find_boundaries_each_block()
        self.blocks['trialsEachBlock'] = np.zeros((self.nTrials,self.blocks['nBlocks']),dtype=bool)
        self.blocks['blockEachTrial'] = np.empty(self.nTrials,dtype=int)
        for block in range(self.blocks['nBlocks']):
            bSlice = slice(self.blocks['firstTrialEachBlock'][block],
                           self.blocks['lastTrialEachBlock'][block]+1)
            self.blocks['trialsEachBlock'][bSlice,block]=True
            self.blocks['blockEachTrial'][bSlice]=block
    def remove_trials(self,trialslist):
        super(FlexCategBehaviorData,self).remove_trials(trialslist)
        self.nTrials = len(self['currentBlock'])
        

if __name__ == "__main__":

    CASE=2
    if CASE==1:
        behavFile = '/data/behavior/santiago/test011/test011_2afc_20140311a.h5'
        bdata = BehaviorData(behavFile)
    if CASE==2:
        bfile=path_to_behavior_data('test020','santiago','2afc','20140421a')
        bdata = FlexCategBehaviorData(bfile,readmode='full')
    if CASE==3:
        bfile=path_to_behavior_data('test020','santiago','2afc','20140421a')
        print(bfile)
        bdata = FlexCategBehaviorData(bfile,readmode='full')
        from pylab import *
        hold(0)
        for p,v in sorted(bdata.items()):
            plot(v,'.')
            title(p)
            waitforbuttonpress()
        
        #h5file = h5py.File(bfile)
        # TO FIX:
        # timeSideIn, timeCenterIn, timeCenterOut
            
