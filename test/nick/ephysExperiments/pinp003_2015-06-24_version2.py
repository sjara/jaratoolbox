from jaratoolbox.test.nick.ephysExperiments import ephys_experiment_v2 as ee2
reload(ee2)

#The session types to use for this kind of experiment
#Can use a dict like this or simply write the sesison types directly
#I used this to avoid typing errors and to save time
sessionTypes = {'nb':'noiseBurst',
                'lp':'laserPulse',
                'lt':'laserTrain',
                'tc':'tuningCurve',
                'bf':'bestFreq',
                '3p':'3mWpulse',
                '1p':'1mWpulse'} 

today = ee2.RecordingDay(animalName = 'pinp003', date = '2015-06-24', experimenter = 'nick')

site1 = ee2.RecordingSite(today, depth = 3543, goodTetrodes = [6])
site1.add_session('15-22-29', None, sessionTypes['nb'])
site1.add_session('15-25-08', None, sessionTypes['lp'])
site1.add_session('15-27-37', None, sessionTypes['lt'])
site1.add_session('15-31-48', 'a', sessionTypes['tc'])
site1.add_session('15-45-22', 'b', sessionTypes['bf'])

site2 = ee2.RecordingSite(today, depth = 3623, goodTetrodes = [6])
site2.add_session('15-54-56', None, sessionTypes['nb'])
site2.add_session('15-57-33', None, sessionTypes['lp'])
site2.add_session('16-00-02', None, sessionTypes['lt'])
site2.add_session('16-04-48', 'c', sessionTypes['tc'])
site2.add_session('16-17-30', 'd', sessionTypes['bf'])
site2.add_session('16-20-11', None, sessionTypes['3p'])
site2.add_session('16-22-37', None, sessionTypes['1p'])

site3 = ee2.RecordingSite(today, depth = 3700, goodTetrodes = [6])
site3.add_session('16-40-44', None, sessionTypes['nb'])
site3.add_session('16-44-01', None, sessionTypes['lp'])
site3.add_session('16-46-20', None, sessionTypes['lt'])
site3.add_session('16-50-03', 'e', sessionTypes['tc'])
site3.add_session('17-03-10', None, sessionTypes['bf'])
site3.add_session('17-06-10', None, sessionTypes['3p'])
site3.add_session('17-09-06', None, sessionTypes['1p'])

site4 = ee2.RecordingSite(today, depth = 3757, goodTetrodes = [3, 6])
site4.add_session('17-15-58', None, sessionTypes['nb'])
site4.add_session('17-18-57', None, sessionTypes['lp'])
site4.add_session('17-21-29', None, sessionTypes['lt'])
site4.add_session('17-25-16', 'g', sessionTypes['tc'])
site4.add_session('17-37-45', 'af', sessionTypes['bf'])
site4.add_session('17-41-31', None, sessionTypes['3p'])
site4.add_session('17-44-25', None, sessionTypes['1p'])

site5 = ee2.RecordingSite(today, depth = 3805, goodTetrodes = [3, 6])
site5.add_session('17-59-53', None, sessionTypes['nb'])
site5.add_session('18-03-50', None, sessionTypes['lp'])
site5.add_session('18-06-31', None, sessionTypes['lt'])
site5.add_session('18-10-38', 'h', sessionTypes['tc'])
site5.add_session('18-24-47', None, sessionTypes['bf'])
site5.add_session('18-29-24', None, sessionTypes['3p'])
site5.add_session('18-33-08', None, sessionTypes['1p'])

site6 = ee2.RecordingSite(today, depth = 3855, goodTetrodes = [6])
site6.add_session('18-44-21', None, sessionTypes['nb'])
site6.add_session('18-47-59', None, sessionTypes['lp'])
site6.add_session('18-51-29', None, sessionTypes['lt'])
site6.add_session('18-55-40', 'i', sessionTypes['tc'])
site6.add_session('19-10-27', None, sessionTypes['bf'])
site6.add_session('19-13-33', None, sessionTypes['3p'])
site6.add_session('19-16-41', None, sessionTypes['1p'])

from jaratoolbox.test.nick.ephysExperiments import laserTCanalysis
reload(laserTCanalysis)
for indSite, site in enumerate(today.siteList):
    laserTCanalysis.laser_tc_analysis(site, indSite+1)
