'''
Analyze the quality of clusters produced by spike-sorting
'''

import numpy as np
import matplotlib.pyplot as plt
from jaratoolbox import ephyscore
from jaratoolbox import spikesorting

def calculate_avg_waveforms(cellDB, wavesize=160):
    '''
    NOTE: This methods should look through sessions, not clusters.
          The idea is to compare clusters within a tetrode, and then across sessions
          but still within a tetrode.
    NOTE: This method is inefficient because it load the spikes file for each cluster.
    '''
    allWaveforms = np.empty((len(cellDB),wavesize))
    for indc,oneCell in enumerate(cellDB):
        print 'Estimating average waveform for {0}'.format(oneCell)
        ephysData = ephyscore.CellData(oneCell)
        waveforms = ephysData.spikes.samples.astype(float)-2**15 #This is specific to open Ephys
        waveforms = (1000.0/ephysData.spikes.gain[0,0]) * waveforms
        alignedWaveforms = spikesorting.align_waveforms(waveforms)
        meanWaveforms = np.mean(alignedWaveforms,axis=0)
        allWaveforms[indc,:] = meanWaveforms.flatten()
    return allWaveforms

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


def plot_correlation(ccSelf,ccAccross):
    nSessions = len(ccSelf)
    plt.clf()
    for inds in range(nSessions):
        plt.subplot2grid((2,nSessions),(0,inds))
        plt.imshow(ccSelf[inds],clim=[0,1], cmap='hot')
        plt.axis('image')
        #title('')
    for inds in range(nSessions-1):
        plt.subplot2grid((2,nSessions-1),(1,inds))
        plt.imshow(ccAccross[inds],clim=[0,1], cmap='hot')
        plt.axis('image')
    plt.colorbar()
    plt.draw()


if __name__=='__main__':
    ### Useful trick:   np.set_printoptions(linewidth=160)
    CASE = 0
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
        oneES = eSession(animalName='test089',
                         ephysSession = '2015-08-21_16-16-16',
                         clustersEachTetrode = {1:range(1,13),2:range(1,13),3:range(1,13),4:range(1,13),
                                                5:range(1,13),6:range(1,13),7:range(1,13),8:range(1,13)},
                         behavSession = '20150821a')
        cellDB.append_session(oneES)

        #awave = calculate_avg_waveforms(cellDB)

        #(ccSelf,ccAccross) = spikeshape_correlation([awave])
        #plot_correlation(ccSelf,ccAccross)

