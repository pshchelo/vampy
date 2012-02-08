import numpy as np
import calc

def main():    
    Rp = float(raw_input('Pipette radius: '))
    filename = 'manual-measure.txt'
    
    press, asp, pip, ves = np.loadtxt(filename, unpack=True)
    La = pip-asp
    Lv = ves-pip
    
    Rv = 0.5*(Lv*Lv+Rp*Rp)/Lv
    tau = 0.5*press/(1/Rp-1/Rv)
    
    A=2*np.pi*(Rp*La+Rv*Rv+Lv*Lv)
    alpha = A/A[0]-1
    
    slope, sd_slope, intercept, sd_intercept = calc.fitting.linregr(np.log(tau[1:]), alpha[1:])
    bend = 1./8/np.pi/slope
    print 'Bending stiffness is %f KbT'%bend
    file = open(filename, 'a')
    footer = '\n#Bending stiffness (KbT): %f'%bend
    file.write(footer)
    file.close()
    raw_input('Paused...')

def fit_tensions(x, sdx, y, sdy, modelname):
    model = calc.fitting.TENSFITMODELS[modelname]
    fitmodel = calc.analysis.TensionFitModel((x, sdx), (y, sdy), model)
    results = fitmodel.fit()
    
    for i,param in enumerate(results['params']):
        print '%s = %f +- %f %s'%(param[0], results['fit'][i], results['sd_fit'][i], param[2])
