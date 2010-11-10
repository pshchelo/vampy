#!/usr/bin/env python
'''
Various bits and errands for VamPy project
'''
import numpy as np
from numpy import sqrt
from scipy import ndimage
import vampy.fitting as vfit
from vampy.features import split_two_peaks

PIX_ERR = 0.5

def max_edges():
    return

def find_edge(ar, centerest):
    '''Fits a steep change in 1D data with some suitable function'''
    sgn = np.sign(ar[centerest+1] - ar[centerest-1])

    #max and min are positions of local maximum and minimum
    #in direct vicinity of centerset
    max = centerest
    while ar[max] <= ar[max+sgn]:
        max += sgn
    min = centerest
    while ar[min] >= ar[min-sgn]:
        min -= sgn

    if sgn < 0:
        min, max = max, min
    #now min and max are just limiting the piece of line to fit
    fit = vfit.fit_si(ar[min-1:max+2], centerest - min + 1)

    #shift the inflection point back to initial coordinates
    fit[0][2] += min - 1
    return fit

def find_peak(ar, centerest):
    '''Fits a peak to equidistant (=1) 1D data.'''
    # find whether the peak is min or max
    found = False
    ctry = centerest
    while not found:
        if ar[ctry] == min(ar[ctry-1:ctry+2]):
            sgn = -1 # peak is a local minimum
            found = True
        elif ar[ctry] == max(ar[ctry-1:ctry+2]):
            sgn = 1 # peak is a local maximum
            found = True
        elif ar[ctry] == ar[ctry-1] and ar[ctry] == ar[ctry+1]:
            ctry += 1
    # find left and right ends of the peak
    left = centerest
    while ar[left] * sgn >= ar[left-1] * sgn:
        left -= 1
    right = centerest
    while ar[right] * sgn >= ar[right+1] * sgn:
        right += 1
    # shorten the peak (delete the highest side)
    y = ar[left:right+1]
    m = sgn * max(sgn * y[0], y[-1] * sgn)
    condition = (y * sgn >= sgn * m)
    y = np.compress(condition, y)
    # find the shift introduced by previous steps
    if ar[left] == y[0]:
        shift = left
    elif ar[right] == y[-1]:
        shift = right - y.size
    # make peak more symmetric
    lim = min(centerest - shift, y.size - 1 - (centerest - shift))
    # assure that there are at least 5 points to fit
    # that is minimum for gaussian fit with 4 fitting parameters
    if lim <= 1:
        lim = 2
    # fit the shortened and symmetrized peak
    fit = vfit.fit_gauss(ar[centerest-lim:centerest+lim+1], sgn)
    # shift the peak center back to initial coordinates
    fit[0][2] += centerest - lim
    return fit

def wall_points_phc_1(img, refsx, sigma, extra):
    '''Get 4 reference points with coordinates on pipette walls
    for Phase Contrast images
    (walls are inner inflection points of inner minima on the profile)
    '''
    extra_walls = []
    refs = np.array([])
    refs_err = np.array([])
    for refx in refsx:
        if extra:
            extra_wall = {}
        jumps = jumps_pos_steep(
                ndimage.gaussian_laplace(img[:, refx], sigma).astype(float), 8)
        y = img[:, refx]

        fit = find_peak(y, jumps[1] + np.argmin(y[jumps[1]:jumps[2]]))
        a, b, x0, s = fit[0]
        refs = np.append(refs, np.asarray((x0 + s, refx)), axis = 1)
        #taking err_x0+err_s while ref = x0+s
        refs_err = np.append(refs_err, sum(sqrt(np.diag(fit[1])[2:])))
        if extra:
            extra_wall['fit1'] = fit[0]

        fit = find_peak(y, jumps[5] + np.argmin(y[jumps[5]:jumps[6]]))
        a, b, x0, s = fit[0]
        refs = np.append(refs, np.asarray((x0 - s, refx)), axis = 1)
        refs_err = np.append(refs_err, sum(sqrt(np.diag(fit[1])[2:])))
        if extra:
            extra_wall['fit2'] = fit[0]
            extra_wall['profile'] = y
            extra_walls.append(extra_wall)
    return refs.reshape(4, 2), refs_err, extra_walls

def wall_points_phc_2(img, refsx, mismatch, extra):
    ''''''
    extra_walls = []
    refs = np.array([])
    refs_err = np.array([])
    for refx in refsx:
#        print refx
        if extra:
            extra_wall = {}
        y = img[:, refx]

        edgel, edger = max_edges(y)
        middle = int((edgel + edger) * 0.5)

        edgel1, edger1 = max_edges(y[edgel:middle])
        shift = edgel
        centerest = shift+edgel1+np.argmin(y[shift+edgel1:shift+edger1+1])
        fit = find_peak(y, centerest)
        err = vfit.fit_err(fit)
        if (fit[-1] != 1) or (err == None) or (sum(err[2:]) >= mismatch):
            refs = np.append(refs, np.asarray((centerest, refx)), axis = 1)
            refs_err = np.append(refs_err, 1)
            print 'Pipette wall 1: No subpix rez'
        else:
            a, b, x0, s = fit[0]
            refs = np.append(refs, np.asarray((x0 + s, refx)), axis = 1)
            #taking err_x0+err_s while ref = x0+s
            refs_err = np.append(refs_err, sum(err[2:]))
        if extra:
            extra_wall['fit1'] = fit

        edgel2, edger2 = max_edges(y[middle:edger+1])
        shift = middle
        centerest = shift+edgel2+np.argmin(y[shift+edgel2:shift+edger2+1])
        fit = find_peak(y, centerest)
        err = vfit.fit_err(fit)
        if (fit[-1] != 1) or (err == None) or (sum(err[2:]) >= mismatch):
            refs = np.append(refs, np.asarray((centerest, refx)), axis = 1)
            refs_err = np.append(refs_err, 1)
            print 'Pipette wall 2: No subpix rez'
        else:
            a, b, x0, s = fit[0]
            refs = np.append(refs, np.asarray((x0 - s, refx)), axis = 1)
            refs_err = np.append(refs_err, sum(err[2:]))
        if extra:
            extra_wall['fit2'] = fit
            extra_wall['profile'] = y
            extra_walls.append(extra_wall)
    return refs.reshape(4, 2), refs_err, extra_walls

def jumps_pos_steep(ar, nJumps):
    '''Finds nJumps steepest jumps (of width 1) in equidistant(=1) 1D array'''
    jumps = np.zeros((2, nJumps))
    for i in range(0, ar.size - 2):
        jump = np.fabs(ar[i] - ar[i+1])
        if jump > min(jumps[1, :]):
            jumps[:, np.argmin(jumps[1, :])] = np.asarray((i, jump))
    return np.sort(jumps[0, :].astype(int))

def wall_points_pix_1(img, refsx):
    '''
    Find reference points on the pipette for PhC image with pixel resolution
    FIXME: Is it the same for both PhC and DiC types of images???
    @param img: array representing the image
    @param refsx: tuple of points where to make a cross-profile to find walls of the pipette
    '''
    #FIXME: BAD - relies heavily on clipped values of brightness corresponding to pipette cross-section 
    refs = np.array([])
    for refx in refsx:
#        print refx
        y = img[:, refx]

        edgel, edger = max_edges(y)
        middle = int((edgel + edger) * 0.5)

        edgel1, edger1 = max_edges(y[edgel:middle])
        shift = edgel
        centerest = shift+edgel1+np.argmin(y[shift+edgel1:shift+edger1+1])
        refs = np.append(refs, np.asarray(((centerest, refx),(PIX_ERR, 0))))
        
        edgel2, edger2 = max_edges(y[middle:edger+1])
        shift = middle
        centerest = shift+edgel2+np.argmin(y[shift+edgel2:shift+edger2+1])
        refs = np.append(refs, np.asarray(((centerest, refx),(PIX_ERR, 0))))
    
    return refs.reshape(-1,2,2)

def wall_points_pix_2(img, refsx, sigma):
    """
    
    @param img:
    @param refsx:
    """
    N = 2  # number of walls to find
    refs = np.array([])
    for refx in refsx:
        prof = img[:,refx]
        gradprof = ndimage.gaussian_gradient_magnitude(prof, sigma)
        start, end = split_two_peaks(gradprof, 1)
        if start > end:
            start, end = end, start
        refy = split_two_peaks(prof[start:end], -1)+start
        dref = np.asarray([PIX_ERR, 0])
        rx = np.tile(refx,N)
        xy = np.column_stack((refy,rx))#.flatten()
        drefe = np.repeat(np.expand_dims(dref,0), N, 0)
        ref = np.concatenate((xy,drefe),1)
        refs = np.append(refs, ref)
    return refs.reshape(-1,2,2)

def wall_points_pix_3(img, refsx, axisy, sigma):
    N=2
    refs = np.array([])
    axisy = np.array([113,115])
    for i,refx in enumerate(refsx):
        prof = img[:,refx]
        mid = axisy[i]
#        mid = len(prof)/2
        filtered = ndimage.gaussian_gradient_magnitude(ndimage.sobel(prof), sigma)
        
        refy = np.asarray((np.argmax(filtered[:mid]), np.argmax(filtered[mid:])+mid))
        dref = np.asarray([PIX_ERR, 0])
        rx = np.tile(refx,N)
        xy = np.column_stack((refy,rx))#.flatten()
        drefe = np.repeat(np.expand_dims(dref,0), N, 0)
        ref = np.concatenate((xy,drefe),1)
        refs = np.append(refs, ref)
    return refs.reshape(-1,2,2)
