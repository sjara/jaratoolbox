"""
Module for speech sounds synthesis.
"""
# Based on code by Santiago originally stored in ~/src/praat/

import os
import copy
import numpy as np
from matplotlib import pyplot as plt
import parselmouth as pm


DEFAULT_TIMING_PARAMS = {'burstDuration': 0.000001,
                         'vowelDuration': 0.22,
                         'formantTransitionDuration': 0.035,
                         'prevoiceDuration': 0,
                         'aspPoint': 0}

DEFAULT_FORMANT_SET = np.array([[80, 100, 0],
                                [220, 710, 50],
                                [1240, 1240, 70],
                                [2500, 2500, 110]], dtype='float')


def show_praat_spectrogram(spectrogram, dynamic_range=70):
    """
    Plot spectrogram generated by Praat.
    
    You can get the spectrogram from a parselmouth.Sound object with the function:
    sound.to_spectrogram()

    Args:
        spectrogram (parselmouth.Spectrogram): object containing spectrogram data.
        dynamic_range (float): max intensity of range. Larger values leads to darker bands.
    """
    Xg, Yg = spectrogram.x_grid(), spectrogram.y_grid()
    sg_db = 10 * np.log10(spectrogram.values)
    cmap = 'Greys' #'afmhot'
    plt.pcolormesh(Xg, Yg, sg_db, vmin=sg_db.max() - dynamic_range, cmap=cmap)
    plt.ylim([spectrogram.ymin, spectrogram.ymax])
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")


def show_spectrogram(soundwave, sampFreq, **kwargs):
    """
    Calculate and show spectrogram of signal.

    Args:
        sound (np.array): 1-D array containing sound samples
        other parameters defined in plt.specgram(): NFFT, noverlap),  Fs, cmap, vmin
    """
    kwargs.setdefault('NFFT', 4096)  # 4096 replicates Praat
    if 'noverlap' not in kwargs:
        noverlap = int(kwargs['NFFT']*0.95)
    kwargs.setdefault('noverlap', noverlap)  # 0.98
    kwargs.setdefault('cmap', 'viridis')
    kwargs.setdefault('vmin', -150)
    plt.specgram(soundwave, Fs=sampFreq, **kwargs)
    plt.xlabel("Time (s)")
    plt.ylabel("Frequency (Hz)")
    #plt.ylim([0, 5000*freqFactor])


class SyllableRange():
    def __init__(self, nFT, nVOT, sampFreq=44100, freqFactor=1):
        self.sampFreq = sampFreq
        self.freqFactor = freqFactor
        self.nFT = nFT
        self.nVOT = nVOT
        self.syllables = []  # nVOT lists of nFT elements [nVOT][nFT]
        self.timingParams = DEFAULT_TIMING_PARAMS.copy()
        self.formantSet = self.freqFactor * DEFAULT_FORMANT_SET
        self.generate_sounds()
    def generate_sounds(self):
        aspPointLimits = [0, 0.08]
        aspPointValues = np.linspace(aspPointLimits[0], aspPointLimits[1], self.nVOT)
        F2on = self.formantSet[2,0]
        F3on = self.formantSet[3,0]
        formant2onset = np.geomspace(F2on/1.4, F2on*1.4, self.nFT)
        formant3onset = np.geomspace(F3on/1.25, F3on*1.25, self.nFT)
        for indvot in range(self.nVOT):
            self.syllables.append([])
            self.timingParams['aspPoint'] = aspPointValues[indvot]
            for indft in range(self.nFT):
                self.formantSet[2,0] = formant2onset[indft]
                self.formantSet[3,0] = formant3onset[indft]
                syllableObj = Syllable(**self.timingParams,
                                       formantSet=self.formantSet,
                                       sampFreq=self.sampFreq)
                self.syllables[indvot].append(syllableObj)
        sound = syllableObj.create_sound()
    def save(self, outputDir='/tmp/'):
        percentVOT = np.linspace(0, 100, self.nVOT)
        percentFT = np.linspace(0, 100, self.nFT)
        for indvot in range(self.nVOT):
            for indft in range(self.nFT):
                fileNameFmt = 'syllable_{0}x_vot{1:03.0f}_ft{2:03.0f}.wav'
                fileName = fileNameFmt.format(self.freqFactor,
                                              percentVOT[indvot], percentFT[indft])
                fullFilename = os.path.join(outputDir,fileName)
                self.syllables[indvot][indft].save(fullFilename)
    def spectrograms(self, maxf=5000):
        plt.clf()
        for indft in range(self.nFT):
            for indvot in range(self.nVOT):
                plt.subplot2grid([self.nVOT, self.nFT], [indvot, indft])
                self.syllables[indvot][indft].spectrogram()
                if indft != 0:
                    plt.gca().set_yticklabels([])
                    plt.gca().set_ylabel('')
                if indvot != self.nVOT-1:
                    plt.gca().set_xticklabels([])
                    plt.gca().set_xlabel('')
                plt.ylim([0, maxf])
        plt.tight_layout()
        plt.show()

'''
        infoStr = ''
infoStr += 60*'-'
infoStr += f'FILENAME: {fileName}\n'
infoStr += self.syllables[indvot][indft].info()
'''

'''
formantSetBA = np.array([[80, 100, 0],
                         [220, 710, 50],
                         [900, 1240, 70],
                         [2000, 2500, 110]], dtype='float')
formantSetDA = np.array([[80, 100, 0],
                         [220, 710, 50],
                         [1240*1.4, 1240, 70],
                         [2500*1.25, 2500, 110]], dtype='float')

def ba(formantSet, sampFreq=44100, freqFactor=1):
    burstDuration = 0.004
    vowelDuration = 0.2
    formantTransitionDuration = 0.035
    prevoiceDuration = 0
    aspPoint = 0
    nFormants = 3
    syllableObj = Syllable(vowelDuration, formantTransitionDuration, aspPoint,
                           burstDuration, prevoiceDuration, nFormants=nFormants, sampFreq=sampFreq)
    syllableObj.set_pitch(formantSet[0,0], formantSet[0,1])
    for indf in np.arange(1, nFormants+1):
        syllableObj.set_formant(indf, formantSet[indf,0], formantSet[indf,1], formantSet[indf,2])
    sound = syllableObj.create_sound()
    return sound
'''

def oldBaPaRange(nItems, sampFreq=44100, freqFactor=1, outputDir=''):
    burstDuration = 0.004
    vowelDuration = 0.315
    formantTransitionDuration = 0.035
    prevoiceDuration = 0
    aspPointLimits = [0, 0.08]
    aspPointValues = np.linspace(aspPointLimits[0], aspPointLimits[1], nItems)
    aspPointPercent = np.linspace(0, 100, nItems)
    sounds = []
    for inds,aspPoint in enumerate(aspPointValues):
        syllableObj = Syllable(vowelDuration, formantTransitionDuration, aspPoint,
                                burstDuration, prevoiceDuration, nFormants=5, sampFreq=sampFreq)
        syllableObj.set_pitch(80*freqFactor, 100*freqFactor)
        syllableObj.set_formant(1, 220*freqFactor, 710*freqFactor, 50*freqFactor)
        syllableObj.set_formant(2, 900*freqFactor, 1240*freqFactor, 70*freqFactor)
        syllableObj.set_formant(3, 2000*freqFactor, 2500*freqFactor, 110*freqFactor)
        syllableObj.set_formant(4, 3600*freqFactor, 3600*freqFactor, 170*freqFactor)
        syllableObj.set_formant(5, 4500*freqFactor, 4500*freqFactor, 250*freqFactor)
        sound = syllableObj.create_sound()
        sounds.append(sound)
        if outputDir:
            fileName = 'bapa_{0}x_{1:03.0f}.wav'.format(freqFactor,aspPointPercent[inds])
            fullFileName = os.path.join(outputDir,fileName)
            print('Saving {}'.format(fullFileName))
            sound.save(fullFileName,'WAV')


def oldBaDaRange(nItems, sampFreq=44100, freqFactor=1, outputDir=''):
    burstDuration = 0.004
    vowelDuration = 0.315
    formantTransitionDuration = 0.035
    prevoiceDuration = 0
    aspPoint = 0
    formant2onset = np.geomspace(1240/1.4, 1240*1.4, nItems)
    formant3onset = np.geomspace(2500/1.25, 2500*1.25, nItems)
    changePercent = np.linspace(0, 100, nItems)
    sounds = []
    for inds in range(nItems):
        syllableObj = Syllable(vowelDuration, formantTransitionDuration, aspPoint,
                                burstDuration, prevoiceDuration, nFormants=5, sampFreq=sampFreq)
        syllableObj.set_pitch(80*freqFactor, 100*freqFactor)
        syllableObj.set_formant(1, 220*freqFactor, 710*freqFactor, 50*freqFactor)
        syllableObj.set_formant(2, formant2onset[inds]*freqFactor, 1240*freqFactor, 70*freqFactor)
        syllableObj.set_formant(3, formant3onset[inds]*freqFactor, 2500*freqFactor, 110*freqFactor)
        syllableObj.set_formant(4, 3600*freqFactor, 3600*freqFactor, 170*freqFactor)
        syllableObj.set_formant(5, 4500*freqFactor, 4500*freqFactor, 250*freqFactor)
        sound = syllableObj.create_sound()
        sounds.append(sound)
        if outputDir:
            fileName = 'bada_{0}x_{1:03.0f}.wav'.format(freqFactor,changePercent[inds])
            #fileName = 'bada_{:03.0f}.wav'.format(changePercent[inds])
            fullFileName = os.path.join(outputDir,fileName)
            print('Saving {}'.format(fullFileName))
            sound.save(fullFileName,'WAV')
            

            
class tempSyllableWave():
    """
    NOT USED. Object containing the waveform of a sound.
    """
    def __init__(self, Syllable):
        tvec, wave = Syllable.as_array()
        self.tvec = tvec
        self.wave = wave
        self.sampFreq = Syllable.sampFreq
    def play(self):
        self.sound.save('/tmp/soundtemp.wav','WAV')
        os.system('aplay /tmp/soundtemp.wav')
    def spectrogram(self, **kwargs):
        show_spectrogram(self.swave, self.sampFreq, **kwargs)
    

class Syllable():
    def __init__(self, vowelDuration, formantTransitionDuration, aspPoint, burstDuration,
                 prevoiceDuration=0, silenceDuration=0.02, formantSet=[], sampFreq=44100,
                 fixedRandom=True):
        """
        Create a consonant-vowel syllable object.

        Args:
            vowelDuration (float)
            formantTransitionDuration (float)
            aspPoint (float)
            burstDuration (float)
            prevoiceDuration (float)
            formantSet (np.array): Each row is one formant. 
                formantSet[0,:] = [pitch_onset, pitch_stable, 0 ] 
                formantSet[1,:] = [F1_onset, F1_stable, F1_bandwidth]
                formantSet[2,:] = ...
            sampFreq (float)
            fixedRandom (bool): If True, fix the random seed, for deterministic instances.
        """
        if fixedRandom:
            pm.praat.run("random_initializeWithSeedUnsafelyButPredictably(0)")
        self.sampFreq = sampFreq
        self.pitch = {}
        self.formantTransitionDuration = formantTransitionDuration
        self.vowelDuration = vowelDuration
        self.aspPoint = aspPoint
        self.burstDuration = burstDuration
        self.prevoiceDuration = prevoiceDuration
        self.silenceDuration = silenceDuration
        self.vowelSound = None
        self.burstSound = None
        self.sound = None
        self.formantSet = formantSet
        self.formants = []
        if len(self.formantSet):
            self.set_formants(self.formantSet)
        else:
            self.nFormants = None
    def set_formants(self, formantSet):
        self.set_pitch(formantSet[0,0], formantSet[0,1])
        self.nFormants = formantSet.shape[0]-1
        self.formants = (self.nFormants)*[{}]
        for indf in np.arange(1, self.nFormants+1):
            self.set_formant(indf, formantSet[indf,0], formantSet[indf,1], formantSet[indf,2])
    def set_pitch(self, onset, stable):
        self.pitch = {'onset':onset, 'stable':stable}
    def set_formant(self, formantID, onset, stable, bandwidth):
        self.formants[formantID-1] = {'onset':onset, 'stable':stable,
                                      'bandwidth':bandwidth}
    def create_sound(self):
        # Last argument of the next call must be string.
        self.silence = pm.praat.call('Create Sound from formula', 'silence', 1, 0,
                                     self.silenceDuration, self.sampFreq, '0')
        if self.burstDuration>0:
            self.create_burst()
        self.create_vowel()
        if self.prevoiceDuration:
            self.create_prevoicing()
            self.sound  = self.silence.concatenate([self.silence, self.burstSound,
                                                    self.prevoiceSound, self.vowelSound])
        else:
            self.sound  = self.silence.concatenate([self.silence, self.burstSound, self.vowelSound])
        return self.sound
    def create_burst(self):
        burstKG = pm.praat.call('Create KlattGrid', 'burst', 0, self.burstDuration,
                                0, 0, 0, 1, 0, 0, 0)
        pm.praat.call(burstKG, 'Add frication formant frequency point', 1, 0, 300)
        pm.praat.call(burstKG, 'Add frication formant bandwidth point', 1, 0, 100)
        pm.praat.call(burstKG, 'Add frication formant amplitude point', 1, 0, 0.005)
        pm.praat.call(burstKG, 'Add frication amplitude point', 0, 0)
        pm.praat.call(burstKG, 'Add frication amplitude point', 0.001, 25)
        pm.praat.call(burstKG, 'Add frication amplitude point', 0.001, 25)
        pm.praat.call(burstKG, 'Add frication amplitude point', self.burstDuration, 0)
        pm.praat.call(burstKG, 'Add voicing amplitude point', 0, 25)
        self.burstSound = pm.praat.call(burstKG, 'To Sound (special)', 0, 0, self.sampFreq,
                                            'yes', 'no', 'yes', 'yes', 'yes', 'yes',
                                            'Powers in tiers', 'yes', 'yes', 'yes',
                                            'Cascade', 1, 5, 1, 1,  1, 1, 1, 1,
                                            1, 1, 1, 1,  1, 1, 1, 6, 'yes')
        pm.praat.call(self.burstSound, 'Scale intensity', 50)
        return self.burstSound
    def create_vowel(self):
        vowelKG = pm.praat.call('Create KlattGrid', 'creation', 0, self.vowelDuration,
                                5, 0, 0, 1, 0, 0, 0)
        for indf in range(self.nFormants):
            pm.praat.call(vowelKG, 'Add oral formant frequency point', indf+1,
                          0, self.formants[indf]['onset'])
            pm.praat.call(vowelKG, 'Add oral formant frequency point', indf+1,
                          self.formantTransitionDuration,
                          self.formants[indf]['stable'])
            pm.praat.call(vowelKG, 'Add oral formant bandwidth point', indf+1,
                          0, self.formants[indf]['bandwidth'])

        pm.praat.call(vowelKG, 'Add pitch point', self.aspPoint, self.pitch['onset'])
        pm.praat.call(vowelKG, 'Add pitch point', self.aspPoint+0.1, self.pitch['stable'])
        pm.praat.call(vowelKG, 'Add pitch point', self.vowelDuration-0.04, 90)
        pm.praat.call(vowelKG, 'Add pitch point', self.vowelDuration, 50)

        pm.praat.call(vowelKG, 'Add voicing amplitude point', 0, 0)
        pm.praat.call(vowelKG, 'Add voicing amplitude point', self.aspPoint, 0)
        pm.praat.call(vowelKG, 'Add voicing amplitude point', self.aspPoint+0.00001, 60)
        pm.praat.call(vowelKG, 'Add voicing amplitude point', self.aspPoint+0.02, 60)
        pm.praat.call(vowelKG, 'Add voicing amplitude point', self.vowelDuration, 50)

        pm.praat.call(vowelKG, 'Add aspiration amplitude point', self.burstDuration, 20)
        pm.praat.call(vowelKG, 'Add aspiration amplitude point', self.burstDuration+0.001, 25)
        pm.praat.call(vowelKG, 'Add aspiration amplitude point', self.aspPoint-0.001, 25)
        pm.praat.call(vowelKG, 'Add aspiration amplitude point', self.aspPoint, 0)

        self.vowelSound = pm.praat.call(vowelKG, 'To Sound (special)', 0, 0.315, self.sampFreq,
                                        'yes', 'yes', 'yes', 'yes', 'yes', 'yes',
                                        'Powers in tiers', 'yes', 'yes', 'yes' ,
                                        'Cascade', 1, 5, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
                                        1, 1, 1, 6, 'yes')
        return self.vowelSound
    def create_prevoicing(self):
        prevoiceKG = pm.praat.call('Create KlattGrid', 'prevoice', 0, self.prevoiceDuration,
                                   1, 0, 0, 1, 0, 0, 0)
        pm.praat.call(prevoiceKG, 'Add oral formant frequency point', 1, 0, 120)
        pm.praat.call(prevoiceKG, 'Add oral formant frequency point', 1, 0, 100)
        pm.praat.call(prevoiceKG, 'Add pitch point', 0, 120)
        pm.praat.call(prevoiceKG, 'Add voicing amplitude point', 0, 50)
        self.prevoiceSound = pm.praat.call(prevoiceKG, 'To Sound (special)', 0,
                                           self.prevoiceDuration, self.sampFreq,
                                          'yes', 'yes', 'yes', 'yes', 'yes', 'yes',
                                          'Powers in tiers', 'yes', 'yes', 'yes',
                                          'Cascade', 1, 5, 1, 1,  1, 1, 1, 1,
                                          1, 1, 1, 1,  1, 1, 1, 6, 'yes')
        pm.praat.call(self.prevoiceSound, 'Scale intensity', 50)
        return self.prevoiceSound
    def play(self):
        if self.sound is None:
            self.create_sound()
        self.sound.save('/tmp/soundtemp.wav','WAV')
        os.system('aplay /tmp/soundtemp.wav')
    def as_array(self):
        if self.sound is None:
            self.create_sound()
        soundWave = self.sound.as_array().squeeze()
        timeVec = np.arange(0,len(soundWave))/self.sampFreq
        return (timeVec, soundWave)
    def spectrogram(self, **kwargs):
        timeVec, swave = self.as_array()
        show_spectrogram(swave, self.sampFreq, **kwargs)
    def info(self):
        formantStr = f'F0 (pitch): {str(self.pitch)}\n'
        for indf in range(self.nFormants):
            formantStr += f'F{indf+1}: {str(self.formants[indf])}\n'
        infoStr = (f'sampFreq: {self.sampFreq}\n'+ formantStr + 
                   f'aspPoint: {self.aspPoint}\n' +
                   f'vowelDuration: {self.vowelDuration}\n' +
                   f'formantTransitionDuration: {self.formantTransitionDuration}\n' +
                   f'burstDuration: {self.burstDuration}\n' +
                   f'prevoiceDuration: {self.prevoiceDuration}\n' +
                   f'silenceDuration: {self.silenceDuration}\n' +
                   '')
        return infoStr
    def save(self, filepath, saveInfo=True, verbose=True):
        if self.sound is None:
            self.create_sound()
        if verbose:
            print('Saving {}'.format(filepath))
        self.sound.save(filepath, 'WAV')
        if saveInfo:
            infofilePath = os.path.splitext(filepath)[0]+'.info'
            infoStr = self.info()
            with open(infofilePath, 'w') as infofile:
                infofile.write(infoStr)
            

if __name__=='__main__':
    sampFreq = 192000  # 44100
    freqFactor = 1     # 1 for human hearing range, 8 for mice.
    nFT = 2
    nVOT = 2

    syRange = speechsynth.SyllableRange(nFT, nVOT, sampFreq=sampFreq, freqFactor=freqFactor)
    syRange.save('/tmp/speechsounds')

    plt.clf()
    for indft in range(nFT):
        for indvot in range(nVOT):
            syRange.syllables[indvot][indft].play();

            plt.subplot2grid([nVOT, nFT], [indvot, indft])
            syRange.syllables[indvot][indft].spectrogram()
            plt.ylim([0, 5000*freqFactor])
            plt.show()
            wait = input("Press Enter to continue.")

