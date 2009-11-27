#!/usr/bin/python
#generate figures for featpos.tex report
#place this file in one folder with featpos.py
import featpos as f
import scipy as s
import pylab as p

piporient = 'l'
sigma = 3
minvesest = 440
minaspest = 240
maxpipoffset = 10

img = f.readImage('img/phc-test01.tif', piporient)

refsx = (maxpipoffset, minaspest)
refs = f.wallPoints_phc(img, refsx, 3, plot = False)
x = s.linspace(0,img.shape[1]-1, img.shape[1])

metric, profile = f.lineProfile(img, (refs[0]+refs[1])/2., (refs[2]+refs[3])/2.)
grad = s.ndimage.gaussian_gradient_magnitude(profile,sigma)

pip = s.argmax(profile)
asp = s.argmax(grad[:minaspest])
ves = s.argmax(grad[minvesest:])+minvesest

p.figure(1)
p.imshow(img, cmap = p.cm.gray)
p.axvline(minvesest, color = 'yellow', lw = 0.5, ls = '-.')
p.axvline(minaspest, color = 'yellow', lw = 0.5, ls = '-.')
p.axvline(maxpipoffset, color = 'yellow', lw = 0.5, ls = '-.')
for ref in refs:
    p.plot([ref[1]], [ref[0]], 'yo')

p.annotate(r'$(x_1, y_1)$', xy = (refs[0][1], refs[0][0]), xycoords='data', 
    xytext=(5, 10), textcoords='offset points', color = 'yellow', size = 'x-large')
p.annotate(r'$(x_2, y_2)$', xy = (refs[1][1], refs[1][0]), xycoords='data', 
    xytext=(5, -30), textcoords='offset points', color = 'yellow', size = 'x-large')
p.annotate(r'$(x_3, y_3)$', xy = (refs[2][1], refs[2][0]), xycoords='data', 
    xytext=(5, 10), textcoords='offset points', color = 'yellow', size = 'x-large')
p.annotate(r'$(x_4, y_4)$', xy = (refs[3][1], refs[3][0]), xycoords='data', 
    xytext=(5, -30), textcoords='offset points', color = 'yellow', size = 'x-large')

linefunc = lambda x, p1, p2: (x-p1[1]) * (p2[0]-p1[0]) / (p2[1]-p1[1]) + p1[0]
axis = lambda x: linefunc(x, (refs[3]+refs[2])/2, (refs[1]+refs[0])/2)

p.plot(linefunc(x, refs[0], refs[2]), ls = '--', color = 'yellow')
p.plot(linefunc(x, refs[1], refs[3]), ls = '--', color = 'yellow')
p.plot(axis(x), lw = 2, color = 'yellow')
p.annotate('system axis', xy = (0.8*img.shape[1], axis(0.8*img.shape[1])), xycoords = 'data',
                xytext = (0.8, 0.2), textcoords = 'axes fraction', 
                arrowprops=dict(facecolor='yellow', shrink=0.02),
                color = 'yellow', size = 'large')
p.axis('image')

p.figure(2)
p.plot(img[:,maxpipoffset], color = 'blue', label = 'profile', lw = 2)
p.plot(s.ndimage.gaussian_laplace(img[:,maxpipoffset],sigma).astype(float),
        color = 'green', label = 'gaussian_laplace(profile)', lw = 2)
p.axvline(refs[0][0], color = 'red', lw = 2)
p.axvline(refs[1][0], color = 'red', lw = 2)
p.xlim(refs[0][0]-50, refs[1][0]+50)

p.figure(3)
p.plot(profile, color = 'blue', lw = 1.5)
p.axis('tight')
for location in (pip, ves, asp):
    p.axvspan(location-10, location+10, facecolor = 'red', alpha = 0.3)

p.figure(4)
p.plot(grad, color = 'blue', lw = 1.5)
for location in (pip, ves, asp):
    p.axvspan(location-10, location+10, facecolor = 'red', alpha = 0.3)
p.axvline(minvesest, color = 'green', lw = 1.5)
p.axvline(minaspest, color = 'green', lw = 1.5)
p.axvline(maxpipoffset, color = 'green', lw = 1.5)

p.figure(5)
vesex = f.fitEdge_phc(profile,ves, plot = True)[0][2]
p.legend(loc = 2)

p.figure(6)
def fitPeak_plot(ar,centerest,plot = False):
    '''Fits a peak to equidistant (=1) 1D data.'''
    # find whether the peak is min or max
    found = False
    ctry = centerest
    while not found:
        if ar[ctry] == min(ar[ctry-1:ctry+2]):
            sign = -1 # peak is a local minimum
            found = True
        elif ar[ctry] == max(ar[ctry-1:ctry+2]):
            sign = 1 # peak is a local maximum
            found = True
        elif ar[ctry] == ar[ctry-1] and ar[ctry] == ar[ctry+1]:
            ctry += 1
    # find left and right ends of the peak
    left = centerest
    while ar[left]*sign >= ar[left-1]*sign:left-= 1
    right = centerest
    while ar[right]*sign >= ar[right+1]*sign: right+= 1
    # shorten the peak (delete the highest side)
    y = ar[left:right+1]
    m = sign*max(sign*y[0],y[-1]*sign)
    condition = (y*sign >= sign*m) #& (y*s <= s*max(s*y))
    y = s.compress(condition, y)
    if y.size < 4:
        print "Error: peak is too narrow!"
        raise AssertionError
        sys.exit()
    # find the shift introduced by previous steps
    if ar[left] == y[0]:
        shift = left
    elif ar[right] == y[-1]:
        shift = right-y.size
    # make peak more symmetric
    lim = min(centerest-shift, y.size-1-(centerest-shift))
    # to assure that there are at least 4 points to fit
    if lim <= 1: lim = 2
    # fit the shortened and symmetrized peak
    fit = f.fitGauss(ar[centerest-lim:centerest+lim+1],sign, plot = False)
    # shift the peak center to coordinates of plot
    fit[0][2] += centerest-lim-shift
    if plot:
        p.plot(ar[left:right+1], color = 'blue', lw = 3)
        p.plot(y, color = 'green', lw = 2)
        x = s.linspace(0, lim*2, lim*2+1)+centerest-lim-shift
        p.plot(x,ar[centerest-lim:centerest+lim+1], color = 'black', lw = 1)
        gauss = lambda p, x: p[0] + p[1]*s.exp(-(x-p[2])*(x-p[2])/(2*p[3]*p[3]))
        xplot = s.linspace(0, lim*2)+centerest-lim-shift
        p.plot(xplot, gauss(fit[0], xplot), color = 'red', lw = 2)
    # shift the peak center back to coordinates of real profile
    fit[0][2] += shift
    return fit

fitPeak_plot(profile, pip, plot = True)

p.figure(7)
img2 = f.readImage('img/dic-test.tif', 'r')
p.plot(img2[206, 20:-20], color = 'blue', lw = 2)
p.axvspan(269, 284, facecolor = 'red', alpha = 0.3)
p.axvspan(345, 390, facecolor = 'red', alpha = 0.3)
p.axvspan(607, 622, facecolor = 'red', alpha = 0.3)


#~ p.figure(1)
#~ p.savefig('pipetteprofile.pdf')
#~ p.figure(2)
#~ p.savefig('pipetteaxis.pdf')
#~ p.figure(3)
#~ p.savefig('phcaxisprofile.pdf')
#~ p.figure(4)
#~ p.savefig('phcprofilegrad.pdf')
#~ p.figure(5)
#~ p.savefig('fitedge.pdf')
#~ p.figure(6)
#~ p.savefig('fitpeak.pdf')
#~ p.figure(7)
#~ p.savefig('dicaxisprofile.pdf')

print "Close all plot windows to exit.."
p.show()