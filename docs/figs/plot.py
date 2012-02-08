#!/usr/bin/python
#generate figures for VAMP-DOC report
import numpy as np
import scipy.ndimage
from matplotlib import pyplot as plt
import calculate as cl

#this is for the first image from 2010-09-30\1-dopc+dope(3-1)\
filename='20100930-1-01.png'
#image mode
mode = 'phc'
polar = None
#analysis settings
darktip = True
order = 2
window=11
#image preprocessing
crop={}
crop['left'] = 0
crop['right'] = 250
crop['top'] = 100
crop['bottom'] = 50
orient='right'
#feature estimates
aspves = (55, 283)
pipette = (31, 12)
axis = (125, 123)
tip = (127, 137)


minaspest, minvesest = aspves
img = cl.load_image(filename, crop, orient)
refsx = (0, aspves[0])
refs = cl.wall_points_pix(img, refsx, axis, pipette)
x = np.linspace(0,img.shape[1]-1, img.shape[1])
linefunc = lambda x, p1, p2: (x-p1[1]) * (p2[0]-p1[0]) / (p2[1]-p1[1]) + p1[0]
axisfunc = lambda x: linefunc(x, (refs[3][0]+refs[2][0])/2, (refs[1][0]+refs[0][0])/2)
profile = scipy.ndimage.map_coordinates(img, [axisfunc(x), x], output = float)
pip = np.argmin(profile[tip[0]:tip[1]])+tip[0]
grad = scipy.ndimage.gaussian_gradient_magnitude(profile,order)
asp = np.argmax(grad[:minaspest])
ves = np.argmax(grad[minvesest:])+minvesest

# pipete cross-section
plt.figure(1) 
plt.plot(img[:,minaspest], c='blue')
plt.axvline(refs[2,0,0], c='red')
plt.axvline(refs[3,0,0], c='red')
plt.axvspan(axis[1]+pipette[0]-pipette[1], axis[1]+pipette[0]+pipette[1], alpha=0.20, fc='green')
plt.axvspan(axis[1]-pipette[0]-pipette[1], axis[1]-pipette[0]+pipette[1], alpha=0.20, fc='green')


# image with pipette walls points and lines and axis
plt.figure(2)
plt.imshow(img, cmap=plt.cm.gray)
plt.plot(refs[:,0,1], refs[:,0,0], 'yo', ms=7, mew=2)
for i, ref in enumerate(refs):
    yp,xp = ref[0]
    if i%2 == 0:
        yoffset=30
    else:
        yoffset=-30
    plt.annotate('$(x_%i, y_%i)$'%(i,i), 
                        xy=(xp, yp), xycoords='data',
                        xytext=(5, yoffset), textcoords='offset points',
                        color = 'yellow', size = 'x-large')
plt.axis('image')

plt.axvline(minvesest, color = 'blue', lw=1, ls='-.')
plt.axvline(minaspest, color = 'blue', lw=1, ls='-.')

plt.plot(linefunc(x, refs[0][0], refs[2][0]), ls = '--', color = 'yellow')
plt.plot(linefunc(x, refs[1][0], refs[3][0]), ls = '--', color = 'yellow')
plt.plot(x, axisfunc(x), color = 'yellow')
plt.annotate('system axis', 
                        xy = (0.6*img.shape[1], axisfunc(0.6*img.shape[1])), xycoords = 'data',
                        xytext = (0.6, 0.2), textcoords = 'axes fraction', 
                        arrowprops=dict(facecolor='yellow', shrink=0.02),
                        color = 'yellow', size = 'large')


# pipette axis profile and regions of interest
plt.figure(3)
plt.plot(profile)
plt.axvspan(tip[0], tip[1], alpha=0.2, fc='green')
plt.axvline(pip, c='red', lw=1)

#gradient of pipette axis profile and features positions
plt.figure(4)
plt.plot(grad, c='blue')
plt.axvline(asp, c='red')
plt.axvline(ves, c='red')

## plt.figure(5)
## vesex = f.fitEdge_phc(profile,ves, plot = True)[0][2]
## plt.legend(loc = 2)

## plt.figure(6)

## fitPeak_plot(profile, pip, plot = True)

## plt.figure(7)
## img2 = f.readImage('img/dic-test.tif', 'r')
## plt.plot(img2[206, 20:-20], color = 'blue', lw = 2)
## plt.axvspan(269, 284, facecolor = 'red', alpha = 0.3)
## plt.axvspan(345, 390, facecolor = 'red', alpha = 0.3)
## plt.axvspan(607, 622, facecolor = 'red', alpha = 0.3)


plt.figure(1)
plt.savefig('pipcrosssection.pdf')
plt.figure(2)
plt.savefig('pipetteaxis.pdf')
plt.figure(3)
plt.savefig('phcaxisprofile.pdf')
plt.figure(4)
plt.savefig('phcprofilegrad.pdf')
## plt.figure(5)
## plt.savefig('fitedge.pdf')
## plt.figure(6)
## plt.savefig('fitpeak.pdf')
## plt.figure(7)
## plt.savefig('dicaxisprofile.pdf')

print "Close all plot windows to exit.."
plt.show()
