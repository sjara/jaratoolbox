'''
Analyze the quality of clusters produced by spike-sorting
'''

import numpy as np
import os
import matplotlib.pyplot as plt
from jaratoolbox import spikesorting
# from jaratoolbox import celldatabase
from jaratoolbox import loadopenephys
from jaratoolbox import settings

import itertools #For making string combinations of all comparisons
import pickle #For saving the waveform objects

#For importing cellDB files
import sys
import importlib

#For calling rsync to get just the data we need
import subprocess

import pandas as pd

#from jaratoolbox import ephyscore

def find_ephys_sessions(cellDB):
    return list(np.unique(cellDB.get_vector('ephysSession')))

def waveforms_many_sessions(subject, ephysSessions, tetrode, clustersPerTetrode=12, wavesize=160):
    '''
    Create a list of arrays containing waveforms for each session for one tetrode.
    '''
    waveformsOneTetrode = []
    for oneSession in ephysSessions:
        waves = calculate_avg_waveforms(subject, oneSession, tetrode,
                                clustersPerTetrode=clustersPerTetrode, wavesize=wavesize)
        waveformsOneTetrode.append(waves)
    return waveformsOneTetrode

def calculate_avg_waveforms(subject, ephysSession, tetrode, clustersPerTetrode=12, wavesize=160):
    '''
    NOTE: This methods should look through sessions, not clusters.
          The idea is to compare clusters within a tetrode, and then across sessions
          but still within a tetrode.
    NOTE: This method is inefficient because it load the spikes file for each cluster.
    '''

    # DONE: Load data for one tetrodes and calculate average for each cluster.
    #ephysFilename = ???
    ephysDir = os.path.join(settings.EPHYS_PATH, subject, ephysSession)
    ephysFilename = os.path.join(ephysDir, 'Tetrode{}.spikes'.format(tetrode))
    spikes = loadopenephys.DataSpikes(ephysFilename)

    # DONE: Load cluster file
    #kkDataDir = os.path.dirname(self.filename)+'_kk'
    #fullPath = os.path.join(kkDataDir,clusterFilename)
    clustersDir = '{}_kk'.format(ephysDir)
    clusterFilename = os.path.join(clustersDir, 'Tetrode{}.clu.1'.format(tetrode))
    clusters = np.fromfile(clusterFilename, dtype='int32', sep=' ')[1:]

    # DONE: loop through clusters
    allWaveforms = np.empty((clustersPerTetrode,wavesize))
    for indc in range(clustersPerTetrode):
        print('Estimating average waveform for {0} T{1}c{2}'.format(ephysSession,tetrode,indc+1))

        # DONE: get waveforms for one cluster
        #Add 1 to the cluster index because clusters start from 1
        waveforms = spikes.samples[clusters==indc+1, :, :]

        alignedWaveforms = spikesorting.align_waveforms(waveforms)
        meanWaveforms = np.mean(alignedWaveforms,axis=0)
        allWaveforms[indc,:] = meanWaveforms.flatten()
    return allWaveforms


###waveforms = ephysData.spikes.samples.astype(float)-2**15 #This is specific to open Ephys
###waveforms = (1000.0/ephysData.spikes.gain[0,0]) * waveforms

def row_corrcoeff(A,B):
    '''
    Row-wise correlation coefficient between two 2-D arrays.
    Note that np.corrcoeff() is not a valid replacement for this method.

    http://stackoverflow.com/questions/30143417/computing-the-correlation-coefficient-between-two-multi-dimensional-arrays
    '''
    # Rowwise mean of input arrays & subtract from input arrays themeselves
    A_mA = A - A.mean(1)[:,None]
    B_mB = B - B.mean(1)[:,None]

    # Sum of squares across rows
    ssA = (A_mA**2).sum(1)
    ssB = (B_mB**2).sum(1)

    # Finally get corr coeff
    return np.dot(A_mA,B_mB.T)/np.sqrt(np.dot(ssA[:,None],ssB[None]))


def spikeshape_correlation(waveforms):
    '''
    Find the correlation between spikes shapes for a session and across sessions.
    Args:
        waveforms (list): each item should be an np.array containing waveforms
                   for all clusters in one session with size [nClusters,nSamples]
    Returns:
        ccSelf (list): each item is an np.array containing the correlation coefficient
                   matrix across clusters for each session.
        ccAcross (list): each item is an np.array containing the corr coeff matrix
                   between clusters from one session and the next.
    '''
    ccSelf = []
    ccAccross = []
    inds=-1 # Needed in case only one waveform
    for inds in range(len(waveforms)-1):
        ccSelf.append(row_corrcoeff(waveforms[inds],waveforms[inds]))
        ccAccross.append(row_corrcoeff(waveforms[inds],waveforms[inds+1]))
    ccSelf.append(row_corrcoeff(waveforms[inds+1],waveforms[inds+1]))
    return (ccSelf,ccAccross)


def plot_correlation(ccSelf,ccAccross,cmap='hot'):
    nSessions = len(ccSelf)
    plt.clf()
    for inds in range(nSessions):
        plt.subplot2grid((2,nSessions),(0,inds))
        plt.imshow(ccSelf[inds],clim=[0,1], cmap=cmap,interpolation='nearest')
        plt.axis('image')
        #title('')
    for inds in range(nSessions-1):
        plt.subplot2grid((2,nSessions-1),(1,inds))
        plt.imshow(ccAccross[inds],clim=[0,1], cmap=cmap,interpolation='nearest')
        plt.axis('image')
    plt.colorbar()
    plt.draw()

def rsync_session_data(subject,
                       session,
                       serverUser = 'jarauser',
                       serverName = 'jarastore',
                       serverEphysPath = '/data2016/ephys',
                       skipIfExists=False):
    '''
    #NOTE: Deprecated now, use jaratest.nick.utils.transferutils module for these rsync funcs
    #TODO: server user and server name as one string
    #TODO: server ephys path and user in settings file
    Rsync just the sessions you need from jarahub
    '''
    fullRemotePath = os.path.join(serverEphysPath, subject, session)
    serverDataPath = '{}@{}:{}'.format(serverUser, serverName, fullRemotePath)
    localDataPath = os.path.join(settings.EPHYS_PATH, subject) + os.sep
    fullLocalPath = os.path.join(localDataPath, session)
    transferCommand = ['rsync', '-av', serverDataPath, localDataPath]
    if skipIfExists:
        if not os.path.exists(fullLocalPath):
            subprocess.call(transferCommand)
    else:
        subprocess.call(transferCommand)

def rsync_ISI_file(subject,
                   serverUser = 'jarauser',
                   serverName = 'jarastore',
                   serverEphysPath = '/data2016/ephys',
                   skipIfExists=False):

    isiFn = 'ISI_Violations.txt'
    fullRemotePath = os.path.join(serverEphysPath, '{}_processed'.format(subject), isiFn)
    serverDataPath = '{}@{}:{}'.format(serverUser, serverName, fullRemotePath)
    localDataPath = os.path.join(settings.EPHYS_PATH, subject) + os.sep
    transferCommand = ['rsync', '-av', serverDataPath, localDataPath]
    fullLocalFilename = os.path.join(localDataPath, isiFn)
    if skipIfExists:
        if not os.path.isfile(fullLocalFilename):
            subprocess.call(transferCommand)
    else:
        subprocess.call(transferCommand)



def comparison_label_array(session1, session2, tetrode):
    '''
    Returns an array of strings that describe the comparisons made between two sessions
    '''
    clabs1 = ['{}_T{}c{}'.format(session1, tetrode, cnum) for cnum in range(1, 13)]
    clabs2 = ['{}_T{}c{}'.format(session2, tetrode, cnum) for cnum in range(1, 13)]
    labs = ['{} x {}'.format(cl1, cl2) for cl1, cl2 in itertools.product(clabs1, clabs2)]
    larray = np.array(labs, dtype=str).reshape((12, 12))
    return larray


def read_ISI_dict(fileName):
    '''
    This is how Billy and Lan read the ISI files
    '''
    ISIFile = open(fileName, 'r')
    ISIDict = {}
    behavName = ''
    for line in ISIFile:
        if (line.split(':')[0] == 'Behavior Session'):
            behavName = line.split(':')[1][:-1] #Drop the suffix, just keep the date
        else:
            ISIDict[behavName] = [float(x) for x in line.split(',')[0:-1]] #There is an extra comma at the end of the line, so take to  -1
    return ISIDict


def session_good_clusters(cellDB, session, tetrode, isiThresh=None, isiDict=None):
    '''
    Return a 12-item vector, containing 1 if the cluster was good quality and zero otherwise
    '''
    allcellsTetrode = cellDB.get_vector('tetrode')
    allcellsSession = cellDB.get_vector('ephysSession')
    allcellsQuality = cellDB.get_vector('quality')
    #The cells to use come from this session, this tetrode
    cellsThisSession = allcellsSession==session
    cellsThisTetrode = allcellsTetrode==tetrode
    cellsToUse = (cellsThisSession & cellsThisTetrode)
    #Whether each cell in the db is good
    allcellsGoodQuality = ((allcellsQuality==1) | (allcellsQuality==6))
    #Whether the cells that we want to use are good
    goodQualityToUse = allcellsGoodQuality[cellsToUse]
    #The cluster number for each cluster (in case not full 12, or does not start at 1)
    allcellsClusterNumber = cellDB.get_vector('cluster')
    clusterNumsToUse = allcellsClusterNumber[cellsToUse]
    #Initialize to zero
    passingClusters = np.zeros(12, dtype='bool')
    # Set the good quality clusters to 1
    for indClust, clusterNum in np.ndenumerate(clusterNumsToUse):
        passingClusters[clusterNum-1]=goodQualityToUse[indClust]

    if isiThresh:
        allcellsBehavSessions = cellDB.get_vector('behavSession')
        behavSessionsThisSession = allcellsBehavSessions[cellsThisSession]
        behavSession = np.unique(behavSessionsThisSession)
        assert len(behavSession)==1, 'More than 1 behavior session for this ephys session'

        #These are already limited by session
        #DONE: Limit to cells this tetrode
        isiThisSession = np.array(isiDict[behavSession[0]])

        tetrodesThisSession = allcellsTetrode[cellsThisSession]
        cellsThisTetrode = tetrodesThisSession==tetrode
        isiThisTetrode = isiThisSession[cellsThisTetrode]

        assert len(isiThisTetrode)==len(passingClusters), "isiThisTetrode not correct length"

        isiPass = isiThisTetrode < isiThresh
        passingClusters = passingClusters & isiPass

    return passingClusters

def comparison_quality_filter(cellDB, session1, session2, tetrode, isiThresh=None, isiDict=None):
    #DONE: FINISH THIS FUNCTION

    session1good = session_good_clusters(cellDB, session1, tetrode, isiThresh, isiDict).astype(int)
    session2good = session_good_clusters(cellDB, session2, tetrode, isiThresh, isiDict).astype(int)

    #Make a boolean matrix from the two quality vectors, with 1 only if both are 1
    #DONE: Which should come first for the across session comparisons?
    #session 1 becomes the rows, which is the same as the corr function
    qualityMat = np.outer(session1good.astype(int), session2good.astype(int)).astype(bool)

    return qualityMat

def triangle_filter(qualityMat):

    #For the self analysis, we want to exclude the diagonal and the top half of the
    #triangle
    #We use the -1th diagonal so that the self comparisons are filtered out
    qualityMat = np.tril(qualityMat, k=-1)
    return qualityMat

def print_reports_clusters(subject, sessions, tetrode, printer):
    '''
    Automatically print (on paper, with a printer) the cluster reports for some sessions
    use lpstat -p to find printers
    use lpadmin -p printername to add a printer as the default
    '''

    reportsDir = os.path.join(settings.EPHYS_PATH, subject, 'reports_clusters')
    for session in sessions:
        reportFilename = '{}_{}_T{}.png'.format(subject, session, tetrode)
        fullReportPath = os.path.join(reportsDir, reportFilename)
        printcommand = ['lpr', '-P {}'.format(printer), fullReportPath]
        print(' '.join(printcommand))
        # subprocess.call(printcommand)


if __name__=='__main__':
    ### Useful trick:   np.set_printoptions(linewidth=160)
    CASE = 4
    if CASE==0:
        nSamples = 4*40
        nClusters = 12
        basewave = np.sin(2*np.pi*np.linspace(0,2,nSamples))
        waveforms1 = basewave + 0.5*np.random.randn(nClusters,nSamples)
        waveforms2 = basewave + 0.5*np.random.randn(nClusters,nSamples)
        waveforms3 = basewave + 0.5*np.random.randn(nClusters,nSamples)

        listwaveforms = [waveforms1,waveforms2,waveforms3]
        #listwaveforms = [waveforms1,waveforms1,waveforms1]

        #cc = np.corrcoef(waveforms1,waveforms2)
        #cc = row_corrcoeff(waveforms1,waveforms2)
        (ccSelf,ccAccross) = spikeshape_correlation(listwaveforms)

        #print ccSelf
        #print ccAccross

        plot_correlation(ccSelf,ccAccross)
    
    elif CASE==1:
        from jaratoolbox import celldatabase
        eSession = celldatabase.EphysSessionInfo
        cellDB = celldatabase.CellDatabase()
        oneES = eSession(animalName='test089',
                         ephysSession = '2015-07-31_14-40-40',
                         clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),
                                                5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                         behavSession = '20150731a')
        cellDB.append_session(oneES)
        oneES = eSession(animalName='test089',
                         ephysSession = '2015-08-21_16-16-16',
                         clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),
                                                5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                         behavSession = '20150821a')
        cellDB.append_session(oneES)

        # -- Get list of sessions --
        sessionsList = np.unique(cellDB.get_vector('ephysSession'))

        #awave = calculate_avg_waveforms(cellDB)

        #(ccSelf,ccAccross) = spikeshape_correlation([awave])
        #plot_correlation(ccSelf,ccAccross)

    elif CASE==2:

        #Load the waveforms for all the sessions and save them
        subject = 'test098'
        sessions = ['2016-07-26_12-18-39','2016-07-26_12-30-36']
        tetrode=1
        sessionWaves = waveforms_many_sessions(subject, sessions, tetrode)

        #Save the list of waveform arrays as compressed binary file
        waveFile = '/tmp/{}waves.npz'.format(subject)
        np.savez_compressed(waveFile, **dict(zip(sessions, sessionWaves)))

        #Read the saved waveforms back in as a list
        #TODO: This returns a dict, which may not be sorted
        arrFile = np.load(waveFile)
        loadWaves = [arr for name, arr in arrFile.items()]
        loadSessions = [name for name, arr in arrFile.items()]

        ccSelf, ccAcross = spikeshape_correlation(loadWaves)

        corrFile = '/tmp/{}corr.npz'.format(subject)
        np.savez_compressed(corrFile, ccSelf=ccSelf, ccAcross=ccAcross)

        loadCorr = np.load(corrFile)
        plot_correlation(loadCorr['ccSelf'], loadCorr['ccAcross'],'viridis')

    elif CASE==3:

        from jaratest.billy.scripts import celldatabase_quality_tuning as cellDB

        ##
        subject = 'adap015'
        tetrodes = range(1, 9)
        corrThresh = 0.7 #The lower limit for the correlation value 
        isiThresh = 0.02 #The upper threshold for ISI violations
        ##

        ### -- DO THIS PER ANIMAL -- ###
        #Get the allcells file
        allcellsFilename = 'allcells_{}_quality'.format(subject)
        sys.path.append(settings.ALLCELLS_PATH)

        allcells = importlib.import_module(allcellsFilename)

        #Get the isi information for each cell in the allcells file
        rsync_ISI_file(subject, skipIfExists=True)
        isiFn = os.path.join(settings.EPHYS_PATH, subject, 'ISI_Violations.txt') #TODO: this is wet
        isiDict = read_ISI_dict(isiFn)

        #Find all the sessions for this allcells file
        sessions = find_ephys_sessions(allcells.cellDB)
        clusterDirs = ['{}_kk'.format(session) for session in sessions]

        #Rsync the data from jarastore for these sessions if needed
        for session in sessions:
            rsync_session_data(subject, session, skipIfExists=True)
        for clusterDir in clusterDirs:
            rsync_session_data(subject, clusterDir, skipIfExists=True)

        ### -- DO THIS PER TETRODE -- ###

        for tetrode in tetrodes:
            #If the waves exist, load them. If not, get them
            waveFile = '/tmp/{}_TT{}waves.p'.format(subject, tetrode)

            # #DONE: stop calculating waves every time
            if os.path.isfile(waveFile):
                #Load the waves
                #NOTE: I first used np.savez, but it saved a dict and did not preserve the order of the sessions. Pickle saves the actual object.
                #TODO: Use np.savez with the data object to save as the list of arrays
                #TODO: Also see if we should use savez_compressed
                print("Loading average waves for {} tetrode {}".format(subject, tetrode))
                sessionWaves = pickle.load(open(waveFile, 'rb'))
            else:
                print("Calculating average waves for Subject {} tetrode {}".format(subject, tetrode))
                sessionWaves = waveforms_many_sessions(subject, sessions, tetrode)
                pickle.dump(sessionWaves, open(waveFile, 'wb'))

            #TODO: if the correlations exist we don't need to load the waves
            corrFile = '/tmp/{}_TT{}corr.npz'.format(subject, tetrode)
            if os.path.isfile(corrFile):
                #Load the correlations if they already exist
                loadCorr = np.load(corrFile)
                ccSelf = loadCorr['ccSelf']
                ccAcross = loadCorr['ccAcross']
            else:
                #Calculate the pairwise correlation between spikes
                ccSelf, ccAcross = spikeshape_correlation(sessionWaves)
                #Save the correlations
                np.savez_compressed(corrFile, ccSelf=ccSelf, ccAcross=ccAcross)

            #Loop self comparisons WITH THRESHOLD and save to file
            #DONE: Name the file according to animal and tetrode
            allSelfCorrVals = []
            allSelfCorrComps = []
            f = open('/tmp/{}_TT{}_SELF_{}thresh.txt'.format(subject, tetrode, corrThresh), 'w')
            header = '{}  TT{}  SELF correlation'.format(subject, tetrode)
            f.write(header)
            f.write('\n')
            for indSession, session in enumerate(sessions):
                selfCompThisSession = ccSelf[indSession]
                qualityMat = comparison_quality_filter(allcells.cellDB, session, session, tetrode, isiThresh, isiDict)
                qualityMat = triangle_filter(qualityMat)
                larray = comparison_label_array(session, session, tetrode)
                goodCorrVals = selfCompThisSession[qualityMat]
                goodCompLabs = larray[qualityMat]
                corrAboveThreshold = goodCorrVals[goodCorrVals>corrThresh]
                compsAboveThreshold = goodCompLabs[goodCorrVals>corrThresh]
                #save out the values
                allSelfCorrVals.extend(list(goodCorrVals))
                message = '\n##------------## Session {} Self Comparison ##------------##\n'.format(session)
                f.write(message)
                # for corr in compsAboveThreshold:
                #     f.write(corr)
                #     f.write('\n')
                for ind in np.argsort(corrAboveThreshold)[::-1]: #Argsort to print in descending order
                    f.write('{0:.2f} - '.format(corrAboveThreshold[ind]))
                    f.write(compsAboveThreshold[ind])
                    f.write('\n')
            f.close()

            #DONE: Name the file according to animal and tetrode
            allCrossCorrVals = []
            allCrossCorrComps = []
            f = open('/tmp/{}_TT{}_CROSS_{}thresh.txt'.format(subject, tetrode, corrThresh), 'w')
            header = '{}  TT{}  CROSS correlation'.format(subject, tetrode)
            f.write(header)
            f.write('\n')
            for indComp, (session1, session2) in enumerate(zip(sessions, sessions[1:])):
                crossCompTheseSessions = ccAcross[indComp]
                qualityMat = comparison_quality_filter(allcells.cellDB, session1, session2, tetrode, isiThresh, isiDict)
                larray = comparison_label_array(session1, session2, tetrode)
                goodCorrVals = crossCompTheseSessions[qualityMat]
                goodCompLabs = larray[qualityMat]
                corrAboveThreshold = goodCorrVals[goodCorrVals>corrThresh]
                compsAboveThreshold = goodCompLabs[goodCorrVals>corrThresh]
                #save out the values
                allCrossCorrVals.extend(list(goodCorrVals))
                message = '\n##------Cross Comp {} x {}------##\n'.format(session1, session2)
                f.write(message)
                for ind in np.argsort(corrAboveThreshold)[::-1]: #Argsort to print in descending order
                    f.write('{0:.2f} - '.format(corrAboveThreshold[ind]))
                    f.write(compsAboveThreshold[ind])
                    f.write('\n')
            f.close()

