#!/usr/bin/env python
'''Part of VAMP project, only for import.

Analysis of data presented by position of features
extracted from vesicle aspiration images.

more details are documented in vamp.tex

prerequisites - installed numpy, scipy

'''
from numpy import pi, sqrt, square, log, fabs, exp  # most common for convenience
import numpy as np
import fitting as vfit

def averageImages(aver, **kwargs):
    if aver > 1:
        for key in kwargs.keys():
            val, err = kwargs[key]
            if val.ndim > 0:
                averval = val.reshape((-1,aver)).mean(axis=1)
                avererr = err.reshape((-1,aver)).mean(axis=1)
                kwargs[key] = np.asarray((averval, avererr))
    return kwargs

def get_geometry(**kwargs):
    '''Calculate geometry of the system based on extracted features'''
    metrics, metrics_err = kwargs['metrics']
    piprads, piprads_err = kwargs['piprads']  # since piprad is measured directly, no scaling with metric is needed
    pips, pips_err = kwargs['pips']
    asps, asps_err = kwargs['asps']
    vess, vess_err = kwargs['vess']

    piprad = piprads.mean()
    piprad_err = sqrt(square(piprads_err).sum())/len(piprads_err)
    print 'Pipette radius: %f with error %f'%(piprad, piprad_err)

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
    piprads = piprad*np.ones_like(aspl)
    cond1 = (piprads <= aspl)
    cond2 = (aspl < piprads) & (aspl >= 2*vesrad - vesl)
    if not np.all(cond1^cond2): # XOR, checking that they are complimentary
        mesg = "Error with detected features in aspirated part\n"
        mesg += "Detected aspirated tip is closer\
                to the pipette mouth than possible\n"
        mesg += "Exiting..."
        return None, mesg
    #FIXME: all the following errors are overestimated, use sqrt(sum(square)))
    area[cond1] += (2 * pi * piprads * aspl)[cond1]
    area[cond2] += (pi * (piprads**2 + aspl**2))[cond2]

    area_err[cond1] += (2*pi * sqrt(aspl**2 * piprad_err**2 +
                                    piprads**2 * aspl_err**2))[cond1]
    area_err[cond2] += (2*pi * sqrt(aspl**2 * aspl_err**2 +
                                    piprads**2 * piprad_err**2))[cond2]

    volume[cond1] += (pi * piprads**2 * (aspl - piprads/3.0))[cond1]
    volume[cond2] += ((3*piprads**2 + aspl**2) * aspl * pi/6.0)[cond2]

    volume_err[cond1] += (pi * piprads * sqrt(
                                piprads**2 * aspl_err**2 +
                                piprad_err**2 * (2*aspl-piprads)**2))[cond1]
    volume_err[cond2] += (0.5*pi * sqrt(
                                4 * piprads**2 * aspl**2 * piprad_err**2 +
                                aspl_err**2 * (piprads**2 + aspl**2)))[cond2]
    results = {}
    results['aspl'] = np.asarray((aspl,aspl_err))
    results['vesl'] = np.asarray((vesl,vesl_err))
    results['vesrad'] = np.asarray((vesrad,vesrad_err))
    results['area'] = np.asarray((area,area_err))
    results['volume'] = np.asarray((volume,volume_err))
    results['piprad'] = np.asarray((piprad,piprad_err))
    return results, None

### model for tension
def tension_evans(P, dP, scale, **kwargs):
    """
    Calculate tensions based on geometry and pressures
    @param pressures: pressure values corresponding to images, as numpy array
    @param scale: physical scale of the image (um/pixel)
    """
    A, dA = kwargs['area']
    Rv, dRv = kwargs['vesrad']
#    piprad, piprad_err = kwargs['piprad']
    Rp, dRp = kwargs['piprad']
#    print 'Pipette radius: %f +- %f'%(Rp,dRp)
#    Rp = piprad.mean()
#    dRp = sqrt(square(piprad_err).sum())/len(piprad_err)
    ### the simplest model for tensions from Evans1987
    tau = 0.5*P/(1/Rp-1/Rv)*scale
    tau_err = sqrt(dP*dP/4+tau*tau*(dRp*dRp/Rp**4+dRv*dRv/Rv**4))/fabs(1/Rp-1/Rv)
#    tau_err[0]=0.5*dP/(1/Rp-1/Rv[0])*scale # could be avoided if the above line is written without 1/P
    
    alpha = (A-A[0])/A[0]
    alpha_err = sqrt(dA*dA+(A*dA[0]/A[0])**2)/A[0]
    
    tensiondata = {}
    tensiondata['tension'] = np.asarray((tau, tau_err))
    tensiondata['dilation'] = np.asarray((alpha,alpha_err))
#    np.savetxt('img-phc-data.csv', np.asarray((tau, alpha, tau_err, alpha_err)).transpose(), delimiter='\t')
    return tensiondata

### alpha ~ log(tau), simple model
def dilation_bend_evans(tau, slope, intercept):
    return slope*log(tau)+intercept

def dilation_elas_evans(tau, slope, intercept):
    return slope*tau+intercept

### model for kappa from alpha ~ log(tau), simple model
def bending_evans(tau, alpha, tau_sd, alpha_sd):
    fit = vfit.odrlin(log(tau), alpha, tau_sd/tau, alpha_sd)
    slope, intercept = fit.beta
    slope_sd, intercept_sd = fit.sd_beta
    bend = 1/(8*pi*slope)
    bend_sd = slope_sd/(8*pi*slope*slope)
    tau0 = exp(-intercept/slope)
    tau0_sd = sqrt(slope*slope*intercept_sd*intercept_sd + slope_sd*slope_sd*intercept*intercept)*tau0/(slope_sd*slope_sd)
    return slope, intercept, bend, bend_sd

def elastic_evans(tau, alpha, tau_sd, alpha_sd):
    fit = vfit.odrlin(tau, alpha, tau_sd, alpha_sd)
    slope, intercept = fit.beta
    slope_sd, intercept_sd = fit.sd_beta
    elas = 1/slope
    elas_sd = slope_sd/(slope*slope)
    return slope, intercept, elas, elas_sd

def bend_elas_evans(tau, A, tau_sd, A_sd):
    fit = vfit.odr_Rawitz(tau, A, tau_sd, A_sd)
    
if __name__ == '__main__':
    ### this is executed only if this source file is run separately
    ### and not imported as module to another source file.
    print __doc__