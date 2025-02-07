#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


def write_slurm(runfile,logfile,jobname,time,cpus,mem,syscall):
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


def wsclean(slurm,container,msname,datacol,imagename,fitsmask,chansout,poly,dirty=False):
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'wsclean -log-time -abs-mem 225 -parallel-reordering 16 '
    syscall += '-name '+imagename+' '
    syscall += '-data-column '+datacol+' '
    syscall += '-field 0 '
    syscall += '-size 10240 10240 -scale 1.1asec -use-wgridder -no-update-model-required '
    syscall += '-weight briggs -0.3 '
    if not dirty:
        syscall += '-save-source-list '
        syscall += '-parallel-deconvolution 2560 -niter 100000 -gain 0.15 -mgain 0.9 '
        syscall += '-fits-mask '+fitsmask+' '
        syscall += '-threshold 5e-6 '
        syscall += '-fit-spectral-pol '+str(poly)+' '
    syscall += '-channels-out '+str(chansout)+' '
    syscall += '-join-channels '
    syscall += '-no-mf-weighting '
    syscall += msname
    return syscall


def image_cube(slurm,container,msname,imagename,chan0,chan1,chansout,tempdir):
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'wsclean -log-time -abs-mem 225 -parallel-reordering 16 '
    syscall += '-make-psf -no-dirty '
    syscall += '-name '+imagename+' '
    syscall += '-no-mf-weighting -no-update-model-required '
    syscall += '-data-column CORRECTED_DATA '
    syscall += '-field 0 -size 4096 4096 -scale 2.0asec '
    syscall += '-use-wgridder -weight briggs 0.5 '
    syscall += '-channel-range '+str(chan0)+' '+str(chan1)+' '
    syscall += '-channels-out '+str(chansout)+' '
    syscall += '-temp-dir '+tempdir+' '
    syscall += msname
    return syscall


def smops(slurm,container,msname,inputprefix,smopschans,polyorder,outputprefix):
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'smops --ms '+msname+' '
    syscall += '--input-prefix '+inputprefix+' '
    syscall += '--channels-out '+str(smopschans)+' '
    syscall += '--polynomial-order '+str(polyorder)+' '
    syscall += '--output-prefix '+outputprefix+' '
    syscall += '--stokes I'
    return syscall


def predict(slurm,container,msname,tempdir,chans,image):
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'wsclean '
    syscall += '-log-time '
    syscall += '-predict '
    syscall += '-temp-dir '+tempdir+' '
    syscall += '-use-wgridder '
    syscall += '-channels-out '+str(chans)+' '
    syscall += '-name '+tempdir+'/'+image+' '
    syscall += '-abs-mem 100 '
    syscall += msname
    return syscall


def tricolour(slurm,container,msname,config,datacolumn,residuals):
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'tricolour -dc '+datacolumn+' '
    syscall += '-nc 8 '
    print('*** Limiting cores to 8 for UKSRC hardware ***')
    if residuals:
        syscall += '-smc MODEL_DATA '
    syscall += '-c '+config+' '
    syscall += '--flagging-strategy polarisation '
    syscall += msname
    return syscall


def cubical(slurm,container,msname,parset,nchan,timechunk):
    cubical_name = msname.split('/')[-1]
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'gocubical '+parset+' '
    syscall += '--data-ms '+msname+' '
    syscall += '--data-time-chunk '+str(timechunk)+' '
    syscall += '--data-freq-chunk '+str(nchan)+' '
    syscall += '--out-dir delaycal_'+cubical_name+'.cc '
    syscall += '--out-name delaycal_'+cubical_name+' ' 
    syscall += '--k-freq-int '+str(nchan)+' '
    syscall += '--k-save-to delaycal_'+cubical_name+'.parmdb'
    return syscall


def cube(slurm,container,msname,tempdir,cubename,chanstart,chanend,chansout):
    syscall = ''
    if slurm:
        syscall = 'singularity exec '+container+' '
    syscall += 'wsclean -log-time -make-psf -no-dirty -abs-mem 225 '
    syscall += '-temp-dir '+tempdir+' '
    syscall += '-parallel-reordering 16 -name '+cubename+' '
    syscall += '-no-mf-weighting -no-update-model-required '
    syscall += '-data-column CORRECTED_DATA -field 0 -size 4096 4096 '
    syscall += '-scale 2.0asec -use-wgridder -weight briggs 0.5 '
    syscall += '-channels-out '+str(chansout)+' '
    syscall += '-channel-range '+str(chanstart)+' '+str(chanend)+' '
    syscall += msname
    return syscall


def hello():
    print('--------------------------------------------------------------------')
    print('')
    print('  +------+.    ') 
    print('  |`.    | `.  ')
    print('  |  `+--+---+ ')
    print('  |   |  |   |    Ich bin eine MIGHTEE-HI Maschine')
    print('  +---+--+.  | ')
    print('   `. |    `.| ')
    print('     `+------+ ') 
    print('')

