'''
2015-08-01 Nick Ponvert

This module will contain report plotting methods that act on entire sites

'''
def nick_lan_daily_report(site, siteName): #FIXME: This was copied, and needs to be updated. 
    '''
    Generate the reports for all of the sessions in this site. This is where we should interface with
    the multiunit clustering code, since all of the sessions that need to be clustered together have
    been defined at this point.

    FIXME: This method should be able to load some kind of report template perhaps, so that the
    types of reports we can make are not a limited. For instance, what happens when we just have
    rasters for a site and no tuning curve? Implementing this is a lower priority for now.

    Incorporated lan's code for plotting the cluster reports directly on the main report
    '''
    #FIXME: import another piece of code to do this?
    #FIXME: OR, break into two functions: one that will do the multisite clustering, and one that
    #knows the type of report that we want. The first one can probably be a method of MSTC, the other
    #should either live in extraplots or should go in someone's directory

    for tetrode in self.goodTetrodes:
        oneTT = cms2.MultipleSessionsToCluster(self.animalName, self.get_session_filenames(), tetrode, '{}_{}'.format(self.date, siteName))
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
        possibleClusters = np.unique(oneTT.clusters)

        ee = EphysExperiment(self.animalName, self.date, experimenter = self.experimenter)

        #Iterate through the clusters, making a new figure for each cluster.
        #for indClust, cluster in enumerate([3]):
        for indClust, cluster in enumerate(possibleClusters):


            mainRasterInds = self.get_session_inds_one_type(plotType='raster', report='main')
            mainRasterSessions = [self.get_session_filenames()[i] for i in mainRasterInds]
            mainRasterTypes = [self.get_session_types()[i] for i in mainRasterInds]

            mainTCinds = self.get_session_inds_one_type(plotType='tc_heatmap', report='main')
            mainTCsessions = [self.get_session_filenames()[i] for i in mainTCinds]

            mainTCbehavIDs = [self.get_session_behavIDs()[i] for i in mainTCinds]
            mainTCtypes = [self.get_session_types()[i] for i in mainTCinds]

            plt.figure() #The main report for this cluster/tetrode/session

            for indRaster, rasterSession in enumerate(mainRasterSessions):
                plt.subplot2grid((6, 6), (indRaster, 0), rowspan = 1, colspan = 3)
                ee.plot_session_raster(rasterSession, tetrode, cluster = cluster, replace = 1, ms=1)
                plt.ylabel('{}\n{}'.format(mainRasterTypes[indRaster], rasterSession.split('_')[1]), fontsize = 10)
                ax=plt.gca()
                extraplots.set_ticks_fontsize(ax,6)

            #We can only do one main TC for now.
            if len(mainTCsessions)>0:
                plt.subplot2grid((6, 6), (0, 3), rowspan = 3, colspan = 3)
                #tcIndex = site.get_session_types().index('tuningCurve')
                tcSession = mainTCsessions[0]
                tcBehavID = mainTCbehavIDs[0]
                ee.plot_session_tc_heatmap(tcSession, tetrode, tcBehavID, replace = 1, cluster = cluster)
                plt.title("{0}\nBehavFileID = '{1}'".format(tcSession, tcBehavID), fontsize = 10)

            nSpikes = len(oneTT.timestamps)
            nClusters = len(possibleClusters)
            #spikesEachCluster = np.empty((nClusters, nSpikes),dtype = bool)
            #if oneTT.clusters == None:
                #oneTT.set_clusters_from_file()
            #for indc, clusterID in enumerate (possibleClusters):
                #spikesEachCluster[indc, :] = (oneTT.clusters==clusterID)

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
            plt.close()


        plt.figure()
        oneTT.save_multisession_report()
        plt.close()
