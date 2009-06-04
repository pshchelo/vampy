#!/usr/bin/env python
"""
loading of various data for VAMP project
"""
import os
import numpy as np
### for loading images to numpy arrays with PIL
from scipy import misc

SIDES = ['left', 'right', 'top', 'bottom']

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
        items = line.split(None,1)
        imgcfg[items[0]] = items[1].rstrip('\n')
    return imgcfg

def preproc_images(images, orientation, crop):
    '''prepocess images
    orientations - member of SIDES
    crop - dictionary with keys as SIDES,
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
    mesg = None
    presfile = open(filename, 'r')
    lines = presfile.readlines()
    presfile.close()
    pressures = []
    for line in lines:
        if line[0] != '#':
            elements = line.split()
            try:
                pressure = float(elements[stage])
            except(ValueError):
                mesg = 'Wrong pressure file format! (%s)'%line
                return None, mesg
            pressures.append(pressure)
    return np.asarray(pressures), mesg

def read_pressures_filenames(filenames, stage):
    mesg = None
    pressures = []
    index = []
    for filename in filenames:
        filename = os.path.basename(filename)
        pressstring, ext = os.path.splitext(filename)
        pressstring = pressstring.replace('-', ' ')
        pressstring = pressstring.replace('_', ' ')
        elements = pressstring.split()
        try:
            pressure = float(elements[stage+1])
            ind = int(elements[-1])
        except(ValueError):
            mesg = 'Wrong filenames format! (%s)'%filename
            return None, mesg
        pressures.append(pressure)
        index.append(ind)
    aver = max(index)+1
    press = np.unique1d(np.asarray(pressures))
#    print aver, len(press), len(pressures)
    if aver*len(press) != len(pressures):
        mesg = 'Some files are missing!'
        return None, mesg
    return press, aver, mesg
