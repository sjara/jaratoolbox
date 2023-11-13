'''
Methods and classes for spike sorting and creating reports.

Things to fix:
#FIXME: This produces a RuntimeWarning (parent module 'module' not found...)
'''

from __future__ import print_function

import matplotlib.pyplot as plt
from jaratoolbox import settings
from jaratoolbox import loadopenephys
from jaratoolbox import extraplots
import numpy as np
import os
import subprocess
import time
import imp
import shutil
#import paramiko

__author__ = 'Santiago Jaramillo'
__version__ = '0.1'


SAMPLES_PER_SPIKE = 40
N_CHANNELS = 4


#KK_PATH = '/var/misc/toolbox/KK2/KlustaKwik'
#REMOTE_SERVER = 'zelk'
#REMOTE_EPHYS_PATH = '/home/sjara/data'

# NOTE: This object is not longer used (in JaraLab).
class SessionToCluster(object):
    '''Define session, send data to remote server, cluster remotely and get results back '''
    def __init__(self,animalName,ephysSession,tetrodes,serverUser=None,serverName=None,serverPath=None):
        self.animalName = animalName
        self.ephysSession = ephysSession
        self.tetrodes = tetrodes
        self.serverUser = serverUser
        self.serverName = serverName
        self.serverPath = serverPath
        self.localAnimalPath = os.path.join(settings.EPHYS_PATH,animalName)
        self.localSessionPath = os.path.join(self.localAnimalPath,ephysSession)
        self.client = None
    def transfer_data_to_server(self):
        destPath = os.path.join(self.serverPath,self.animalName)
        remotePath = '%s@%s:%s'%(self.serverUser,self.serverName,destPath)
        transferCommand = ['rsync','-a', '--progress', self.localSessionPath, remotePath]
        print(' '.join(transferCommand))
        subprocess.call(transferCommand)
    def run_clustering_remotely(self):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.connect(self.serverName, 22, self.serverUser)
        commandFormat = 'python /home/bard/src/extracellpy/runclustering.py %s %s %d'

        ######## FIXME: HARDCODED PATH #########

        for oneTetrode in self.tetrodes:
            #oneTetrode=7
            commandStr = commandFormat%(self.animalName,self.ephysSession,oneTetrode)
            print('TT%d : creating FET files, clustering and creating report...'%oneTetrode)
            (stdin,stdout,stderr) = self.client.exec_command(commandStr)
            #print stderr.readlines()
            print('DONE!')
        self.client.close()
    def delete_fet_files(self):
        kkResultsPathRemote = os.path.join(self.serverPath,self.animalName,self.ephysSession)+'_kk'
        commandStr = 'mv %s/*.fet.* /tmp/'%kkResultsPathRemote
        print('Deleting FET files...')
        print(commandStr)
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.connect(self.serverName, 22, self.serverUser)
        (stdin,stdout,stderr) = self.client.exec_command(commandStr)
        #print commandStr
        print('DONE!')
    def transfer_results_back(self):
        destPath = os.path.join(self.serverPath,self.animalName)
        remotePath = '%s@%s:%s'%(self.serverUser,self.serverName,destPath)
        remotePathResults = os.path.join(remotePath,self.ephysSession+'_kk')
        remotePathReports = os.path.join(remotePath,self.ephysSession+'_report')
        transferCommandResults = ['rsync','-a', '--progress', '--exclude', "'*.fet.*'",
                                  remotePathResults, self.localAnimalPath]
        transferCommandReports = ['rsync','-a', '--progress', remotePathReports, self.localAnimalPath]
        print(' '.join(transferCommandResults))
        subprocess.call(transferCommandResults)
        print(' '.join(transferCommandReports))
        subprocess.call(transferCommandReports)
    def consolidate_reports(self):
        # Create dest folder
        # Copy reports to that folder
        reportsDir = os.path.join(self.localAnimalPath,'clusters_report')
        thisSessionReportsDir = self.localSessionPath+'_report'
        if not os.path.exists(reportsDir):
            print('Creating output directory: %s'%(reportsDir))
            os.makedirs(reportsDir)
        commandList = ['rsync','-a',thisSessionReportsDir+'/*',reportsDir]
        commandStr = ' '.join(commandList)
        print('Consolidating reports...')
        print(commandStr)
        subprocess.call(commandStr,shell=True)
        print('DONE!')


class TetrodeToCluster(object):
    def __init__(self,subject,ephysSession,tetrode,features=None):
        self.subject = subject
        self.ephysSession = ephysSession
        self.tetrode = tetrode
        # self.dataTT = None
        self.timestamps = None
        self.samples = None
        self.clusters = None
        self.nSpikes = None

        '''
        self.dataDir = os.path.join(settings.EPHYS_PATH,'%s/%s/'%(self.subject,self.ephysSession))
        self.clustersDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(self.subject,self.ephysSession))
        #self.reportDir = os.path.join(settings.EPHYS_PATH,'%s/%s_report/'%(self.subject,self.ephysSession))
        self.reportDir = os.path.join(settings.EPHYS_PATH,'%s/%s_report/'%(self.subject,self.ephysSession))
        self.tetrodeFile = os.path.join(self.dataDir,'Tetrode%d.spikes'%tetrode)
        self.fetFilename = os.path.join(self.clustersDir,'Tetrode%d.fet.1'%self.tetrode)
        '''

        self.dataDir = os.path.join(settings.EPHYS_PATH,self.subject,self.ephysSession)
        self.clustersDir = os.path.join(settings.EPHYS_PATH,self.subject,self.ephysSession+'_kk')
        self.tetrodeFile = os.path.join(self.dataDir,'Tetrode{0}.spikes'.format(tetrode))
        self.fetFilename = os.path.join(self.clustersDir,'Tetrode{0}.fet.1'.format(tetrode))
        #self.reportDir = os.path.join(settings.EPHYS_PATH,self.subject,'reports_clusters')

        self.reportFileName = '{0}_{1}_T{2}.png'.format(self.subject,ephysSession,tetrode)
        self.report = None

        if features is None:
            self.featureNames = ['peak','valley','energy']
        else:
            self.featureNames = features
        self.nFeatures = len(self.featureNames)
        self.featureValues = None

        self.process = None
    def load_waveforms(self):
        '''
        https://github.com/open-ephys/GUI/wiki/Data-format
        Since the samples are saved as unsigned integers, converting them to microvolts
        involves subtracting 32768, dividing by the gain, and multiplying by 1000.
        '''
        print('Loading data...')
        dataTT = loadopenephys.DataSpikes(self.tetrodeFile) #,readWaves=True)
        self.nSpikes = dataTT.nRecords# FIXME: this is specific to the OpenEphys format
        self.samples = dataTT.samples.astype(float)-2**15# FIXME: this is specific to OpenEphys
        # FIXME: This assumes the gain is the same for all channels and records
        self.samples = (1000.0/dataTT.gain[0,0]) * self.samples
        self.timestamps = dataTT.timestamps/dataTT.samplingRate
    def create_fet_files(self):
        # -- Create output directory --
        if not os.path.exists(self.clustersDir):
            print('Creating clusters directory: %s'%(self.clustersDir))
            os.makedirs(self.clustersDir)
        if self.samples is None:
            self.load_waveforms()
        self.featureValues = calculate_features(self.samples,self.featureNames)
        write_fet_file(self.fetFilename,self.featureValues)
    def run_clustering(self, MinClusters=10, MaxClusters=12, MaxPossibleClusters=12):
        # FIXME: it should not depend on dataTT, that way one can run it with just the FET file
        maxNumberOfEventsToUse = 1e5
        Subset = np.floor(self.nSpikes/min(self.nSpikes,maxNumberOfEventsToUse))
        MinClusters = MinClusters #10          # See KlustaKwik.C for definition
        MaxClusters = MaxClusters #24          # See KlustaKwik.C for definition
        MaxPossibleClusters = MaxPossibleClusters  # See KlustaKwik.C for definition
        UseFeatures = (self.nFeatures*N_CHANNELS)*'1'
        KKtetrode = 'Tetrode%s'%(self.tetrode)
        KKsuffix = '1'
        KKpath = settings.KK_PATH
        KKcommandAndParams = [KKpath,KKtetrode,KKsuffix, '-Subset','%d'%Subset,
                              '-MinClusters','%d'%MinClusters, '-MaxClusters','%d'%MaxClusters,
                              '-MaxPossibleClusters','%d'%MaxPossibleClusters,
                              '-UseFeatures',UseFeatures]
        print(' '.join(KKcommandAndParams))
        returnCode = subprocess.call(KKcommandAndParams,cwd=self.clustersDir)
        if returnCode:
            print('WARNING! clustering gave an error')
        '''

        #KKparamsFormat = '-Subset %d -MinClusters %d -MaxClusters %d -MaxPossibleClusters %d -UseFeatures %s';
        #KKparams = KKparamsFormat%(Subset,MinClusters,MaxClusters,MaxPossibleClusters,UseFeatures)
        #commandToRun = '%s %s %s %s'%(KKpath,KKtetrode,KKsuffix,KKparams)
        # NOTE: redirecting to PIPE did not work. The process goes idle after 20+ sec.
        ###self.process = subprocess.Popen([KKpath,KKtetrode,KKsuffix,KKparams],stdout=subprocess.PIPE,cwd=self.clustersDir)
        #self.process = subprocess.Popen([KKpath,KKtetrode,KKsuffix,KKparams],stdout=open('/dev/null','w'),cwd=self.clustersDir)
        while self.process.poll() is None:
            print 'Not yet: %f'%(time.time())
            time.sleep(4)
        print 'Done!'
        '''
    def save_report(self, dirname='reports_clusters'):
        reportDir = os.path.join(settings.EPHYS_PATH,self.subject,dirname)
        if self.samples is None:
            self.load_waveforms()
        # self.dataTT.set_clusters(os.path.join(self.clustersDir,'Tetrode%d.clu.1'%self.tetrode))
        self.set_clusters_from_file()
        figTitle = self.dataDir+' (T%d)'%self.tetrode
        self.report = ClusterReportFromData(self.timestamps,
                                            self.samples,
                                            self.clusters,
                                            outputDir=reportDir,
                                            filename=self.reportFileName,figtitle=figTitle,
                                            showfig=False)
    def set_clusters_from_file(self):
        #TODO: This is a method stolen from loadopenephys.DataSpikes and needs to be defined only once, because its strange
        clusterFile = os.path.join(self.clustersDir,'Tetrode%d.clu.1'%self.tetrode)
        self.clusters = np.fromfile(clusterFile,dtype='int32',sep=' ')[1:]


'''
subprocess.call(['scp','/var/tmp/CageTheElephant.iso','bard@bard02:/tmp/'])
myp=subprocess.Popen(['scp','/var/tmp/CageTheElephant.iso','bard@bard02:/tmp/'],stdout=subprocess.PIPE)

'''
def calculate_features(waveforms,featureNames):
    '''
    Parameters:
      waveforms: [nSpikes,nChannels,nSamples]
      featureNames: list of strings: 'peak','peakFirstHalf','valley','energy'

    Returns:
      featureValues: [nSpikes, nFeatures*NChannels]
    '''
    nFeatures = len(featureNames)
    [nSpikes,nChannels,nSamples] = waveforms.shape
    featureValues = np.empty((nSpikes,0),dtype=float)
    for oneFeature in featureNames:
        print('Calculating {0} ...'.format(oneFeature))
        if oneFeature=='peak':
            theseValues = waveforms.max(axis=2)
            featureValues = np.hstack((featureValues,theseValues))
        elif oneFeature=='peakFirstHalf':
            halfSample = waveforms.shape[2]//2
            theseValues = waveforms[:,:,:halfSample].max(axis=2)
            featureValues = np.hstack((featureValues,theseValues))
        elif oneFeature=='valley':
            theseValues = waveforms.min(axis=2)
            featureValues = np.hstack((featureValues,theseValues))
        elif oneFeature=='valleyFirstHalf':
            halfSample = waveforms.shape[2]//2
            theseValues = waveforms[:,:,:halfSample].min(axis=2)
            featureValues = np.hstack((featureValues,theseValues))
        elif oneFeature=='energy':
            theseValues = np.sqrt(np.sum(waveforms.astype(float)**2,axis=2))
            featureValues = np.hstack((featureValues,theseValues))
    return featureValues


def write_fet_file(filename,fetArray):
    '''
    Save a file with features from all spikes, to be used by KlustaKwik.
    '''
    print('Saving features to {0}'.format(filename))
    nTotalFeatures = fetArray.shape[1]
    fid = open(filename,'w')
    fid.write('{0}\n'.format(nTotalFeatures))
    for onerow in fetArray:
        #strarray = ['%0.2f'%val for val in onerow]
        strarray = ['{0}'.format(val) for val in onerow]
        oneline = '\t'.join(strarray) + '\n'
        fid.write(oneline)
    fid.close()


def pp_features(featureValues,nvals=4):
    for indr in range(nvals):
        for oneval in featureValues[indr,:]:
            print('%0.2f '%oneval, end='')
        print('')
    print(' ...')
    for oneval in featureValues[-1,:]:
        print('%0.2f '%oneval, end='')
    print('')



def plot_isi_loghist(timeStamps,nBins=350,fontsize=8):
    '''
    Plot histogram of inter-spike interval (in msec, log scale)

    Parameters
    ----------
    timeStamps : array (float in sec)
    '''
    fontsizeLegend = fontsize
    xLims = [1e-1,1e4]
    ax = plt.gca()
    ISI = np.diff(timeStamps)
    if np.any(ISI<0):
        raise 'Times of events are not ordered (or there is at least one repeated).'
    if len(ISI)==0:  # Hack in case there is only one spike
        ISI = np.array(10)
    logISI = np.log10(ISI)
    [ISIhistogram,ISIbinsLog] = np.histogram(logISI,bins=nBins)
    ISIbins = 1000*(10**ISIbinsLog[:-1]) # Conversion to msec
    fractionViolation = np.mean(ISI<1e-3) # Assumes ISI in usec
    fractionViolation2 = np.mean(ISI<2e-3) # Assumes ISI in usec

    hp, = plt.semilogx(ISIbins,ISIhistogram,color='k')
    plt.setp(hp,lw=0.5,color='k')
    yLims = plt.ylim()
    plt.xlim(xLims)
    plt.text(0.15,0.85*yLims[-1],'N={0}'.format(len(timeStamps)),fontsize=fontsizeLegend,va='top')
    plt.text(0.15,0.6*yLims[-1],'{0:0.2%}\n{1:0.2%}'.format(fractionViolation,fractionViolation2),
             fontsize=fontsizeLegend,va='top')
    #plt.text(0.15,0.6*yLims[-1],'%0.2f%%\n%0.2f%%'%(percentViolation,percentViolation2),
    #         fontsize=fontsizeLegend,va='top')
    #'VerticalAlignment','top','HorizontalAlignment','left','FontSize',FontSizeAxes);
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    plt.xlabel('Interspike interval (ms)')
    ax.set_yticks(plt.ylim())
    extraplots.set_ticks_fontsize(ax,fontsize)
    return (hp,ISIhistogram,ISIbins)

def plot_events_in_time(timeStamps,nBins=50,fontsize=8):
    '''
    Plot histogram of inter-spike interval (in msec, log scale)

    Parameters
    ----------
    timeStamps : array (float in sec)
    '''
    ax = plt.gca()
    timeBinEdges = np.linspace(timeStamps[0],timeStamps[-1],nBins) # in microsec
    # FIXME: Limits depend on the time of the first spike (not of recording)
    (nEvents,binEdges) = np.histogram(timeStamps,bins=timeBinEdges)
    hp, = plt.plot((binEdges-timeStamps[0])/60.0, np.r_[nEvents,0], drawstyle='steps-post')
    plt.setp(hp,lw=1,color='k')
    plt.xlabel('Time (min)')
    plt.axis('tight')
    ax.set_yticks(plt.ylim())
    extraplots.boxoff(ax)
    extraplots.set_ticks_fontsize(ax,fontsize)
    return hp

def plot_waveforms(waveforms, ntraces=40, fontsize=8):
    """
    Plot waveforms given array of shape (nSpikes, nChannels, nSamplesPerSpike)

    The average waveform is over the randomly-selected spikes, and not all of the spikes.
    """
    (nSpikes, nChannels, nSamplesPerSpike) = waveforms.shape
    spikesToPlot = np.random.randint(nSpikes,size=ntraces)
    alignedWaveforms = align_waveforms(waveforms[spikesToPlot,:,:])

    meanWaveforms = np.mean(alignedWaveforms,axis=0)
    scalebarSize = abs(meanWaveforms.min())

    xRange = np.arange(nSamplesPerSpike)

    allWaves = []
    meanWaves = []

    for indc in range(nChannels):
        newXrange = xRange+indc*(nSamplesPerSpike+2)
        wavesToPlot = alignedWaveforms[:,indc,:].T
        wave = plt.plot(newXrange,wavesToPlot,color='k',lw=0.4,clip_on=False)
        # plt.hold(True)
        meanWave, = plt.plot(newXrange,meanWaveforms[indc,:],color='0.75',lw=1.5,clip_on=False)
        allWaves.append(wave)
        meanWaves.append(meanWave)
    scaleBar, = plt.plot(2*[-7],[0,-scalebarSize],color='0.5',lw=2)
    plt.text(-10,-scalebarSize/2,'{0:0.0f}uV'.format(np.round(scalebarSize)),
             ha='right',va='center',ma='center',fontsize=fontsize)
    # plt.hold(False)
    plt.axis('off')

    return allWaves, meanWaves, scaleBar


def align_waveforms(waveforms,peakPosition=8):
    '''
    Shift waveforms so that peaks align.
    Note that this should be applied to a SINGLE cluster, not the whole data set.
    '''
    meanWaveforms = np.mean(waveforms,axis=0)
    minEachChan = meanWaveforms.min(axis=1)
    minChan = minEachChan.argmin()
    minSampleEachSpike = waveforms[:,minChan,:].argmin(axis=1)
    wavesToShift = np.flatnonzero(minSampleEachSpike!=peakPosition)
    newWaveforms = waveforms.copy()
    for indw in wavesToShift:
        newWaveforms[indw,:,:] = np.roll(waveforms[indw,:,:],peakPosition-minSampleEachSpike[indw],axis=1)
    return(newWaveforms)

def plot_projections(waveforms,npoints=200):
    (nSpikes,nChannels,nSamplesPerSpike) = waveforms.shape
    spikesToPlot = np.random.randint(nSpikes,size=npoints)
    #peaks = np.max(waveforms[spikesToPlot,:,:],axis=2)
    peaks = -np.min(waveforms[spikesToPlot,:,:],axis=2)
    plt.plot(peaks[:,0],peaks[:,1],'.k',ms=0.5)
    plt.plot(-peaks[:,2],peaks[:,3],'.k',ms=0.5)
    plt.plot(0,0,'+',color='0.5')
    plt.axis('off')


class ClusterReportFromData(object):
    '''
    Need to finish reports when more than nrows<clusters.
    '''
    def __init__(self,timestamps,samples,clusters,outputDir=None,filename=None,showfig=True,figtitle='',nrows=12):
        self.timestamps = timestamps
        self.samples = samples
        self.clusters = clusters
        self.nSpikes = 0
        self.clustersList = []
        self.nClusters = 0
        self.spikesEachCluster = [] # Bool
        #self.fig = plt.figure(fignum)
        self.fig = None
        self.nRows = nrows
        self.set_parameters() # From dataTT
        self.nPages = 0
        self.figTitle = figtitle

        self.plot_report(showfig=showfig)
        if outputDir is not None:
            self.save_report(outputDir,filename)
    def set_parameters(self):
        self.nSpikes = len(self.timestamps)
        self.clustersList = np.unique(self.clusters)
        self.nClusters = len(self.clustersList)
        self.find_spikes_each_cluster()
        self.nPages = self.nClusters//(self.nRows+1)+1
    def __str__(self):
        return '%d clusters'%(self.nClusters)
    def find_spikes_each_cluster(self):
        self.spikesEachCluster = np.empty((self.nClusters,self.nSpikes),dtype=bool)
        for indc,clusterID in enumerate(self.clustersList):
            self.spikesEachCluster[indc,:] = (self.clusters==clusterID)
    def plot_report(self,showfig=False):
        print('Plotting report...')
        #plt.figure(self.fig)
        self.fig = plt.gcf()
        self.fig.clf()
        self.fig.set_facecolor('w')
        nCols = 3
        nRows = self.nRows
        #for indc,clusterID in enumerate(self.clustersList[:3]):
        for indc,clusterID in enumerate(self.clustersList):
            #print('Preparing cluster %d'%clusterID)
            if (indc+1)>self.nRows:
                print('WARNING! This cluster was ignore (more clusters than rows)')
                continue
            tsThisCluster = self.timestamps[self.spikesEachCluster[indc,:]]
            wavesThisCluster = self.samples[self.spikesEachCluster[indc,:],:,:]
            # -- Plot ISI histogram --
            plt.subplot(self.nRows,nCols,indc*nCols+1)
            plot_isi_loghist(tsThisCluster)
            if indc<(self.nClusters-1): #indc<2:#
                plt.xlabel('')
                plt.gca().set_xticklabels('')
            plt.ylabel('c%d'%clusterID,rotation=0,va='center',ha='center')
            # -- Plot events in time --
            plt.subplot(2*self.nRows,nCols,2*(indc*nCols)+6)
            plot_events_in_time(tsThisCluster)
            if indc<(self.nClusters-1): #indc<2:#
                plt.xlabel('')
                plt.gca().set_xticklabels('')
            # -- Plot projections --
            plt.subplot(2*self.nRows,nCols,2*(indc*nCols)+3)
            plot_projections(wavesThisCluster)
            # -- Plot waveforms --
            plt.subplot(self.nRows,nCols,indc*nCols+2)
            plot_waveforms(wavesThisCluster)
        #figTitle = self.get_title()
        plt.figtext(0.5,0.92, self.figTitle,ha='center',fontweight='bold',fontsize=10)
        if showfig:
            #plt.draw()
            plt.show()
    def get_title(self):
        return ''
    def get_default_filename(self,figformat):
        return 'clusterReport.%s'%(figformat)
    def save_report(self,outputdir,filename=None,figformat=None):
        # -- Create output directory --
        if not os.path.exists(outputdir):
            print('Creating clusters directory: %s'%(outputdir))
            os.makedirs(outputdir)
        self.fig.set_size_inches((8.5,11))
        if figformat is None:
            figformat = 'png' #'png' #'pdf' #'svg'
        if filename is None:
            filename = self.get_default_filename(figformat)
        fullFileName = os.path.join(outputdir,filename)
        print('Saving figure to %s'%fullFileName)
        self.fig.savefig(fullFileName,format=figformat)
        #plt.close(self.fig)
        ###def closefig(self):


#NOTE: We never use this in jaralab
class ClusterReportTetrode(ClusterReportFromData):
    def __init__(self,animalName,ephysSession,tetrode,outputDir=None,showfig=False,
                 figtitle=None,nrows=12):
        self.animalName = animalName
        self.ephysSession = ephysSession
        self.tetrode = tetrode
        self.dataDir = ''
        self.clustersFile = ''
        self.tetrodeFile = ''
        #self.dataTT = []

        if figtitle is None:
            self.figTitle = self.dataDir+' (T%d)'%self.tetrode  #tetrodeFile
        else:
            self.figTitle = figtitle
        self.load_data()
        super(ClusterReportTetrode, self).__init__(self.dataTT,outputDir=outputDir,
                                                   showfig=showfig,figtitle=self.figTitle,
                                                   nrows=nrows)
    def load_data(self):
        self.dataDir = os.path.join(settings.EPHYS_PATH,'%s/%s/'%(self.animalName,self.ephysSession))
        clustersDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(self.animalName,self.ephysSession))
        self.tetrodeFile = os.path.join(self.dataDir,'TT%d.ntt'%self.tetrode)
        print('Loading data %s'%(self.tetrodeFile))
        dataTT = loadneuralynx.DataTetrode(self.tetrodeFile,readWaves=True)
        #dataTT.timestamps = dataTT.timestamps.astype(np.float64)*1e-6  # in sec
        ### The following line is not needed anymore (not done when loading data)
        #dataTT.samples = dataTT.samples.reshape((N_CHANNELS,SAMPLES_PER_SPIKE,-1),order='F')
        # -- Load clusters --
        self.clustersFile = os.path.join(clustersDir,'TT%d.clu.1'%self.tetrode)
        dataTT.set_clusters(self.clustersFile)
        self.dataTT = dataTT
        #def get_title(self):
        #return self.dataDir+' (T%d)'%self.tetrode  #tetrodeFile
    def __str__(self):
        return '%s  %s  T%d\n%d clusters'%(self.animalName,self.ephysSession,self.tetrode,self.nClusters)
    def get_default_filename(self,figformat):
        return '%s_%s_T%02d.%s'%(self.animalName,self.ephysSession,self.tetrode,figformat)

def save_all_reports(animalName,ephysSession,tetrodes,outputDir):
    if not os.path.exists(outputDir):
        print('Creating output directory: %s'%(outputDir))
        os.makedirs(outputDir)
    for onetetrode in tetrodes:
        sreport = ClusterReportTetrode(animalName,ephysSession,onetetrode)
        sreport.save_report(outputDir)

def merge_kk_clusters(animalName, ephysSession, tetrode, clustersToMerge):
    """
    Merge two clusters from a single ephys session.
    Args:
        clustersToMerge (list): list of integers indicating the two clusters to merge.
    NOTES:
    - This function creates a backup of the original .clu file.
    - This function does not regenerate the cluster report.
    """
    dataDir = os.path.join(settings.EPHYS_PATH, animalName, f'{ephysSession}_kk')
    fileName = f'Tetrode{tetrode}.clu.1'
    fullFileName = os.path.join(dataDir, fileName)
    backupFileName = os.path.join(dataDir, fileName+'.orig')
    if os.path.isfile(backupFileName):
        print(f'\nThe backup file already exists: {backupFileName}')
        answer = input('Are you sure you want to continue (no new backup will be created) [y/n]? ')
        if answer != 'y':
            return
    else:
        # --- Make backup of original cluster file ---
        print(f'Making backup to {backupFileName}')
        shutil.copy2(fullFileName,backupFileName)
    # --- Load cluster data, replace and resave ---
    clusterData = np.fromfile(fullFileName, dtype='int32', sep='\n')
    indFirstSpike = np.flatnonzero(clusterData==clustersToMerge[1])[0]
    clusterData[clusterData==clustersToMerge[1]] = clustersToMerge[0]
    clusterData[indFirstSpike] = clustersToMerge[1] # Keep the first spike so it's not empty
    clusterData.tofile(fullFileName, sep='\n', format='%d')
    print('Clusters {} and {} are now merged replacing cluster {}'.format(clustersToMerge[0],
        clustersToMerge[1],clustersToMerge[0]))

def OLD_merge_kk_clusters(animalName,ephysSession,tetrode,clustersToMerge,reportDir=None):
    dataDir = os.path.join(settings.EPHYS_PATH,'%s/%s_kk/'%(animalName,ephysSession))
    #reportDir = os.path.join(settings.EPHYS_PATH,'%s/%s_reportkk/'%(animalName,ephysSession))
    if reportDir is None:
        reportDir = os.path.join(settings.PROCESSED_REVERSAL_PATH,settings.CLUSTERS_REPORTS_DIR)
    fileName = 'Tetrode%d.clu.1'%(tetrode)
    fullFileName = os.path.join(dataDir,fileName)
    backupFileName = os.path.join(dataDir,fileName+'.orig')
    if os.path.isfile(backupFileName):
        print(f'\nThe backup file already exists: {backupFileName}')
        answer = input('Are you sure you want to continue (no new backup will be created) [y/n]? ')
        if answer != 'y':
            return
    else:
        # --- Make backup of original cluster file ---
        print('Making backup to %s'%backupFileName)
        os.system('rsync -a %s %s'%(fullFileName,backupFileName))
    # --- Load cluster data, replace and resave ---
    clusterData = np.fromfile(fullFileName,dtype='int32',sep='\n')
    #indNoiseSpike = np.flatnonzero(clusterData==1)[0]
    indFirstSpike = np.flatnonzero(clusterData==clustersToMerge[1])[0]
    clusterData[clusterData==clustersToMerge[1]] = clustersToMerge[0]
    #clusterData[indNoiseSpike] = clustersToMerge[1]
    clusterData[indFirstSpike] = clustersToMerge[1] # Keep the first spike so it's not empty
    clusterData.tofile(fullFileName,sep='\n',format='%d')
    print('Clusters {} and {} are now merged replacing cluster {}'.format(clustersToMerge[0],
        clustersToMerge[1],clustersToMerge[0]))
    # -- Create report --
    #print('Creating report in %s'%reportDir)
    #ClusterReportTetrode(animalName,ephysSession,tetrode,reportDir)


def estimate_spike_peaks(waveforms, srate, align=True, ninterp=200):
    '''
    This function calculates the peaks of the spike.
    The peaks of the action potential are: (1) capacitive, (2) Na+, (3) K+
    The function assumes Na+ peak is negative.

    waveforms: (numpy.array float) [nSpikes, nChannels, nSamples] Baseline of waveforms should zero.
    srate: (float) Sampling rate in samples/sec.
    align: (boolean) align spikes if True.
    ninterp: (int) number of samples to use in the interpolated waveform.

    Returns:
    (peakTimes, peakAmplitudes, averageWaveform)
    peakTimes and peakAmplitudes have 3 elements (one for each peak)
    '''
    from scipy.interpolate import interp1d
    if align:
        # FIXME: will this change waveforms outside this method?
        waveforms = align_waveforms(waveforms)
    avWaveforms = np.mean(waveforms,0)
    energyEachChannel = np.sum(np.abs(avWaveforms),1)
    maxChannel = np.argmax(energyEachChannel)
    spikeShape = avWaveforms[maxChannel,:]
    spikeShapeSD = np.std(waveforms[:,maxChannel,:],0)
    sampVals = np.arange(0,len(spikeShape)/srate,1/srate)

    interpFun = interp1d(sampVals, spikeShape, kind='cubic')
    interpSampVals = np.linspace(0, sampVals[-1], ninterp)
    interpSpikeShape = interpFun(interpSampVals)

    # -- Calculate the change in sign of slope (and pad to align to original vector)
    dsign = np.r_[0,np.diff(np.sign(np.diff(interpSpikeShape)))]

    peakNaSample = np.argmin(interpSpikeShape)
    peakNaTime = interpSampVals[peakNaSample]
    peakNaAmp = interpSpikeShape[peakNaSample]

    extremePointsPre = np.flatnonzero(dsign[0:peakNaSample])
    peakCapSample = extremePointsPre[-1] if len(extremePointsPre) else 0
    peakCapTime = interpSampVals[peakCapSample]
    peakCapAmp = interpSpikeShape[peakCapSample]

    extremePointsPost = np.flatnonzero(dsign[peakNaSample+1:])
    peakKSample = extremePointsPost[0]+peakNaSample+1 if len(extremePointsPost) else len(extremePointsPost)-1
    peakKTime = interpSampVals[peakKSample]
    peakKAmp = interpSpikeShape[peakKSample]

    peakTimes = [peakCapTime, peakNaTime, peakKTime]
    peakAmplitudes = [peakCapAmp, peakNaAmp, peakKAmp]
    return (peakTimes, peakAmplitudes, spikeShape, spikeShapeSD)


class MultipleSessionsToCluster(TetrodeToCluster):

    '''
    Cluster many ephys ephysSessions at the same time

    This class will compile the spikes from multiple ephysSessions into a single data structure,
    cluster the entire set of spikes at once, and then save the appropriate cluster files
    as if one had simply clustered a session on its own.
    '''

    def __init__(self, subject, ephysSessions, tetrode, clusterFolder, features=None):
        '''
        Args:
            subject (str): Name of the animal
            ephysSessions (list): List of ephys session directories to cluster together (format 'YYYY-MM-DD_HH-MM-SS')
            tetrode (int): The tetrode to cluster
            clusterFolder (str): An identifier used to name the directory that contains the clustering results.
                            Use something like 'exp0site1' or '{date}_{depth}'

        '''
        #To init the super I just use the first session. Will this mess me up?
        super(MultipleSessionsToCluster, self).__init__(subject, ephysSessions[0], tetrode, features)
        self.ephysSessions = ephysSessions
        self.clusterFolder = clusterFolder
        self.recordingNumber = np.array([])
        self.samples = None
        self.timestamps = None
        self.clusters = None
        self.nSpikes = None
        self.clusterFolder = clusterFolder
        self.clustersDir = os.path.join(settings.EPHYS_PATH,self.subject,self.clusterFolder)
        self.fetFilename = os.path.join(self.clustersDir,'Tetrode%d.fet.1'%self.tetrode)
        self.report = None
        self.reportFileName = '{0}.png'.format(self.tetrode)
        if features is None:
            self.featureNames = ['peak','valleyFirstHalf']
        self.nFeatures = len(self.featureNames)
        self.featureValues = None
        self.reportFileName = '{}_{}_Tetrode{}.png'.format(self.subject, self.clusterFolder, self.tetrode)

    def load_waveforms(self):
        self.nSpikes = 0
        for ind, session in enumerate(self.ephysSessions):
            if session: #This is a fix for when some ephysSessions are 'None'
                ephysDir = os.path.join(settings.EPHYS_PATH, self.subject, session)
                spikeFile = os.path.join(ephysDir, 'Tetrode{0}.spikes'.format(self.tetrode))
                dataSpkObj = loadopenephys.DataSpikes(spikeFile)
                self.nSpikes += dataSpkObj.nRecords
                try:
                    numSpikes = dataSpkObj.nRecords
                    #Add the ind to a vector of zeros, indicates which recording this is from.
                    sessionVector = np.zeros(numSpikes)+ind
                    samplesThisSession = dataSpkObj.samples.astype(float)-2**15# FIXME: this is specific to OpenEphys
                    samplesThisSession = (1000.0/dataSpkObj.gain[0,0]) * samplesThisSession
                    timestampsThisSession = dataSpkObj.timestamps/dataSpkObj.samplingRate
                except AttributeError:
                    numSpikes = 0
                    samplesThisSession = None
                    timestampsThisSession = None
                #Set the values when working with the first non-empty session, then append for the other ephysSessions.
                if numSpikes != 0:
                    if self.samples is None:
                        self.samples = samplesThisSession
                        self.timestamps = timestampsThisSession
                        self.recordingNumber = sessionVector
                    else:
                        self.samples = np.concatenate([self.samples, samplesThisSession])
                        # Check to see if next session ts[0] is lower than self.timestamps[-1]
                        # If so, add self.timestamps[-1] to all new timestamps before concat
                        if timestampsThisSession[0]<self.timestamps[-1]:
                            timestampsThisSession = timestampsThisSession + self.timestamps[-1]
                        self.timestamps = np.concatenate([self.timestamps, timestampsThisSession])
                        self.recordingNumber = np.concatenate([self.recordingNumber, sessionVector])

    #TODO: Finish this
    def sanitize_timestamps(self):
        '''
        If timestamps are not sequential, there will be problems plotting time hists and isi hists.
        This function forces timestamps to be sequential. It does this by detecting negative isi vals
        and shifting all timestamps after this up by the value of the last timestamp.
        '''
        pass

    def create_multisession_fet_files(self):
        if not os.path.exists(self.clustersDir):
            print('Creating clusters directory: %s'%(self.clustersDir))
            os.makedirs(self.clustersDir)
        if self.samples is None:
            self.load_all_waveforms()
        self.featureValues = calculate_features(self.samples,self.featureNames)
        write_fet_file(self.fetFilename, self.featureValues)

    def set_clusters_from_file(self):
        clusterFile = os.path.join(self.clustersDir,'Tetrode%d.clu.1'%self.tetrode)
        self.clusters = np.fromfile(clusterFile,dtype='int32',sep=' ')[1:]

    def save_single_session_clu_files(self):
        '''
        Use the stored cluster and session information to write an individual clu file for each session.
        This will make it easier for us to go back and work with the data later. There is also the option
        to copy over the multisession cluster report to each directory that was included in the clustering.
        '''
        if self.clusters is None:
            self.set_clusters_from_file()
        clusters = self.clusters
        recordingNumber = self.recordingNumber
        ephysSessions = self.ephysSessions
        nClusters = len(np.unique(clusters))
        for indSession, session in enumerate(self.ephysSessions):
            #Make the cluster file directory for this session if it does not already exist
            sessionClusterDir = os.path.join(settings.EPHYS_PATH,self.subject,session+'_kk')
            if not os.path.exists(sessionClusterDir):
                print('Creating clusters directory: %s'%(sessionClusterDir))
                os.makedirs(sessionClusterDir)
            sessionClusterFile = os.path.join(sessionClusterDir,'Tetrode{}.clu.1'.format(self.tetrode))
            fid = open(sessionClusterFile,'w')
            fid.write('{0}\n'.format(nClusters))
            clusterNumsThisSession = self.clusters[self.recordingNumber == indSession]
            print("Writing .clu.1 file for session {}".format(session))
            for cn in clusterNumsThisSession:
                fid.write('{0}\n'.format(cn))
            fid.close()

class ClusterInforec(object):

    def __init__(self, inforecPath):
        '''
        Class for clustering sites from inforec files
        Args:
            inforecPath (str): The path to the inforec file
        '''

        self.filepath = inforecPath
        self.inforec = self.load_inforec()

    def load_inforec(self):
        inforec = imp.load_source('module.name', self.filepath)
        #FIXME: This produces a RuntimeWarning (parent module 'module' not found...)
        return inforec

    def process_tetrode(self, experiment, site, tetrode,
                        saveSingleSessionCluFiles=True,
                        minClusters=3,
                        maxClusters=6,
                        maxPossibleClusters=6,
                        recluster=True):
        '''
        Cluster a single tetrode from a site.
        Args:
            experiment (int): Index of experiment in inforec to use
            site (int): Index of site in experiment to use
            tetrode (int): Tetrode number to cluster (starts from 1)
            saveSingleSessionCluFiles (bool): Whether to save clu files for individual sessions
            minClusters (int): Minimum number of clusters for KK to find
            maxClusters (int): Max clusters for KK to find
            maxPossibleClusters (int): Max clusters for KK to find
            recluster (bool): Whether to recluster the site if clustering has been done already
        '''

        siteObj = self.inforec.experiments[experiment].sites[site]
        #clusterFolder = 'exp{}site{}'.format(experiment, site)
        clusterFolder = siteObj.clusterFolder
        oneTT = cluster_many_sessions(siteObj.subject,
                                        siteObj.session_ephys_dirs(),
                                        tetrode,
                                        clusterFolder,
                                        saveSingleSessionCluFiles=saveSingleSessionCluFiles,
                                        minClusters=minClusters,
                                        maxClusters=maxClusters,
                                        maxPossibleClusters=maxPossibleClusters,
                                        recluster=recluster)
        return oneTT

    def process_site(self, experiment, site, **kwargs):
        '''
        For available kwargs, see help(process_tetrode)
        '''
        siteObj = self.inforec.experiments[experiment].sites[site]
        for tetrode in siteObj.tetrodes:
            self.process_tetrode(experiment, site, tetrode, **kwargs)

    def process_all_sites(self, indExperiment, **kwargs):
        '''
        For available kwargs, see help(process_tetrode)
        '''
        experiment = self.inforec.experiments[indExperiment]
        for indSite, site in enumerate(experiment.sites):
            self.process_site(indExperiment, indSite, **kwargs)

    def process_all_experiments(self, **kwargs):
        '''
        For available kwargs, see help(process_tetrode)
        '''
        for indExperiment, _ in enumerate(self.inforec.experiments):
            self.process_all_sites(indExperiment, **kwargs)

    def pretty_print_inforec(self, sites=True, sessions=False):
        message = []
        for indExperiment, experiment in enumerate(self.inforec.experiments):
            message.append('[{}]: {}'.format(indExperiment, experiment.pretty_print(sites=sites, sessions=sessions)))
        print(''.join(message))

    def find_tetrodes_with_no_spikes(self):
        message = []
        for indExperiment, experiment in enumerate(self.inforec.experiments):
            for indSite, _ in enumerate(experiment.sites):
                siteObj = self.inforec.experiments[indExperiment].sites[indSite]
                #clusterFolder = 'exp{}site{}'.format(indExperiment, indSite)
                clusterFolder = siteObj.clusterFolder
                for tetrode in siteObj.tetrodes:
                    oneTT = MultipleSessionsToCluster(siteObj.subject,
                                                    siteObj.session_ephys_dirs(),
                                                    tetrode,
                                                    clusterFolder)
                    oneTT.load_waveforms()
                    if oneTT.timestamps is None:
                        message.append('{}_tetrode{}'.format(clusterFolder, tetrode))

        print('\n'.join(message))

def cluster_many_sessions(subject, sessions,
                          tetrode, clusterFolder,
                          saveSingleSessionCluFiles=True,
                          minClusters=10,
                          maxClusters=12,
                          maxPossibleClusters=12,
                          recluster=False):
    '''
    Run clustering for many ephys sessions
    Args:
        subject (str): Name of subject
        sessions (list): List of session directories (e.g. ['2016-01-01_12-12-12', etc.])
        tetrode (int): Tetrode number to cluster (starts from 1)
        clusterFolder (str): A unique identifier for the multisession clustering (usually 'multisession_date_depth')
        saveSingleSessionCluFiles (bool): Whether to save clu files for individual sessions
        minClusters (int): Minimum number of clusters for KK to find
        maxClusters (int): Max clusters for KK to find
        maxPossibleClusters (int): Max clusters for KK to find
        recluster (bool): Whether to recluster the site if clustering has been done already
    Returns:
        saves a clusterStats file with the following attributes:
            clusterPeakAmplitudes: an array of shape (nClusters, 3) with amps of cap peak, Na peak, K peak
    '''

    oneTT = MultipleSessionsToCluster(subject,
                                      sessions,
                                      tetrode,
                                      clusterFolder)
    oneTT.load_waveforms()

    if oneTT.nSpikes == 0:
        raise ValueError('This tetrode has no spikes. Please remove it.')

    clusterFile = os.path.join(oneTT.clustersDir,
                            'Tetrode%d.clu.1'%oneTT.tetrode)
    if os.path.isfile(clusterFile) and not recluster:
        oneTT.set_clusters_from_file()
    else:
        oneTT.create_fet_files()
        oneTT.run_clustering(minClusters, maxClusters, maxPossibleClusters)
        oneTT.set_clusters_from_file()
        oneTT.save_report()
    if saveSingleSessionCluFiles:
        oneTT.save_single_session_clu_files()

    # -- Save cluster stats --

    #Init empty arrays
    statsFn = 'Tetrode{}_stats.npz'.format(tetrode)
    outputFullPath = os.path.join(oneTT.clustersDir, statsFn)
    uniqueClusters = np.unique(oneTT.clusters)
    isiViolations = np.empty(len(uniqueClusters))
    clusters = np.empty(len(uniqueClusters), dtype=int) #INT
    nSpikes = np.empty(len(uniqueClusters), dtype=int) #INT
    clusterQuality = np.empty(len(uniqueClusters))
    nSamples = 40
    nChannels = 4
    clusterSpikeShape = np.empty((len(uniqueClusters), nSamples))
    clusterSpikeSD = np.empty((len(uniqueClusters), nSamples))
    clusterPeakTimes = np.empty((len(uniqueClusters), 3))
    clusterPeakAmplitudes = np.empty((len(uniqueClusters), 3))

    #Fill in measurements for each cluster
    for indc, cluster in enumerate(uniqueClusters):
        clusters[indc] = cluster
        clusterTimestamps = oneTT.timestamps[oneTT.clusters==cluster]
        clusterWaves = oneTT.samples[oneTT.clusters==cluster]
        clusterISIviolations = calculate_ISI_violations(clusterTimestamps)
        clusterNspikes = len(clusterTimestamps)
        isiViolations[indc] = clusterISIviolations
        nSpikes[indc] = clusterNspikes
        srate=30000.0
        (peakTimes, peakAmplitudes, spikeShape, spikeShapeSD) = estimate_spike_peaks(clusterWaves,srate)
        clusterSpikeShape[indc, :] = spikeShape
        clusterSpikeSD[indc, :] = spikeShapeSD
        clusterPeakTimes[indc, :] = peakTimes
        clusterPeakAmplitudes[indc, :] = peakAmplitudes

    print("Saving tetrode stats to {}".format(outputFullPath))
    np.savez(outputFullPath,
             ephysSessions=oneTT.ephysSessions,
             clusters=clusters,
             subject=oneTT.subject,
             isiViolations=isiViolations,
             nSpikes=nSpikes,
             featureNames=oneTT.featureNames,
             minClusters=minClusters,
             maxClusters=maxClusters,
             maxPossibleClusters=maxPossibleClusters,
             clusterPeakAmplitudes=clusterPeakAmplitudes,
             clusterPeakTimes=clusterPeakTimes,
             clusterSpikeShape=clusterSpikeShape,
             clusterSpikeSD=clusterSpikeSD)
    return oneTT

def calculate_ISI_violations(timestamps, threshold=2e-3):
    '''
    Calculate the percentage of ISIs that are smaller than some threshold
    Args:
        timestamps (array): spike timestamps (in SECONDS if you want to use default threshold)
        threshold (float): threshold for calling an ISI a violation
    Returns:
        isiViolations (float): fraction of ISIs that were smaller than the threshold
    '''
    ISI = np.diff(timestamps)
    if len(ISI)==0:  # Hack in case there is only one spike
        ISI = np.array(10)
    isiViolations = np.mean(ISI<threshold) # Assumes ISI in usec
    return isiViolations

def distance_to_centroid(featureMat):
    '''
    Mahalanobis distance:  d = sqrt ( (x-u)T * invCov * (x-u) )

    Args:
        featureMat (np.array): size (nSamples, nDim)
    Returns:
        dMahalanobis: Mahalanobis distance from each point to cluster center
    '''
    nPoints, nDim = featureMat.shape
    points = featureMat.T
    pMean = points.mean(axis=1)
    zPoints = points-pMean[:,np.newaxis]
    pCov = np.cov(zPoints)
    pInvCov = np.linalg.inv(pCov)
    # -- Calculate distance from each point to origin --
    dMahalanobis = np.empty(points.shape[1])
    for ind in range(nPoints):
        zPoint = zPoints[:,ind]
        term2 = np.dot(pInvCov, zPoint)
        term1 = np.dot(zPoint.T, term2)
        dMahalanobis[ind] = np.sqrt(term1)
    return dMahalanobis


def rescue_clusters(celldb, isiThreshold=0.02):
    '''
    Cleans clusters by removing spikes that are very different from the average spike.
    This reduces the ISI violations.

    The function takes each cluster from the database with ISI violations
    greater than a threshold. For each of these clusters, it sequentially
    removes the spikes farthest away from the centroid until ISI violations
    fall below the threshold.

    Args:
        celldb (pandas.DataFrame): created by celldatabase.py
        isiThreshold (float): maximum ISI

    This function doesn't return anything, but it creates new .clu files in the
    same folder as the originals, using the name 'Tetrode{}.clu.modified'

    FIXME: this function is not very clean because of a few reasons:
    - It imports new packages
    - It requires knowledge of the database structure.
    '''
    from sklearn import neighbors
    from jaratoolbox import ephyscore

    cellsToRescue = celldb.query('isiViolations>@isiThreshold')
    for indRow, dbRow in cellsToRescue.iterrows():
        cell = ephyscore.Cell(dbRow)
        print(dbRow['subject'], dbRow['date'], dbRow['pdepth'])
        timestamps, samples, recordingNumber = cell.load_all_spikedata()
        tetrode = dbRow['egroup']
        cluster = dbRow['cluster']

        #isiViolations = spikesorting.calculate_ISI_violations(timestamps)
        isiViolations = dbRow['isiViolations']
        print("isi violations: %{}".format(isiViolations*100))
        print("nSpikes: {}".format(len(timestamps)))
        featuresToUse = ['peakFirstHalf', 'valleyFirstHalf', 'energy']
        if len(timestamps)!=0:
            featuresMat = calculate_features(samples, featuresToUse)

            #To sort by nearest-neighbor distance
            print("Calculating NN distance")
            tic = time.time()
            #This will use all the processors
            nbrs = neighbors.NearestNeighbors(n_neighbors=2, algorithm='auto', n_jobs=-1).fit(featuresMat)
            distances, indices = nbrs.kneighbors(featuresMat)
            toc = time.time()
            elapsed = toc-tic
            print("NN done, elapsed time: {}".format(elapsed/60.))
            sortArray = np.argsort(distances[:,1]) #Take second neighbor distance because first is self (0)

            #To sort by mahalanobis distance to the cluster centroid
            # centroid = featuresMat.mean(axis=0)

            spikesToRemove = 0
            thisISIviolation = isiViolations #The isi violations including all the spikes
            jumpBy = int(len(timestamps)*0.01) #Jump by 1% of spikes each time
            if jumpBy == 0:
                jumpBy = 1 #remove at least 1 spike
            while thisISIviolation>0.02:
                spikesToRemove+=jumpBy
                #We start to throw spikes at the end of the sort array away
                includeBool = sortArray < (len(sortArray)-spikesToRemove)
                # timestampsToInclude = sortedTimestamps[:-1*spikesToRemove]
                timestampsToInclude = timestamps[includeBool]
                thisISIviolation = calculate_ISI_violations(np.sort(timestampsToInclude))
                print("Removing {} spikes, ISI violations: {}".format(spikesToRemove, thisISIviolation))
            print("Final included spikes: {} out of {}".format(len(timestampsToInclude), len(timestamps)))

            #The inds of all the spikes that get to stay (have to have a low number in sort array)
            #Sort array is in chronological order, so this include bool array is also chronological
            # includeBool = sortArray < (len(sortArray)-spikesToRemove)

            try:
                for thisRecordingNum in np.unique(recordingNumber):
                    #Which spikes in the total come from this recording
                    indsThisRecording = np.flatnonzero(recordingNumber == thisRecordingNum)
                    #What are the values in includeBool for those inds?
                    includeThisRecording = includeBool[indsThisRecording]

                    #load the .clu file
                    #Need the recording info
                    subject = cell.dbRow['subject']
                    date = cell.dbRow['date']
                    ephysTimeThisRecording = cell.dbRow['ephysTime'][thisRecordingNum]
                    clusterDir = "{}_kk".format("_".join([date, ephysTimeThisRecording]))
                    clusterFullPath = os.path.join(settings.EPHYS_PATH, subject, clusterDir)
                    clusterFile = os.path.join(clusterFullPath,'Tetrode{}.clu.1'.format(tetrode))

                    allClustersThisTetrode = np.fromfile(clusterFile,dtype='int32',sep=' ')[1:]

                    nClusters = len(np.unique(allClustersThisTetrode))

                    #The inds of the spikes from the cluster we are working on
                    indsThisCluster = np.flatnonzero(allClustersThisTetrode == cluster)

                    #For each spike from this cluster we have a bool value to include it or not
                    assert len(indsThisCluster) == len(includeThisRecording)

                    #For every spike in the cluster, we determine whether to keep or remove
                    for indIter, indThisSpike in enumerate(indsThisCluster):
                        includeThisSpike = includeThisRecording[indIter]
                        if includeThisSpike == 0: #If we remove, just set the value in allClustersThisTetrode to 0
                            allClustersThisTetrode[indThisSpike] = 0

                    #Then just re-save the allClustersThisTetrode as a modified clu file
                    modifiedClusterFile = os.path.join(clusterFullPath,'Tetrode{}.clu.modified'.format(tetrode))

                    # FIXME: Make sure that adding cluster 0 does not mess up creating databases or
                    #        other processes where we need to read the clu file
                    fid = open(modifiedClusterFile,'w')
                    #We added a new garbage cluster (0)
                    fid.write('{0}\n'.format(nClusters+1))
                    print("Writing .clu.modified file for session {}".format(ephysTimeThisRecording))
                    for cn in allClustersThisTetrode:
                        fid.write('{0}\n'.format(cn))
                    fid.close()

                    #Save the new ISI violation
                    celldb.loc[indRow, 'modifiedISI'] = thisISIviolation

            except:
                print("Could not save modified .clu files")

    return celldb




if __name__ == "__main__":
    CASE = 4
    if CASE==1:
        animalName   = 'saja125'
        ephysSession = '2012-01-31_14-37-44'
        tetrode = 6
        sreport = ClusterReportTetrode(animalName,ephysSession,tetrode,'/tmp/reports')
        #sreport.save_report('/tmp/reports/')
        #sreport.closefig()
    elif CASE==1.2:
        animalName   = 'saja129'
        ephysSession = '2012-08-19_14-03-17'
        tetrode = 6
        sreport = ClusterReportTetrode(animalName,ephysSession,tetrode,'/tmp/reports',nrows=24)
        #sreport.save_report('/tmp/reports/')
        #sreport.closefig()
    elif CASE==1.3:
        oneTT = TetrodeToCluster('saja000','2011-04-04_11-54-29',8)
        oneTT.load_waveforms()
        oneTT.run_clustering()
    elif CASE==2:
        animalName   = 'saja125'
        ephysSession = '2012-04-23_16-10-15'
        #save_all_reports(animalName,ephysSession,np.arange(1,8+1),'/var/data/neuralynx/saja125_processed/cluster_reports')
        save_all_reports(animalName,ephysSession,[2],'/tmp/reports')
    elif CASE==3:
        animalName   = 'saja125'
        ephysSession = '2012-04-23_16-10-15'
        tetrode = 2
        #merge_kk_clusters(animalName,ephysSession,tetrode,[2,5],reportDir='/tmp/reports')
        #merge_kk_clusters(animalName,ephysSession,tetrode,[2,10],reportDir='/tmp/reports')
    elif CASE==4:
        '''Test SessionToCluster (which runs the whole moving data and clustering remotely '''
        animalName   = 'saja000'
        ephysSession = '2011-04-04_11-54-29'
        tetrodes = [1,2]
        thisSession = SessionToCluster(animalName,ephysSession,tetrodes,'bard',
                                       'bard02','/home/bard/data/santiago/')
        #thisSession.transfer_data_to_server()
        #thisSession.run_clustering_remotely()
        #thisSession.create_fet_files()
        thisSession.delete_fet_files()

'''
animalName   = 'saja125'
ephysSession = '2012-02-07_14-18-20'
tetrode = 2
sreport = ClusterReportTetrode(animalName,ephysSession,tetrode,'/tmp/reports')
'''
