#!/usr/bin/env python
"""
"""

import numpy as np
from scipy.odr import Model
from scipy.optimize import leastsq
from scipy import ndimage
from scipy.ndimage import gaussian_gradient_magnitude
from scipy.ndimage import map_coordinates

from common import PIX_ERR
from features import line_profile

def contour(img, A0, R0, phi1=-np.pi/2, phi2=np.pi/2, dphi=np.pi/180, DR=0.2,
            sigma=3):
#this is just a rough draft not intended to be working
    y0, x0 = A0
    phi = np.arange(phi1, phi2, dphi)
    x1 =  x0+R0*(1-DR)*np.cos(phi)
    y1 =  y0+R0*(1-DR)*np.sin(phi)
    x2 =  x0+R0*(1+DR)*np.cos(phi)
    y2 =  y0+R0*(1+DR)*np.sin(phi)
    rim=[]
    Nphi, = phi.shape
    for i in range(Nphi):
        A1 = np.asarray(((y1[i],x1[i]),(PIX_ERR, PIX_ERR)))
        A2 = np.asarray(((y2[i],x2[i]),(PIX_ERR, PIX_ERR)))
        metrics, metrics_err, profile = line_profile(img, A1[i], A2[i])
        rel_rim = find_rim(profile, sigma)*metrics
        
        real_rim = A1 + rel_rim
        rim.append(real_rim)
    return rim

def find_rim(profile, sigma=3):
    grad = ndimage.gaussian_gradient_magnitude(
        ndimage.gaussian_filter1d(profile,sigma) , sigma)
    return np.argmax(grad)

def line_from_points(point1, point2):
    """
    
    @param point1: array in numpy order = (y,x)
    @param point2:
    """
    k = (point2 - point1)[0] / (point2 - point1)[1]
    b = point1[0] - k * point1[1]
    return k, b

def line_perpendicular(k,b,x):
    """
    
    @param k: y=kx+b
    @param b: y=kx+b
    @param x: where the perpendicular has to intersect the line
    """
#    y = k*x+b
    k_perp = -1./k
    b_perp = (k - k_perp) * x + b
    return k_perp, b_perp

def circle_fcn(B, x, y):
    return B[0]**2 - (B[1]-x)**2 - (B[2]-y)**2

def _circle_fjacb(B,x,y):
    fjacb = np.empty((x.shape[0],3))
    fjacb[:,0] = 2*B[0]
    fjacb[:,1] = -2*(B[1]-x)
    fjacb[:,2] = -2*(B[2]-y)
    return fjacb

def _circle_fjacd(B,x,y):
    fjacd = np.empty((x.shape[0],2))
    fjacd[:,0] = 2*(B[1]-x)
    fjacd[:,1] = 2*(B[1]-y)
    return fjacd

def _circle_est(x,y):
    return np.mean((x.ptp(), y.ptp()))/2.0, x.mean(), y.mean()

def _circle_meta():
    return {'name':'Equation of a circle'}

circle_model = Model(circle_fcn, estimate=_circle_est, 
                     fjacb=_circle_fjacb, fjacd=_circle_fjacd, 
                     meta=_circle_meta, implicit=True)

def FitCircle(x,y):
    '''
    leastsq without errors
    '''
    return leastsq(circle_fcn, _circle_est(x,y), (x, y), Dfun=_circle_fjacb, full_output=1)

def section_profile(img, point1, point2):
    '''define the brightness profile along the line defined by 2 points

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
    
    dk = np.sqrt(dy1*dy1 + dy2*dy2 + k*k*(dx1*dx1+dx2*dx2) )/np.fabs(x2-x1)

    # number of points for profile
    # it is assumed that pipette is more or less horizontal
    # so that axis intersects left and right image sides
    nPoints = int(max(np.fabs(y2-y1), np.fabs(x2-x1)))

    #coordinates of points in the profile
    x = np.linspace(x1, x2, nPoints)
    y = np.linspace(y1, y2, nPoints)

    #calculate profile metric - coefficient for lengths in profile vs pixels
    if np.fabs(k) <=1:
        metric = np.sqrt(1 + k*k)
        metric_err = np.fabs(k)*dk/metric
    else:
        metric = np.sqrt(1 + 1/(k*k))
        metric_err = dk/np.fabs(metric * k*k*k)
    #output interpolated values at points of profile and profile metric
    return metric, metric_err, map_coordinates(img, [y, x], output = float)

def CircleFunc(r, N=100):
    phi = np.linspace(0,2*np.pi,N)
    return r*np.cos(phi), r*np.sin(phi)
    
def VesicleEdge_phc(img, x0, y0, r0, N=100, phi1=0, phi2=2*np.pi, sigma=1):
    Xedge = np.empty(N)
    Yedge = np.empty(N)
    for i, phi in enumerate(np.linspace(phi1, phi2, N)):
        x = x0+r0*np.cos(phi)
        y = y0+r0*np.sin(phi)
        if x < 0:
            x = 0
            y = y0+(x-x0)*np.tan(phi)
        elif x > img.shape[1]-1:
            x = img.shape[1]-1
            y = y0+(x-x0)*np.tan(phi)
        if y < 0:
            y = 0
            x = x0+(y-y0)/np.tan(phi)
        elif y > img.shape[0]-1:
            y = img.shape[1]-1
            x = x0+(y-y0)/np.tan(phi)
        
        point1 = np.asarray(((y0,x0),(PIX_ERR, PIX_ERR)))
        point2 = np.asarray(((y,x),(PIX_ERR, PIX_ERR)))
        metric, metric_err, line = section_profile(img, point1, point2)
        grad = gaussian_gradient_magnitude(line,sigma)
        pos = np.argmax(grad)
        Xedge[i] = x0+pos*np.cos(phi)*metric
        Yedge[i] = y0+pos*np.sin(phi)*metric
    return Xedge, Yedge
