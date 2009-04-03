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
from scipy import append, argmax, argmin, argsort, array, asarray, average, compress, \
                diag, empty, empty_like, exp, fabs, linspace, ndimage, ones_like, optimize, \
                pi, sign, sort, special, sqrt, square, sum, zeros
PIX_ERR = 0.5 # error for pixel resolution
import fitting as vfit

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
    
    dk = sqrt(dy1*dy1 + dy2*dy2 + k*k*(dx1*dx1+dx2*dx2) )/fabs(x2-x1)

    # number of points for profile
    # it is assumed that pipette is more or less horizontal
    # so that axis intersects left and right image sides
    nPoints = max(fabs(k) * (img.shape[1] - 1) + 1, img.shape[1])

    #coordinates of points in the profile
    x = linspace(0, img.shape[1] - 1, nPoints)
    y = linspace(b, k * (img.shape[1] - 1) + b, nPoints)

    #calculate profile metric - coefficient for lengths in profile vs pixels
    if fabs(k) <=1:
        metric = sqrt(1 + k*k)
        metric_err = fabs(k)*dk/metric
    else:
        metric = sqrt(1 + 1/(k*k))
        metric_err = dk/fabs(metric * k*k*k)
    #output interpolated values at points of profile and profile metric
    return metric, metric_err, ndimage.map_coordinates(img, [y, x], output = float)

def jumps_pos_steep(ar, nJumps):
    '''Finds nJumps steepest jumps (of width 1) in equidistant(=1) 1D array'''
    jumps = zeros((2, nJumps))
    for i in range(0, ar.size - 2):
        jump = fabs(ar[i] - ar[i+1])
        if jump > min(jumps[1, :]):
            jumps[:, argmin(jumps[1, :])] = asarray((i, jump))
    return sort(jumps[0, :].astype(int))

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
    y = compress(condition, y)
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
    refs = array([])
    refs_err = array([])
    for refx in refsx:
        if extra:
            extra_wall = {}
        jumps = jumps_pos_steep(
                ndimage.gaussian_laplace(img[:, refx], sigma).astype(float), 8)
        y = img[:, refx]

        fit = fit_peak(y, jumps[1] + argmin(y[jumps[1]:jumps[2]]))
        a, b, x0, s = fit[0]
        refs = append(refs, asarray((x0 + s, refx)), axis = 1)
        #taking err_x0+err_s while ref = x0+s
        refs_err = append(refs_err, sum(sqrt(diag(fit[1])[2:])))
        if extra:
            extra_wall['fit1'] = fit[0]

        fit = fit_peak(y, jumps[5] + argmin(y[jumps[5]:jumps[6]]))
        a, b, x0, s = fit[0]
        refs = append(refs, asarray((x0 - s, refx)), axis = 1)
        refs_err = append(refs_err, sum(sqrt(diag(fit[1])[2:])))
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
    ind = argsort(ar) # ascending indices of an array 
    condition = (ar[ind] == ar.max()) #condition for clipped values
    ind = compress(condition, ind) # leave only those where condition is met
    return ind.min(), ind.max()

def wall_points_phc_2(img, refsx, mismatch, extra):
    ''''''
    extra_walls = []
    refs = array([])
    refs_err = array([])
    for refx in refsx:
#        print refx
        if extra:
            extra_wall = {}
        y = img[:, refx]

        edgel, edger = max_edges(y)
        middle = int((edgel + edger) * 0.5)

        edgel1, edger1 = max_edges(y[edgel:middle])
        shift = edgel
        centerest = shift+edgel1+argmin(y[shift+edgel1:shift+edger1+1])
        fit = fit_peak(y, centerest)
        err = fiterr(fit)
        if (fit[-1] != 1) or (err == None) or (sum(err[2:]) >= mismatch):
            refs = append(refs, asarray((centerest, refx)), axis = 1)
            refs_err = append(refs_err, 1)
            print 'Pipette wall 1: No subpix rez'
        else:
            a, b, x0, s = fit[0]
            refs = append(refs, asarray((x0 + s, refx)), axis = 1)
            #taking err_x0+err_s while ref = x0+s
            refs_err = append(refs_err, sum(err[2:]))
        if extra:
            extra_wall['fit1'] = fit

        edgel2, edger2 = max_edges(y[middle:edger+1])
        shift = middle
        centerest = shift+edgel2+argmin(y[shift+edgel2:shift+edger2+1])
        fit = fit_peak(y, centerest)
        err = fiterr(fit)
        if (fit[-1] != 1) or (err == None) or (sum(err[2:]) >= mismatch):
            refs = append(refs, asarray((centerest, refx)), axis = 1)
            refs_err = append(refs_err, 1)
            print 'Pipette wall 2: No subpix rez'
        else:
            a, b, x0, s = fit[0]
            refs = append(refs, asarray((x0 - s, refx)), axis = 1)
            refs_err = append(refs_err, sum(err[2:]))
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
    
    dk = sqrt(dy1*dy1 + dy2*dy2 + k*k*(dx1*dx1+dx2*dx2) )/fabs(x2-x1)
    db = sqrt(dy1*dy1 + x1*x1*dk*dk + k*k*dx1*dx1)
    dist_err = sqrt(k*k*dx0*dx0 + dk*dk*x0*x0 + db*db + dy0*dy0 + 
                    k*k*dk*dk*(k*x0+b-y0)**2/(1+k*k))/(1+k*k)
    return asarray((fabs(dist), dist_err))

def find_edge(ar, centerest):
    '''Fits a steep change in 1D data with some suitable function'''
    sgn = sign(ar[centerest+1] - ar[centerest-1])

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
    @param refsx: tuple of points where to make a cross-profile to fine walls of the pipette
    '''
    #FIXME: BAD - relies heavily on clipped values of brightness corresponding to pipette cross-section 
    refs = array([])
    for refx in refsx:
#        print refx
        y = img[:, refx]

        edgel, edger = max_edges(y)
        middle = int((edgel + edger) * 0.5)

        edgel1, edger1 = max_edges(y[edgel:middle])
        shift = edgel
        centerest = shift+edgel1+argmin(y[shift+edgel1:shift+edger1+1])
        refs = append(refs, asarray(((centerest, refx),(PIX_ERR, 0))))
        
        edgel2, edger2 = max_edges(y[middle:edger+1])
        shift = middle
        centerest = shift+edgel2+argmin(y[shift+edgel2:shift+edger2+1])
        refs = append(refs, asarray(((centerest, refx),(PIX_ERR, 0))))
    
    return refs.reshape(-1,2,2)

def wall_points_subpix(img, refs, mode):
    return refssub, refs_err, extra_walls

def line_to_line(refs):
    '''
    Return mean distance between two (not parallel) lines
    @param refs: 3d numpy array, each refs[i,:] is a (y,x) point.
                first line is defined by refs[0] & refs[2], second line by refs[1] & refs[3] 
    '''
    #TODO: rewrite it in cycle, maybe rearrange refs for this
   
    dists = empty((2,4))
    
    dists[:,0] = point_to_line_dist(refs[0,:], refs[1,:], refs[3,:])
    dists[:,1] = point_to_line_dist(refs[1,:], refs[0,:], refs[2,:])
    dists[:,2] = point_to_line_dist(refs[2,:], refs[1,:], refs[3,:])
    dists[:,3] = point_to_line_dist(refs[3,:], refs[0,:], refs[2,:])
    dist = dists[0].mean()
    dist_err = sqrt(sum(square(dists[1])))/4
    
    return asarray((dist, dist_err))

def extract_pix(profile, sigma, minaspest, mivesest, mode):
    if mode[0] == 'phc':
        return extract_pix_phc(profile, sigma, minaspest, mivesest)
    elif mode[0] == 'dic':
        return extract_pix_dic(profile, minaspest, mivesest, mode[1])

def extract_pix_phc(profile, sigma, minaspest, minvesest):
    #gradient of gauss-presmoothed image
    grad = ndimage.gaussian_gradient_magnitude(profile, sigma)
    # find pipette tip
    pip = argmax(profile[minaspest:minvesest])+minaspest
    #aspirated vesicle edge - pixel rez
    asp = argmax(grad[:minaspest])
    #outer vesicle edge - pixel rez
    ves = argmax(grad[minvesest:]) + minvesest
    return pip, asp, ves

def extract_pix_dic(profile, minaspest, mivesest, polar):
    pip = argmax(profile[minaspest:minvesest])+minaspest
    if polar == 'right':
        asp = argmax(profile[:minaspest])
        ves = argmin(profile[minvesest:]) + minvesest
    elif polar == 'left':
        asp = argmin(profile[:minaspest])
        ves = argmax(profile[minvesest:]) + minvesest
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

def locate(**kwargs):
    '''Extracts features of interest from set of images.

    extra_out is a list of dictionaries, with every dictionary corresponds to a single image.

    '''

    images = kwargs['images'] #3d numpy array of images (uint8?)
    
    mode = kwargs['mode']

    sigma = kwargs['sigma'] #int or float parameter for Gauss smoothing of brightness profiles    
    minvesest = kwargs['minvesest'] #int (over)estimation of the aspirated tip closest to the pipette mouth
    minaspest = kwargs['minaspest'] #int (over)estimation of the outer vesicle edge closest to the pipette mouth

    subpix = kwargs['subpix'] #Bool, make subpixel resolution or not
    mismatch = kwargs['mismatch'] #int or float threshold to discard sub-pix resolution 
    extra = kwargs['extra'] #Boolean, whether to return extra outputs

    refsx = (0, minaspest) #where to measure pipette radius
    imgN = images.shape[0] #total number of images
    metrics = empty(imgN)
    metrics_err = empty_like(metrics)
    piprads = empty_like(metrics) #pipette radius
    piprads_err = empty_like(metrics)
    asps = empty_like(metrics) #aspirated edge
    asps_err = empty_like(metrics)
    pips = empty_like(metrics) # pipette tip
    pips_err = empty_like(metrics)
    vess = empty_like(metrics) # outer vesicle edge
    vess_err = empty_like(metrics)
    results = [metrics, metrics_err, piprads, piprads_err, asps, asps_err, pips, pips_err, vess, vess_err]
    extra_out = [] # list of extra outputs to return

    for imgindex in range(imgN):
        img = images[imgindex,:]
#        print "Using Image %02i"%(imgindex+1)

        #reference points on pipette walls (with respective errors)
        refs = wall_points_pix(img, refsx)
        if subpix:
            refs, refs_err, extra_walls = wall_points_subpix(img, refs, mode)
        #pipette radius
        piprad, piprad_err = line_to_line(refs)/2

        # extract brightness profile along the axis
        metric, metric_err, profile = line_profile(img, (refs[0,:]+refs[1,:])/2., (refs[2,:]+refs[3,:])/2.)
        #find features positions with pixel resolution
        pip, asp, ves = extract_pix(profile, sigma, minaspest, minvesest, mode)
        pip_err = PIX_ERR
        asp_err = PIX_ERR
        ves_err = PIX_ERR

        if subpix:
            pipfit, aspfit, vesfit = extraxt_subpix(profile, pip, asp, ves, mode)
            if extra:
                extra_img = {}
                extra_img['refs'] = refs
                extra_img['walls'] = extra_walls
                extra_img['piprad'] = asarray((piprad, pix_err))
                extra_img['profile'] = profile
                extra_img['pip'] = pip
                extra_img['pipfit'] = pipfit
                extra_img['asp'] = asp
                extra_img['aspfit'] = aspfit
                extra_img['ves'] = ves
                extra_img['vesfit'] = vesfit
                extra_out.append(extra_img)
            # use subpix only if it is within mismatch from pix
            if pipfit[-1] == 1 and fabs(pip - pipfit[0][2]) < mismatch:
                pip = pipfit[0][2]
                pip_err = fit_err(pipfit)[2]
            if aspfit[-1] == 1 and fabs(asp - aspfit[0][2]) < mismatch:
                asp = aspfit[0][2]
                asp_err = fit_err(aspfit)[2]
            if vesfit[-1] == 1 and fabs(ves - vesfit[0][2]) < mismatch:
                ves = vesfit[0][2]
                ves_err = fit_err(vesfit)[2]
        #populate arrays with results
        result = [metric, metric_err, piprad, piprad_err, asp, asp_err, pip, pip_err, ves, ves_err]
        for index, item in enumerate(results):
            item[imgindex] = result[index]
        
    # making dictionary outputs, so that to care of names and not the position 
    out = {}
    out['metrics'] = asarray((metrics, metrics_err))
    out['piprads'] = asarray((piprads, piprads_err))
    out['pips'] = asarray((pips, pips_err))
    out['vess'] = asarray((vess, vess_err))
    out['asps'] = asarray((asps, asps_err))
    return out, extra_out

if __name__ == '__main__':
    # this is executed only if this source file is run separately
    # and not imported as module to another source file.
    print __doc__