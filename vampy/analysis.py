#!/usr/bin/env python
'''Part of VAMP project, only for import.

Analysis of data presented by position of features
extracted from vesicle aspiration images.

more details are documented in vamp.tex

prerequisites - installed numpy, scipy
TODO: check for error values in dilation (too big?!)
'''
from numpy import pi, sqrt, square, log, fabs  # most common for convenience
import numpy as np
from scipy import odr

import fitting

#implemented models for calculating tension from geometry
TENSMODELS = {}

def averageImages(aver, **kwargs):
    if aver > 1:
        for key in kwargs.keys():
            val, err = kwargs[key]
            if val.ndim > 0:
                averval = val.reshape((-1,aver)).mean(axis=1)
                avererr = err.reshape((-1,aver)).mean(axis=1)
                kwargs[key] = np.asarray((averval, avererr))
    return kwargs

def get_geometry(argsdict):
    '''Calculate geometry of the system based on extracted features'''
    metrics, metrics_err = argsdict['metrics']
    piprads, piprads_err = argsdict['piprads']  # since piprad is measured directly, no scaling with metric is needed
    pips, pips_err = argsdict['pips']
    asps, asps_err = argsdict['asps']
    vess, vess_err = argsdict['vess']

    piprad = piprads.mean()
    piprad_err = sqrt(square(piprads_err).sum())/len(piprads_err)

    aspl = (pips - asps) * metrics
    aspl_err = sqrt((pips_err**2 + asps_err**2) * metrics**2 + (pips - asps)**2 * metrics_err**2)

    vesl = (vess - pips) * metrics
    vesl_err = sqrt((pips_err**2 + vess_err**2) * metrics**2 + (vess-pips)**2 * metrics_err**2)
    
    ### outer vesicle radius
    vesrad = (vesl**2 - piprad**2) / (2 * vesl)
    term = piprad**2 / (vesl**2)
    vesrad_err = sqrt(term * piprad_err**2 + (1+term)**2 * vesl_err**2 / 4.0)

    ### total vesicle surface and area
    ### outer part
    area = pi*(vesl**2 + piprad**2)
    area_err = 2*pi * sqrt(vesl**2 * vesl_err**2 + piprad**2 * piprad_err**2)
    volume = (3*piprad**2 + vesl**2) * vesl * pi/6.0
    volume_err = 0.5*pi * sqrt(4 * piprad**2 * vesl**2 * piprad_err**2 +
                                vesl_err**2 * (piprad**2 + vesl**2)**2)

    ### plus aspirated part depending on the length of aspirated part
    cond1 = (piprad <= aspl)
    cond2 = (aspl < piprad) & (aspl >= 2*vesrad - vesl)
    if not np.all(cond1^cond2): # XOR, checking that they are complimentary
        mesg = "Error with detected features in aspirated part\n"
        mesg += "Detected aspirated tip is closer\
                to the pipette mouth than possible\n"
        mesg += "Exiting..."
        return None, mesg
    area[cond1] += (2 * pi * piprad * aspl)[cond1]
    area[cond2] += (pi * (piprad**2 + aspl**2))[cond2]

    area_err[cond1] += (2*pi * sqrt(aspl**2 * piprad_err**2 +
                                    piprad**2 * aspl_err**2))[cond1]
    area_err[cond2] += (2*pi * sqrt(aspl**2 * aspl_err**2 +
                                    piprad**2 * piprad_err**2))[cond2]

    volume[cond1] += (pi * piprad**2 * (aspl - piprad/3.0))[cond1]
    volume[cond2] += ((3*piprad**2 + aspl**2) * aspl * pi/6.0)[cond2]

    volume_err[cond1] += (pi * piprad * sqrt(
                                piprad**2 * aspl_err**2 +
                                piprad_err**2 * (2*aspl-piprad)**2))[cond1]
    volume_err[cond2] += (0.5*pi * sqrt(
                                4 * piprad**2 * aspl**2 * piprad_err**2 +
                                aspl_err**2 * (piprad**2 + aspl**2)**2))[cond2]
    results = {}
    results['aspl'] = np.asarray((aspl,aspl_err))
    results['vesl'] = np.asarray((vesl,vesl_err))
    results['vesrad'] = np.asarray((vesrad,vesrad_err))
    results['area'] = np.asarray((area,area_err))
    results['volume'] = np.asarray((volume,volume_err))
    results['piprad'] = np.asarray((piprad,piprad_err))
    results['metrics'] = argsdict['metrics']
    
    ax_angle = np.arccos(1/metrics)
    ax_angle_err = metrics_err / (metrics*sqrt(metrics*metrics-1))
    results['angle'] = np.degrees(np.asarray((ax_angle, ax_angle_err)))
    
    return results, None

class TensionFitModel(object):
    def __init__(self, datax, datay, model):
        self.x, self.x_err = datax
        self.y, self.y_err = datay
        self.set_model(model)
    
    def set_model(self, model):
        self.model = model
            
    def get_func(self):
        return self.model.fcn
    
    def fit(self):
        data = odr.RealData(self.x, self.y, sx=self.x_err, sy=self.y_err)
        fitter = odr.ODR(data, self.model)
        out = fitter.run()
        report = self.model.meta
        report['fit'] = out.beta
        report['sd_fit'] = out.sd_beta
        return report
                   

def tension_evans(P, dP, scale, geometrydict):
    """
    Calculate tensions based on geometry and pressures
    according to simplest model from Evans1987
    @param P: pressure values corresponding to images, as numpy array
    @param dP: pressure accuracy 
    @param scale: physical scale of the image (um/pixel)
    @param geometrydict: dictionary of various vesicle geometry data
    """
    A, dA = geometrydict['area']
    Rv, dRv = geometrydict['vesrad']
    Rp, dRp = geometrydict['piprad']

    tau = 0.5*P/(1/Rp-1/Rv)*scale
    tau_err = scale*sqrt(dP*dP/4+tau*tau*(dRp*dRp/Rp**4+dRv*dRv/Rv**4))/fabs(1/Rp-1/Rv)
    
    alpha = (A-A[0])/A[0]
    alpha_err = sqrt(dA*dA+(A*dA[0]/A[0])**2)/A[0]
    
    tensiondata = {}
    tensiondata['tension'] = np.asarray((tau, tau_err)) #in uN/m
    tensiondata['dilation'] = np.asarray((alpha,alpha_err))
    tensiondata['tensdim'] = ('uN/m','$\\frac{\\mu N}{m}$')
    return tensiondata

TENSMODELS['Evans'] = tension_evans

def tension_henriksen(P, dP, scale, geometrydict):
    """
    Calculate tensions based on geometry and pressures
    according to the model used in Henriksen2004
    @param P: pressure values corresponding to images, as numpy array
    @param dP: pressure accuracy 
    @param scale: physical scale of the image (um/pixel)
    @param geometrydict: dictionary of various vesicle geometry data
    """
    Rv, dRv = geometrydict['vesrad']
    Rp, dRp = geometrydict['piprad']
    L, dL = geometrydict['aspl']
    
    dL0 = dL[0]
    dL = sqrt(dL**2+dL[0]**2)
    
    tau = 0.5*P/(1/Rp-1/Rv)*scale
    tau_err = scale*sqrt(dP*dP/4+tau*tau*(dRp*dRp/Rp**4+dRv*dRv/Rv**4))/fabs(1/Rp-1/Rv)
    
    gamma = 1 - (2*Rp*L[0]+Rp**2)/(4*Rv[0]**2)

    beta = 0.5*Rp*(L-L[0])/Rv[0]**2

    delta = 1.5*beta*Rp/Rv[0]

    Beta = beta+(1-delta)**(2/3)-1
    
    Delta = 1/(1-delta)**(1/3)
    
    alpha=gamma*Beta
    dalpha_dRp = -0.5*Beta*(L[0]+Rp)/Rv[0]**2 + gamma*beta*(1/Rp-2*Delta/Rv[0])
    dalpha_dRv = 2*Beta*(1-gamma)/Rv[0]**2+gamma*beta*(3*Rp*Delta/Rv[0]-2/Rv[0])
    dalpha_dL0 = -0.5*Rp*Beta/Rv[0]**2
    dalpha_dL = 0.5*gamma*Rp*(1-Rp*Delta*Rv[0])/Rv[0]**2
    
    alpha_err = sqrt(dalpha_dRp**2*dRp**2+dalpha_dRv**2*dRv**2+
                      dalpha_dL**2*dL**2+dalpha_dL0**2*dL0**2)
    
    tensiondata = {}
    tensiondata['tension'] = np.asarray((tau, tau_err)) #in uN/m
    tensiondata['dilation'] = np.asarray((alpha, alpha_err))
    tensiondata['tensdim'] = ('uN/m','$\\frac{\\mu N}{m}$')
    return tensiondata

TENSMODELS['alpha corr']=tension_henriksen

### alpha ~ log(tau), simple model
def dilation_bend_evans(tau, slope, intercept):
    return slope*log(tau)+intercept

def dilation_elas_evans(tau, slope, intercept):
    return slope*tau+intercept

### model for kappa from alpha ~ log(tau), simple model
def bending_evans(tau, alpha, tau_sd, alpha_sd):
    fit = fitting.odrlin(log(tau), alpha, tau_sd/tau, alpha_sd)
    slope, intercept = fit.beta
    slope_sd, intercept_sd = fit.sd_beta
    bend = 1/(8*pi*slope)
    bend_sd = slope_sd/(8*pi*slope*slope)
#    tau0 = exp(-intercept/slope)
#    tau0_sd = sqrt(slope*slope*intercept_sd*intercept_sd + slope_sd*slope_sd*intercept*intercept)*tau0/(slope_sd*slope_sd)
    return slope, intercept, bend, bend_sd

def elastic_evans(tau, alpha, tau_sd, alpha_sd):
    fit = fitting.odrlin(tau, alpha, tau_sd, alpha_sd)
    slope, intercept = fit.beta
    slope_sd, intercept_sd = fit.sd_beta
    elas = 1/slope
    elas_sd = slope_sd/(slope*slope)
    return slope, intercept, elas, elas_sd

def bend_elas_evans(tau, A, tau_sd, A_sd):
    fit = fitting.odr_Rawitz(tau, A, tau_sd, A_sd)
    return fit
    
if __name__ == '__main__':
    ### this is executed only if this source file is run separately
    ### and not imported as module to another source file.
    print __doc__