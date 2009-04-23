#!/usr/bin/env python
"""
loading of various data for VAMP project
"""
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

def read_images(filenames):
    '''Reads images to numpy array
    Arguments:
    filenames - list of filenames to load

    Output:
    returnes 2-tuple of 3d numpy array
    corresponding to list of images (None in case of errors)
    and an error message if there were errors (None if success).
    '''
    test, mesg = read_grey_image(filenames[0])
    if mesg:
        return None, mesg
    images = np.empty((len(filenames), test.shape[0], test.shape[1]), test.dtype)
    for index, filename in enumerate(filenames):
        ### open the image file
        img, mesg = read_grey_image(filename)
        if mesg:
            return None, mesg
        ### test that the image has the same shape as others
        if img.shape != test.shape:
            mesg = 'Error: Images have different dimensions!'
            return None, mesg
        images[index, :] = img
    imgcfg = read_conf_file()
    return images, imgcfg, mesg

def read_conf_file():
    imgcfg = {}
    for side in SIDES:
        imgcfg[side]=0
    try:
        conffile = open('vampy-crop.cfg', 'r')
    except IOError:
        return imgcfg
    lines = conffile.readlines()
    conffile.close()
    for line in lines:
        items = line.split()
        if items[0] in SIDES:
            imgcfg[items[0]] = items[1]
    return imgcfg 
            
            
    return conf
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

def read_pressures(filename, stage):
    """
    Reads pressures from file used in acquisition.
    @param filename:
    @param stage:
    """
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
                print 'Wrong file format!'
                return None
            pressures.append(pressure)
    return np.asarray(pressures)
    