from jaratoolbox import loadbehavior
from jaratoolbox import loadopenephys
import os
from matplotlib.mlab import PCA
from sklearn.mixture import GMM
from pylab import *
import matplotlib.pyplot as plt

'''
Computes PCA components for a group of spike waveforms and clusters them using a Gaussian Mixture Model. 
'''

__author__='Nick Ponvert'
__date__='2014-08-16'

GAIN = 5000.0

ephys_path = '/home/nick/data/ephys/hm4d002/cno_08-14'
ephys_session = os.listdir(ephys_path)[0]
tetrode = 3

# -- Read ephys data
ephys_file = os.path.join(ephys_path, ephys_session, 'Tetrode{0}.spikes'.format(tetrode))
spikes = loadopenephys.DataSpikes(ephys_file)

# -- take first channel only (for now)
ch0 = spikes.samples[:,0]
#ch0 = ((ch0 - 32768)/GAIN)*1000

# -- Compute PCs (weight vectors, %var, projected pts)
#results = PCA(ch0)


# -- New Attempt: use the concatenated traces from all four channels. 
conc=[]
for ind, channels in enumerate(spikes.samples):
    conc.append(concatenate(channels))

conc=array(conc)
results=PCA(conc)


threshold = 0.75  #threshold for proportion of variance described

comps_to_use=6 # FIXME: hardcoded number of comps to use,
               # commented code below can be used but need new colors (line 100)
figure()
plot(cumsum(results.fracs))  # scree plot
show()
'''
for comp, var in enumerate(cumsum(results.fracs)):
    if var > threshold:
        comps_to_use = comp+1
        break
'''
# -- Collect the points projected into the number of Pcs we want to use
X = results.Y[:, 0:comps_to_use]

# -- Initialize the GMM. Should we tell it to find a cluster for each comp?
g=GMM(n_components=comps_to_use)


# -- Fit the GMM with the data, and then predict the cluster for each data point. 
g.fit(X)
preds = g.predict(X)



case=5

if case==1:
    # Clustered points in the first two PCs
    plot(results.Y[:,0][preds==0], results.Y[:,1][preds==0], 'b.', ms=1)
    plot(results.Y[:,0][preds==1], results.Y[:,1][preds==1], 'r.', ms=1)

elif case==2:
    # First 100 waveforms of spikes from cluster 0
    for spike in ch0[preds==0][:100]:
        plot(spike, 'b-', alpha=0.1)

    # First 100 waveforms of spikes from cluster 1
    for spike in ch0[preds==1][:100]:
        plot(spike, 'r-', alpha=0.1)

elif case ==3:  #Plot the clusters 
    figure()
    for cluster_num in set(preds):
        #print cluster_num
        plot(results.Y[:,0][preds==cluster_num], results.Y[:,1][preds==cluster_num], '.', ms=1)
    show()

elif case == 4:  #Plot the waveforms for each cluster
    some_colors=['b', 'g', 'r', 'c', 'm', 'y', 'k']
    figure()
    for cluster_num in set(preds):
        subplot(max(preds)+1, 1, cluster_num+1)
        for sample in ch0[preds==cluster_num][:25]:
            plot((sample-32768)/GAIN*1000, '{0}-'.format(some_colors[cluster_num]), alpha=0.1)
    show()

elif case==5: #plot clusters and waveforms

    figure()
    ax2 = plt.subplot2grid((max(preds)+1,2), (0, 0), colspan=1, rowspan=max(preds)+1)
    for cluster_num in set(preds):
        #print cluster_num
        plot(results.Y[:,0][preds==cluster_num], results.Y[:,1][preds==cluster_num], '.', ms=1)
    xlabel('PC0')
    ylabel('PC1')
    #show()
    

    some_colors=['b', 'g', 'r', 'c', 'm', 'y', 'k']
    #figure()
    for cluster_num in set(preds):
        ax2 = plt.subplot2grid((max(preds)+1,2), (cluster_num, 1), colspan=1, rowspan=1)

        for sample in spikes.samples[preds==cluster_num][:100]:
            plot((concatenate(sample)-32768.00)/GAIN*1000.0, '{0}-'.format(some_colors[cluster_num]), alpha=0.1)


        '''
        for sample in ch0[preds==cluster_num][:25]:
            plot((sample-32768.00)/GAIN*1000.0, '{0}-'.format(some_colors[cluster_num]), alpha=0.1)
        '''

    show()


    


#cl1_samples=spikes.samples[cluster1]

#Approach:
#DONE: Take a spikes file and read it (loadopenephys.DataSpikes)
#DONE: Compute PCs, maybe for one channel at a time (matplotlib.mlab.PCA)
#DONE: Determine the optimal number of PCs to use (based on some threshold)
#DONE: Cluster the projected points (sklearn.mixture.GMM or Kmeans)
#DONE: Predict the cluster for each point
#DONE: Apply the cluster data to the original spike data

#TODO: Should I use more than ch0 for the original PCA?

#TODO: We will need to track spikes between multiple sessions. I see several ways that this could happen. 
# - We can sort each trial and then manually look for similarities in the sorted waveforms. This is a bad idea. 
# - Concatenate ALL of the data for the whole session and run it through the PCA and GMM, then seperate it back out (or have a vector of session numbers)
# - Do PCA on a subset of the data, train the GMM, and then use the fitted model to predict the cluster for all of the other observations. If this works, it would likely be the fastest way.
# - Concatenate all four channels together before we do PCA? This might help us if the small-magnitude portions of spikes on one channel look similar to noise but have large-magnitude portions on other channels. 



#TODO: Use santiago's cluster summary plotting routeines.
#TODO: CLuster CNO experiment data, plot time series per clustered spike
#    -Can we show the same spike across multiple experiments though? 
#        - Get all spike data for the entire experiment and cluster it #          all at the same time?

#???
#Profit



