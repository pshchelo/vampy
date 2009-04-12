#!/usr/bin/env python
"""
loading of various data for VAMP project
"""
from scipy import asarray, empty, rollaxis, rot90
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
    if img.dtype == int32:
        img = asrray(asfarray(img), int32)
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
    images = empty((len(filenames), test.shape[0], test.shape[1]), test.dtype)
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
    return images, mesg

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
    rolled = rollaxis(rollaxis(images, 1), 2, 1)  # make first axis last
    if orientation == 'right':
        rolled = rot90(rolled, 2)  # rot90 rotates only 2 first axes
    if orientation == 'top':
        rolled = rot90(rolled, 1)
    elif orientation == 'bottom':
        rolled = rot90(rolled, 3)
    return rollaxis(rolled, 2)  # bring the original first axis back from last

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
        elements = line.split()
        try:
            pressure = float(elements[stage])
        except(ValueError):
            return None
        pressures.append(pressure)
    return asarray(pressures)
    