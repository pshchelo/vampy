#!/usr/bin/env python
"""
"""

import numpy as np
from numpy import pi
from scipy.odr import Model
from scipy.optimize import leastsq
import features as feat

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
    
def RadialScanAsp(img, x0,y0,r0, phi0=3*pi/4, k0, b0):
    edge = np.array((2,1))
    alpha = np.arctan(k0)
    for theta in np.linspace(-phi0/2.,phi0/2., 100):
        x = x0-1.5*r0*np.cos(alpha+theta)
        y = y0-1.5*r0*np.sin(alpha+theta)
        
        line = feat.line_profile(img, (), ())
    return edge