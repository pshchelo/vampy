'''
Various useful supporting functions
'''

import math
from scipy import ndimage

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