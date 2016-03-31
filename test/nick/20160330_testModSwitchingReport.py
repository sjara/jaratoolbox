from jaratoolbox import loadbehavior
from jaratoolbox.test.nick import behavioranalysis_vnick as behavioranalysis
from jaratoolbox import extraplots

fn = '/var/tmp/data/santiago/nick/nick_2afc_20160330a.h5'

bdata = loadbehavior.BehaviorData(fn)


trialsAmpMod = bdata['soundType']==bdata.labels['soundType']['amp_mod']
trialsChords = bdata['soundType']==bdata.labels['soundType']['chords']

choice = bdata['choice']
choiceRight = choice==bdata.labels['choice']['right']

choiceRightAmpMod = choiceRight[trialsAmpMod]
choiceRightChords = choiceRight[trialsChords]

targetFrequencyAmpMod = bdata['targetFrequency'][trialsAmpMod]
targetFrequencyChords = bdata['targetFrequency'][trialsChords]

valid = bdata['valid']
validAmpMod = valid[trialsAmpMod]
validChords = valid[trialsChords]

#Chords
figure()
(possibleValues,fractionHitsEachValue,ciHitsEachValue,nTrialsEachValue,nHitsEachValue)=\
    behavioranalysis.calculate_psychometric(choiceRightChords,targetFrequencyChords,validChords)

(pline, pcaps, pbars, pdots) = extraplots.plot_psychometric(1e-3*possibleValues,
                                                            fractionHitsEachValue,
                                                            ciHitsEachValue,
                                                            xTickPeriod=1)



#Amp Mod
figure()
(possibleValues,fractionHitsEachValue,ciHitsEachValue,nTrialsEachValue,nHitsEachValue)=\
    behavioranalysis.calculate_psychometric(choiceRightAmpMod,targetFrequencyAmpMod,validAmpMod)

(pline, pcaps, pbars, pdots) = extraplots.plot_psychometric(1e-3*possibleValues,
                                                            fractionHitsEachValue,
                                                            ciHitsEachValue,
                                                            xTickPeriod=1)




def plot_frequency_psycurve_soundtype(bdata, soundType, fontsize=12):
    '''
    Show psychometric curve (for any arbitrary sound type)
    '''

    trialsSoundType = bdata['soundType']==bdata.labels['soundType'][soundType]
    choice = bdata['choice']
    choiceRight = choice==bdata.labels['choice']['right']
    choiceRightSoundType = choiceRight[trialsSoundType]
    targetFrequencySoundType = bdata['targetFrequency'][trialsSoundType]
    valid = bdata['valid']
    validSoundType = valid[trialsSoundType]
    (possibleValues,fractionHitsEachValue,ciHitsEachValue,nTrialsEachValue,nHitsEachValue)=\
        behavioranalysis.calculate_psychometric(choiceRightSoundType,targetFrequencySoundType,validSoundType)
    (pline, pcaps, pbars, pdots) = extraplots.plot_psychometric(1e-3*possibleValues,
                                                                fractionHitsEachValue,
                                                                ciHitsEachValue,
                                                                xTickPeriod=1)
    plt.xlabel('Frequency (kHz)',fontsize=fontsize)
    plt.ylabel('Rightward trials (%)',fontsize=fontsize)
    extraplots.set_ticks_fontsize(plt.gca(),fontsize)
    return (pline, pcaps, pbars, pdots)

figure()
plot_frequency_psycurve_soundtype(bdata, 'amp_mod')

figure()
plot_frequency_psycurve_soundtype(bdata, 'chords')
