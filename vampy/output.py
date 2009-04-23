#!/usr/bin/env python
"""
output of various data for VAMP project
"""
### for plotting
import pylab
from numpy import linspace, log, pi

FITS_IMPLEMENTED = {'bend and elast':plot_fit_full, 
        'bend':plot_fit_bend, 
        'elast':plot_fit_elast, 
        'bend or elast':plot_fit_sep}

def plot_fit_full():
    pass
def plot_fit_bend():
    pass
def plot_fit_elast():
    pass
def plot_fit_sep():
    pass
def file_output(folder, piprad, **kwargs):
    ''''''
    header = "#Images from folder %s\n"%folder
    header += "#Pipette radius is %f +- %f\n"%(piprad[0], piprad[1])
    header += "#No."
    length = kwargs.keys()[0]
    if length == 1:
        length = kwargs.keys()[-1]
    for key in sorted(kwargs.keys()):
        header += "\t%s"%key
    header += '\n'

    fileoutname = '%s.dat'%folder
    mesg = 'File %s is going to be (over)written! Press Enter to proceed..'\
            %fileoutname
    raw_input(mesg)
    fileout = open(fileoutname, 'w')
    fileout.write(header)
    for i in range(0, length):
        line = '%i'%(i+1)
        for key in sorted(kwargs.keys()):
            line += '\t%f'%kwargs[key][i]
        line+= '\n'
        fileout.write(line)
    fileout.close()

def plot_output(**kwargs):
    ''''''
    x = range(0, len(kwargs['aspl'][1]))

    pylab.subplot(221)
    area, area_err = kwargs['area']
    pylab.errorbar(x, area, area_err, label='Area')
    pylab.legend()

    pylab.subplot(222)
    volume, volume_err = kwargs['volume']
    pylab.errorbar(x, volume, volume_err, label='Volume')
    pylab.legend()

    pylab.subplot(223)
    vesrad, vesrad_err = kwargs['vesrad']
    pylab.errorbar(x, vesrad, vesrad_err, label='Vesicle Radius')
    pylab.legend()

    pylab.subplot(224)
    aspl, aspl_err = kwargs['aspl']
    pylab.errorbar(x, aspl, aspl_err, label='Aspirated Length')
    pylab.legend()

    print "Close all plot windows to continue..."
    pylab.show()

def extra_output(args):
    ''''''
    pass  # dummy for extra returned parameters

def plot_tensions(**kwargs):
    tau = kwargs['tension']
    area = kwargs['dilation']
    slope, intercept = kwargs['fit']
    print slope, intercept
    pylab.semilogx(tau, area, label = 'Area dilation vs tension')
    pylab.title('kappa = %f'%(1/(8*pi*slope[0])))
    x = linspace(log(tau[0]),log(tau[-1]))
    pylab.plot(x, intercept[0]+log(x)*slope[0], label = 'Fit')
    pylab.legend()
    print "Close all plot windows to continue..."
    pylab.show()
    