#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import numpy
import os
import glob


def write_casa(cubename,fitsname,casafile):
    f = open(casafile,'w')
    f.writelines(['import os\n',
        'ia.imageconcat("'+cubename+'",infiles="*fits",relax=True,reorder=True)\n',
        'exportfits(imagename="'+cubename+'",fitsimage="'+fitsname+'")\n',
        'os.system("rm -rf '+cubename+'")\n'])
    f.close()


def write_slurm(container,runfile,logfile,jobname,time,cpus,mem,syscall):
    f = open(runfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+runfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time='+time+'\n',
        '#SBATCH --partition=Main\n'
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task='+str(cpus)+'\n',
        '#SBATCH --mem='+mem+'\n',
        '#SBATCH --output='+logfile+'\n',
        'SECONDS=0\n',
        syscall+'\n',
        'echo "****ELAPSED "$SECONDS" '+jobname+'"\n'])
    f.close()


container = '/users/ianh/containers/oxkat-0.42.sif'
rootdir = os.getcwd()
chans = 384
fitslist = sorted(glob.glob(rootdir+'/images/*image.fits'))

ptgs = sorted(glob.glob('COSMOS*/MID/images/pony.*/filtered'))

j = 0

for ptg in ptgs:
    os.chdir(ptg)
    fitslist = sorted(glob.glob('*fits'))
    nfits = len(fitslist)
    chunks = int(numpy.ceil(nfits/chans))
    for i in range(0,chunks):
        chunklist = (fitslist[:chans])
        start_chan = chunklist[0].split('-image')[0].split('-')[-1]
        end_chan = chunklist[-1].split('-image')[0].split('-')[-1]
        cubename = (fitslist[0].split('_r0p5')[0]+'_r0p5_'+start_chan+'-'+end_chan+'.image.cube.im').split('/')[-1]
        fitsname = (fitslist[0].split('_r0p5')[0]+'_r0p5_'+start_chan+'-'+end_chan+'.image.cube.fits').split('/')[-1]
        print(ptg+': Chunk %s has %s planes (chans %s to %s)' % (i,len(chunklist),start_chan,end_chan))
        del fitslist[:chans]
        chunkdir = os.getcwd()+'/cube'+str(i)
        if not os.path.isdir(chunkdir): 
            os.mkdir(chunkdir)
            os.chdir(chunkdir)
            for item in chunklist:
                os.system('ln -s ../'+item+' .')
            casafile = 'casa_make_cube_'+str(i)+'.py'
            slurmfile = 'slurm_make_cube_'+str(i)+'.sh'
            logfile = 'slurm_make_cube_'+str(i)+'.log'
            syscall = 'singularity exec '+container+' casa -c '+casafile+' --nologger --log2term --nogui'
            write_casa(cubename,fitsname,'casa_make_cube_'+str(i)+'.py')
            write_slurm(container,
                slurmfile,
                logfile,
                'QB'+str(j).zfill(2)+'_'+str(i).zfill(3),
                '06:00:00',
                8,
                '60GB',
                syscall)
#            os.system('sbatch '+slurmfile)
            os.chdir('../')
    os.chdir(rootdir)
    j+=1
