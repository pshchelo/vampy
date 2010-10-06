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
from numpy import sqrt, square, sum  # these are the most common ones just for convenience
import numpy as np
from scipy import ndimage
from fitting import fit_err
import smooth

from common import PIX_ERR

def section_profile(img, point1, point2):
    '''define the brightness profile along the section between 2 points

    coordinates of end points with their errors are supplied as numpy arrays 
    in notation array((y,x),(dy,dx))!
    #TODO:might as well submit other options to map_coordinates function

    '''
    # define the line given by 2 ends
    y1,x1,dy1,dx1 = point1.flatten()
    y2,x2,dy2,dx2 = point2.flatten()
    #fast solving of trivial cases
    if x1==x2:
        return 1, 0, img[y1:y2,x1]
    if y1==y2:
        return 1, 0, img[y1,x1:x2]
    
    deltax = np.fabs(x2-x1)
    deltay = np.fabs(y2-y1)
    ddeltax = np.sqrt(dx1**2+dx2**2)
    ddeltay = np.sqrt(dy1**2+dy2**2)

    longleg = max(deltax, deltay)
    shortleg = min(deltax, deltay)
    
    # number of points for profile
    nPoints = int(longleg)

    #coordinates of points in the profile
    x = np.linspace(x1, x2, nPoints)
    y = np.linspace(y1, y2, nPoints)
    #interpolated values at points of profile
    profile = ndimage.map_coordinates(img, [y, x], output = float)
    
    #calculate profile metric - coefficient for lengths in profile vs pixels
    k = np.sqrt(deltax**2+deltay**2) / longleg
    
    metric = sqrt(1-k**2)

    metric_err = PIX_ERR
    return metric, metric_err, profile

def line_profile2(img, point1, point2):
    '''define the brightness profile along the line defined by 2 points
        across the whole image

    coordinates of points with their errors are supplied as numpy arrays 
    in notation array((y,x),(dy,dx))!
    might as well submit other options to map_coordinates function

    '''
    y1,x1,dy1,dx1 = point1.flatten()
    y2,x2,dy2,dx2 = point2.flatten()
    #fast solving of trivial cases
    if x1==x2:
        return 1, 0, img[:,x1]
    if y1==y2:
        return 1, 0, img[y1,:]
    
    k = (y2 - y1) / (x2 - x1)
    b = y1 - k*x1
    
    dk = sqrt(dy1*dy1 + dy2*dy2 + k*k*(dx1*dx1+dx2*dx2) )/np.fabs(x2-x1)
    
    #find ponits of intersection with image borders
    sizey, sizex = img.shape
    ends = {'yleft':(b,0),
            'yright':((sizex-1)*k+b,sizex-1),
            'xbottom':(0,-b/k),
            'xtop':(sizey-1,(sizey-1-b)/k)}
    for key, value in ends:
        x,y = value
        if 'x' in key:
            if not (0 <= x <= sizex-1):
                ends.pop(key)
        elif 'y' in key:
            if not (0 < y < sizey-1):
                ends.pop(key)
    assert len(ends) == 2
    end1, end2 = ends.values
    
def line_profile(img, point1, point2):
    '''define the brightness profile along the line defined by 2 points
        across the whole image

    coordinates of points with their errors are supplied as numpy arrays 
    in notation array((y,x),(dy,dx))!
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

def wall_points_subpix(img, refsx, mode):
#    return refssub, refs_err, extra_walls
    return

def split_two_peaks(ar, mode):
    """
    
    @param ar:
    @param mode: >=0 if peaks are maxima, <0 if minima
    """
    indices = np.argsort(ar)
    if mode >= 0:
        indices = np.flipud(indices)
    peak1 = indices[0]
    peak2=indices[-1] #so that it works if only minimum is in the range, and no two peaks
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
    
def wall_points_pix(img, refsx, axis, pipette):
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

def extract_pix(mode, profile, minaspest, mivesest, tiplimits, darktip, smoothing):
    """
    Extract positions of pipette tip, aspirated vesicle tip and outer vesicle edge
    with pixel resolution.
    @param mode: 2-tuple of strings of image type and additional type parameter
    @param profile: actual 1D data array to process
    @param sigma: pre-smoothing parameter for various filters
    @param minaspest: rightmost overestimated position of aspirated tip
    @param minvesest: leftmost overestimated position of outer vesicle edge
    @param tiplimits: range where to look for a pipette tip
    @param darktip: bool, true if the pipette tip is a local minimum, False if it is a maximum
    """
    imgtype, polar = mode
    if imgtype == 'phc':
        return extract_pix_phc(profile, minaspest, mivesest, tiplimits, darktip, smoothing)
    elif imgtype == 'dic':
        return extract_pix_dic(polar, profile, minaspest, mivesest, tiplimits, darktip)

def extract_pix_phc(profile, minaspest, minvesest, tiplimits, darktip, smoothing):
    """
    Extract positions of pipette tip, aspirated vesicle tip and outer vesicle edge
    for Phase Contrast images with pixel resolution.
    @param profile: actual 1D data array to process
    @param smoothing: pre-smoothing parameters for various filters
    @param minaspest: rightmost overestimated position of aspirated tip
    @param minvesest: leftmost overestimated position of outer vesicle edge
    @param tiplimits: range where to look for a pipette tip
    @param darktip: bool, true if the pipette tip is a local minimum, False if it is a maximum
    """
    # find pipette tip
    tiplimleft, tiplimright = tiplimits
    tipprof = profile[tiplimleft:tiplimright]
    if darktip:
        peak1, peak2 = split_two_peaks(tipprof, 1)
        pip = np.argmin(tipprof[peak1:peak2])+peak1
        
    else:
        pip = np.argmax(tipprof)
    pip += tiplimleft
    
    #smoothing parameters
    window = smoothing['window']
    order = smoothing['order']
    mode = smoothing['mode']
    # Svitzky-Golay smoothed gradient
#    grad = smooth.savitzky_golay(profile, window, order, diff=1)
    # Smoothed gradient
    grad = smooth.smooth1d(profile, mode, order, window, diff=1)
    
    
#    #gradient of gauss-presmoothed image
#    grad = smooth.gauss(profile, order, order=1)

    #aspirated vesicle edge - pixel rez
    asp = np.argmax(abs(grad[:minaspest]))
    #outer vesicle edge - pixel rez
    ves = np.argmax(abs(grad[minvesest:])) + minvesest
    return pip, asp, ves

def extract_pix_dic(polar, profile, minaspest, minvesest, tiplimits, darktip):
    tiplimleft, tiplimright = tiplimits
    tipprof = profile[tiplimleft:tiplimright]
    pip = np.argmax(tipprof)+tiplimleft
    
    if polar == 'right':
        asp = np.argmin(profile[:minaspest])
        ves = np.argmax(profile[minvesest:]) + minvesest
    elif polar == 'left':
        asp = np.argmax(profile[:minaspest])
        ves = np.argmin(profile[minvesest:]) + minvesest
    return pip, asp, ves

def extract_subpix(profile, pip, asp, ves, mode):
    imgtype, polar = mode
    if imgtype == 'phc':
        return extract_subpix_phc(profile, pip, asp, ves)
    elif imgtype == 'dic':
        return extract_subpix_dic(profile, pip, asp, ves, polar)

#TODO: more accurate subpix code for phase contrast
def extract_subpix_phc(profile, pip, asp, ves):
#    pipfit = fit_peak(profile, pip)
#    aspfit = fit_edge_phc(profile, asp)
#    vesfit = fit_edge_phc(profile, ves)
#    return pipfit, aspfit, vesfit
    return

#TODO: more accurate subpix code for DIC
def extract_subpix_dic(profile, pip, asp, ves, polar):
#    pipfit = fit_peak(profile, pip)
#    aspfit = fit_peak(profile, asp)
#    vesfit = fit_peak(profile, ves)
#    return pipfit, aspfit, vesfit
    return

def locate(argsdict):
    '''Extracts features of interest from set of images.

    extra_out is a list of dictionaries, with every dictionary corresponds to a single image.

    '''

    images = argsdict['images'] #3d numpy array of images (uint8?)
    
    mode = argsdict['mode'], argsdict['polar']

    # parameters for smoothing of brightness profiles
    smoothing = {'mode':argsdict['smoothing'],
                 'window':argsdict['window'],
                 'order':argsdict['order'],
                 } 
    
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
        refs = wall_points_pix(img, refsx, axis, pipette)
        if subpix:
            refs, refs_err, extra_walls = wall_points_subpix(img, refs, mode)
        #pipette radius
        piprad, piprad_err = line_to_line(refs)/2

        # extract brightness profile along the axis
        metric, metric_err, profile = line_profile(img, (refs[0,:]+refs[1,:])/2., (refs[2,:]+refs[3,:])/2.)
        #find features positions with pixel resolution
        pip, asp, ves = extract_pix(mode, profile, minaspest, minvesest, tiplimits , darktip, smoothing)
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
            pipfit, aspfit, vesfit = extract_subpix(mode, profile, pip, asp, ves)
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