'''
Created on 23 Oct 2009

@author: family
'''

from os.path import dirname
from sys import argv 
OWNPATH = dirname(argv[0])

SIDES = ['left','right','top','bottom']
DATWILDCARD = "Data files (TXT, CSV, DAT)|*.txt;*.TXT;*.csv;*.CSV;*.dat;*.DAT | All files (*.*)|*.*"
CFG_FILENAME = 'vampy.cfg'

DEFAULT_SCALE = 0.31746  # micrometer/pixel, Teli CS3960DCL, 20x overall magnification, from the ruler
DEFAULT_PRESSACC = 0.00981  # 1 micrometer of water stack
PIX_ERR = 0.5  # error for pixel resolution