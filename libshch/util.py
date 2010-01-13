'''
Various useful supporting functions
'''

import math
from scipy import ndimage
import numpy as np

def split_to_int(line, dflt=None):
    mesg=None
    if line == '':
        return dflt, mesg
    if dflt == None:
        strlst = line.split()
    else:
        Nval = len(dflt)
        strlst = line.split()[0:Nval]
        if len(strlst) != Nval :
            mesg = 'Wrong format, using defaults...'
            return list(dflt), mesg
    try:
        value = map(int, strlst)
    except ValueError:
        value = list(dflt)
        mesg = 'Values could not be converted, using defaults...'
    return value, mesg

def grid_size(N):
    """
    Find optimal dimensions to put elements on 2D grid,
    with the resulting grid being as quadratic as possible.
    @param N: number of elements to put on a grid
    """
    n = math.ceil(math.sqrt(N))
    m = math.ceil(N/float(n))
    return n,m

def get_gradient(x, sigma):
    return ndimage.gaussian_gradient_magnitude(ndimage.sobel(x), sigma)
    
def averages1d(data, sd=None):
    '''Calculate various averages of 1-D inputs
    
    @param data - array to average, 1d or 2d.
                if data.ndim = 1, then sd are standard deviations (used for weighted averaging),
                    if no sd supplied, sd = 1 for all data
                if data.ndim = 2, then data[0] assumed to be data to average and
                    data[1] to be respective standard deviations, sd argument will be ignored
                
    @param sd - 1d array, standard deviations for data. Ignored if data is 2d.
                Omitting it sets all sd for all data to be 1. 
    
    if data is no 1d or 2d, or sd is not 1d, or shapes of data and sd are different, ValueError is raised 
    
    Returns two tuples (mean, standard error) for simple and weighted averages. 
    '''
    
    if data.ndim not in (1,2):
        raise ValueError('dimension of input data is wrong')
    
    if data.shape[0] == 2: #that is data on top level consists of 2 arrays
        x = data[0]
        sd = data[1]
    else: #data is 1d
        if not sd: #if no sd, sd are equal 1, so weighted mean = arithmetic mean
            sd = np.ones_like(x)
        elif sd.shape != 1:
            raise ValueError('dimension of standard deviation is wrong')
        if x.shape != sd.shape:
            raise ValueError('mismatch of argument shapes')
    
    N = len(x) #number of samples
    mean = np.average(x) # arithmetic mean
    ssd = np.sqrt(np.sum((x-mean)*(x-mean))/(N-1)) # sample standard deviation (unbiased)
    sem = ssd/np.sqrt(N) # sample standard error
    w = 1/(sd*sd) # weights
    w = w/w.sum() #normalized weights
    w2 = np.sum(w*w)
    wmean = np.average(x, weights=w) # weighted mean
    wssd2 = 1/(1-w2)*np.sum(w*(x-wmean)*(x-wmean)) #unbiased variance estimator for weighted mean
    wsem = np.sqrt(wssd2/N) # standard error of weighted mean
    return (mean, sem), (wmean, wsem)