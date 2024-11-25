#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import json
import os
import sys
import generators as gen


gen.hello()


# ------------------------------------------------------------------
# Load config

with (open("aux/config.json")) as f:
    config = json.load(f)

# ------------------------------------------------------------------
# Try to find everything, setup some parameters, do some error capture


myms = glob.glob('*.mms')
if len(myms) == 0:
    print('No MMS found, please check')
    sys.exit()
else:
    myms = myms[0]


mslist = sorted(glob.glob('*.mms/SUBMSS/*.ms'))
if len(mslist) == 0:
    print('This does not appear to be a MMS, please check')
    sys.exit()
nsubms = len(mslist)


fitsmask = glob.glob('*mask.fits')
if len(fitsmask) == 0:
    print('No FITS mask found, please check')
    sys.exit()
else:
    fitsmask = fitsmask[0]


for item in ['L1','L2','L3']:
    if item in myms:
        band = config[item]['band']
        nchan = config[item]['nchan']
        smopschans = config[item]['smopschans']
        timechunk = config[item]['timechunk']
        chansout = config[item]['chansout']
        polyorder = config[item]['polyorder']


container = config['CONTAINER']
CWD = os.getcwd()+'/'
image_dir = CWD+'IMAGES/'
smops_dir = CWD+'SMOPSCUBE/'
cube_dir = CWD+'CUBE/'
scripts_dir = CWD+'SCRIPTS/'
logs_dir = CWD+'LOGS/'
image_name = 'img_'+myms.rstrip('/')+'_datamask'
resid_name = 'img_'+myms.rstrip('/')+'_pcalresid'
smopsmodel = image_name+'-smops'
image_name = image_dir+image_name
resid_name = image_dir+resid_name
smopsmodel = smops_dir+smopsmodel
tricolour_config = 'aux/target_flagging_1.yaml'
cubical_config = 'aux/2GC_delaycal_residuals.parset'
submit_file = 'submit_process_mms_jobs.sh'
kill_file = 'kill_process_mms_jobs.sh'
master_job_list = []


# ------------------------------------------------------------------
# Setup folders and symlink scripts


for i in range(0,nsubms):
    tempdir = 'temp_'+str(i).zfill(3)
    if not os.path.isdir(tempdir): os.mkdir(tempdir)
for mydir in [image_dir,smops_dir,cube_dir,scripts_dir,logs_dir]:
    if not os.path.isdir(mydir): os.mkdir(mydir)


# ------------------------------------------------------------------
# Report

print('----------------------------+---------------------------------------')
print('Found                       : %s' %myms)
print('Number of sub MS            : %s' %(str(nsubms)))
print('Sub-band                    : %s' % band)
print('Number of channels          : %s' % nchan)
print('Continuum interpolation     : %s' % smopschans)
print('FITS mask                   : %s' % fitsmask)
print('----------------------------+---------------------------------------')

f = open(submit_file,'w')
f.write('#!/usr/bin/env bash\n')


# ------------------------------------------------------------------
# Loop per sub-MS

i = 0
post_loop_dependencies = []

for submsname in mslist:


    label = str(i).zfill(2)
    tempdir = CWD+'/temp_'+str(i).zfill(3)


    # ------------------------------------------------------------------
    # Step 0i

    f.write('\n# --------------------------------------------------\n')
    f.write('# Flagging '+submsname+'\n')
    flag_name = 'TRICO1'+label
    flag_runfile = scripts_dir+'slurm_'+flag_name+'.sh'
    flag_logfile = flag_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
    flag_syscall = gen.tricolour(container,submsname,tricolour_config,'DATA',residuals=False)
    gen.write_slurm(flag_runfile,flag_logfile,flag_name,'03:00:00',16,'115GB',flag_syscall)
    flag_run_command = flag_name+"=`sbatch "+flag_runfile+" | awk '{print $4}'`\n"
    f.write(flag_run_command)
    master_job_list.append(flag_name)
    post_loop_dependencies.append(flag_name)

    i += 1

post_loop_dependencies = ("$" + ":$".join(post_loop_dependencies))


# ------------------------------------------------------------------
# Step 1 

f.write('\n# --------------------------------------------------\n')
f.write('# Initial imaging with mask to get continuum model\n')

wsclean_name = 'WSCLN1'
wsclean_runfile = scripts_dir+'slurm_'+wsclean_name+'.sh'
wsclean_logfile = wsclean_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
wsclean_syscall = gen.wsclean(container,myms,'DATA',image_name,fitsmask,chansout,polyorder,dirty=False)
gen.write_slurm(wsclean_runfile,wsclean_logfile,wsclean_name,'24:00:00',32,'230GB',wsclean_syscall)
run_command = wsclean_name+"=`sbatch -d afterok:"+post_loop_dependencies+" "+wsclean_runfile+" | awk '{print $4}'`\n"
f.write(run_command)
master_job_list.append(wsclean_name)


# ------------------------------------------------------------------
# Step 2

f.write('\n# --------------------------------------------------\n')
f.write('# Frequency interpolation of continuum model\n')

smops_name = 'SMOPS'
smops_runfile = scripts_dir+'slurm_'+smops_name+'.sh'
smops_logfile = smops_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
smops_syscall = gen.smops(container,myms,image_name,smopschans,3,smopsmodel)+'\n'
for i in range(0,nsubms): # symlink the interpolated models into the temp folders
    smops_syscall += 'ln -s '+smopsmodel+'* temp_'+str(i).zfill(3)+'/\n'
gen.write_slurm(smops_runfile,smops_logfile,smops_name,'03:00:00',16,'115GB',smops_syscall)
run_command = smops_name+"=`sbatch -d afterok:$"+wsclean_name+" "+smops_runfile+" | awk '{print $4}'`\n"
f.write(run_command)
master_job_list.append(smops_name)


# ------------------------------------------------------------------
# Loop per sub-MS

i = 0
post_loop_dependencies = []

for submsname in mslist:


    label = str(i).zfill(2)
    tempdir = CWD+'/temp_'+str(i).zfill(3)


    # ------------------------------------------------------------------
    # Step 3i

    f.write('\n# --------------------------------------------------\n')
    f.write('# Predicting model for '+submsname+'\n')
    predict_name = 'PRDICT'+label
    predict_runfile = scripts_dir+'slurm_'+predict_name+'.sh'
    predict_logfile = predict_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
    predict_syscall = gen.predict(container,submsname,tempdir,smopschans,smopsmodel.split('/')[-1])
    gen.write_slurm(predict_runfile,predict_logfile,predict_name,'12:00:00',16,'115GB',predict_syscall)
    predict_run_command = predict_name+"=`sbatch -d afterok:$"+smops_name+" "+predict_runfile+" | awk '{print $4}'`\n"
    f.write(predict_run_command)
    master_job_list.append(predict_name)


    # ------------------------------------------------------------------
    # Step 4i

    f.write('\n# --------------------------------------------------\n')
    f.write('# Selfcal and continuum subtraction for '+submsname+'\n')
    selfcal_name = 'CUBICL'+label
    selfcal_runfile = scripts_dir+'slurm_'+selfcal_name+'.sh'
    selfcal_logfile = selfcal_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
    selfcal_syscall = gen.cubical(container,submsname,cubical_config,nchan,timechunk)
    gen.write_slurm(selfcal_runfile,selfcal_logfile,selfcal_name,'08:00:00',32,'230GB',selfcal_syscall)
    selfcal_run_command = selfcal_name+"=`sbatch -d afterok:$"+predict_name+" "+selfcal_runfile+" | awk '{print $4}'`\n"
    f.write(selfcal_run_command)
    master_job_list.append(selfcal_name)


    # ------------------------------------------------------------------
    # Step 5i

    f.write('\n# --------------------------------------------------\n')
    f.write('# Flagging '+submsname+'\n')
    flag_name = 'TRICO2'+label
    flag_runfile = scripts_dir+'slurm_'+flag_name+'.sh'
    flag_logfile = flag_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
    flag_syscall = gen.tricolour(container,submsname,tricolour_config,'CORRECTED_DATA',residuals=True)
    gen.write_slurm(flag_runfile,flag_logfile,flag_name,'03:00:00',16,'115GB',flag_syscall)
    flag_run_command = flag_name+"=`sbatch -d afterok:$"+selfcal_name+" "+flag_runfile+" | awk '{print $4}'`\n"
    f.write(flag_run_command)
    master_job_list.append(flag_name)
    post_loop_dependencies.append(flag_name)

    i += 1


#print("$" + ":$".join(post_loop_dependencies))
post_loop_dependencies = ("$" + ":$".join(post_loop_dependencies))


# ------------------------------------------------------------------
# Step 6

f.write('\n# --------------------------------------------------\n')
f.write('# Image residuals to check continuum subtraction and selfcal\n')

wsclean_name = 'WSCLN2'
wsclean_runfile = scripts_dir+'slurm_'+wsclean_name+'.sh'
wsclean_logfile = wsclean_runfile.replace('.sh','.log').replace(scripts_dir,logs_dir)
wsclean_syscall = gen.wsclean(container,myms,'CORRECTED_DATA',resid_name,fitsmask,chansout,polyorder,dirty=True)
gen.write_slurm(wsclean_runfile,wsclean_logfile,wsclean_name,'24:00:00',32,'230GB',wsclean_syscall)
run_command = wsclean_name+"=`sbatch -d afterok:"+post_loop_dependencies+" "+wsclean_runfile+" | awk '{print $4}'`\n"
f.write(run_command)
master_job_list.append(wsclean_name)


# ------------------------------------------------------------------
# Write the kill commands and close the submit file

f.write('\n# --------------------------------------------------\n')
f.write('# Kill commands\n')
for job_id in master_job_list:
    if job_id == master_job_list[0]:
        kill = 'echo "scancel $'+job_id+' #'+job_id+'" > '+kill_file+'\n'
    else:
        kill = 'echo "scancel $'+job_id+' #'+job_id+'" >> '+kill_file+'\n'
    f.write(kill)
f.close()
print('Submit jobs                 : source %s' %submit_file)
print('----------------------------+---------------------------------------\n')
