'''
2015-08-01 Nick Ponvert

This module will contain report plotting methods that act on entire sites

'''
from jaratoolbox.test.nick.ephysExperiments import clusterManySessions_v2 as cms2
reload(cms2)
from jaratoolbox.test.nick.database import dataloader
from jaratoolbox.test.nick.database import dataplotter
reload(dataplotter)
from jaratoolbox import extraplots
from jaratoolbox import spikesorting
import matplotlib.pyplot as plt
import numpy as np
import os

def cluster_site(site, siteName, tetrode, report=True): 
    oneTT = cms2.MultipleSessionsToCluster(site.animalName, site.get_session_ephys_filenames(), tetrode, '{}_{}'.format(site.date, siteName))
    oneTT.load_all_waveforms()

    #Do the clustering if necessary.
    clusterFile = os.path.join(oneTT.clustersDir,'Tetrode%d.clu.1'%oneTT.tetrode)
    if os.path.isfile(clusterFile):
        oneTT.set_clusters_from_file()
    else:
        oneTT.create_multisession_fet_files()
        oneTT.run_clustering()
        oneTT.set_clusters_from_file()

    oneTT.save_single_session_clu_files()

    if report:
        plt.clf()
        oneTT.save_multisession_report()

    return oneTT #This is a little bit lazy, it should really spit out some attributes not the whole object


def nick_lan_daily_report(site, siteName, mainRasterInds, mainTCind):
    '''

    '''

    loader = dataloader.DataLoader('offline', experimenter=site.experimenter)

    for tetrode in site.tetrodes:
        oneTT = cluster_site(site, siteName, tetrode)
        possibleClusters=np.unique(oneTT.clusters)


        #Iterate through the clusters, making a new figure for each cluster.
        #for indClust, cluster in enumerate([3]):
        for indClust, cluster in enumerate(possibleClusters):


            mainRasterEphysFilenames = [site.get_mouse_relative_ephys_filenames()[i] for i in mainRasterInds]
            mainRasterTypes = [site.get_session_types()[i] for i in mainRasterInds]
            if mainTCind:
                mainTCsession = site.get_mouse_relative_ephys_filenames()[mainTCind]
                mainTCbehavFilename = site.get_mouse_relative_behav_filenames()[mainTCind]
                mainTCtype = site.get_session_types()[mainTCind]
            else:
                mainTCsession=None

            # plt.figure() #The main report for this cluster/tetrode/session
            plt.clf()

            for indRaster, rasterSession in enumerate(mainRasterEphysFilenames):
                plt.subplot2grid((6, 6), (indRaster, 0), rowspan = 1, colspan = 3)

                rasterSpikes = loader.get_session_spikes(rasterSession, tetrode)
                spikeTimestamps = rasterSpikes.timestamps[rasterSpikes.clusters==cluster]

                rasterEvents = loader.get_session_events(rasterSession)
                eventOnsetTimes = loader.get_event_onset_times(rasterEvents)

                dataplotter.plot_raster(spikeTimestamps, eventOnsetTimes, ms=1)

                plt.ylabel('{}\n{}'.format(mainRasterTypes[indRaster], rasterSession.split('_')[1]), fontsize = 10)
                ax=plt.gca()
                extraplots.set_ticks_fontsize(ax,6) #Should this go in dataplotter?

            #We can only do one main TC for now.
            if mainTCsession:

                plt.subplot2grid((6, 6), (0, 3), rowspan = 3, colspan = 3)


                bdata = loader.get_session_behavior(mainTCbehavFilename)
                plotTitle = loader.get_session_filename(mainTCsession)
                eventData = loader.get_session_events(mainTCsession)
                spikeData = loader.get_session_spikes(mainTCsession, tetrode)

                spikeTimestamps = spikeData.timestamps[spikeData.clusters==cluster]

                eventOnsetTimes = loader.get_event_onset_times(eventData)

                freqEachTrial = bdata['currentFreq']
                intensityEachTrial = bdata['currentIntensity']

                possibleFreq = np.unique(freqEachTrial)
                possibleIntensity = np.unique(intensityEachTrial)

                xlabel='Frequency (kHz)'
                ylabel='Intensity (dB SPL)'

                # firstSortLabels = ["%.1f" % freq for freq in possibleFreq/1000.0]
                # secondSortLabels = ['{}'.format(inten) for inten in possibleIntensity]

                # dataplotter.two_axis_heatmap(spikeTimestamps,
                #                             eventOnsetTimes,
                #                             freqEachTrial,
                #                             intensityEachTrial,
                #                             firstSortLabels,
                #                             secondSortLabels,
                #                             xlabel,
                #                             ylabel,
                #                             plotTitle=plotTitle,
                #                             flipFirstAxis=False,
                #                             flipSecondAxis=True,
                #                             timeRange=[0, 0.1])

                freqLabels = ["%.1f" % freq for freq in possibleFreq/1000.0]
                intenLabels = ["%.1f" % inten for inten in possibleIntensity]

                dataplotter.two_axis_heatmap(spikeTimestamps,
                                            eventOnsetTimes,
                                            intensityEachTrial,
                                            freqEachTrial,
                                            intenLabels,
                                            freqLabels,
                                            xlabel,
                                            ylabel,
                                            plotTitle,
                                            flipFirstAxis=True,
                                            flipSecondAxis=False,
                                            timeRange=[0, 0.1])

                plt.title("{0}\n{1}".format(mainTCsession, mainTCbehavFilename), fontsize = 10)
                plt.show()


            nSpikes = len(oneTT.timestamps)
            nClusters = len(possibleClusters)

            tsThisCluster = oneTT.timestamps[oneTT.clusters==cluster]
            wavesThisCluster = oneTT.samples[oneTT.clusters==cluster]
            # -- Plot ISI histogram --
            plt.subplot2grid((6,6), (4,0), rowspan=1, colspan=3)
            spikesorting.plot_isi_loghist(tsThisCluster)
            plt.ylabel('c%d'%cluster,rotation=0,va='center',ha='center')
            plt.xlabel('')

            # -- Plot waveforms --
            plt.subplot2grid((6,6), (5,0), rowspan=1, colspan=3)
            spikesorting.plot_waveforms(wavesThisCluster)

            # -- Plot projections --
            plt.subplot2grid((6,6), (4,3), rowspan=1, colspan=3)
            spikesorting.plot_projections(wavesThisCluster)

            # -- Plot events in time --
            plt.subplot2grid((6,6), (5,3), rowspan=1, colspan=3)
            spikesorting.plot_events_in_time(tsThisCluster)

            plt.subplots_adjust(wspace = 0.7)
            fig_path = oneTT.clustersDir
            fig_name = 'TT{0}Cluster{1}.png'.format(tetrode, cluster)
            full_fig_path = os.path.join(fig_path, fig_name)
            print full_fig_path
            #plt.tight_layout()
            plt.savefig(full_fig_path, format = 'png')
            #plt.show()
            # plt.close()

def am_mod_report(site, siteName, amSessionInd):
    '''

    '''
    loader = dataloader.DataLoader('offline', experimenter=site.experimenter)

    for tetrode in site.tetrodes:
        oneTT = cluster_site(site, siteName, tetrode)
        possibleClusters=np.unique(oneTT.clusters)

        for indClust, cluster in enumerate(possibleClusters):


            amFilename = site.get_mouse_relative_ephys_filenames()[amSessionInd]
            amBehav = site.get_mouse_relative_behav_filenames()[amSessionInd]

            plt.clf()

            spikeData = loader.get_session_spikes(amFilename, tetrode, cluster=cluster)
            spikeTimes = spikeData.timestamps

            eventData = loader.get_session_events(amFilename)
            eventOnsetTimes = loader.get_event_onset_times(eventData)
            
            bdata = loader.get_session_behavior(amBehav)

            currentFreq = bdata['currentFreq']

            dataplotter.plot_raster(spikeTimes, eventOnsetTimes, sortArray=currentFreq)
            fig_path = oneTT.clustersDir
            fig_name = 'TT{0}Cluster{1}_Amp_Mod.png'.format(tetrode, cluster)
            full_fig_path = os.path.join(fig_path, fig_name)
            print full_fig_path
            plt.savefig(full_fig_path, format = 'png')