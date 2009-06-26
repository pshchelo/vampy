#!/usr/bin/env python
"""
output of various data for VAMP project
"""
### for plotting
import pylab
from numpy import linspace, log, pi
import fitting as vfit

class DataWriter():
    def __init__(self, datadict):
        self.data = datadict
        self.allfields = sorted(datadict.keys())
        self.paramfields= []
        self.datafields = self.allfields
        self._extract_param_fields()
        
    def set_fields(self, fieldslist):
        self.datafields = fieldslist
        self._extract_param_fields()
    
    def _extract_param_fields(self):
        """
        extract one-item values (parameters) from self.fields
        
        side-effect - changes self.datafields and self.paramfields
                    by moving some values from one to another
        """
        print self.datafields
        for field in self.datafields:
            print field, self.data[field].shape
            if len(self.data[field].shape) == 1:
                self.paramfields.append(field)
                self.datafields.remove(field)
        print self.paramfields
        print self.datafields
                               
    def _make_header(self):
        header = '#Data export file\n'
        if len(self.paramfields) > 0:
            for param in self.paramfields:
                value = self.data[param]
                header += '#%s (+-error): '%param
                header += len(value)*'\t%f'%tuple(value)+'\n'
        header += '#No.'
        for field in self.datafields:
            header +='\t%s\t%s_error'%(field, field)
        header += '\n'
        return header
    
    def write_file(self, filename):
        try:
            outfile = open(filename, 'w')
        except IOError:
            mesg = 'Can not open file %s for writing!'%filename
            return mesg
        outfile.write(self._make_header())
        length = self.data[self.datafields[0]].shape[-1]
#        print self.datafields
        for i in range(0, length):
            line = '%i'%(i+1)
            for field in self.datafields:
#                print field
                data = self.data[field][:,i]
                line += len(data)*'\t%f'%tuple(data)
            line += '\n'
            outfile.write(line)
        outfile.close()
        return
    
def plot_fit_full():
    return fitfunc, fit, title

def plot_fit_bend(tau, alpha, sd_tau, sd_alpha):
    fit_out = vfit.odrlinlog(tau, alpha, sd_tau, sd_alpha)
    fit_params = fit_out.beta
    fitx = linspace(tau.min, tau.max)
    fity = fitfunc(fit_params, fitx)
    fit_params[0] = 1/(8*pi*fit_params[0])
    fit_sd = fit_out.sd_beta
    fit_sd[0] = fit_sd[0]/(8*pi*fit_params[0]*fit_params[0])
    title = 'Kappa = %f+-%f KbT'%(fit_params[0], fit_sd[0])
    return fitx, fity, fit_params, fit_sd, title

def plot_fit_elast():
    return fitfunc, fit, title

def plot_fit_sep():
    return fitfunc, fit, title

FITS_IMPLEMENTED = {'bend and elast':plot_fit_full, 
        'bend':plot_fit_bend, 
        'elast':plot_fit_elast, 
        'bend or elast':plot_fit_sep}

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
    