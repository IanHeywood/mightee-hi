#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import logging
import numpy
import os
import scipy.signal
import shutil
import subprocess
import sys

from astropy import wcs
from astropy.convolution import convolve,Gaussian2DKernel
from astropy.io import fits
from multiprocessing import Pool
from datetime import datetime
from optparse import OptionParser


prefix = sys.argv[1]


date_time = datetime.now()
timestamp = date_time.strftime('%d%m%Y_%H%M%S')
logfile = 'chanconv_'+prefix+'_'+timestamp+'.log'
#logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s:: %(levelname)-5s :: %(message)s %(funcName)s', datefmt='%d/%m/%Y %H:%M:%S ')
logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s:: %(levelname)-5s :: %(message)s', datefmt='%d/%m/%Y %H:%M:%S ',force=True)
logging.getLogger().addHandler(logging.StreamHandler())



def get_image(fitsfile):
        input_hdu = fits.open(fitsfile)[0]
        if len(input_hdu.data.shape) == 2:
                image = numpy.array(input_hdu.data[:,:])
        elif len(input_hdu.data.shape) == 3:
                image = numpy.array(input_hdu.data[0,:,:])
        elif len(input_hdu.data.shape) == 4:
                image = numpy.array(input_hdu.data[0,0,:,:])
        else:
                image = numpy.array(input_hdu.data[0,0,0,:,:])
        return image


def flush_fits(newimage,fitsfile):
        f = fits.open(fitsfile,mode='update')
        input_hdu = f[0]
        if len(input_hdu.data.shape) == 2:
                input_hdu.data[:,:] = newimage
        elif len(input_hdu.data.shape) == 3:
                input_hdu.data[0,:,:] = newimage_
        elif len(input_hdu.data.shape) == 4:
                input_hdu.data[0,0,:,:] = newimage
        else:
                input_hdu.data[0,0,0,:,:] = newimage
        f.flush()


def drop_deg(fitsfile):
    f = fits.open(fitsfile)
    data = f[0].data.squeeze() 
    hdr = f[0].header
    inpwcs = wcs.WCS(hdr).celestial
    hdr1 = inpwcs.to_header()
    f1 = fits.PrimaryHDU(data = data, header = hdr1)
    f1.writeto(fitsfile)


def deg2rad(xx):
    return numpy.pi*xx/180.0


def get_header(fitsfile):
    input_hdu = fits.open(fitsfile)[0]
    hdr = input_hdu.header
    bmaj = hdr.get('BMAJ')
    bmin = hdr.get('BMIN')
    bpa = hdr.get('BPA')
    pixscale = hdr.get('CDELT2')
    return bmaj,bmin,bpa,pixscale


def beam_header(fitsfile,bmaj,bmin,bpa):
    outhdu = fits.open(fitsfile,mode='update')
    outhdr = outhdu[0].header
    outhdr.set('BMAJ',bmaj,after='BUNIT')
    outhdr.set('BMIN',bmin,after='BMAJ')
    outhdr.set('BPA',bpa,after='BMIN')
    outhdr.remove('HISTORY')
    outhdu.flush()



def process_chan(chan):

    imagelist = sorted(glob.glob('*/*'+chan+'*residual.fits'))
    beams = []
    for ii in imagelist:
        chan = ii.split('-')[-2]
        bmaj,bmin,bpa,pixscale = get_header(ii)
        beams.append((ii,bmaj,bmin,bpa,chan))
        logging.info(f'[{chan}] {ii} BMAJ:{bmaj} BMIN:{bmin} BPA:{bpa}')

    bmax = 0.0
    for beam in beams:
        if beam[1] > bmax: bmax = beam[1]

    logging.info(f'[{chan}] Maximum beam size {bmax}')

    scale_factor = 0.7
    beam_template = 'beam_template.fits'
    cropsize = 51

    target_bmaj = bmax*scale_factor
    target_bmin = bmax*scale_factor
    target_bpa = 0.0

    for beam in beams:

        opfits = beam[0].replace("residual.fits", "image.conv.fits")
        target_beam_fits = beam[0].replace("residual.fits", "residual.target_beam.fits")
        fitted_beam_fits = beam[0].replace("residual.fits", "residual.fitted_beam.fits")
        kernel_fits = beam[0].replace("residual.fits", "residual.kernel.fits")
        model_fits = beam[0].replace("residual.fits","model.fits")
        model_conv_fits = beam[0].replace("residual.fits","model.conv.fits")
        bmaj = beam[1]*scale_factor
        bmin = beam[2]*scale_factor

        if bmaj != 0.0 and bmin != 0.0 and not os.isfile(opfits):

            bpa = beam[3]
            shutil.copyfile(beam[0],opfits)
            shutil.copyfile(beam_template,target_beam_fits)
            shutil.copyfile(beam_template,fitted_beam_fits)
            shutil.copyfile(beam[0],model_conv_fits)

            # Render restoring beam image
            xstd = bmin/(2.3548*pixscale)
            ystd = bmaj/(2.3548*pixscale)
            theta = deg2rad(bpa)
            fitted = Gaussian2DKernel(x_stddev=xstd,y_stddev=ystd,theta=theta,x_size=cropsize,y_size=cropsize,mode='center')
            fitted_beam_image = fitted.array
            fitted_beam_image = fitted_beam_image / numpy.max(fitted_beam_image)
            logging.info(f'[{chan}] Writing {fitted_beam_fits}')
            flush_fits(fitted_beam_image,fitted_beam_fits)

            # Render target beam image
            target_xstd = target_bmin/(2.3548*pixscale)
            target_ystd = target_bmaj/(2.3548*pixscale)
            target_theta = deg2rad(target_bpa)
            target_gaussian = Gaussian2DKernel(x_stddev=target_xstd,y_stddev=target_ystd,theta=target_theta,x_size=cropsize,y_size=cropsize,mode='center')
            target_beam_image = target_gaussian.array
            target_beam_image = target_beam_image / numpy.max(target_beam_image)
            logging.info(f'[{chan}] Writing {target_beam_fits}')
            flush_fits(target_beam_image,target_beam_fits)

            # Call pypher to generate homogenisation kernel
            syscall = 'pypher '+fitted_beam_fits+' '+target_beam_fits+' '+kernel_fits
            syscall = syscall.split()
            logging.info(f'[{chan}] Writing {kernel_fits} (pypher)')
            result = subprocess.run(syscall,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


            # Open residual image and convolve with homogenisation kernel
            resid_image = get_image(beam[0])
            homogenisation_beam = get_image(kernel_fits)
            resid_conv_image = scipy.signal.fftconvolve(resid_image, homogenisation_beam, mode='same')

            # Open model image and convolve with target beam
            model_image = get_image(model_fits)
            model_conv_image = scipy.signal.fftconvolve(model_image, fitted_beam_image, mode='same')

            final_image = resid_conv_image + model_conv_image

            logging.info(f'[{chan}] Writing {opfits} [Final convolved image]')
            flush_fits(final_image,opfits)

            logging.info(f'[{chan}] Adding beam info to header {fitsfile}')
            beam_header(opfits,target_bmaj,target_bmin,target_bpa)

        else:

            logging.info(f'[{chan}] Either fitted beam has failed (blank channel?) or {opfits} exists, skipping')

imagelist = sorted(glob.glob('*'+prefix+'*/*image.fits'))
j = 18
chans = []

for ii in imagelist:
    chan = ii.split('-')[-2]
    if chan not in chans:
        chans.append(chan)

nchans = len(chans)
logging.info(f'Found {nchans} channels(s) from prefix {prefix}')

pool = Pool(processes=j)
pool.map(process_chan,chans)



