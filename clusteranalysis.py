'''
Analyze the quality of clusters produced by spike-sorting
'''

'''
Useful trick:
np.set_printoptions(linewidth=160)
'''

import numpy as np

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


def OBSOLETE_spikeshape_correlation(waveforms1, waveforms2):
    '''
    Find the correlation between spikes shapes across sessions.
    Args:
        waveforms1 (np.array): waveforms for all clusters in one session
                               with size [nClusters,nSamples]
        waveforms2 (np.array): waveforms for all clusters in one session
                               with size [nClusters,nSamples]
    '''
    ccmat = row_corrcoeff(waveforms1,waveforms2)
    return ccmat


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
    for inds in range(len(waveforms)-1):
        ccSelf.append(row_corrcoeff(waveforms[inds],waveforms[inds]))
        ccAccross.append(row_corrcoeff(waveforms[inds],waveforms[inds+1]))
    ccSelf.append(row_corrcoeff(waveforms[inds+1],waveforms[inds+1]))
    return (ccSelf,ccAccross)


if __name__=='__main__':
    # -- Test ---
    nSamples = 40
    nClusters = 12
    basewave = np.sin(2*np.pi*np.linspace(0,2,nSamples))
    waveforms1 = basewave + 0.4*np.random.randn(nClusters,nSamples)
    waveforms2 = basewave + 0.4*np.random.randn(nClusters,nSamples)
    waveforms3 = basewave + 0.4*np.random.randn(nClusters,nSamples)

    listwaveforms = [waveforms1,waveforms2,waveforms3]
    #listwaveforms = [waveforms1,waveforms1,waveforms1]
    
    #cc = np.corrcoef(waveforms1,waveforms2)
    #cc = row_corrcoeff(waveforms1,waveforms2)
    (ccSelf,ccAccross) = spikeshape_correlation(listwaveforms)

    #print ccSelf
    #print ccAccross

    from pylab import *
    nSessions = len(listwaveforms)
    clf()
    for inds in range(nSessions):
        subplot2grid((2,nSessions),(0,inds))
        imshow(ccSelf[inds],clim=[0,1], cmap='hot')
        axis('image')
    for inds in range(nSessions-1):
        subplot2grid((2,nSessions-1),(1,inds))
        imshow(ccAccross[inds],clim=[0,1], cmap='hot')
        axis('image')
    colorbar()

    draw()
