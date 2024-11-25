import sys
import os

field = sys.argv[1]
msname = sys.argv[2]
token = sys.argv[3]

syscall = f'srun --job-name={field} \
     --partition=Main \
     --ntasks=1 \
     --nodes=1 \
     --cpus-per-task=16 \
     --time=96:00:00 \
     --mem=115GB \
     --output=archive_download.log \
     bash -c "source ~/venv/katdal/bin/activate && mvftoms.py --verbose -o {msname} --no-auto --flags cam,data_lost --applycal l1 --target {field} --quack 1 {token}"'

os.system(syscall)