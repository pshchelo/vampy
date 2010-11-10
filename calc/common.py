'''
Miscellaneous helper functions and constants for the VamPy project
'''

from os.path import dirname
from sys import argv
import math

OWNPATH = dirname(argv[0])

SIDES = ['left','right','top','bottom']
DATWILDCARD = "Data files (TXT, CSV, DAT)|*.txt;*.TXT;*.csv;*.CSV;*.dat;*.DAT | All files (*.*)|*.*"
CFG_FILENAME = 'vampy.cfg'

DEFAULT_SCALE = 0.31746  # micrometer/pixel, Teli CS3960DCL, 20x overall magnification, from the ruler
DEFAULT_PRESSACC = 0.00981  # 1 micrometer of water stack in Pascals
PIX_ERR = 0.5  # error for pixel resolution

def split_to_int(line, dflt=None):
    mesg=None
    if line == '':
        return dflt, mesg
    if dflt == None:
        strlst = line.split()
    else:
        Nval = len(dflt)
        strlst = line.split()[0:Nval]
        if len(strlst) != Nval :
            mesg = 'Wrong format, using defaults...'
            return list(dflt), mesg
    try:
        value = map(int, strlst)
    except ValueError:
        value = list(dflt)
        mesg = 'Values could not be converted, using defaults...'
    return value, mesg

def grid_size(N):
    """
    Find optimal dimensions to put elements on 2D grid,
    with the resulting grid being as quadratic as possible.
    @param N: number of elements to put on a grid
    """
    n = int(math.ceil(math.sqrt(N)))
    m = int(math.ceil(N/float(n)))
    return n,m