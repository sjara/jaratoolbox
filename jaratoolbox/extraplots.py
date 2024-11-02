"""
Additional function for modifying plots and tabular bdata.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize


def boxoff(ax, keep='left', yaxis=True):
    """
    Hide axis lines, except left and bottom.
    You can specify which axes to keep: 'left' (default), 'right', 'none'.
    """
    ax.spines['top'].set_visible(False)
    xtlines = ax.get_xticklines()
    ytlines = ax.get_yticklines()
    if keep == 'left':
        ax.spines['right'].set_visible(False)
    elif keep == 'right':
        ax.spines['left'].set_visible(False)
    elif keep == 'none':
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        for t in xtlines+ytlines:
            t.set_visible(False)
    for t in xtlines[1::2]+ytlines[1::2]:
        t.set_visible(False)
    if not yaxis:
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ytlines = ax.get_yticklines()
        for t in ytlines:
            t.set_visible(False)


def adjust_pos(ax, modifier):
    """
    THIS METHOD IS NOT FINISHED.

    Adjust the position of axes.
    modifier is a list of 4 elements (left, bottom, width, height) to add to the original position
    """
    axPos = ax.get_position()
    axPosArray = np.array([axPos.x0, axPos.y0, axPos.width, axPos.height])
    newPos = axPosArray + np.array(modifier)
    '''
    xVals = np.array([axPos.xmin+modifier[0],
                      axPos.xmax+modifier[0]])
    yVals = np.array([axPos.ymin+modifier[1],
                      axPos.ymax+modifier[3]])
    axPos.update_from_data(xVals, yVals)
    '''
    ax.set_position(newPos)


def set_axes_color(ax, axColor):
    """
    Change the color of axes, ticks and labels.
    """
    import matplotlib
    for child in ax.get_children():
        if isinstance(child, matplotlib.axis.XAxis) or isinstance(child, matplotlib.axis.YAxis):
            for gchild in child.get_children():
                try:
                    gchild.set_color(axColor)
                except AttributeError:
                    for ggchild in gchild.get_children():
                        ggchild.set_color(axColor)
        if isinstance(child, matplotlib.spines.Spine):
            child.set_color(axColor)


def set_ticks_fontsize(ax, fontSize):
    """
    Set fontsize of axis tick labels
    """
    plt.setp(ax.get_xticklabels(), fontsize=fontSize)
    plt.setp(ax.get_yticklabels(), fontsize=fontSize)


def trials_each_cond_inds(trialsEachCond, nTrials):
    """
    Create trialsEachCond as a list of indexes with trials for each condition.
    """
    if isinstance(trialsEachCond, np.ndarray):
        # -- Convert boolean matrix to list of trial indexes --
        trialsEachCondInds = [np.flatnonzero(trialsEachCond[:, ind]) for ind in range(trialsEachCond.shape[1])]
    if trialsEachCond==[]:
        nCond=1
        # trialsEachCond = [np.arange(indexLimitsEachTrial.shape[1])]
        trialsEachCondInds = [np.arange(nTrials)]
    else:
        nCond = len(trialsEachCondInds)
    nTrialsEachCond = [len(x) for x in trialsEachCondInds]
    return trialsEachCondInds, nTrialsEachCond, nCond


def raster_plot(spikeTimesFromEventOnset, indexLimitsEachTrial, timeRange, trialsEachCond=[],
                colorEachCond=None, fillWidth=None, labels=None, rasterized=True):
    """
    Plot spikes raster plot grouped by condition
    Returns (pRaster,hcond,zline)
    First trial is plotted at y=0

    trialsEachCond can be a list of lists of indexes, or a boolean array of shape [nTrials,nConditions]
    """
    nTrials = len(indexLimitsEachTrial[0])
    (trialsEachCondInds, nTrialsEachCond, nCond) = trials_each_cond_inds(trialsEachCond, nTrials)

    if colorEachCond is None:
        colorEachCond = ['0.5', '0.75']*int(np.ceil(nCond/2.0))

    if fillWidth is None:
        fillWidth = 0.05*np.diff(timeRange).item()

    nSpikesEachTrial = np.diff(indexLimitsEachTrial, axis=0)[0]
    nSpikesEachTrial = nSpikesEachTrial*(nSpikesEachTrial > 0)  # FIXME: Some are negative(?)
    trialIndexEachCond = []
    spikeTimesEachCond = []
    for indcond, trialsThisCond in enumerate(trialsEachCondInds):
        spikeTimesThisCond = np.empty(0, dtype='float64')
        trialIndexThisCond = np.empty(0, dtype='int')
        for indtrial, thisTrial in enumerate(trialsThisCond):
            indsThisTrial = slice(indexLimitsEachTrial[0, thisTrial],
                                  indexLimitsEachTrial[1, thisTrial])
            spikeTimesThisCond = np.concatenate((spikeTimesThisCond,
                                                 spikeTimesFromEventOnset[indsThisTrial]))
            trialIndexThisCond = np.concatenate((trialIndexThisCond,
                                                 np.repeat(indtrial, nSpikesEachTrial[thisTrial])))
        trialIndexEachCond.append(np.copy(trialIndexThisCond))
        spikeTimesEachCond.append(np.copy(spikeTimesThisCond))

    xpos = timeRange[0]+np.array([0, fillWidth, fillWidth, 0])
    lastTrialEachCond = np.cumsum(nTrialsEachCond)
    firstTrialEachCond = np.r_[0, lastTrialEachCond[:-1]]

    hcond=[]
    pRaster = []
    ax = plt.gca()
    zline = plt.axvline(0, color='0.75', zorder=-10)
    # plt.hold(True)  # As of matplotlib 2.0, plt.hold is unecessary and was completely removed as axes are held until specified not to be

    for indcond in range(nCond):
        pRasterOne, = plt.plot(spikeTimesEachCond[indcond],
                               trialIndexEachCond[indcond]+firstTrialEachCond[indcond], '.k',
                               rasterized=rasterized)
        pRaster.append(pRasterOne)
        ypos = np.array([firstTrialEachCond[indcond],firstTrialEachCond[indcond],
                         lastTrialEachCond[indcond],lastTrialEachCond[indcond]])-0.5
        hcond.extend(plt.fill(xpos,ypos,ec='none',fc=colorEachCond[indcond]))
        hcond.extend(plt.fill(xpos+np.diff(timeRange)-fillWidth, ypos, ec='none',
                              fc=colorEachCond[indcond]))
    # plt.hold(False)  # As of matplotlib 2.0, plt.hold is unecessary and was completely removed as axes are held until specified not to be

    plt.xlim(timeRange)
    plt.ylim(-0.5,lastTrialEachCond[-1]-0.5)

    if labels is not None:
        labelsPos = (lastTrialEachCond+firstTrialEachCond)/2.0 -0.5
        ax.set_yticks(labelsPos)
        ax.set_yticklabels(labels)

    return pRaster, hcond, zline


def plot_psth(spikeCountMat, smoothWinSize, binsStartTime, trialsEachCond=[],
              colorEachCond=None, linestyle=None, linewidth=3, downsamplefactor=1, hidesamples=0):
    """
    TODO:
    - Check if the windowing is non-causal
    - Check the units of the vertical axis (is it spikes/sec?)
    """

    # from scipy.signal import hanning
    # winShape = hanning(smoothWinSize) # Hanning
    # winShape = np.ones(smoothWinSize) # Square (non-causal)
    winShape = np.concatenate((np.zeros(smoothWinSize), np.ones(smoothWinSize)))  # Square (causal)
    winShape = winShape/np.sum(winShape)

    nTrials = spikeCountMat.shape[0]
    (trialsEachCond, nTrialsEachCond, nCond) = trials_each_cond_inds(trialsEachCond, nTrials)

    if colorEachCond is None:
        colorEachCond = ['0.5']*nCond
    if linestyle is None:
        linestyle = ['-']*nCond
    pPSTH = []
    for indc in range(nCond):
        thisCondCounts = spikeCountMat[trialsEachCond[indc], :]
        thisPSTH = np.mean(thisCondCounts, axis=0)
        smoothPSTH = np.convolve(thisPSTH, winShape, mode='same')
        sSlice = slice(hidesamples, len(smoothPSTH)-hidesamples, downsamplefactor)
        ph, = plt.plot(binsStartTime[sSlice], smoothPSTH[sSlice], ls=linestyle[indc])
        pPSTH.append(ph)
        pPSTH[-1].set_linewidth(linewidth)
        pPSTH[-1].set_color(colorEachCond[indc])
    return pPSTH


def plot_psychometric(possibleValues, fractionHitsEachValue, ciHitsEachValue=None, xTicks=None,
                      xTickPeriod=1000, xscale='log'):
    if ciHitsEachValue is not None:
        upperWhisker = ciHitsEachValue[1, :]-fractionHitsEachValue
        lowerWhisker = fractionHitsEachValue-ciHitsEachValue[0, :]
        (pline, pcaps, pbars) = plt.errorbar(possibleValues, 100*fractionHitsEachValue,
                                             yerr=[100*lowerWhisker, 100*upperWhisker], color='k')
    else:
        pline = plt.plot(possibleValues, 100*fractionHitsEachValue, 'k')
        pcaps = None
        pbars = None
    pdots = plt.plot(possibleValues, 100*fractionHitsEachValue, 'o', mec='none', mfc='k', ms=8)
    plt.setp(pline, lw=2)
    #plt.axhline(y=50, color='0.5', ls='--')
    ax = plt.gca()
    ax.set_xscale(xscale)
    if xTicks is None:
        xTicks = [possibleValues[0], possibleValues[-1]]
    ax.set_xticks(xTicks)
    ax.set_xticks(np.arange(possibleValues[0], possibleValues[-1], xTickPeriod), minor=True)
    from matplotlib.ticker import ScalarFormatter
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_formatter(ScalarFormatter())

    plt.ylim([0, 100])
    if xscale == 'log':
        plt.xlim([possibleValues[0]/1.2, possibleValues[-1]*1.2])
    elif xscale == 'linear':
        valRange = possibleValues[-1]-possibleValues[0]
        plt.xlim([possibleValues[0]-0.1*valRange, possibleValues[-1]+0.1*valRange])
    # plt.xlabel('Frequency (kHz)')
    # plt.ylabel('Rightward trials (%)')
    return pline, pcaps, pbars, pdots


def plot_psychometric_fit(xValues, nTrials, nHits, curveParams=[], color='k'):
    """
    Plot average performance for each value and fitted curve.
    """
    import extrastats
    solidXvalues = np.flatnonzero((nTrials/sum(nTrials).astype(float))>(1.0/len(nTrials)))
    yValues = nHits.astype(float)/nTrials
    xRange = xValues[-1]-xValues[1]
    hfit = []
    if len(curveParams):
        fitxval = np.linspace(xValues[0]-0.1*xRange, xValues[-1]+0.1*xRange, 40)
        fityval = extrastats.psychfun(fitxval, *curveParams)
        hfit = plt.plot(fitxval, 100*fityval, '-', linewidth=2, color=color)
        plt.hold(True)
    hp = []
    for ind in range(len(xValues)):
        htemp, = plt.plot(xValues[ind], 100*yValues[ind], 'o', mfc=color)
        hp.append(htemp)
        plt.hold(True)
    plt.setp(hp, mec=color, mfc='w', mew=2, markersize=6)
    for solid in solidXvalues:
        plt.setp(hp[solid], mfc=color, markersize=8)
    # ylim([-0.1,1.1])
    plt.ylim([-10, 110])
    # hline = axhline(0.5)
    # setp(hline,linestyle=':',color='k')
    return hp, hfit


def set_log_ticks(ax, tickValues, axis='x'):
    tickLogValues = np.log10(tickValues)
    tickLabels = ['%d' % (1e-3*xt) for xt in tickValues]
    if axis == 'x':
        ax.set_xticks(tickLogValues)
        ax.set_xticklabels(tickLabels)
    else:
        ax.set_yticks(tickLogValues)
        ax.set_yticklabels(tickLabels)


def scalebar(xpos, ypos, width, height, xstring, ystring, fontsize=10):
    """Show scale bars with labels"""
    pbar = plt.plot([xpos, xpos, xpos+width], [ypos+height, ypos, ypos], 'k', lw=2, clip_on=False)
    xstring = plt.text(xpos+0.5*width, ypos-0.15*height, xstring,
                       va='top', ha='center', fontsize=fontsize, clip_on=False)
    ystring = plt.text(xpos-0.15*width, ypos+0.5*height, ystring, rotation=90,
                       va='center', ha='right', fontsize=fontsize, clip_on=False)
    return pbar, xstring, ystring


def significance_stars(xRange, yPos, yLength, color='k', starMarker='*', starSize=8, starString=None, gapFactor=0.1):
    """
    xRange: 2-element list or array with x values for horizontal extent of line.
    yPos: scalar indicating vertical position of line.
    yLength: scalar indicating length of vertical ticks
    starMarker: the marker type to use (e.g., '*' or '+')
    starString: if defined, use this string instead of a marker. In this case fontsize=starSize
    """
    nStars=1  # I haven't implemented plotting more than one star.
    # plt.hold(True)  # FIXME: Use holdState
    xGap = gapFactor*nStars
    xVals = [xRange[0], xRange[0],
             np.mean(xRange)-xGap*np.diff(xRange)[0], np.nan,
             np.mean(xRange)+xGap*np.diff(xRange)[0],
             xRange[1], xRange[1]]
    yVals = [yPos-yLength, yPos, yPos, np.nan, yPos, yPos, yPos-yLength]
    hlines, = plt.plot(xVals, yVals, color=color)
    hlines.set_clip_on(False)
    xPosStar = []  # FINISH THIS! IT DOES NOT WORK WITH nStars>1
    starsXvals = np.mean(xRange)
    if starString is None:
        hs, = plt.plot(starsXvals, np.tile(yPos, nStars),
                       starMarker, mfc=color, mec='None', clip_on=False)
        hs.set_markersize(starSize)
    else:
        hs = plt.text(starsXvals, yPos, starString, fontsize=starSize,
                      va='center', ha='center', color=color, clip_on=False)
    # plt.hold(False)
    return [hs, hlines]


def new_significance_stars(xRange, yPos, yLength, color='k', starMarker='*', fontSize=10, gapFactor=0.1, ax=None):
    """
    xRange: 2-element list or array with x values for horizontal extent of line.
    yPos: scalar indicating vertical position of line.
    yLength: scalar indicating length of vertical ticks
    starMarker (str): The string to use for the 'star'. Can be '*', or 'n.s.'
    """
    if ax == None:
        ax = plt.gca()
    nStars = 1  # I haven't implemented plotting more than one star.
    # plt.hold(True)  # FIXME: Use holdState
    xGap = gapFactor*nStars
    xVals = [xRange[0], xRange[0],
             np.mean(xRange)-xGap*np.diff(xRange), np.nan,
             np.mean(xRange)+xGap*np.diff(xRange),
             xRange[1], xRange[1]]
    yVals = [yPos-yLength, yPos, yPos, np.nan, yPos, yPos, yPos-yLength]
    hlines, = ax.plot(xVals, yVals, color=color)
    hlines.set_clip_on(False)
    xPosStar = []  # FINISH THIS! IT DOES NOT WORK WITH nStars>1
    starsXvals = np.mean(xRange)

    # hs, = plt.plot(starsXvals,np.tile(yPos,nStars),
    #                starMarker,mfc=color, mec='None')
    ax.text(starsXvals, yPos, starMarker, fontsize=fontSize, va='center', ha='center', clip_on=False)
    # plt.hold(False)


def spread_plot(xVal, yVals, spacing=0.1, **kwargs):
    """
    Plot at one x position samples that are quantized in y, by spreading dots equally.
    """
    uniqueY = np.unique(yVals)
    allMarkers = []
    for oneY in uniqueY:
        nVals = np.sum(yVals == oneY)
        possibleOffsets = spacing * np.arange(-nVals/2.0+0.5, nVals/2.0, 1)
        #print(possibleOffsets)
        xOffset = possibleOffsets[:nVals]
        #hp, = plt.plot(np.tile(xVal, nVals)+xOffset, np.tile(oneY, nVals), 'o', mfc='none')
        #hp, = plt.plot(np.tile(xVal, nVals)+xOffset, np.tile(oneY, nVals), **kwargs)
        hp, = plt.plot(np.tile(xVal, nVals)+xOffset, np.tile(oneY, nVals), 'o', mfc='none', **kwargs)
        allMarkers.append(hp)
    return allMarkers


def spread_offsets(data, spacing, delta=0):
    """
    Calculate offsets for a spread plot of continuous values.

    Args:
        data (np.array): values to plot.
        spacing (float): minimum final offset.
        delta (float): minimum difference between values to be offset.
    """
    m1, m2 = np.meshgrid(data, data)
    dmat = np.abs(m1-m2) <= delta
    dmat *= ~np.eye(len(data), dtype=bool)
    pairs = np.nonzero(np.triu(dmat))

    offsets = np.zeros(len(data))
    for ind1, ind2 in zip(*pairs):
        offsets[ind1] += -spacing/2
        offsets[ind2] += spacing/2
    return offsets


def breakaxis(xpos, ypos, width, height, gap=0.25):
    # plt.hold(1)
    xvals = np.array([xpos-width/2.0,xpos+width/2.0])
    yvals = np.array([ypos-height/2.0, ypos+height/2.0])
    plt.plot([xpos-0.25*width, xpos+0.25*width], [ypos,ypos], color='white', lw=4, clip_on=False, zorder=10)
    plt.plot(xvals-gap*width, yvals, color='k', clip_on=False, zorder=11)
    plt.plot(xvals+gap*width, yvals, color='k', clip_on=False, zorder=11)


def save_figure(filename, fileformat, figsize, outputDir='./', facecolor='none', **kwargs):
    plt.gcf().set_size_inches(figsize)
    figName = filename+'.{0}'.format(fileformat)
    fullName = os.path.join(outputDir, figName)
    if facecolor == 'none':
        plt.gcf().set_frameon(False)
    plt.savefig(fullName, format=fileformat, facecolor=facecolor, **kwargs)
    plt.gcf().set_frameon(True)
    print('Figure saved to {0}'.format(fullName))


class FlipThrough(object):
    def __init__(self, plotter, data, fig=None, **kwargs):
        """
        Allow flipping through data plots.
        Args:
            plotter (function): function that plots data.
            data (list): Inputs for the plotter function to loop through.
                         Each element can be a tuple.
            pargs (dict): additional "fixed" parameters to the plotter.
            fig (plt.Figure): figure to use.
        """
        self.plotter = plotter
        self.data = data
        self.counter = 0
        self.maxDataInd = len(data)-1
        if fig is None:
            self.fig = plt.figure()
        else:
            self.fig = fig
        self.kwargs = kwargs
        self.redraw() # Plot data
        self.kpid = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

    def redraw(self):
        self.fig.clf()
        if isinstance(self.data[self.counter], tuple):
            # FIXME: this will fail if the function requires a tuple as input
            self.plotter(*self.data[self.counter], **self.kwargs)
        else:
            self.plotter(self.data[self.counter], **self.kwargs)
        plt.suptitle('{}/{}: Press < or > to flip through data'.format(self.counter+1,
                                                                       self.maxDataInd+1))
        #self.fig.canvas.draw() # Added 2024-11-01
        self.fig.show()

    def on_key_press(self, event):
        """
        Method to listen for keypresses and flip to next/previous view
        """
        if event.key == '<' or event.key == ',' or event.key == 'left':
            if self.counter > 0:
                self.counter -= 1
            else:
                self.counter = self.maxDataInd
            self.redraw()
        elif event.key == '>' or event.key == '.' or event.key == 'right':
            if self.counter < self.maxDataInd:
                self.counter += 1
            else:
                self.counter = 0
            self.redraw()


def dataframe_to_html(dframe, outputfile):
    """
    Save an HTML file (with CSS) given a pandas dataframe.

    Args:
        dframe (pandas DataFrame): dataframe to display as HTML.
        outputfile (string): full path to the output HTML file (including extension).
    
    Note: if you want to reverse the datafram, use dframe.iloc[::-1]
    Note: indentation in the HTML file will be messy, but it won't affect rendering.
    """

    title = os.path.splitext(os.path.basename(outputfile))[0]
        
    htmlString = '''
    <html>
      <head><title>{title}</title></head>
      <style>
        {css}
      </style>
      <body>
        {table}
      </body>
    </html>
    '''

    cssString = '''
    table {
        border-collapse: collapse;
        margin: 20px 0;
        font-family: sans-serif;
        border: thin solid #cccccc;
    }
    thead {
        background-color: #2980b9;
        color: #ffffff;
    }
    tr, th, td {
        padding: 10px 15px;
        border: none;
        text-align: center;
    }
    tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    tbody tr:hover {
        background-color: #ffffdd;
    }
    '''    

    htmlTable = dframe.to_html()
    with open(outputfile, 'w') as fobj:
        fobj.write(htmlString.format(title=title, css=cssString, table=htmlTable))



def gaussian(x, a, x0, sigma, y0):
    """
    Gaussian function.
    """
    return a*np.exp(-(x-x0)**2/(2*sigma**2))+y0

def gaussian_full_width_half_max(sigma):
    return 2.355*sigma

def fit_tuning_curve(possibleValues, averageFiringRate):
    """
    Fit tuning curve values with a Gaussian.

    Note that for frequency tuning, you want to pass the possibleLogFreq 
    rather than just possibleFreq.
    """
    nValues = len(possibleValues)
    # Order of parameters: a, x0, sigma, y0
    p0 = [1, possibleValues[nValues//2], 1, 0]
    bounds = ([0, possibleValues[0], 0, 0],
              [np.inf, possibleValues[-1], np.inf, np.inf])
    fitParams, pcov = scipy.optimize.curve_fit(gaussian, possibleValues,
                                          averageFiringRate, p0=p0, bounds=bounds)
    # -- Calculate R^2 --
    gaussianResp = gaussian(possibleValues, *fitParams)
    residuals = averageFiringRate - gaussianResp
    ssquared = np.sum(residuals**2)
    ssTotal = np.sum((averageFiringRate-np.mean(averageFiringRate))**2)
    Rsquared = 1 - (ssquared/ssTotal)
    return (fitParams, Rsquared)


def plot_tuning_curve(possibleValues, averageFiringRate, fitParams=None, xscale='log'):
    """
    Plot tuning curve with Gaussian fit.

    xscale can be 'linear' or 'log'
    """
    if xscale=='linear':
        raise ValueError('xscale linear is not implemented yet')
    possibleLogFreq = np.log2(possibleValues)
    xvals = np.linspace(possibleLogFreq[0], possibleLogFreq[-1], 60)
    yvals = gaussian(xvals, *fitParams)
    pdots = plt.plot(possibleLogFreq, averageFiringRate, 'o')
    pfit = plt.plot(xvals, yvals, '-', lw=3)
    plt.ylabel('Firing rate (Hz)')
    plt.xlabel('Frequency (kHz)')
    xTickLabels = [f'{freq/1000:0.0f}' for freq in possibleValues]
    plt.xticks(possibleLogFreq, xTickLabels)
    return (pdots, pfit)


if __name__ == '__main__':
    rdata = np.random.randint(0, 9, (10, 3, 3))
    dataList = [(m,) for m in rdata]
    ft = FlipThrough(plt.imshow, dataList)
