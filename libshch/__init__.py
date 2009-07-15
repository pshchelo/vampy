#!/usr/bin/env python
'''Package initialization file'''

import cliutil, util, wxutil

from os.path import join, dirname 
_OWNDIR = dirname(__file__)
_RES_DIR = join(_OWNDIR, 'res')

def _get_res_file(filename):
    return join(_RES_DIR, filename)

WXPYTHON = _get_res_file('wxpython.png')
SAVETXT = _get_res_file('savetxt.png')

CUSTOMART = [SAVETXT, WXPYTHON]