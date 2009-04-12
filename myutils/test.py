#!/usr/bin/env python
"""
test pieces for VAMP project
"""
### from scipy cookbook
def smooth(x,window_len=10,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    todo: the window parameter could be the window itself if an array instead of a string
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=numpy.r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='same')
    return y[window_len-1:-window_len+1]

### found on scipy-users mailing list
def canny(image, high_threshold, low_threshold):
    '''Canny edge finding'''
    grad_x = ndimage.sobel(image, 0)
    grad_y = ndimage.sobel(image, 1)
    grad_mag = numpy.sqrt(grad_x**2+grad_y**2)
    grad_angle = numpy.arctan2(grad_y, grad_x)
    # next, scale the angles in the range [0, 3] and then round to quantize
    quantized_angle = numpy.around(3 * (grad_angle + numpy.pi) / (numpy.pi * 2))
    # Non-maximal suppression: an edge pixel is only good if its  magnitude is
    # greater than its neighbors normal to the edge direction. We quantize
    # edge direction into four angles, so we only need to look at four
    # sets of neighbors
    NE = ndimage.maximum_filter(grad_mag, footprint=_NE)
    W  = ndimage.maximum_filter(grad_mag, footprint=_W)
    NW = ndimage.maximum_filter(grad_mag, footprint=_NW)
    N  = ndimage.maximum_filter(grad_mag, footprint=_N)
    thinned = (((grad_mag > W)  & (quantized_angle == _N_d )) |
              ((grad_mag > N)  & (quantized_angle == _W_d )) |
              ((grad_mag > NW) & (quantized_angle == _NE_d)) |
              ((grad_mag > NE) & (quantized_angle == _NW_d)) )
    thinned_grad = thinned * grad_mag
    # Now, hysteresis thresholding: find seeds above a high threshold,  then
    # expand out until we go below the low threshold
    high = thinned_grad > high_threshold
    low = thinned_grad > low_threshold
    canny_edges = ndimage.binary_dilation(high, iterations=-1, mask=low)
    return grad_mag, thinned_grad, canny_edges

def maxpeakspos(ar, delta=10):
    '''in array find positions of peaks with given width delta (default = 10)'''
    peaks = asarray(())
    for i in range(delta/2, ar.size-delta/2):
        if ar[i] == max(ar[i-delta/2:i+delta/2]):
            peaks = append(peaks, i)
    return peaks.astype(int)

def peakspos(mode, ar, nPeaks, delta=5):
    '''in 1d-array ar find positions of (minimal or maximal) peaks
    with given halfwidth delta (default = 5), sort them according to
    "sharpness" of the peak and output positions of nPeaks sharpest ones.
    '''
    peaks = zeros((2,nPeaks))

    if mode == 'min':
        for i in range(delta, ar.size-delta):
            if ar[i] == min(ar[i-delta:i+delta]):
                sharp = min(max(ar[i-delta:i]),max(ar[i:i+delta])) - ar[i]
                if sharp > min(peaks[1,:]):
                    peaks[:,argmin(peaks[1,:])] = asarray((i,sharp))
    elif mode == 'max':
        for i in range(delta, ar.size-delta):
            if ar[i] == max(ar[i-delta:i+delta]):
                sharp = max(min(ar[i-delta:i]),min(ar[i:i+delta])) - ar[i]
                if sharp > min(peaks[1,:]):
                    peaks[:,argmin(peaks[1,:])] = asarray((i,sharp))
    else:
        raise TypeError
    return peaks[0,:].astype(int)


def fitline(y):
    '''fit line to equidistant array y'''
    fitfunc = lambda p, x: p[0] + p[1] * x
    errfunc = lambda p, x, y: y - fitfunc(p, x)
    x = linspace(0,y.size-1, y.size)
    pinit = ((y[-1]-y[0])/(x[-1] - x[0]),
               y[0]-x[0]*(y[-1]-y[0])/(x[-1] - x[0]))
    return optimize.leastsq(errfunc, pinit, args=(x,y))

def jumpspos_fit(ar, nJumps, delta):
    '''find steep jumps of width delta (=5) in 1d-array ar, that are not peaks
    '''
    jumps = zeros((3,nJumps))
    #jumps[0,:] = positions of points
    #jumps[1,:] = |k| at corresponding points
    #jumps[3,:] = jump value (max-min) around corresponding points
    for i in range(delta, ar.size-delta):
        (b,k),ierr = fitline(ar[i-delta:i+delta])
        if fabs(k) >= min(jumps[1,:]) and \
           not any(fabs(jumps[0,:]-i) <= (delta+delta)) and \
           ar[i-delta:i+delta].ptp() >= min(jumps[2,:]):
                jumps[:,argmin(jumps[2,:])] = asarray((i,fabs(k),
                                                ar[i-delta:i+delta].ptp()))
    print jumps.transpose().astype(int)
    return jumps[0,:].astype(int)

def jumpspos_jumps(ar,nJumps, delta):
    ''''''
    jumps = zeros((2,nJumps))
    for i in range(delta, ar.size-delta):
        jump = ar[i-delta:i+delta].ptp()
        if jump > min(jumps[1,:]) and \
           not any(fabs(jumps[0,:]-i) <= (delta+delta)):
            jumps[:,argmin(jumps[1,:])] = asarray((i,jump))
    print jumps.transpose().astype(int)
    return jumps[0,:].astype(int)

def jumpspos_dif(ar,nJumps, delta):
    ''''''
    jumps = zeros((3,nJumps))
    for i in range(delta, ar.size-delta):
        jump = ar[i-delta:i+delta].ptp()
        if jump > min(jumps[1,:]) and \
           not any(fabs(jumps[0,:]-i) <= (delta+delta)):
            jumps[:,argmin(jumps[1,:])] = asarray((i,jump))
    print jumps.transpose().astype(int)
    return jumps[0,:].astype(int)

def minpeaksspos(ar, nPeaks, delta=10):
    '''in 1d-array ar find positions of peaks with given width delta (default = 10),
    sort them according to "sharpness" of the peak and output positions of
    nPeaks sharpest ones
    '''
    peaks = zeros(2,nPeaks)
    for i in range(delta/2, ar.size-delta/2):
        if ar[i] == min(ar[i-delta/2:i+delta/2]):
            sharp = fabs(a[i] - max(ar[i-delta/2:i+delta/2]))
            if sharp >= max(peaks[1,:]):
                peaks[:,argmin(peaks[1,:])] = array[i,sharp]

    return peaks[0,:].astype(int)

def deriv(ar):
    '''calculate derivative of data in numpy-array ar

    ar.shape = (...,2)
    ar[][0] is argument
    ar[][1] is function to derivate
    output has the same structure with length 1 shorter
    and argument values in the middle between corresponding input arguments
    '''

    deriv = zeros((ar.shape[0]-1,2))
    for i in range(deriv.shape[0]):
        deriv[i][0] = (ar[i][0]+ar[i+1][0])/2.0
        deriv[i][1] = (ar[i+1][1]-ar[i][1])/(ar[i+1][0]-ar[i][0])
    return deriv

def maxroot(ar):
    '''Calculate the maximum gap through the x-axis'''
    f = zeros(ar.shape[0]-1)
    for i in range(f.size):
        if (ar[i][1]*ar[i+1][1] < 0):
            f[i] = fabs(ar[i][1]-ar[i+1][1])
        else:
            f[i]=0
    return f

def fitBoltzm(y,x0,plot = 'no'):
    '''Fit equidistant (distance = 1) data with Boltzmann function.'''
    fitfunc = lambda p,x: p[0]+p[1]/(1+exp((x-p[2])/p[3]))
    errfunc = lambda p,x,y: y-fitfunc(p,x)
    x = linspace(0,y.size-1, y.size)
    pinit = (min(y),y.ptp(),x0,-y.ptp()/((y[x0+1]-y[x0-1])*2))
    fit = optimize.leastsq(errfunc, pinit, args=(x,y))
    ### test plotting
    if plot == 'yes':
        xplot = linspace(0,y.size-1)
        p.plot(xplot,fitfunc(fit[0],xplot), color = 'red')
        p.plot(xplot,fitfunc(pinit,xplot), color = 'magenta')
    return fit

def fitErf(y,x0,plot = 'no'):
    '''Fit equidistant (distance = 1) data with error function.'''
    fitfunc = lambda p,x: p[0]+p[1]*special.erf((x-p[2])/p[3])
    errfunc = lambda p,x,y: y-fitfunc(p,x)
    x = linspace(0,y.size-1, y.size)
    pinit = (y[x0],y.ptp()/2.0,x0,2.0*y.ptp()/((y[x0+1]-y[x0-1])*sqrt(pi)))
    fit = optimize.leastsq(errfunc, pinit, args=(x,y))
    ### test plotting
    if plot == 'yes':
        xplot = linspace(0,y.size-1)
        p.plot(xplot,fitfunc(fit[0],xplot), color = 'green')
        p.plot(xplot,fitfunc(pinit,xplot), color = 'yellow')
    return fit

#peakspos = maxpeakspos(line) #positions of peaks

#positions of peaks sorted ascending by the peak value
#peakspossorted = take(peakspos, argsort(take(line, peakspos)))

#check for double entries and find 3 maximal values

#this is a straight-forward element-wise elimination of double entries
#maximapos = zeros(3)
#i = 0
#j=1
#sort out plateu-like peaks
#while i <= 2:
#    if line[peakspossorted[-j-1]] != line[peakspossorted[-j]]:
#        maximapos[i] = peakspossorted[-j]
#        i += 1
#    j += 1

# this is too twisted, but it's somehow the numpy way
# (no direct element-wise operations) and it works.
# but can it be simplified??? it's too non-Pythonic...
#maximapos = take(peakspossorted, searchsorted(take(line,peakspossorted),
#                unique(sort(take(line,peakspos)))))

# assuming we are interested only in 3 highest peaks (2 from pipette
# and 1 from outer vesicle) and lowest minimum (vesivle tip)
#maximapos = append(maximapos[maximapos.size-3:],minpeak)
#
#print "4 points of interest are at:", maximapos

#===============================================================================
#
#f = maxroot(deriv(line))
#
#
#fsorted = argsort(f)
#
#for i in range(1,11):
#    print f[fsorted[-i]], line[fsorted[-i]][0]


#x = linspace(0,profile.size,profile.size)
#tck = interpolate.splrep(x,profile)
#x1 = linspace(0,profile.size,profile.size*100)
#y = interpolate.splev(x1, tck)
#plot(x,profile, 'o', x1,y)

#file = open('test.out', 'w')
#writer = csv.writer(file, delimiter = '\t')
#for i in range(line.shape[0]-1):
#    out = (line[i][0], line[i][1], deriv[i][0], deriv[i][1])
#    writer.writerow(out)
#file.close()