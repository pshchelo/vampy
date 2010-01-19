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

CUSTOMART = [SAVETXT, WXPYTHON]