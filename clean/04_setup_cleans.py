#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

import glob
import numpy
import os
import sys

def write_slurm(runfile,logfile,jobname,time,ncpu,mem,syscall):
    f = open(runfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+runfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time='+time+'\n',
        '#SBATCH --partition=Main\n'
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task='+str(ncpu)+'\n',
        '#SBATCH --mem='+mem+'\n',
        '#SBATCH --output='+logfile+'\n',
        'SECONDS=0\n',
        syscall+'\n',
        'echo "****ELAPSED "$SECONDS" '+jobname+'"\n'])
    f.close()


container = '/idia/software/containers/STIMELA_IMAGES/stimela_wsclean_1.7.3.sif'


ptgs = []
scan = os.scandir('.')
for ii in scan:
    if ii.is_dir(): ptgs.append(ii.name)
scan.close()

# syscall = 'singularity exec /idia/software/containers/STIMELA_IMAGES/stimela_wsclean_1.7.3.sif wsclean -log-time '
# syscall += '-abs-mem 225 -parallel-reordering 8 -name '+opname+' -data-column DATA -parallel-deconvolution 2048 '
# syscall += '-field 0 -size 4096 4096 -scale 2.0asec -use-wgridder -no-update-model-required -weight briggs 0.0 '
# syscall += '-niter 80000 -gain 0.15 -mgain 0.9 -channels-out 199 -channel-range 1 200 -fits-mask '+mask+' '
# syscall += '-threshold 0.00013 '+myms

idx = 0

nope = ['SCRIPTS/slurm_image_cube_1617809470_sdp_l0_COSMOS_1_MID_4609-4992.mms.sh','SCRIPTS/slurm_image_cube_1586705155_sdp_l2.full_J0959+0151_MID_4609-4992.mms.sh']

for ptg in ptgs:
    os.chdir(ptg)
    if not os.path.isdir('SCRIPTS'): os.mkdir('SCRIPTS')
    if not os.path.isdir('LOGS'): os.mkdir('LOGS')
    mslist = glob.glob('*.mms')
    msid = 0
    for myms in mslist:
        chans = myms.split('MID_')[-1].split('.mms')[0]
        chan0,chan1 = chans.split('-')
        nchan = int(chan1)+1 - int(chan0)

        if 'full' in myms:
            field = myms.split('full_')[-1].split('_MID')[0]
        elif 'l0' in ptg:
            field = myms.split('l0_')[-1].split('_MID')[0]
        else:
            field = myms.split('l2_')[-1].split('_MID')[0]

        maskcube = glob.glob('/idia/projects/mightee/ianh/HI/*/MID/images/pony.o*/filtered/cube*/*'+field+'*'+chans+'*fits')[0]

        jobname = 'CL_'+str(idx).zfill(2)+'_'+str(msid).zfill(2)
        runfile = 'SCRIPTS/slurm_image_cube_'+myms.rstrip('/')+'.sh'
        logfile = 'LOGS/slurm_image_cube_'+myms.rstrip('/')+'.log'

        opdir = 'output_'+myms+'_'+jobname
        if not os.path.isdir(opdir): os.mkdir(opdir)
        opname = opdir+'/img_'+myms+'_r0p0'

        syscall = 'singularity exec '+container+' wsclean -log-time '
        syscall += '-abs-mem 225 -parallel-reordering 8 -name '+opname+' '
        syscall += '-tempdir '+opdir+' -data-column DATA -parallel-deconvolution 2048 '
        syscall += '-field 0 -size 4096 4096 -scale 2.0asec -use-wgridder -weight briggs 0.0 '
        syscall += '-niter 80000 -gain 0.15 -mgain 0.9 -channels-out '+str(nchan)+' '
        syscall += '-channel-range 0 '+str(nchan)+' -fits-mask '+maskcube+' '
        syscall += '-auto-threshold 1.0 '+myms

        write_slurm(runfile,logfile,jobname,'07:00:00',32,'230GB',syscall)
        if runfile not in nope:
            print('# '+ptg,chan0,chan1,nchan,field,maskcube)
            print('sbatch '+runfile)
            print('')
        else:
            print('\n')
            print(runfile,'nope')
            print('************\n')
        msid += 1
    os.chdir('../')
    idx += 1
