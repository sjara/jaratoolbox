from jaratoolbox.test.nick.ephysExperiments import ephys_experiment
reload(ephys_experiment)
from jaratoolbox.test.nick.ephysExperiments.ephys_experiment import RecordingSite
from jaratoolbox.test.nick.ephysExperiments.ephys_experiment import EphysExperiment

site1 = RecordingSite(depth = 3543,
                      noiseburstEphysSession  = '2015-06-24_15-22-29',
                      laserPulseEphysSession  = '2015-06-24_15-25-08',
                      laserTrainEphysSession = '2015-06-24_15-27-37',
                      tuningCurveEphysSession  = '2015-06-24_15-31-48',
                      tuningCurveBehavIdentifier  = 'a',
                      bfEphysSession  = '2015-06-24_15-45-22',
                      bfBehavIdentifier = 'b',
                      laserPulseEphysSession3mW  = None,
                      laserPulseEphysSession1mW = None,
                      goodTetrodes = [6])

        
site2 = RecordingSite(depth = 3623,
                      noiseburstEphysSession  = '2015-06-24_15-54-56',
                      laserPulseEphysSession  = '2015-06-24_15-57-33',
                      laserTrainEphysSession = '2015-06-24_16-00-02',
                      tuningCurveEphysSession  = '2015-06-24_16-04-48',
                      tuningCurveBehavIdentifier  = 'c',
                      bfEphysSession  = '2015-06-24_16-17-30',
                      bfBehavIdentifier = 'd',
                      laserPulseEphysSession3mW  = '2015-06-24_16-20-11',
                      laserPulseEphysSession1mW = '2015-06-24_16-22-37',
                      goodTetrodes = [6])

site3 = RecordingSite(depth = 3700,
                      noiseburstEphysSession  = '2015-06-24_16-40-44',
                      laserPulseEphysSession  = '2015-06-24_16-44-01',
                      laserTrainEphysSession = '2015-06-24_16-46-20',
                      tuningCurveEphysSession  = '2015-06-24_16-50-03',
                      tuningCurveBehavIdentifier  = 'e',
                      bfEphysSession  = '2015-06-24_17-03-10',
                      bfBehavIdentifier = None,
                      laserPulseEphysSession3mW  = '2015-06-24_17-06-10',
                      laserPulseEphysSession1mW = '2015-06-24_16-17-09-06',
                      goodTetrodes = [6])

site4 = RecordingSite(depth = 3757,
                      noiseburstEphysSession  = '2015-06-24_17-15-58',
                      laserPulseEphysSession  = '2015-06-24_17-18-57',
                      laserTrainEphysSession = '2015-06-24_17-21-29',
                      tuningCurveEphysSession  = '2015-06-24_17-25-16',
                      tuningCurveBehavIdentifier  = 'g',
                      bfEphysSession  = '2015-06-24_17-37-45',
                      bfBehavIdentifier = 'af',
                      laserPulseEphysSession3mW  = '2015-06-24_17-41-31',
                      laserPulseEphysSession1mW = '2015-06-24_17-44-25',
                      goodTetrodes = [3, 6])

site5 = RecordingSite(depth = 3805,
                      noiseburstEphysSession  = '2015-06-24_17-59-53',
                      laserPulseEphysSession  = '2015-06-24_18-03-50',
                      laserTrainEphysSession = '2015-06-24_18-06-31',
                      tuningCurveEphysSession  = '2015-06-24_18-10-38',
                      tuningCurveBehavIdentifier  = 'h',
                      bfEphysSession  = '2015-06-24_17-18-24-47',
                      bfBehavIdentifier = None,
                      laserPulseEphysSession3mW  = '2015-06-24_18-29-24',
                      laserPulseEphysSession1mW = '2015-06-24_18-33-08',
                      goodTetrodes = [3, 6])

site6 = RecordingSite(depth = 3855,
                      noiseburstEphysSession  = '2015-06-24_18-44-21',
                      laserPulseEphysSession  = '2015-06-24_18-47-59',
                      laserTrainEphysSession = '2015-06-24_18-51-29',
                      tuningCurveEphysSession  = '2015-06-24_18-55-40',
                      tuningCurveBehavIdentifier  = 'i',
                      bfEphysSession  = '2015-06-24_17-19-10-27',
                      bfBehavIdentifier = None,
                      laserPulseEphysSession3mW  = '2015-06-24_19-13-33',
                      laserPulseEphysSession1mW = '2015-06-24_19-16-41',
                      goodTetrodes = [6])

siteList = [site1, site2, site3, site4, site5, site6]

exp = EphysExperiment('pinp003', '2015-06-24')

exp.process_site(site1)
