'''
Created on 23 Oct 2009

@author:
'''
import os.path

_OWNDIR = os.path.dirname(__file__)
_RES_DIR = os.path.join(_OWNDIR, 'res')

def _get_res_file(filename):
    return os.path.join(_RES_DIR, filename)

WXPYTHON = _get_res_file('wxpython.png')
SAVETXT = _get_res_file('savetxt.png')
OPENTXT = _get_res_file('document-open.png')
OPENFOLDER = _get_res_file('folder-open.png')
MICROSCOPE = _get_res_file('Microscope.png')
PLOT = _get_res_file('Plot.png')
MEASURE = _get_res_file('Measure.png')
PREFS = _get_res_file('preferences-system.png')

CUSTOMART = [SAVETXT, WXPYTHON, OPENTXT, OPENFOLDER, MICROSCOPE, MEASURE, PLOT, PREFS]