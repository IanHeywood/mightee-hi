import glob
import os 
import numpy

container = '/users/ianh/containers/oxkat-0.42.sif'

chans = [(0, 1, 384),
    (1, 385, 768),
    (2, 769, 1152),
    (3, 1153, 1536),
    (4, 1537, 1920),
    (5, 1921, 2304),
    (6, 2305, 2688),
    (7, 2689, 3072),
    (8, 3073, 3456),
    (9, 3457, 3840),
    (10, 3841, 4224),
    (11, 4225, 4608),
    (12, 4609, 4992),
    (13, 4993, 5376),
    (14, 5377, 5760),
    (15, 5761, 6144),
    (16, 6145, 6528),
    (17, 6529, 6912),
    (18, 6913, 7296),
    (19, 7297, 7680),
    (20, 7681, 8064),
    (21, 8065, 8448),
    (22, 8449, 8803)]



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


def split_channels(msname,jobname,chan0,chan1,opms):
    
    casascript = 'SCRIPTS/casa_split_'+msname.split('/')[-1]+'.'+str(chan0).zfill(4)+'.py'
    f = open(casascript,'w')
    casacall = 'split(vis="'+msname+'",outputvis="'+opms+'",spw="0:'+str(chan0)+'~'+str(chan1+1)+'",datacolumn="corrected",keepmms=True)\n'
    f.writelines([casacall])

    syscall = 'singularity exec '+container+' casa -c '+casascript+' --nologger --log2term --nogui'
    slurmfile = 'SCRIPTS/slurm_casa_split_'+opms.split('/')[-1]+'.'+str(chan0).zfill(4)+'.sh'
    logfile = 'LOGS/slurm_casa_split_'+opms.split('/')[-1]+'.'+str(chan0).zfill(4)+'.log'
    write_slurm(slurmfile,logfile,jobname,'07:00:00',8,'57GB',syscall)

    return slurmfile


#/scratch3/users/ianh/MID_clean
#1586705155_sdp_l2.full_J0959+0151_MID.mms

if not os.path.isdir('SCRIPTS'): os.mkdir('SCRIPTS')
if not os.path.isdir('LOGS'): os.mkdir('LOGS')

msid = 0

ptgs = glob.glob('*MID*')
for ptg in ptgs:
    jobnames = []
    if 'full' in ptg:
        field = ptg.split('full_')[-1].split('_MID')[0]
    elif 'l0' in ptg:
        field = ptg.split('l0_')[-1].split('_MID')[0]
    else:
        field = ptg.split('l2_')[-1].split('_MID')[0]
    opdir = '/scratch3/users/ianh/MID_clean/'+field
    if not os.path.isdir(opdir): os.mkdir(opdir)
    for chan in chans:
        idx = chan[0]
        chan0 = chan[1]
        chan1 = chan[2]
        jobname = 'SP_'+str(msid).zfill(2)+'_'+str(idx).zfill(2)
        opms = opdir+'/'+ptg.replace('.mms','_'+str(chan0).zfill(4)+'-'+str(chan1).zfill(4)+'.mms')
        slurmfile = split_channels(ptg,jobname,chan0,chan1,opms)
        if idx == 0:
            runcall = jobname+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
            jobnames.append(jobname)
        else:
            runcall = jobname+"=`sbatch -d afterok:$"+jobnames[-1]+" "+slurmfile+" | awk '{print $4}'`"
            jobnames.append(jobname)
        print(runcall)
    msid+=1






