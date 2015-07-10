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

today = ee2.RecordingDay(animalName = 'd1pi001', date = '2015-07-07', experimenter = 'lan')

site1 = ee2.RecordingSite(today, depth = 2750, goodTetrodes = [3])
site1.add_session('14-10-13', None, sessionTypes['nb'])
site1.add_session('14-11-42', None, sessionTypes['lp'])
site1.add_session('14-14-00', None, sessionTypes['lt'])
site1.add_session('14-17-54', 'a', sessionTypes['tc'])

site2 = ee2.RecordingSite(today, depth = 2900, goodTetrodes = [3])
site2.add_session('15-12-17', None, sessionTypes['nb'])
site2.add_session('15-14-12', None, sessionTypes['lp'])
site2.add_session('15-16-18', None, sessionTypes['lt'])
site2.add_session('15-18-44', 'b', sessionTypes['tc'])

site3 = ee2.RecordingSite(today, depth = 3025, goodTetrodes = [3, 6])
site3.add_session('12-28-47', None, sessionTypes['nb'])
site3.add_session('12-31-21', None, sessionTypes['lp'])
site3.add_session('12-34-00', None, sessionTypes['lt'])
site3.add_session('12-37-29', 'c', sessionTypes['tc'])
site3.add_session('12-50-34', None, sessionTypes['bf'])
site3.add_session('12-53-57', None, sessionTypes['3p'])
site3.add_session('12-56-04', None, sessionTypes['1p'])

site4 = ee2.RecordingSite(today, depth = 3654, goodTetrodes = [3, 6])
site4.add_session('13-06-27', None, sessionTypes['nb'])
site4.add_session('13-09-00', None, sessionTypes['lp'])
site4.add_session('13-11-25', None, sessionTypes['lt'])
site4.add_session('13-15-01', 'd', sessionTypes['tc'])
site4.add_session('13-28-12', None, sessionTypes['bf'])
site4.add_session('13-30-00', None, sessionTypes['3p'])
site4.add_session('13-31-58', None, sessionTypes['1p'])

from jaratoolbox.test.nick.ephysExperiments import laserTCanalysis
reload(laserTCanalysis)
for indSite, site in enumerate(today.siteList):
    laserTCanalysis.laser_tc_analysis(site, indSite+1)
