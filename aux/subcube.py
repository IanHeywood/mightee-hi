import glob
import numpy
import os
from astLib import astCoords as ac

# NGC 895
# start_chan = 150
# end_chan = 220
# ra = '02:21:36.1959564888'
# dec = '-05:31:10.2453452681'

#
# start_chan = 165
# end_chan = 200
# ra = '02:23:50.6385955329'
# dec = '-04:37:08.3208359710'

# 
start_chan = 855
end_chan = 885
ra = '02:25:23.1062796057'
dec = '-04:55:24.7506048697'

imsize = 5.0/60.0


ra_d = ac.hms2decimal(ra,delimiter=':')
dec_d = ac.dms2decimal(dec,delimiter=':')

chans = numpy.arange(start_chan,end_chan+1)

for chan in chans:
	chan = str(chan).zfill(4)
	inp_fits = glob.glob('../*cube1_r0p5-'+chan+'-image.fits')[0]
	op_fits = 'subcube_'+chan+'_'+str(ra_d)+'_'+str(dec_d)+'.fits'
	op_png = op_fits.replace('.fits','.png')
	op_gif = 'subcube_'+str(ra_d)+'_'+str(dec_d)+'.gif'
	syscall = 'mSubimage -d '+inp_fits+' '+op_fits+' '+str(ra_d)+' '+str(dec_d)+' '+str(imsize)
	os.system(syscall)
	syscall = 'mViewer -ct 0 -gray '+op_fits+' -0.0005 0.001 -out '+op_png
	os.system(syscall)

syscall = 'convert-im6 -loop 0 -delay 10 *png '+op_gif
os.system(syscall)