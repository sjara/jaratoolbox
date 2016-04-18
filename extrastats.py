# -*- coding: utf-8 -*-
'''
Some statistics functions.

binofit: Parameter estimates and confidence intervals for binomial data.
'''

import scipy.stats
import numpy as np
import sys

def psychometric_fit(xValues, nTrials, nHits, constraints=None, alpha=0.05):
    '''
    Given performance for each value of parameter, estimate the curve.
    This function uses psignifit (BootstrapInference)
    
    xValues: 1-D array of size M
    nHits:   1-D array of size M
    nTrials: 1-D array of size M

    '''
    import pypsignifit as psi

    if constraints is None:
        constraints = ( 'flat', 'Uniform(0,0.3)' ,'Uniform(0,0.2)', 'Uniform(0,0.2)')
    data = np.c_[xValues,nHits,nTrials]
    session = psi.BootstrapInference(data,sample=False,priors=constraints,nafc=1)
    #session = psi.BayesInference(data,sample=False,priors=constraints,nafc=1)
    (pHit,confIntervals) = binofit(nHits,nTrials,alpha)
    return (session.estimate,pHit,confIntervals)



if __name__ == "__main__":
    xValues = np.array([ 3.48,  3.6 ,  3.72,  3.85,  3.97,  4.09,  4.21])
    nRight = np.array([115,   5,  11, 689,  32,  26,  32])
    nTrials = np.array([1147,  122,   29,  944,   36,   26,   32])
    psyparams,pHit,ci = psychometric_fit(xValues,nTrials,nRight,alpha=0.05)
    print psyparams
    print ci
    
    from extracellpy import behavioranalysis
    from pylab import *
    clf()
    hold(1)
    behavioranalysis.plot_psychcurve_fit(xValues,nTrials,nRight,psyparams)
    errorvals = np.transpose(ci-pHit[:,newaxis])
    (hel,hec,heb) =  errorbar(xValues,100*pHit,100*errorvals*c_[-1,1].T)
    setp(hel,visible=False)
    hold(0)
    draw(); show()
