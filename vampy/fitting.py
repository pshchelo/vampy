#!/usr/bin/env python
"""
Collection of fit procedures for VAMPy project
Provides:
classes:
 fitcurve(func, x, y, init, Dfun=None, **lsq_kwargs)
"""
from numpy import diag, exp, linspace, sqrt, pi, log
from scipy.optimize import leastsq
from scipy.special import sici
from scipy.stats import linregress
from scipy.odr import models, RealData, ODR

class fitcurve():
    """
    Simple wrapper for scipy.optimize.leastsq
    """
    def __init__(self, func, x, y, pinit, Dfun=None, **lsq_kwargs):
        """
        Constructor method
        @param func: function to fit in the form of f(params,x)
        @param x:
        @param y:
        @param pinit: initial guess for parameters
        @param Dfun: Jacobian function, see help for scipy.optimize.leastsq
        lsq_kwargs: dictionary of other options to pass to scipy.optimize.leastsq, see its help
        """
        self.func = func
        self.x = x
        self.y = y
        self.pinit = pinit
        self.Dfun = Dfun
        self.lsq_kwargs = lsq_kwargs
    
    def fit(self):
        """
        Fitting method
        Correction of raw covariance matrix with standard error of the estimate is implemented.
        returns fit results with respective standard errors, and message and success flag from leastsq
        """
        errfunc = lambda p, x, y: y - self.func(p, x)
        fit, cov, info, mesg, success = leastsq(
            errfunc, self.pinit, (self.x, self.y), Dfun = self.Dfun, full_output=1, **self.lsq_kwargs)
        df = len(self.x)-len(fit)
        #this correction is according to http://thread.gmane.org/gmane.comp.python.scientific.user/19482
        see = sqrt((errfunc(fit, self.x, self.y)**2).sum()/df)
        if cov == None:
            stderr = None
        else:
            stderr = sqrt(diag(cov))*see
        return fit, stderr, mesg, success

def odrlin(x,y, sx, sy):
    """
    Linear fit of 2-D data set made with Orthogonal Distance Regression
    @params x, y: data to fit
    @param sx, sy: respective errors of data to fit
    """
    model = models.unilinear #defines model as beta[0]*x + beta[1]
    data = RealData(x,y,sx=sx,sy=sy)
    kinit = (y[-1]-y[0])/(x[-1]-x[0]) 
    init = (kinit, y[0]-kinit*x[0])
    linodr = ODR(data, model, init)
    return linodr.run()

def alpha_Rawitz(flag):
    if flag == 'sphere':
        coeff = 1/24/pi
    elif flag == 'plane':
        coeff = 1/pi/pi
    else:
        raise AssertionError
        return
    f = lambda p,x: 1/(8*pi*p[0])*log(1+x*coeff/p[1])+x/p[2]
    return f

def odr_Rawitz(t,A,st,sA):
    pass

def nls_Rawitz(t, alpha, flag):
    f = alpha_Rawitz(flag)
    pinit = [25,1,1.0e5]
    Rawitz_fit = fitcurve(f, t, alpha, pinit)
    return Rawitz_fit.fit()

def alpha_Fournier():
    f = lambda p,x: p[0] + 1/(8*pi*p[1])*log(x)+x/p[2]
    return f

def nls_Fournier(t, alpha):
    f = alpha_Fournier()
    pinit = [0,20,200]
    Fournier_fit = fitcurve(f, t, alpha, pinit)
    return Fournier_fit.fit()

def odr_Fournier(t, alpha, dt, dalpha):
    pass

def linregr(x,y):
    """
    Linear regression made with stats.linregress
    @params x, y: data to fit as numpy array
    """
    slope, intercept, r, prob2, see = linregress(x,y)
    see = sqrt(((y-slope*x-intercept)**2).sum()/(len(x)-2)) # apparently there is a bug in stats.linregress as of scipy 0.7
    mx = x.mean()
    sx2 = ((x-mx)**2).sum()
    sd_intercept = see * sqrt((x*x).sum()/sx2/len(x))
    sd_slope = see/sqrt(sx2)
    #FIXME: check this by comparing with something else (Origin?)
    return slope, sd_slope, intercept, sd_intercept

def fit_linear(x, y):
    """
    Linear regression of data made with ONLS
    @param y: 1d-numpy array of y-values, element index is x-value
    """
    linear = lambda p, x: p[0]*x + p[1]
    kinit = (y[-1] - y[0]) / (x[-1] - x[0])
    pinit = [kinit, y[0] - kinit * x[0]]
    linfit = fitcurve(linear, x, y, pinit)
    return linfit.fit()
   
def fit_si(y, x0):
    '''Fits equidistant (=1) 1D data with integral sine.'''
    # fitting function
    integralsine = lambda p, x: p[0] + p[1] * sici((x - p[2]) / p[3])[0]
    # choose initial params
    pinit = (y[x0], y.ptp() / 3.7, x0, (y.argmax() - y.argmin()) / (2 * pi))
    x = linspace(0, y.size - 1, y.size)
    si_fit = fitcurve(integralsine, x, y, pinit)
    return si_fit.fit()
   
def fit_gauss(y, sgn):
    '''fit gaussian bell to 1-d equidistant(=1) data y'''
    # fitting function - Gaussian bell
    gauss = lambda p, x: p[0] + p[1] * exp(-(x-p[2])**2/(2*p[3]**2))
    # choose the right init params for max and min cases
    if sgn == 1:
        pinit = (min(y), sgn*y.ptp(), y.argmax(), y.size/4)
    elif sgn == -1:
        pinit = (max(y), sgn*y.ptp(), y.argmin(), y.size/4)
    x = linspace(0, y.size - 1, y.size)
    gauss_fit = fitcurve(gauss, x, y, pinit)
    return gauss_fit.fit()
      
if __name__ == '__main__':
	print __doc__