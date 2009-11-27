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
    
def weighted_average(x, sd, out=False):
    '''Calculates weighted average and it's standard deviation (normal and corrected for under/over dispersion'''
    ave = np.average(x)
    avew = np.average(x, weights=sd)
    avewvar= 1/np.sum(1/sd**2)
    avewvarcorr=avewvar*np.sum((x-avew)**2/sd**2)/(len(x)-1)
    if out:
        print 8*'='
        print 'x ave:', ave
        print "sd ave:", np.average(sd)
        print "sd ssq ave:", np.sqrt(np.sum(sd**2))/len(sd)
        print "x avew:", avew
        print "sd of avew:", np.sqrt(avewvar)
        print "corrected sd of avew:", np.sqrt(avewvarcorr)
        return
    else:
        return ave, avew, np.sqrt(avewvar), np.sqrt(avewvarcorr)