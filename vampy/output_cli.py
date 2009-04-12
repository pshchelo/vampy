#!/usr/bin/env python
"""
output of various data for VAMP project tailored for CLI version
"""
### setting this here since for CLI it should be the first time to use plotting
from matplotlib import use
use('WxAgg')  # keeping this only for the CLI version
import output as vout

def file_output(folder, piprad, **kwargs):
    vout.file_output(folder, piprad, **kwargs)
    
def plot_output(**kwargs):
    vout.plot_output(**kwargs)

def extra_output(args):
    vout.extra_output(args)
    
def plot_tensions(**kwargs):
    vout.plot_tensions()