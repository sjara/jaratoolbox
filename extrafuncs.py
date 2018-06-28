#!/usr/bin/env python

'''
Additional functions often used but not available in python modules.
'''


import numpy as np
import datetime

def pad_float_list(listOfLists, length=None, pad=np.NaN):
    '''Pad a list of lists of floats with nan to the same length.
    Args:
        listOfLists: a list of lists of floats.
        length: optional argument for the length wish to pad all the sublist to.
        pad: value to pad empty slots with, default to np.NaN since datatype is float.
    Returns:
        A list of lists where all the sublists are of the same length.
    '''
    if length == None:
        # Take the longest length of all the sublists
        length = len(sorted(listOfLists, key=len, reverse=True)[0])
    resultList = [np.concatenate((sublist, [pad] * (length-len(sublist)))) for sublist in listOfLists]
    return resultList

def interpolate_nan(xvals):
    '''Creates a new array with interpolated values where elements were NaN'''
    ixvals = xvals.copy()
    nans = np.isnan(xvals)
    indfun = lambda z: z.flatnonzero()
    ixvals[nans]= np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), xvals[~nans])
    return ixvals

def parse_isodate(dateStr):
    '''
    Convert ISO-formatted date (e.g., 2011-12-31) to python date.    
    '''
    dateElems = dateStr.split('-')
    dateElems = [int(x) for x in dateElems]
    return datetime.date(*dateElems)


def datesrange_to_dateslist(datesRange,dateformat='%Y%m%d'):
    '''
    Create a list of date-strings (formatted accoring to dateformat) given the date limits.
    datesRange must be a list with two elements in ISO format (e.g., 2012-02-28)
    '''
    datesLims = [parse_isodate(dateStr) for dateStr in datesRange]
    allDates = [datesLims[0]+datetime.timedelta(n) \
                for n in range((datesLims[-1]-datesLims[0]).days+1)]
    allSessions = [oneDate.strftime(dateformat) for oneDate in allDates]
    return allSessions


def reverse_dict(onedict):
    '''
    Reverse dictionary so that keys become values and values become keys.
    It ignores keys if the value already exists.
    '''
    # {v:k for k, v in onedict.items()} # For Python 2.7+
    return onedict.__class__(map(reversed, onedict.items()))


def moving_average_masked(thearray,winsize,sem=False):
    '''
    Moving average that works with masked arrays (of multiple rows).

    Args:
        thearray is R x n

    Returns:
        valMean : if 'sem' is false
        (valMean,valSEM) : if 'sem' is true

    For each point, the average is taken over all elements in columns inside a
    moving window. The calculation is causal so the first elements of the result
    are the mean over less samples than nsamples.
    '''
    if len(thearray.shape)==1:
        marray=np.ma.masked_array(thearray[np.newaxis,:])
    else:
        marray = np.ma.masked_array(thearray)
    (nRepeats, nSamples) = marray.shape
    valMean = np.ma.empty(nSamples,dtype='float')
    valSEM = np.ma.empty(nSamples,dtype='float')
    for indi in range(min(nSamples,winsize)):
        thisChunk = marray[:,:indi+1]
        valMean[indi] = thisChunk.mean()
        if sem:
            valSEM[indi] = thisChunk.std()/np.sqrt(thisChunk.count())
    for indi in range(winsize,nSamples):
        thisChunk = marray[:,indi-winsize+1:indi+1]
        valMean[indi] = thisChunk.mean()
        if sem:
            valSEM[indi] = thisChunk.std()/np.sqrt(thisChunk.count())
    if sem:
        return (valMean,valSEM)
    else:
        return valMean
