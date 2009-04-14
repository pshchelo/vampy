#!/usr/bin/env python
"""
command-line interface to VAMP project
"""
import sys  # for system level operations
import glob  # for file searchng

from vampy import analysis, features, load, output_cli
from cliutils import *
SIDES = ('left', 'right', 'top', 'bottom')

def get_input(defaults):
    '''Get inputs for extract_features procedure.'''
    arg_dict = {}
    crop = {}
    if defaults:
        folder = 'img-phc'
        fileext = 'tif'
        crops = [80, 150, 150, 80]
        crop = dict(zip(SIDES, crop))
        orientation = 'left'
        
        arg_dict['mode'] = 'phc', 'left'
        
        arg_dict['minvesest'] = 350
        arg_dict['minaspest'] = 100
        arg_dict['sigma'] = 3.0
        
        arg_dict['subpix'] = False
        arg_dict['mismatch'] = 3.0
        arg_dict['extra'] = False

        print "Using defaults."
    else:
        ### gathering info on what files to load
        folder = ask_string('Directory to load?', 'img-phc')
        fileext = ask_string('File ext to load?', 'tif')

        ### image croppings
        for side in SIDES:
            mesg = 'Cropping for %s side?'%side
            crop[side] = ask_int(mesg, 0)

        ### pipette orientation flag, member of piporientations
        ### means which side of the picture does pipette intersect
        ### is used afterwards to transforn the picture to the 'l' orientation
        mesg = 'Images orientation?'
        orientation = ask_choice(sides, mesg, 'left')

        ### estimation of the vesicle center closest to the pipette tip
        mesg = 'Minimal vesicle edge estimation?'
        arg_dict['minvesest'] = ask_int(mesg, 440)

        ### estimation of aspirated tip closest to the pipette tip
        mesg = 'Minimal aspirated edge estimation?'
        arg_dict['minaspest'] = ask_int(mesg, 240)

        ### check input params
        if not (arg_dict['minvesest'] > arg_dict['minaspest'] and
                arg_dict['minaspest'] > arg_dict['maxpipoffset']):
            print 'Wrong parameters. Exiting...'
            sys.exit()

        ### width parameter for a gaussian filtering
        mesg = 'Gauss presmoothing strength?'
        arg_dict['sigma'] = ask_float(mesg, 3.0)

        ### mismatch parameter for a fit judging
        mesg = 'Subpixel mismatch judjing?'
        arg_dict['mismatch'] = ask_float(mesg, 3.0)

        ### whether to output additional info
        arg_dict['extra'] = ask_bool('Make extra output?', False)

    ### generating list of filenames
    filenames = glob.glob(folder+'/*.'+fileext) #somehow can't sort right here
    if len(filenames) == 0:
        print 'No such files can be found. Exiting...'
        sys.exit()
    print 'Found %i images. Processing...'%len(filenames)
    filenames.sort()
    arg_dict['images'], mesg = load.read_images(filenames)
    if mesg:
        print mesg
        sys.exit()
    arg_dict['images'] = load.preproc_images(arg_dict['images'],
                                orientation, crop)
    if mesg:
        print mesg
        sys.exit()
    return arg_dict, folder

def main():
    ### get input parameters as well load images from files
    arg_dict, folder = get_input(ask_bool('Proceed with defaults?', True))
    ### actuall call for feature extraction procedure
    out, extra_out = features.locate(**arg_dict)

    if len(extra_out) > 0:  # dummy for extra returned parameters
        output_cli.extra_output(extra_out)

    geometry, mesg = analysis.get_geometry(**out)
    if ask_bool('Make file output?', False):
        output_cli.file_output(folder, out['pipradius'], **geometry)

    if ask_bool('Plot results?', True):
        output_cli.plot_output(**geometry)

if __name__ == '__main__':
    ### this is executed only if this source file is run separately
    ### and not imported as module to another source file.
    print '='*20
    print "Command-line interface to VAMP project."
    print '='*20
    main()