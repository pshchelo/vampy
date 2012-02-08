#!/usr/bin/env python
'''
Here are copies from VamPy functions to produce images
'''
import numpy as np
import scipy as sp
import scipy.misc
import scipy.ndimage

PIX_ERR=0.5

def load_image(filename, crop, orientation):
	'''loads, crops and rotates single image (greyscale)'''
	img = scipy.misc.imread(filename)
	if img.dtype == np.int32:
		img = np.asarray(np.asfarray(img), np.int32)
	img= img[crop['top']:-crop['bottom'], crop['left']:-crop['right']]
	if orientation == 'right':
		img = np.rot90(img, 2)  # rot90 rotates only 2 first axes
	if orientation == 'top':
		img = np.rot90(img, 1)
	elif orientation == 'bottom':
		img = np.rot90(img, 3)
	return img
	
def wall_points_pix(img, refsx, axis, pipette):
    piprad, pipthick = pipette
    N=2
    refs = np.array([])
    for index, refx in enumerate(refsx):
        pipprof = img[:, refx]
        center = axis[index]
        refy2 = np.argmin(pipprof[center+piprad:center+piprad+pipthick])+center+piprad
        refy1 = np.argmin(pipprof[center-piprad-pipthick:center-piprad])+center-piprad-pipthick
        refy = np.asarray((refy1, refy2))
        dref = np.asarray([PIX_ERR, 0])
        rx = np.tile(refx,N)
        xy = np.column_stack((refy,rx))#.flatten()
        drefe = np.repeat(np.expand_dims(dref,0), N, 0)
        ref = np.concatenate((xy,drefe),1)
        refs = np.append(refs, ref)
    return refs.reshape(-1,2,2)

