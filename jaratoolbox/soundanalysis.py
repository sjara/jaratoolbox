"""
This module defines classes for analysis of statistics of sound textures.

Santiago Jaramillo

TO DO:
-  make method for reconstruction --
"""

import os
import sys
import numpy as np
import scipy.io.wavfile
import scipy.signal
from matplotlib import pyplot as plt

DEFAULT_COMPRESSION = 0.3

def plot_spectrum(wave, samplingRate, dc=True, maxFreq=None):
    '''
    dc: If False, it will not plot the DC component.
    '''
    signalFFT = np.fft.fft(wave)
    fvec = np.fft.fftfreq(len(wave), 1/samplingRate)
    if dc:
        samplesToPlot = (fvec>=0)
    else:
        samplesToPlot = (fvec>0)
    if maxFreq is not None:
        samplesToPlot = samplesToPlot & (fvec<=maxFreq)
    plt.plot(fvec[samplesToPlot],np.log10(np.abs(signalFFT[samplesToPlot])))
    return (fvec, signalFFT)


def plot_spectrogram(wave, samplingRate, window='hanning', nfft=2048, noverlap=1024):
    """
    Display spectrogram.
    """
    [sgramF, sgramT, sgramV] = scipy.signal.stft(wave, fs=samplingRate,
                                   window=window, nperseg=nfft, noverlap=noverlap)
    INTERP = 'nearest'
    sgramVsq = np.abs(sgramV**2)
    minVal =  np.min(sgramVsq[sgramVsq!=0])
    sgramVsq[sgramVsq==0] = minVal
    sgramVals = np.log10(sgramVsq)

    intensityRange = sgramVals.max()-sgramVals.min()
    VMAX=None; VMIN = sgramVals.min()+0.25*intensityRange
    #plt.clf()
    plt.imshow(sgramVals, cmap='viridis', aspect='auto',
               interpolation=INTERP, vmin=VMIN, vmax=VMAX,
               extent=(sgramT[0],sgramT[-1],sgramF[-1],sgramF[0]))
    #plt.ylim(np.array([200,0]))
    plt.gca().invert_yaxis()
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    cbar = plt.colorbar()
    #cbar.set_label('log(A^2)', rotation=270)
    cbar.set_label('log(A)')
    #plt.show()
    return (sgramF, sgramT, sgramV)
        

def play_waveform(waveform, samplingRate, amp=1):
    '''NOTE: This function is designed for Linux systems only.'''
    tempFile = '/tmp/tempsound.wav'
    wave16bit = (amp*waveform).astype('int16')
    scipy.io.wavfile.write(tempFile, samplingRate, wave16bit)
    os.system('aplay {}'.format(tempFile))
    
        
def hertz_to_erbs(freqHz):
    """
    Return number of equivalent rectangular bandwidths below the given frequency.

    Glasberg & Moore (1990) Eq.4 (with freq in Hz)
    https://en.wikipedia.org/wiki/Equivalent_rectangular_bandwidth
    """
    return 21.4 * np.log10(1 + 0.00437*freqHz)


def erbs_to_hertz(nERBs):
    """
    Return frequency with nERBs equivalent rectangular bandwidths below it.

    Inverse of Eq.4 (with freq in Hz) from Glasberg & Moore (1990) 
    https://en.wikipedia.org/wiki/Equivalent_rectangular_bandwidth
    """
    return (10**(nERBs/21.4)-1)/0.00437


def voss(nrows, ncols=16):
    """Generates pink noise using the Voss-McCartney algorithm.

    https://github.com/AllenDowney/ThinkDSP/blob/master/code/voss.ipynb

    nrows: number of values to generate
    rcols: number of random sources to add
    
    returns: NumPy array
    """
    import pandas as pd   # FIXME: imported here during testing
    array = np.full((nrows, ncols), np.nan)
    array[0, :] = np.random.random(ncols)
    array[:, 0] = np.random.random(nrows)
    
    # the total number of changes is nrows
    n = nrows
    cols = np.random.geometric(0.5, n)
    cols[cols >= ncols] = 0
    rows = np.random.randint(nrows, size=n)
    array[rows, cols] = np.random.random(n)

    df = pd.DataFrame(array)
    df.fillna(method='ffill', axis=0, inplace=True)
    total = df.sum(axis=1)

    return total.values


class StepError(Exception):
    pass


class SoundAnalysis(object):
    """
    Analysis of frequency bands of a sound.

    Calculate frequency bands using a filterbank and estimates
    marginal statistics and cross-correlations for each band.
    """
    def __init__(self, waveform=[], fs=None, soundfile=None, downsample=1):
        """
        If soundfile is specified, the sound file is used instead of waveform.
        Args:
            waveform (np.ndarray): 1D array with waveform values
            fs (float): sampling rate
            soundfile (string): full path to file to load.
                If soundfile is specified, you don't need the other arguments.
            downsample: downsampling factor for bands envelopes.
        """
        if soundfile is not None:
            self.samplingRate, self.wave = scipy.io.wavfile.read(soundfile)
        else:
            self.samplingRate = fs
            self.wave = waveform
        self.downsampleFactor = downsample
        self.nSamples = len(self.wave)
        self.timeVec = np.arange(0, len(self.wave)/self.samplingRate, 1/self.samplingRate)
        self.filename = soundfile
        
        # -- Frequency decomposition --
        self.fvec = []
        self.spectrum = []
        self.nBands = None
        self.bandsFourier = [] # Complex [nBands, nSamples]
        self.bands = []        # Real [nBands, nSamples]
        self.bandsEnvelopes = []
        self.bandsEnvelopesTimeVec = []
        #self.bandsEnvelopesCompressed = False # Will be set to True after compression
        
        # -- Stats --
        #self.bandsStats = {'mean':[], 'var':[], 'skew':[]}
        self.bandsStats = {}
        
    def get_sound_parameters(self):
        return(self.nSamples, self.samplingRate, self.nSamples/self.samplingRate)
    
    def get_waveform(self, samples=None):
        """
        Returns:
            timeVec
            wave
        """
        if samples is None:
            return (self.timeVec, self.wave)
        else:
            return (self.timeVec[samples], self.wave[samples])
        
    def plot_spectrogram(self, window='hanning', nfft=2048, noverlap=1024):
        """
        Display spectrogram.
        """
        (sgramF, sgramT, sgramV) = plot_spectrogram(self.wave, self.samplingRate,
                                                    window, nfft, noverlap)
        return (sgramF, sgramT, sgramV)
        
    def play(self, amp=1):
        """
        Play sound waveform.
        """
        play_waveform(self.wave, self.samplingRate, amp=amp)

    def play_from_file(self):
        """
        Play sound file (using Linux ALSA player).
        """
        if filename:
            os.system('aplay {}'.format(self.filename))
        else:
            print('No sound file associated with this object')

    def apply_filterbank(self, fbankTF):
        """
        Calculate bands by applying filterbank (in the frequency domain).
        Args:
            fbankTF (np.ndarray): [nBands, nSamples] filters transfer function (frequency domain).
                The array should contain the transfer function for both positive and negative
                frequencies, so it should symmetric on axis 1.
        """
        self.nBands = fbankTF.shape[0]
        self.fvec = np.fft.fftfreq(len(self.wave), 1/self.samplingRate)
        self.spectrum = np.fft.fft(self.wave)
        self.bandsFourier =  fbankTF * self.spectrum
        self.bands = np.real(np.fft.ifft(self.bandsFourier, axis=1))
        return self.get_bands()
    
    def get_bands(self):
        """
        Returns:
            timeVec
            bands
        """
        if not len(self.bands):
            raise StepError('Before get_bands(), you need to apply_filterbank().')
        return (self.timeVec, self.bands)
    
    def calculate_bands_envelopes(self):
        """
        Calculate envelope of each band.

        FIXME: downsampling can lead to negative envelope values,
               should we set those to zero?
        """
        self.bandsEnvelopes = np.abs(scipy.signal.hilbert(self.bands,axis=1))
        if self.downsampleFactor!=1:
            self.bandsEnvelopes = scipy.signal.decimate(self.bandsEnvelopes, self.downsampleFactor,
                                                        axis=1, zero_phase=True)
            # Decimating caould create negative numbers, but envelopes must be non-negative.
            self.bandsEnvelopes[self.bandsEnvelopes<0]=0
        self.bandsEnvelopesTimeVec = self.timeVec[::self.downsampleFactor]
        return self.get_bands_envelopes()
    
    def get_bands_envelopes(self):
        """
        Returns:
            Time vector
            Envelope for each band
        """
        if not len(self.bandsEnvelopes):
            raise StepError('Before get_bands_envelopes(), you need to calculate_bands_envelopes().')
        return (self.bandsEnvelopesTimeVec, self.bandsEnvelopes)
    
    def play_band(self, bandInd, duration=None):
        if not len(self.bands):
            raise StepError('Before play_band(), you need to apply_filterbank().')
        tempFile = '/tmp/tempsound.wav'
        if duration is None:
            samplesToPlay = len(self.wave)
        else:
            samplesToPlay = int(self.samplingRate*duration)
        play_waveform(self.bands[bandInd,:samplesToPlay], self.samplingRate)

    def plot_cochleagram(self):
        """
        Display cochleagram.
        """
        if not len(self.bandsEnvelopes):
            raise StepError('Before plot_cochleagram(), you need to calculate_bands_envelopes().')
        INTERP = 'nearest'
        cgramVals = self.bandsEnvelopes
        #np.log10(np.abs(self.specgramV)**2)
        VMAX=None; VMIN = None #cgramVals.min()+7
        plt.clf()
        plt.gca().set_axis_bgcolor('k')
        plt.imshow(cgramVals, cmap='viridis', aspect='auto',
                   interpolation=INTERP, vmin=VMIN, vmax=VMAX)
        #plt.ylim(np.array([200,0]))
        plt.gca().invert_yaxis()
        plt.colorbar()
        plt.show()

    def apply_compression(self, compressionExponent=DEFAULT_COMPRESSION):
        """
        Apply power-law compression to bands envelopes.
        """
        if not len(self.bandsEnvelopes):
            raise StepError('Before apply_compression(), you need to calculate_bands_envelopes().')
        self.bandsEnvelopes = self.bandsEnvelopes**compressionExponent
        return self.get_bands_envelopes()
        
    def plot_bands_distributions(self):
        if not len(self.bandsEnvelopes):
            raise StepError('Before plot_bands_distributions(), you need to calculate_bands_envelopes().')
        plt.clf()
        maxBin = np.percentile(self.bandsEnvelopes[:],99.99)
        firstAx = plt.subplot(self.nBands,1,self.nBands)
        for indband in range(self.nBands):
            thisAx = plt.subplot(self.nBands,1,self.nBands-indband, sharex=firstAx)
            bins = np.linspace(0,maxBin,100)
            plt.hist(self.bandsEnvelopes[indband,:],bins)
            plt.ylabel('Band {}'.format(indband))
            if indband==0:
                plt.xlabel('Envelope value')
            else:
                pass#thisAx.set_xticklabels([])
        plt.show()
        
    def calculate_bands_stats(self):
        if not len(self.bandsEnvelopes):
            raise StepError('Before calculate_bands_stats(), you need to calculate_bands_envelopes().')
        # -- Marginals --
        self.bandsStats['mean'] = np.mean(self.bandsEnvelopes, axis=1)
        self.bandsStats['var'] = np.var(self.bandsEnvelopes, axis=1)
        self.bandsStats['var/meanSq'] = np.var(self.bandsEnvelopes, axis=1)/self.bandsStats['mean']**2
        self.bandsStats['skew'] = scipy.stats.skew(self.bandsEnvelopes, axis=1)
        self.bandsStats['kurt'] = scipy.stats.kurtosis(self.bandsEnvelopes, axis=1, fisher=False)
        self.bandsStats['corr'] = np.corrcoef(self.bandsEnvelopes)
        return (self.bandsStats)
    
    def plot_bands_stats(self):
        if not self.bandsStats:
            raise StepError('Before plot_bands_stats(), you need to calculate_bands_stats().')
        plt.clf()
        statsToPlot = ['mean','var','var/meanSq','skew','kurt']
        for indstat, oneStat in enumerate(statsToPlot):
            thisAx = plt.subplot(len(statsToPlot), 1, indstat+1)
            if oneStat=='kurt':
                statValues = self.bandsStats[oneStat]-3
                yLabel = 'kurt-3'
            else:
                statValues = self.bandsStats[oneStat]
                yLabel = oneStat
            plt.stem(statValues, basefmt='C5-', use_line_collection=True)
            plt.ylabel(yLabel)
            if indstat==len(statsToPlot)-1:
                plt.xlabel('Band')
            else:
                thisAx.set_xticklabels([])
        plt.show()

    def analyze(self, nBands, freqLims, verbose=True):
        """
        Run complete analysis to estimate sound statistics.
        Args:
            nBands (int): number of filters in filterbank.
            freqLims (list): 2-element array with [lowestCenterFreq,highestCenterFreq].
        """
        if verbose: print('Creating filterbank...')
        fbank = FilterBank(nBands, freqLims, self.nSamples, self.samplingRate)
        if verbose: print('Applying filterbank...')
        self.apply_filterbank(fbank.get_transfer_function())
        if verbose: print('Calculating envelopes...')
        self.calculate_bands_envelopes()
        if verbose: print('Applying compression...')
        self.apply_compression()
        if verbose: print('Calculating statistics...')
        bandStats = self.calculate_bands_stats()
        return (bandStats,fbank)



class FilterBank(object):
    """
    Define bank of filters in the frequency domain equally spaced in ERB space.

    It creates a bank of zero-phase filters with amplitude (in the frequency domain)
    in the shape of the positive portion of a cosine function.
    """
    def __init__(self, nBands, freqLims, nSamples, samplingRate):
        """
        Args:
            nBands (int): number of filters.
            freqLims (list): 2-element array with [lowestCenterFreq,highestCenterFreq].
            nSamples (int): number of samples in the signal to filter.
            samplingRate (int): sampling rate of the signal to filter.
        """
        self.nBands = nBands
        self.nSamples = nSamples
        if nSamples%2:
            raise ValueError('NOT IMPLEMENTED: Odd number of samples')
        self.nFreqs = nSamples//2  # Ignore DC component ???
        self.samplingRate = samplingRate
        self.fullFreqVec = np.fft.fftfreq(self.nSamples, 1/self.samplingRate)
        self.freqVec = self.fullFreqVec[:self.nFreqs]
        self.filtersTFpos = np.zeros((self.nBands, self.nFreqs))
        
        bandCenterERBs = np.linspace(hertz_to_erbs(freqLims[0]),
                                     hertz_to_erbs(freqLims[1]), self.nBands)
        # -- Append centers for end filters --
        stepERBs = bandCenterERBs[1]-bandCenterERBs[0]
        bandCenterERBsWithEnds = np.hstack((bandCenterERBs[0]-stepERBs,
                                            bandCenterERBs,
                                            bandCenterERBs[-1]+stepERBs))
        # -- Define filter parameters in Hx --
        self.bandCenterHz = erbs_to_hertz(bandCenterERBsWithEnds)
        self.bandLimsHz = np.vstack((self.bandCenterHz[:-2],
                                     self.bandCenterHz[2:]))

        # -- Create each filter in the frequency domain --
        for indFilter in range(self.nBands):
            support = (self.freqVec>self.bandLimsHz[0,indFilter]) & \
                      (self.freqVec<=self.bandLimsHz[1,indFilter])
            freqVecERB = hertz_to_erbs(self.freqVec[support])
            bandLimsERB = hertz_to_erbs(self.bandLimsHz[:,indFilter])
            midPointERB = (bandLimsERB[0]+bandLimsERB[1])/2
            widthERB = (bandLimsERB[1]-bandLimsERB[0])
            filterShape = np.cos(np.pi*(freqVecERB-midPointERB)/widthERB)
            # -- Make end filters flat on corresponding ends --
            if indFilter==0:
                filterShape[freqVecERB<midPointERB]=1
            elif indFilter==self.nBands-1:
                filterShape[freqVecERB>midPointERB]=1
            self.filtersTFpos[indFilter,support] = filterShape

    def get_transfer_function(self):
        """
        Return filter matrix including negative frequencies.
        """
        fullTransferFunction = np.hstack((self.filtersTFpos, self.filtersTFpos[:,-1,np.newaxis],
                                          np.fliplr(self.filtersTFpos[:,1:])))
        return fullTransferFunction
    
    def get_frequencies(self):
        """
        Return vector of frequencies for each point in the transfer function.
        """
        return self.fullFreqVec
    
    def plot(self, samples=False):
        if samples:
            plt.plot(self.filtersTFpos.T, '-')
            plt.xlabel('Samples')
        else:
            plt.plot(self.freqVec, self.filtersTFpos.T, '-')
            lowLim = max(self.bandLimsHz[0,0], 0)
            highLim = min(self.bandLimsHz[1,-1], self.freqVec[-1])
            plt.xlim((lowLim, highLim))
            plt.xlabel('Frequency (Hz)')
        plt.ylabel('Transfer function magnitude')


class SoundSynthesis(SoundAnalysis):
    """
    """
    def __init__(self, nBands, freqLims, nSamples, samplingRate, downsample=1):
        """
        Args:
            nBands (int): number of filters.
            freqLims (list): 2-element array with [lowestCenterFreq,highestCenterFreq].
            nSamples (int): number of samples in the signal to generate.
            samplingRate (int): sampling rate of the signal to generate
        """
        self.samplingRate = samplingRate
        #self.duration = duration
        #self.nSamples = self.duration*self.samplingRate)
        self.nSamples = nSamples

        #np.random.seed(0)  # FIXME: I'm fixing the random seed for testing
        PINK = 0
        if PINK: 
            pinknoise = voss(self.nSamples)
            self.seedWaveform = pinknoise-pinknoise.mean()
        else:
            self.seedWaveform = np.random.randn(self.nSamples)
            
        super().__init__(self.seedWaveform, self.samplingRate, downsample=downsample)
        #self.soundObj = SoundAnalysis(self.seedWaveform, self.samplingRate)

        self.nBands = nBands
        self.freqLims  = freqLims
        self.fbank = FilterBank(self.nBands, self.freqLims, self.nSamples,
                                self.samplingRate)
        self.fbankTF = self.fbank.get_transfer_function()

    def analyze(self, verbose=True):
        """
        Calculate band envelopes and statistics.
        """
        return super().analyze(self.nBands, self.freqLims, verbose)
    
    def impose_bands_envelopes(self, envelopes, randomize=False, decorrelate=False,
                               compression=DEFAULT_COMPRESSION):
        """
        Multiply bands by specified envelopes.
        
        Args:
            envelopes (2D array): as areturned by SoundAnalysis.get_bands_envelopes()
            compression (float): exponent used for compression. Default is DEFAULT_COMPRESSION.
            randomize (bool): if True samples of each envelope will be randomized.
            decorrelate (bool): if True, each envelope will be shifted randomly.
        """
        if not len(self.bandsEnvelopes):
            raise StepError('Before get_bands_envelopes(), you need to calculate_bands_envelopes().')
        # FIXME: it assumes compression exponent
        #exponent = 1/DEFAULT_COMPRESSION if compressed else 1
        tvec, bands = self.get_bands()
        stDevs = bands.std(axis=1)
        uncompEnvelopes = envelopes**(1/compression)
        if randomize:
            for indb in range(self.nBands):
                uncompEnvelopes[indb,:] = np.random.permutation(uncompEnvelopes[indb,:])
        if decorrelate:
            for indb in range(self.nBands):
                rollAmount = np.random.randint(self.bandsEnvelopes.shape[1])
                #indb*int(self.nSamples/self.nBands)
                uncompEnvelopes[indb,:] = np.roll(uncompEnvelopes[indb,:], rollAmount)
        if self.downsampleFactor!=1:
            uncompEnvelopes = scipy.signal.resample_poly(uncompEnvelopes, self.downsampleFactor, 1, axis=1)
        newBands = bands * uncompEnvelopes / stDevs[:,np.newaxis]
        #newBands = bands * (envelopes**(1/compressionExponent))
        self.bands = newBands
    
    def impose_bands_marginals(self, stats):
        """
        Multiply bands by specified envelopes.
        
        Args:
            envelopes (np.ndarray): as areturned by SoundAnalysis.get_bands_envelopes()
            compressed (boolean): True is envelopes have already been compressed
        """
        if not len(self.bandsEnvelopes):
            raise StepError('Before get_bands_envelopes(), you need to calculate_bands_envelopes().')
        # FIXME: it assumes compression exponent
        exponent = 1/DEFAULT_COMPRESSION if compressed else 1
        tvec, bands = self.get_bands()
        newBands = bands * (envelopes**exponent)
        self.bands = newBands
        #self.calculate_stats()
        #self.soundStats = stats
        pass
       
    def impose_oneband(self, indband, newMean=None, newVar=None):
        """ Testing imposing statistics """
        compressionExp = DEFAULT_COMPRESSION
        stats = self.calculate_stats()
        if newVar is not None:
            oldVar = stats['var'][indband]
            scaleFactor = (np.sqrt(newVar)/np.sqrt(oldVar))**(1/compressionExp)
            #print(np.var(self.bands[indband,:]))
            self.bands[indband,:] = scaleFactor*self.bands[indband,:]
            #print(np.var(self.bands[indband,:]))
        if newMean is not None:
            oldMean = stats['mean'][indband]
            scaleFactor = 2*newMean/oldMean
            self.bands[indband,:] = scaleFactor*self.bands[indband,:]
        
    def reconstruct_waveform(self):
        """
        Apply filterbank and add bands to recontruct waveform.
        """
        tvec, bands = self.get_bands()
        bandsFFT = np.fft.fft(bands, axis=1)
        componentFFT = self.fbankTF * bandsFFT
        components = np.fft.ifft(componentFFT, axis=1)
        newWave = np.real(np.sum(components, axis=0))
        print('Max imag: {}'.format(np.max(np.abs(np.imag(np.sum(components, axis=0))))))
        self.wave = newWave
        return (tvec, newWave)

    def save(self, filename):
        wave16bit = self.wave.astype('int16')
        scipy.io.wavfile.write(filename, self.samplingRate, wave16bit)
        print('Saved waveform as {}'.format(filename))


if __name__=='__main__':

    #filename = './Example_Textures/Bubbling_water.wav'
    '''
    allFilenames = ['Bubbling_water.wav',
                    'Applause_-_enthusiastic2.wav',
                    'Writing_with_pen_on_paper.wav',
                    'white_noise_5s.wav']
    filename = os.path.join('~/src/soundtextures/Example_Textures/',allFilenames[0])
    '''
    allFilenames = ['bubbles.wav']
    filename = os.path.join('/home/sjara/src/jaranotebooks/soundsamples/',allFilenames[0])
    #filename = './bubbles.wav'
    #filename = './forest02.wav'
    
    sana = SoundAnalysis(soundfile=filename)
    
    CASE = 99
    if CASE == 0:
        plt.clf()
        sana.plot_spectrogram()
    if CASE == 1:
        fbins = np.fft.fftfreq(len(sana.wave), 1/sana.samplingRate)
        ff = np.fft.fft(sana.wave)
        plt.clf()
        #plt.plot(fbins,np.log10(np.abs(ff)))
        plt.plot(fbins,np.abs(ff))
        plt.xlabel('Frequency')
        plt.ylabel('abs(FFT(x))')
    if CASE == 2:
        fs = 20000
        fLims = [50,8000]
        fbank = FilterBank(6, fLims, 10*fs, fs)
        plt.clf()
        ax0=plt.subplot(2,1,1)
        fbank.plot()
        #plt.gca().set_xscale('log')
        plt.ylabel('Filter amplitude')
        plt.xlabel('Frequency')
        ax1=plt.subplot(2,1,2,sharex=ax0)
        #plt.plot(np.sum(fbank.filterHalfMat,axis=0))
        plt.plot(fbank.freqVec,np.sum(fbank.filtersTFpos**2,axis=0))
        plt.ylim([0,1.5])
        plt.show()
    if CASE == 3:
        fbank = FilterBank(6, [50,8000], len(sana.wave), sana.samplingRate)
        #(fvec, fullTF) = fbank.get_transfer_function()
        fullTF = fbank.get_transfer_function()
        sana.apply_filterbank(fullTF)
        plt.clf()
        #plt.plot(sana.timeVec,np.real(sana.wave))
        #plt.plot(np.abs(sana.bandsFourier[5,:]))
        plt.plot(np.abs(sana.bandsFourier.T))
        #plt.plot(fullTF.T)
        plt.show()
    if CASE == 4:
        fbank = FilterBank(6, [50,8000], len(sana.wave), sana.samplingRate)
        #(fvec, fullTF) = fbank.get_transfer_function()
        fullTF = fbank.get_transfer_function()
        sana.apply_filterbank(fullTF)
        #plt.clf()
        #plt.plot(sana.timeVec,np.real(sana.bands[0,:]))
        #plt.show()
        for indband in range(6):
            sana.play_band(indband, 3)  # Play only 3 seconds
        
    if CASE == 5:
        fbank = FilterBank(12, [50,8000], len(sana.wave), sana.samplingRate)
        #(fvec, fullTF) = fbank.get_transfer_function()
        fullTF = fbank.get_transfer_function()
        sana.apply_filterbank(fullTF)
        downsampleFactor = 1
        sana.calculate_bands_envelopes(downsampleFactor=downsampleFactor)
        samplesToPlot = np.arange(5000)
        samplesToPlotEnv = np.arange(5000//downsampleFactor)
        plt.clf()
        fig, axs = plt.subplots(nrows=sana.nBands, ncols=1, sharex=True, num=1)
        for indband in range(sana.nBands):
            #axs[indband].subplot(sana.nBands,1,indband+1)
            axs[indband].plot(sana.timeVec[samplesToPlot],sana.bands[indband,samplesToPlot])
            axs[indband].plot(sana.bandsEnvelopesTimeVec[samplesToPlotEnv],
                              sana.bandsEnvelopes[indband,samplesToPlotEnv],'-')
        plt.show()
        
    if CASE == 6:
        fbank = FilterBank(6, [20,8000], len(sana.wave), sana.samplingRate)
        #fbank = FilterBank(34, [20,10000], len(sana.wave), sana.samplingRate)
        #(fvec, fullTF) = fbank.get_transfer_function()
        fullTF = fbank.get_transfer_function()
        sana.apply_filterbank(fullTF)
        sana.calculate_bands_envelopes()
        plt.figure(1)
        sana.plot_bands_distributions()
        plt.figure(2)
        sana.apply_compression(0.3)
        sana.plot_bands_distributions()
        bandStats = sana.calculate_bands_stats()
        print(bandStats)
        sys.exit()

    if CASE == 7:
        fbank = FilterBank(6, [20,8000], len(sana.wave), sana.samplingRate)
        #fbank = FilterBank(34, [20,10000], len(sana.wave), sana.samplingRate)
        #(fvec, fullTF) = fbank.get_transfer_function()
        fullTF = fbank.get_transfer_function()
        sana.apply_filterbank(fullTF)
        sana.calculate_bands_envelopes()
        sana.apply_compression(0.3)
        bandStats = sana.calculate_bands_stats()
        sana.plot_bands_stats()
        print(bandStats)
        sys.exit()

    if CASE == 8:
        fbank = FilterBank(6, [20,8000], len(sana.wave), sana.samplingRate)
        fullTF = fbank.get_transfer_function()
        sana.apply_filterbank(fullTF)
        tvec,bands = sana.get_bands()
        bandsFFT = np.fft.fft(bands, axis=1)
        componentFFT = fullTF * bandsFFT
        components = np.fft.ifft(componentFFT, axis=1)
        newWave = np.real(np.sum(components, axis=0))
        errorWave = newWave-sana.wave
        samplesToPlot = np.arange(1000)
        plt.clf()
        #plt.plot(sana.wave[samplesToPlot],'.')
        #plt.plot(newWave[samplesToPlot],'o',mfc='none')
        plt.plot(errorWave)
        plt.show()
        # play_waveform(newWave, sana.samplingRate)

    if CASE == 9:
        (soundStats, fbank) = sana.analyze(6, [20,8000])
        sys.exit()
        
    if CASE == 10:
        ssyn = SoundSynthesis(6, [20,8000], len(sana.wave)//2, sana.samplingRate)
        soundStats = ssyn.calculate_stats()
        plt.figure(2)
        ssyn.soundObj.plot_bands_stats()
        plt.figure(1)
        ssyn.soundObj.plot_bands_distributions()
        #print(soundStats)
    
    if CASE == 11:
        ssyn = SoundSynthesis(6, [20,8000], len(sana.wave)//2, sana.samplingRate)
        indband = 2
        statName = 'mean'
        newVar = 0.02
        newMean = 1.0
        soundStats = ssyn.calculate_stats()
        print('Band {} {} (before): {}'.format(indband, statName, soundStats[statName][2]))
        print('Band {} {} (before): {}'.format(indband, 'var', soundStats['var'][2]))
        ssyn.impose_oneband(indband, newMean, None)
        ssyn.soundObj.calculate_bands_envelopes()
        ssyn.soundObj.apply_compression()
        newSoundStats = ssyn.soundObj.calculate_bands_stats()
        print('Band {} {} (before): {}'.format(indband, statName, newSoundStats[statName][2]))
        print('Band {} {} (before): {}'.format(indband, 'var', soundStats['var'][2]))
        ssyn.soundObj.plot_bands_distributions()

        
    CASE = 12
    if CASE == 12:
        allFilenames = ['bubbles.wav','whitenoise.wav','pinknoise.wav','forest02.wav']
        filename = os.path.join('../jaranotebooks/soundsamples/',allFilenames[3])
        sana = SoundAnalysis(soundfile=filename)
        sana.analyze(6, [20,8000])
        #sana.plot_bands_distributions()
        #sana.plot_bands_stats()
        print(sana.bandsStats['skew'])
        print(sana.bandsStats['kurt']-3)

        #ac = np.correlate(sana.bandsEnvelopes[2],sana.bandsEnvelopes[2],'same')
        plt.clf()
        #plot_spectrogram(sana.bandsEnvelopes[2], sana.samplingRate, nfft=2048*4)
        for indband in range(sana.nBands):
            thisAx = plt.subplot(sana.nBands,1,sana.nBands-indband)
            plot_spectrum(sana.bandsEnvelopes[indband], sana.samplingRate, dc=False, maxFreq=100)
            plt.ylabel('Band {}'.format(indband))
            plt.xlim([-5,100])

    plt.show()
