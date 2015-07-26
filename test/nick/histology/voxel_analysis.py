import os
import csv
from pandas.io.parsers import read_csv
import numpy as np


basePath = '/home/nick/Desktop/'

anat030_str = read_csv(os.path.join(basePath, 'Anat030_str_red_left.csv'), header=None)
anat030_mgn = read_csv(os.path.join(basePath, 'Anat030_mgn_red_left.csv'), header=None)
anat024_str = read_csv(os.path.join(basePath, 'Anat024_str_red_left.csv'), header=None)
anat024_mgn = read_csv(os.path.join(basePath, 'Anat024_mgn_red_left.csv'), header=None)


anat030_str = np.reshape(np.array(anat030_str), [16, 3, 3])
anat030_mgn = np.reshape(np.array(anat030_mgn), [13, 3, 3])
anat024_str = np.reshape(np.array(anat024_str), [16, 3, 3])
anat024_mgn = np.reshape(np.array(anat024_mgn), [13, 3, 3])

thal_test_coords = [2, 1, 1]
#anat030 is positive at this location, anat024 is negative

pos_array = np.ones((16, 3,3))
neg_array = np.ones((16, 3,3))*-1

anat030_filter = anat030_str>0
anat024_filter = anat024_str>0
#pos_times_injection_anat030 = pos_array*anat030_filter
#neg_times_injection_anat024 = neg_array*anat024_filter
#pos_but_not_neg = pos_times_injection_anat030+neg_times_injection_anat024
#pos_but_not_neg = np.ones((16, 3, 3))*(pos_but_not_neg>0)

final = anat030_filter*np.logical_not(anat024_filter)
