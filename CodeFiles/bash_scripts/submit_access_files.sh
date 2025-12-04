#!/bin/bash
#PBS -A UHWM0066
#PBS -N python
#PBS -q main
#PBS -l job_priority=economy
#PBS -l walltime=03:00:00
#PBS -l select=1:ncpus=1:mem=5GB
#PBS -M air673@hawaii.edu
#PBS -m bea

cd $PBS_O_WORKDIR

# --- Setup ---
module load conda
conda activate npl
export HDF5_USE_FILE_LOCKING=FALSE
export PYTHONUNBUFFERED=TRUE

# --- Convert and Run ---
SCRIPT="access_files.py"

python -u "$SCRIPT" > ${SCRIPT%.py}-${PBS_JOBID}.out 2>&1
