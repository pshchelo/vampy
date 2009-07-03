#!/usr/bin/python
'''Part of VAMP project, only for import.

Extracts feature positions from images of aspirated vesicles
(as of now only for Phase Contrast images) - extracts a brightness profile
along the system axis, finds positions of pipette tip,
vesicle and aspirated vesicle tip.

more details are documented in vamp.tex

prerequisites - installed numpy, scipy
'''
#for arrays and math
from numpy import pi, sqrt, square, sum  # these are the most common ones just for convenience
import numpy as np
from scipy import ndimage, optimize, special

import fitting as vfit

PIX_ERR = 0.5 # error for pixel resolution

def line_profile(img, point1, point2):
    '''define the brightness profile along the line defined by 2 points

    coordinates of points with their errors are supplied as numpy arrays in notation array((y,x),(dy,dx))!
    might as well submit other options to map_coordinates function

    it is assumed that pipette is more or less horizontal
    so that axis intersects left and right image sides
    '''
    # define the line going though 2 points
    y1,x1,dy1,dx1 = point1.flatten()
    y2,x2,dy2,dx2 = point2.flatten()
    k = (y2 - y1) / (x2 - x1)
    b = y1 - k*x1
    
    dk = sqrt(dy1*dy1 + dy2*dy2 + k*k*(dx1*dx1+dx2*dx2) )/np.fabs(x2-x1)

    # number of points for profile
    # it is assumed that pipette is more or less horizontal
    # so that axis intersects left and right image sides
    nPoints = max(np.fabs(k) * (img.shape[1] - 1) + 1, img.shape[1])

    #coordinates of points in the profile
    x = np.linspace(0, img.shape[1] - 1, nPoints)
    y = np.linspace(b, k * (img.shape[1] - 1) + b, nPoints)

    #calculate profile metric - coefficient for lengths in profile vs pixels
    if np.fabs(k) <=1:
        metric = sqrt(1 + k*k)
        metric_err = np.fabs(k)*dk/metric
    else:
        metric = sqrt(1 + 1/(k*k))
        metric_err = dk/np.fabs(metric * k*k*k)
    #output interpolated values at points of profile and profile metric
    return metric, metric_err, ndimage.map_coordinates(img, [y, x], output = float)

def jumps_pos_steep(ar, nJumps):
    '''Finds nJumps steepest jumps (of width 1) in equidistant(=1) 1D array'''
    jumps = np.zeros((2, nJumps))
    for i in range(0, ar.size - 2):
        jump = np.fabs(ar[i] - ar[i+1])
        if jump > min(jumps[1, :]):
            jumps[:, np.argmin(jumps[1, :])] = np.asarray((i, jump))
    return np.sort(jumps[0, :].astype(int))

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

def wall_points_phc(img, refsx, sigma, extra):
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

        fit = fit_peak(y, jumps[1] + np.argmin(y[jumps[1]:jumps[2]]))
        a, b, x0, s = fit[0]
        refs = np.append(refs, np.asarray((x0 + s, refx)), axis = 1)
        #taking err_x0+err_s while ref = x0+s
        refs_err = np.append(refs_err, sum(sqrt(np.diag(fit[1])[2:])))
        if extra:
            extra_wall['fit1'] = fit[0]

        fit = fit_peak(y, jumps[5] + np.argmin(y[jumps[5]:jumps[6]]))
        a, b, x0, s = fit[0]
        refs = np.append(refs, np.asarray((x0 - s, refx)), axis = 1)
        refs_err = np.append(refs_err, sum(sqrt(np.diag(fit[1])[2:])))
        if extra:
            extra_wall['fit2'] = fit[0]
            extra_wall['profile'] = y
            extra_walls.append(extra_wall)
    return refs.reshape(4, 2), refs_err, extra_walls

def max_edges(ar):
    '''
    Finds leftmost and rightmost indices of clipped elements in an array
    @param ar: array which is clipped by some value (has max plateaus)
    '''
    ind = np.argsort(ar) # ascending indices of an array 
    condition = (ar[ind] == ar.max()) #condition for clipped values
    ind = np.compress(condition, ind) # leave only those where condition is met
    return ind.min(), ind.max()

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
        fit = fit_peak(y, centerest)
        err = fiterr(fit)
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
        fit = fit_peak(y, centerest)
        err = fiterr(fit)
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

def point_to_line_dist(point, point1, point2):
    '''Point to line distance.
    Finds distance (unsigned) from point to line defined by 2 points
    point - point from which distance is calculated (with errors)
    point1, point2 - 2 points forming the line from which distance is calculated (with errors)

    all arguments are in numpy-array notation, i.e. array((y,x),(dy,dx))!
    '''
    y0,x0,dy0,dx0 = point.flatten()
    y1,x1,dy1,dx1 = point1.flatten()
    y2,x2,dy2,dx2 = point2.flatten()
    
    k = (y2-y1)/(x2-x1)
    b = y1-k*x1
    dist = (k*x0-y0+b)/sqrt(1+k*k)
    
    dk = sqrt(dy1*dy1 + dy2*dy2 + k*k*(dx1*dx1+dx2*dx2) )/np.fabs(x2-x1)
    db = sqrt(dy1*dy1 + x1*x1*dk*dk + k*k*dx1*dx1)
    dist_err = sqrt(k*k*dx0*dx0 + dk*dk*x0*x0 + db*db + dy0*dy0 + 
                    k*k*dk*dk*(k*x0+b-y0)**2/(1+k*k))/(1+k*k)
    return np.asarray((np.fabs(dist), dist_err))

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

def wall_points_pix(img, refsx):
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

def wall_points_subpix(img, refsx, mode):
    return refssub, refs_err, extra_walls

def split_two_peaks(ar, mode):
    """
    
    @param ar:
    @param mode: >=0 if peaks are maxima, <0 if minima
    """
    indices = np.argsort(ar)
    if mode >= 0:
        indices = np.flipud(indices)
    peak1 = indices[0]
    for pos in indices[1:]:
        left, right = peak1, pos
        if left > right:
            left, right = right, left
        if ((mode>= 0 and ar[pos] > ar[left:right+1].min()) or
            (mode < 0 and ar[pos] < ar[left:right+1].max())):
            peak2 = pos
    if peak1 > peak2:
        peak1, peak2 = peak2, peak1
    return np.asarray((peak1, peak2))
        
def wall_points_pix2(img, refsx, sigma):
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

def wall_points_pix3(img, refsx, axisy, sigma):
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
    
def wall_points_pix4(img, refsx, axis, pipette):
    piprad, pipthick = pipette
    N=2
    refs = np.array([])
    for index, refx in enumerate(refsx):
        pipprof = img[:, refx]
        center = axis[index]
        refy2 = np.argmin(pipprof[center+piprad:center+piprad+pipthick])+center+piprad
        refy1 = np.argmin(pipprof[center-piprad-pipthick:center-piprad])+center-piprad-pipthick
        refy = np.asarray((refy1, refy2))
        dref = np.asarray([PIX_ERR, 0])
        rx = np.tile(refx,N)
        xy = np.column_stack((refy,rx))#.flatten()
        drefe = np.repeat(np.expand_dims(dref,0), N, 0)
        ref = np.concatenate((xy,drefe),1)
        refs = np.append(refs, ref)
    return refs.reshape(-1,2,2)

def line_to_line(refs):
    '''
    Return mean distance between two (not parallel) lines
    @param refs: 3d numpy array, each refs[i,:] is a point with errors ((y,x),(dy,dx)).
                first line is defined by refs[0] & refs[2], second line by refs[1] & refs[3] 
    '''
    #TODO: rewrite it in cycle, maybe rearrange refs for this
   
    dists = np.empty((2,4))
    
    dists[:,0] = point_to_line_dist(refs[0,:], refs[1,:], refs[3,:])
    dists[:,1] = point_to_line_dist(refs[1,:], refs[0,:], refs[2,:])
    dists[:,2] = point_to_line_dist(refs[2,:], refs[1,:], refs[3,:])
    dists[:,3] = point_to_line_dist(refs[3,:], refs[0,:], refs[2,:])
    dist = dists[0].mean()
    dist_err = sqrt(sum(square(dists[1])))/4
    
    return np.asarray((dist, dist_err))

def extract_pix(mode, profile, sigma, minaspest, mivesest, tiplimits, darktip):
    if mode[0] == 'phc':
        return extract_pix_phc(profile, sigma, minaspest, mivesest, tiplimits, darktip)
    elif mode[0] == 'dic':
        return extract_pix_dic(mode[1], profile, minaspest, mivesest, tiplimits, darktip)

def extract_pix_phc(profile, sigma, minaspest, minvesest, tiplimits, darktip):
    # find pipette tip
#    darktip = False
    tiplimleft, tiplimright = tiplimits
    tipprof = profile[tiplimleft:tiplimright]
    if darktip:
#        peak1, peak2 = split_two_peaks(tipprof, 1)
#        pip = np.argmin(tipprof[peak1:peak2])+peak1
        peak1, peak2 = split_two_peaks(tipprof, 1)
        pip = np.argmin(tipprof[peak1:peak2])+peak1
    else:
        pip = np.argmax(tipprof)
    pip += tiplimleft
    #gradient of gauss-presmoothed image
    grad = ndimage.gaussian_gradient_magnitude(ndimage.gaussian_filter1d(profile,sigma) , sigma)
    #aspirated vesicle edge - pixel rez
    asp = np.argmax(grad[:minaspest])
    #outer vesicle edge - pixel rez
    ves = np.argmax(grad[minvesest:]) + minvesest
    return pip, asp, ves

def extract_pix_dic(profile, minaspest, mivesest, polar, darktip):
    pip = np.argmax(profile[minaspest:minvesest])+minaspest
    if polar == 'right':
        asp = np.argmax(profile[:minaspest])
        ves = np.argmin(profile[minvesest:]) + minvesest
    elif polar == 'left':
        asp = np.argmin(profile[:minaspest])
        ves = np.argmax(profile[minvesest:]) + minvesest
    return pip, asp, ves

def extract_subpix(profile, pip, asp, ves, mode):
    if mode[0] == 'phc':
        return extract_subpix_phc(profile, pip, asp, ves)
    elif mode[0] == 'dic':
        return extract_subpix_dic(profile, pip, asp, ves)

#TODO: more accurate subpix code for phase contrast
def extract_subpix_phc(profile, pip, asp, ves):
    pipfit = fit_peak(profile, pip)
    aspfit = fit_edge_phc(profile, asp)
    vesfit = fit_edge_phc(profile, ves)
    return pipfit, aspfit, vesfit

#TODO: more accurate subpix code for DIC
def extract_subpix_dic(profile, pip, asp, ves):
    pipfit = fit_peak(profile, pip)
    aspfit = fit_peak(profile, asp)
    vesfit = fit_peak(profile, ves)
    return pipfit, aspfit, vesfit

def locate(argsdict):
    '''Extracts features of interest from set of images.

    extra_out is a list of dictionaries, with every dictionary corresponds to a single image.

    '''

    images = argsdict['images'] #3d numpy array of images (uint8?)
    
    mode = argsdict['mode'], argsdict['polar']

    sigma = argsdict['sigma'] #int or float parameter for Gauss smoothing of brightness profiles    

#    int (over)estimation of the aspirated tip closest to the pipette mouth
#    int (over)estimation of the outer vesicle edge closest to the pipette mouth
    minaspest, minvesest = argsdict['aspves']
    tiplimits = argsdict['tip']

    subpix = argsdict['subpix'] #Bool, make subpixel resolution or not
    mismatch = argsdict['mismatch'] #int or float threshold to discard sub-pix resolution 
    extra = argsdict['extra'] #Boolean, whether to return extra outputs

    refsx = (0, minaspest) #where to measure pipette radius
    axis = argsdict['axis'] #points on y-values on respective refsx giving estimate of pipette axis
    pipette = argsdict['pipette'] #tuple of estimates for pipette radius and thickness
    darktip = argsdict['darktip'] #whether the pipette tip corresponds to dark or to bright
    imgN = images.shape[0] #total number of images
    metrics = np.empty(imgN) #coefficient arising from not strictly horizontal pipette axis
    metrics_err = np.empty_like(metrics)
    piprads = np.empty_like(metrics) #pipette radius
    piprads_err = np.empty_like(metrics)
    asps = np.empty_like(metrics) #aspirated edge
    asps_err = np.empty_like(metrics)
    pips = np.empty_like(metrics) # pipette tip
    pips_err = np.empty_like(metrics)
    vess = np.empty_like(metrics) # outer vesicle edge
    vess_err = np.empty_like(metrics)
    results = [metrics, metrics_err, piprads, piprads_err, asps, asps_err, pips, pips_err, vess, vess_err]
    extra_out = [] # list of extra outputs to return

    for imgindex in range(imgN):
        img = images[imgindex,:]
#        print "Using Image %02i"%(imgindex+1)

        #reference points on pipette walls (with respective errors)
#        refs = wall_points_pix2(img, refsx, sigma)
#        refs = wall_points_pix3(img, refsx, None, sigma)
        refs = wall_points_pix4(img, refsx, axis, pipette)
        if subpix:
            refs, refs_err, extra_walls = wall_points_subpix(img, refs, mode)
        #pipette radius
        piprad, piprad_err = line_to_line(refs)/2

        # extract brightness profile along the axis
        metric, metric_err, profile = line_profile(img, (refs[0,:]+refs[1,:])/2., (refs[2,:]+refs[3,:])/2.)
        #find features positions with pixel resolution
        pip, asp, ves = extract_pix(mode, profile, sigma, minaspest, minvesest, tiplimits , darktip)
        pip_err = PIX_ERR
        asp_err = PIX_ERR
        ves_err = PIX_ERR
        
        if extra:
            extra_img = {}
            extra_img['refs'] = refs
            extra_img['piprad'] = np.asarray((piprad, PIX_ERR))
            extra_img['profile'] = profile
            extra_img['pip'] = pip
            extra_img['asp'] = asp
            extra_img['ves'] = ves
                
        if subpix:
            pipfit, aspfit, vesfit = extraxt_subpix(mode, profile, pip, asp, ves)
            if extra:
                extra_img['walls'] = extra_walls
                extra_img['pipfit'] = pipfit
                extra_img['aspfit'] = aspfit
                extra_img['vesfit'] = vesfit
            # use subpix only if it is within mismatch from pix
            if pipfit[-1] == 1 and np.fabs(pip - pipfit[0][2]) < mismatch:
                pip = pipfit[0][2]
                pip_err = fit_err(pipfit)[2]
            if aspfit[-1] == 1 and np.fabs(asp - aspfit[0][2]) < mismatch:
                asp = aspfit[0][2]
                asp_err = fit_err(aspfit)[2]
            if vesfit[-1] == 1 and np.fabs(ves - vesfit[0][2]) < mismatch:
                ves = vesfit[0][2]
                ves_err = fit_err(vesfit)[2]
        #populate arrays with results
        if extra:
            extra_out.append(extra_img)
        result = [metric, metric_err, piprad, piprad_err, asp, asp_err, pip, pip_err, ves, ves_err]
        for index, item in enumerate(results):
            item[imgindex] = result[index]
        
    # making dictionary outputs, so that to care of names and not the position 
    out = {}
    out['metrics'] = np.asarray((metrics, metrics_err))
    out['piprads'] = np.asarray((piprads, piprads_err))
    out['pips'] = np.asarray((pips, pips_err))
    out['vess'] = np.asarray((vess, vess_err))
    out['asps'] = np.asarray((asps, asps_err))
    return out, extra_out

if __name__ == '__main__':
    # this is executed only if this source file is run separately
    # and not imported as module to another source file.
    print __doc__