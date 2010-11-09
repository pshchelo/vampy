#!/usr/bin/env python
"""
loading of various data for VAMP project
"""
import os
import numpy as np
### for loading images to numpy arrays with PIL
from scipy import misc
from vampy.common import PIX_ERR

def read_grey_image(filename):
    '''read single greyscale image'''
    mesg = None
    try:
        img = misc.imread(filename) #8bit as uint8, 16bit as int32
    except(IOError):
        mesg = "Error: Can't open file %s!"%filename
        return None, mesg
    ### check for greyscale
    if img.ndim > 2:
        mesg = "Error: file %s is not greyscale!"%filename
        return None, mesg
    ### check if the image was more than 8-bit - scipy/PIL has a bug on it
    if img.dtype == np.int32:
        img = np.asarray(np.asfarray(img), np.int32)
    return img, mesg

def read_conf_file(filename):
    imgcfg = {}
    try:
        conffile = open(filename, 'r')
    except IOError:
        return imgcfg
    lines = conffile.readlines()
    conffile.close()
    for line in lines:
        key, value = line.split(None,1)
        imgcfg[key] = value.rstrip('\n')
    return imgcfg

def preproc_images(images, orientation, crop):
    '''prepocess images
    orientations - member of vampy.SIDES
    crop - dictionary with keys as vampy.SIDES,
           with respective relative crop amounts'''
    ### crop image
    crop['bottom'] = images.shape[1] - crop['bottom']
    crop['right'] = images.shape[2] - crop['right']
    images = images[:,crop['top']:crop['bottom'], crop['left']:crop['right']]
    
    ### rotate according to orientation flag
    rolled = np.rollaxis(np.rollaxis(images, 1), 2, 1)  # make first axis last
    if orientation == 'right':
        rolled = np.rot90(rolled, 2)  # rot90 rotates only 2 first axes
    if orientation == 'top':
        rolled = np.rot90(rolled, 1)
    elif orientation == 'bottom':
        rolled = np.rot90(rolled, 3)
    return np.rollaxis(rolled, 2)  # bring the original first axis back from last

def read_pressures_file(filename, stage):
    """
    Reads pressures from file used in acquisition.
    @param filename:
    @param stage:
    """
    try:
        pressures = np.loadtxt(filename, unpack=1)
    except IOError, value:
        return None, value
    except ValueError, value:
        return None, value
    return np.asarray(pressures)[stage], None

def read_pressures_filenames(filenames, stage):
    mesg = None
    pressures = []
    index = []
    fnames = map(os.path.basename, filenames)
    pressstrings, exts = zip(*map(os.path.splitext, fnames))
    try:
        ind, press1, press2, subind = zip(*[x.replace('_','-').split('-') for x in pressstrings])
    except ValueError:
        mesg = 'Wrong filenames format!'
        return None, None, mesg   
    aver = len(filenames)/len(np.unique(ind))
    if stage == 0:
        press = press1
    elif stage == 1:
        press = press2
    else:
        mesg = 'Wrong stage number supplied!'
        return None, None, mesg
    try:
        pressures = map(float, press)
    except ValueError:
        mesg = 'Wrong filenames format!'
        return None, mesg
    #reduce sequences of identical values to respective single value
    pressure = [x for i,x in enumerate(pressures) if i == 0 or x != pressures[i-1]]
    if aver*len(pressure) != len(pressures):
        mesg = 'Different number of images per pressure!'
        return None, None, mesg
    return np.asarray(pressure), aver, mesg

def read_tensions(filename):
    try:
        data = np.loadtxt(filename, unpack=True)
    except IOError, value:
        return None, value
    except ValueError, value:
        return None, value
    tensiondata={}
    tensiondata['tensdim'] = ('tension units', 'tension units')
    tensiondata['dilation'] = data[1:3]
    tensiondata['tension'] = data[3:5]
    return tensiondata, None

def read_geometry_simple(filename):
    """Read hand-measured geometry file
    
    This must be a tab-separated file (with #-comments if necessary) with 4 columns:
    pipette radius, 
    position of aspirated vesicle part, 
    position of pipette mouth, 
    position of outside part of the vesicle.
    
    The distances are assumed to already corrected by the tilt (as ImageJ does it), 
    so that the metrics is 1 and it's error is zero.
    
    The single errors are taken to be sqrt(2)*PIX_ERR for pipette radius, 
    and PIX_ERR for everything else.
    
    Returns dictionary of geometry data as accepted by analysis routines 
    and a message with reason of failure if any.
    
    """
    try:
        data = np.loadtxt(filename, unpack=True)
    except IOError, value:
        return None, value
    except ValueError, value:
        return None, value
    piprad, asp, pip, ves = data
    out={}
    out['piprads'] = np.asarray((piprad, PIX_ERR*np.sqrt(2)*np.ones_like(piprad)))
    out['asps'] = np.asarray((asp, PIX_ERR*np.ones_like(asp)))
    out['pips'] = np.asarray((pip, PIX_ERR*np.ones_like(pip)))
    out['vess'] = np.asarray((ves, PIX_ERR*np.ones_like(ves)))
    out['metrics'] = np.asarray((np.ones_like(asp), np.zeros_like(asp)))
    return out, None
    
    

def read_geometry_full():
    pass
