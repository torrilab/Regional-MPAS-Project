#!/bin/bash
#PBS -A UHWM0066
#PBS -N python
#PBS -q main
#PBS -l job_priority=economy
#PBS -l walltime=02:30:00
#PBS -l select=1:ncpus=1:mem=20GB
#PBS -M air673@hawaii.edu
#PBS -m bea

cd $PBS_O_WORKDIR

# --- Setup ---
module load conda
conda activate my_environment
export HDF5_USE_FILE_LOCKING=FALSE
export PYTHONUNBUFFERED=TRUE
mkdir -p job_out

# --- Convert and Run ---
NOTEBOOK="FractionSkillScore_3D.ipynb"
SCRIPT="${NOTEBOOK%.ipynb}.py"

jupyter nbconvert --to script "$NOTEBOOK"
python -u "$SCRIPT" > job_out/${SCRIPT%.py}-${PBS_JOBID}.out 2>&1
