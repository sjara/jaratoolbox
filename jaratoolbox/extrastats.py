"""
Some statistics functions.

binofit: Parameter estimates and confidence intervals for binomial data.
"""

import scipy.stats
import numpy as np
import sys


def weibull(xval, alpha, beta):
    '''Weibull function
    alpha: bias
    beta: related to slope
    NOTE: this function isnot symmetric
    '''
    return 1 - np.exp(-pow(xval/alpha, beta))


def gaussianCDF(xval, mu, sigma):
    from scipy.stats import norm
    return norm.cdf(xval, mu, sigma)


def logistic(xval, alpha, beta):
    return 1/(1+np.exp(-(xval-alpha)/beta))


def psychfun(xval, alpha, beta, lamb, gamma):
    """
    Psychometric function (allows defining asymptotes)

    Args:
        alpha: bias
        beta : related to slope
        lamb : lapse term (up). It should be a non-negative value, zero means curve goes to one.
        gamma: lapse term (down). It should be a non-negative value, zero means curve goes to zero.
    """
    return gamma + (1-gamma-lamb)*logistic(xval, alpha, beta)

def invpsychfun(yval, alpha, beta, lamb, gamma):
    """
    Inverse of psychometric function. See psychfun() for parameters.
    """
    return alpha - beta * np.log((1-lamb-gamma)/(yval-gamma) - 1)
    

'''
# Example for fitting psychometric curve:
paramInitial = [0, -0.5, 0, 0]
paramBounds = [[-np.inf, -np.inf, 0, 0], [np.inf, np.inf, 0.5, 0.5]]
curveParams, pCov = scipy.optimize.curve_fit(extrastats.psychfun, xValues, yValues,
                                             p0=paramInitial, bounds=paramBounds)
'''


def psychometric_fit(xValues, nTrials, nHits, constraints=None, alpha=0.05):
    '''
    Given trial data for each value of parameter, estimate the psychometric curve.
    This function uses psignifit (BootstrapInference)
    http://psignifit.sourceforge.net/TUTORIAL_BOOTSTRAP.html

    xValues: 1-D array of size M
    nHits:   1-D array of size M
    nTrials: 1-D array of size M
    constraints: For logistic it will be (alpha,beta,lambda,gamma). See:
        http://psignifit.sourceforge.net/MODELSPECIFICATION.html#logistic-function

    '''
    import pypsignifit as psi

    if constraints is None:
        constraints = ( 'flat', 'Uniform(0,0.3)' ,'Uniform(0,0.2)', 'Uniform(0,0.2)')
    data = np.c_[xValues,nHits,nTrials]
    session = psi.BootstrapInference(data,sample=False, priors=constraints, nafc=1)
    # session = psi.BayesInference(data,sample=False,priors=constraints,nafc=1)
    # (pHit,confIntervals) = binofit(nHits,nTrials,alpha)
    # return (session.estimate,pHit,confIntervals)
    return session.estimate


if __name__ == "__main__":
    xValues = np.array([ 3.48,  3.6 ,  3.72,  3.85,  3.97,  4.09,  4.21])
    nRight = np.array([115,   5,  11, 689,  32,  26,  32])
    nTrials = np.array([1147,  122,   29,  944,   36,   26,   32])
    psyparams,pHit,ci = psychometric_fit(xValues,nTrials,nRight,alpha=0.05)
    print(psyparams)
    print(ci)
    
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
