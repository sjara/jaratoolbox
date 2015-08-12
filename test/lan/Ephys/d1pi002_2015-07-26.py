#Write into JSON database only cells with good amp (>=40uV), consistent firing throughout recording, good waveform, with either sound or laser response or both.

from jaratoolbox.test.nick.ephysExperiments import recordingday as rd
reload(rd)
from jaratoolbox.test.nick.ephysExperiments import ephys_experiment_v3 as ee3
reload(ee3)
import matplotlib.pyplot as plt
import os
from jaratoolbox import settings

sessionTypes = {'nb':'noiseBurst',
                'lp':'laserPulse',
                'lt':'laserTrain',
                'tc':'tuningCurve',
                'bf':'bestFreq',
                '3p':'3mWpulse',
                '1p':'1mWpulse'}
 
exp0726 = rd.Recording(animalName = 'd1pi002', date = '2015-07-26', experimenter = 'lan', paradigm='laser_tuning_curve')


site1 = exp0726.add_site(depth = 2702, goodTetrodes = [3])
site1.add_session('15-26-00', None, sessionTypes['nb'])  #amp = 0.45
site1.add_session('15-28-10', None, sessionTypes['lp']) #power=2.5mW
site1.add_session('15-29-48', None, sessionTypes['lt']) #power=2.5mW
site1.add_session('15-32-31', 'a', sessionTypes['tc'])
site1.add_session('15-47-57', 'b', sessionTypes['tc'])
site1.add_session('16-00-02', None, sessionTypes['3p'])
site1.add_session('16-01-34', None, sessionTypes['nb']) #comment='amp = 0.5'


site2 = exp0726.add_site(depth = 2872, goodTetrodes = [3])
site2.add_session('16-36-53', None, sessionTypes['lp'])  #comment='no response')
site2.add_session('16-37-53', None, sessionTypes['nb'])
site2.add_session('16-39-40', None, sessionTypes['lt'])  #comment='no response')
site2.add_session('16-42-14', 'c', sessionTypes['tc'])


site3 = exp0726.add_site(depth = 2936, goodTetrodes = [3, 4])
site3.add_session('16-57-55', None, sessionTypes['lp'])
site3.add_session('17-02-35', None, sessionTypes['lt'])
site3.add_session('17-05-19', None, sessionTypes['nb']) #comment='amp=0.5')
site3.add_session('17-07-37', None, sessionTypes['bf']) #comment='4freq from 15k-40kHz, 40-70dB')
site3.add_session('17-09-20', 'd', sessionTypes['tc'])

#cluster5 = site3.add_cluster(clusterNumber=5, tetrode=3, soundResponsive=True, laserPulseResponse=False, followsLaserTrain=False, comments='good cell')
#cluster4 = site3.add_cluster(clusterNumber=4, tetrode=6, soundResponsive=True, laserPulseResponse=False, followsLaserTrain=False, comments='good cell')


site4 = exp0726.add_site(depth = 3300, goodTetrodes = [3, 4])
site4.add_session('17-56-14', None, sessionTypes['lp'])
site4.add_session('17-57-56', None, sessionTypes['nb'])
site4.add_session('17-59-52', None, sessionTypes['lt'])
site4.add_session('18-01-59', 'e', sessionTypes['tc'])
site4.add_session('18-15-25', None, sessionTypes['bf']) # comment='4freq from 15k-30kHz @60dB')
#cluster4 = site4.add_cluster(clusterNumber=4, tetrode=3, soundResponsive=True, laserPulseResponse=False, followsLaserTrain=False, comments='good cell')
#cluster6 = site4.add_cluster(clusterNumber=6, tetrode=3, soundResponsive=True, laserPulseResponse=True, followsLaserTrain=True, comments='good cell')

site5 = exp0726.add_site(depth = 3357, goodTetrodes = [3, 4])
site5.add_session('18-22-41', None, sessionTypes['nb'])
site5.add_session('18-25-06', None, sessionTypes['lp'])
site5.add_session('18-27-48', None, sessionTypes['lt'])
site5.add_session('18-32-17', 'f', sessionTypes['tc'])
site5.add_session('18-44-29', None, sessionTypes['bf']) #comment='4freq from 15k-30kHz @60dB')
site5.add_session('18-46-11', None, sessionTypes['1p'])

#cluster11 = site5.add_cluster(clusterNumber=11, tetrode=3, soundResponsive=True, laserPulseResponse=False, followsLaserTrain=False, comments='good cell')
#cluster12 = site5.add_cluster(clusterNumber=12, tetrode=3, soundResponsive=True, laserPulseResponse=False, followsLaserTrain=False, comments='good cell')
#cluster2 = site5.add_cluster(clusterNumber=2, tetrode=3, soundResponsive=True, laserPulseResponse=True, followsLaserTrain=True, comments='good cell')

site6 = exp0726.add_site(depth = 3402, goodTetrodes = [3, 4])
site6.add_session('18-48-41', None, sessionTypes['1p'])
site6.add_session('18-49-47', None, sessionTypes['nb'])
site6.add_session('18-51-43', None, sessionTypes['lp'])
site6.add_session('18-53-23', None, sessionTypes['lt'])
site6.add_session('18-55-37', 'g', sessionTypes['tc'])
site6.add_session('19-07-31', None, sessionTypes['bf']) #comment='4freq from 8k-12kHz @60dB')
site6.add_session('19-08-55', None, sessionTypes['bf']) #comment='4freq from 18k-27kHz @60dB')

'''
This code is for making tuning curve heatmap figures for each recording site before clustering

ephys0726 = ee3.EphysExperiment(animalName = 'd1pi002', date = '2015-07-26', experimenter = 'lan')

for indS, Site in enumerate(exp0726.siteList): 
    for Session in Site.sessionList:
        if Session.sessionType == 'tuningCurve':
            for Tetrode in Site.goodTetrodes:
                plt.figure()
                ephys0726.plot_session_tc_heatmap(Session.session, Tetrode, Session.behavFileIdentifier)
                fig_path = os.path.join(settings.EPHYS_PATH,Site.animalName,Site.date,'tcheatmap')
                fig_name = '{}tetrode{}site{}{}.png'.format(Site.date, Tetrode, (indS+1), Session.session)
                full_fig_path = os.path.join(fig_path, fig_name)
                plt.show()
                if not os.path.exists(fig_path):
                    os.makedirs(fig_path)
                plt.savefig(full_fig_path)
                plt.close()
'''


