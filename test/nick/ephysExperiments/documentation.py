'''
This file will contain an example showing how to use EphysExperiment to process data during an experiment
'''

import ephys_experiment_v3 as ee3
reload(ee3)

ex0624 = ee3.EphysExperiment('pinp003', '2015-06-24', experimenter = 'nick')

#ex0624.plot_array_raster('15-27-37', replace = 0, ms = 1, timeRange = [-0.5, 1.5])
#ex0624.plot_session_tc_heatmap('15-31-48', 6, 'a')


'''
TODO

Add tetrode labels to the array raster plot
also space in xlabel between time and seconds
sharex between the tetrodes

Pass spikes already aligned to the tc heatmap code, 
using the code to find trials each condition
add parameter for the timerange for the tc heatmap, 
which must also update the labels. 
labels for frequency and intensity, including units
also pass the clim param. 
also possibly a smart scale parameter? That would set the color limits intelligently?
use a diverging colormap with the zero point set at the baseline firing rate? 

Use the other raster plotting code to plot the sorted tuning curve rasters. 
these axes should be shared as well

it would be awesome if we could cluster quickly and tell whether the same unit is really 
responsive to the sound and the laser

move this to the repo as ephysexperiment

find a better name for RecordingDay - this will be the top class and have a method to add new sites

we also need a module name for this. 

The behavFileIdentifier needs to be well documented. Currently it relies on an EphysExperiment object

We need to specify the paradigm in the recording file


Are the event IDs for the laser and the sound the same eventID?


NEXT TIME: How are we going to interface with a database that stores cells for later?


Santiago:
Use rsync to automatically send the behavior data to jarahub when the user saves the data


'''
