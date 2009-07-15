#!/usr/bin/env python
'''VAMPy - package for the VAMP project.'''

import analysis, features, fitting, load, output

from os.path import dirname
from sys import argv 
OWNPATH = dirname(argv[0])

SIDES = ['left','right','top','bottom']
DATWILDCARD = "Data files (TXT, CSV, DAT)|*.txt;*.TXT;*.csv;*.CSV;*.dat;*.DAT | All files (*.*)|*.*"
DEFAULT_SCALE = 0.31746  # micrometer/pixel, Teli CS3960DCL, 20x overall magnification, from the ruler
DEFAULT_PRESSACC = 0.00981  # 1 micrometer of water stack
CFG_FILENAME = 'vampy.cfg'

TENSFITMODELS = {'Bend Evans':fitting.bend_evans_model,
                 'Stretch simple':fitting.stretch_simple_model}

TENSMODELS = {'Evans':analysis.tension_evans}