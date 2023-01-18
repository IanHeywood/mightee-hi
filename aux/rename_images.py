#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import re
import shutil


def natural_sort(l): 

    """
    https://stackoverflow.com/questions/4836710/is-there-a-built-in-function-for-string-natural-sort
    """

    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


suffixes = ['-psf.fits','-image.pbcor.fits','-image.pb.fits']

image_list = natural_sort(glob.glob('*image.fits'))

i = 0

for image in image_list:
	chan = str(i).zfill(4)
	opimage = image.split('.mms')[0]+'.mms_cube_r0p5-'+chan+'-image.fits'
	print(chan,image,opimage)
	for suffix in suffixes:
		infile = image.replace('-image.fits',suffix)
		outfile = opimage.replace('-image.fits',suffix)
		print(chan,infile,outfile)
	i+=1