#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import json
import os
import generators as gen


with (open("aux/config.json")) as f:
    config = json.load(f)

container = config['CONTAINER']
CWD = os.getcwd()+'/'
scripts_dir = CWD+'SCRIPTS/'
logs_dir = CWD+'LOGS/'

for mydir in [scripts_dir,logs_dir]:
    if not os.path.isdir(mydir): os.mkdir(mydir)

submit_file = 'submit_split_job.sh'
kill_file = 'kill_split_job.sh'

f = open(submit_file,'w')
f.write('#!/usr/bin/env bash\n')
f.write('\n# --------------------------------------------------\n')
f.write('# mstransform to split out sub-bands and Doppler correct\n')
split_name = 'MSTRANS'
split_runfile = scripts_dir+'slurm_'+split_name+'.sh'
split_logfile = split_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
split_syscall = 'casa -c aux/casa_mstransform.py --nologger --log2term --nogui'
gen.write_slurm(split_runfile,split_logfile,split_name,'48:00:00',16,'115GB',split_syscall)
split_run_command = split_name+"=`sbatch "+split_runfile+" | awk '{print $4}'`\n"
f.write(split_run_command)

