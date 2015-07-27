import os
import csv
from pandas.io.parsers import read_csv
import numpy as np
import itertools
import matplotlib.pyplot as plt
from sklearn.metrics import jaccard_similarity_score
from sklearn import manifold

basePath = '/home/nick/src/jaratoolbox/test/nick/histology/'

anat030_str = read_csv(os.path.join(basePath, 'Anat030_str_red_left.csv'), header=None)
anat030_mgn = read_csv(os.path.join(basePath, 'Anat030_mgn_red_left.csv'), header=None)
anat024_str = read_csv(os.path.join(basePath, 'Anat024_str_red_left.csv'), header=None)
anat024_mgn = read_csv(os.path.join(basePath, 'Anat024_mgn_red_left.csv'), header=None)


anat030_str = np.reshape(np.array(anat030_str), [16, 3, 3]) 
anat024_str = np.reshape(np.array(anat024_str), [16, 3, 3])
print "FIXME: Hardcoded array shapes"

mouse_strs = [anat030_str, anat024_str]

anat030_mgn = np.reshape(np.array(anat030_mgn), [13, 3, 3])
anat024_mgn = np.reshape(np.array(anat024_mgn), [13, 3, 3])  

mouse_mgns = [anat030_mgn, anat024_mgn]


results_by_thal_vox = []
results_array = np.zeros((13, 3, 3, 16, 3, 3), dtype=bool)

# for indThalVox in [7]: #testing
for voxelInd in itertools.product(*map(xrange, np.shape(mouse_mgns[0]))): #Iterate through the thalamus voxels
    positives = np.zeros((16, 3, 3), dtype = bool)
    negatives = np.zeros((16, 3, 3), dtype = bool) #Init arrays to hold pos and neg. data 
    for indmouse, mgn in enumerate( mouse_mgns ): #Iterate through the mgn data
        if mgn[voxelInd]>0: #Positive injection
            positives = positives + (mouse_strs[indmouse]>0) #adding boolean arrays
        elif mgn[voxelInd]==0: #Negative Injection
            negatives = negatives + (mouse_strs[indmouse]>0)

        all_mouse_results = positives * np.logical_not(negatives) #take pos. list, flip to false any that are true in the negative list

       
    results_by_thal_vox.append(all_mouse_results)
    results_array[voxelInd[0], voxelInd[1], voxelInd[2], :, :, :] = all_mouse_results


ravel_array_shape = (len(anat030_mgn.ravel()), len(anat030_str.ravel()))
    
str_ap_heatmap = np.zeros(ravel_array_shape)
str_dv_heatmap = np.zeros(ravel_array_shape)
str_ml_heatmap = np.zeros(ravel_array_shape)


for indRavelMgn in range(len(anat030_mgn.ravel())):
    str_this_mgn = results_by_thal_vox[indRavelMgn]
    str_ap_heatmap[indRavelMgn, :] = str_this_mgn.ravel()


for indRavelMgn in range(len(anat030_mgn.ravel())):
    str_this_mgn = results_by_thal_vox[indRavelMgn]
    str_dv_heatmap[indRavelMgn, :] = np.swapaxes(str_this_mgn, 0, 1).ravel()


for indRavelMgn in range(len(anat030_mgn.ravel())):
    str_this_mgn = results_by_thal_vox[indRavelMgn]
    str_ml_heatmap[indRavelMgn, :] = np.swapaxes(str_this_mgn, 0, 2).ravel()


import sklearn
from sklearn import neighbors

#dice_sim = neighbors.DistanceMetric.get_metric('dice')
#
#similarities = dice_sim.pairwise(str_ap_heatmap)

#similarities = sklearn.metrics.pairwise.euclidean_distances(str_ap_heatmap)
similarities = sklearn.metrics.pairwise.pairwise_distances(str_ap_heatmap, metric='cosine')

seed = np.random.RandomState(seed=3)
mds = manifold.MDS(n_components=2, max_iter=3000, eps=1e-9, random_state=seed,
                   dissimilarity="precomputed", n_jobs=1)

pos = mds.fit(similarities).embedding_



#plt.subplot(3, 1, 1)
#plt.imshow(str_ap_heatmap, cmap = "Blues")
#
#plt.subplot(3, 1, 2)
#plt.imshow(str_dv_heatmap, cmap = "Blues")
#
#plt.subplot(3, 1, 3)
#plt.imshow(str_ml_heatmap, cmap = "Blues")
#plt.show()


##Testing
test_shape = (5, 4, 3)          # 5 slices, 4 D-V boxes, 3 M-L boxes


rav_len = len(np.zeros(test_shape).ravel())

test_array = np.reshape(np.array(range(rav_len)), test_shape)

ap_ravel = test_array.ravel()

dv_ravel = np.swapaxes(test_array, 0, 1).ravel()

ml_ravel = np.swapaxes(test_array, 0, 2).ravel()


###If we make an array from reshape(range())..., then we can swapaxes it and ravel it
#and we will have the indices to re-create that transform with (by raveling the data
#and slicing by the raveled indices. 


#thal_test_coords = [[2, 1, 1]]
##anat030 is positive at this location, anat024 is negative
#
#pos_array = np.ones((16, 3,3))
#neg_array = np.ones((16, 3,3))*-1
#
#anat030_filter = anat030_str>0
#anat024_filter = anat024_str>0
##pos_times_injection_anat030 = pos_array*anat030_filter
##neg_times_injection_anat024 = neg_array*anat024_filter
##pos_but_not_neg = pos_times_injection_anat030+neg_times_injection_anat024
##pos_but_not_neg = np.ones((16, 3, 3))*(pos_but_not_neg>0)
#
#final = anat030_filter*np.logical_not(anat024_filter)
#
