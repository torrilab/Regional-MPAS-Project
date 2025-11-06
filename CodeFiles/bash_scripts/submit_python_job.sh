#!/bin/bash
#PBS -A UHWM0066
#PBS -N python_jobarray
#PBS -q main
#PBS -J 11-20:1
#PBS -l walltime=00:30:00
#PBS -l select=1:ncpus=1:mem=20GB
#PBS -M air673@hawaii.edu
#PBS -m bea

cd $PBS_O_WORKDIR

# --- Setup Variables ---
NOTEBOOK="SurfaceVariableAnimation.ipynb"
SCRIPT="${NOTEBOOK%.ipynb}.py"
JOB_DIR="job_out/${SCRIPT%.py}"   # e.g. job_out/SurfaceVariableAnimation

# --- Make Output Folder ---
mkdir -p "$JOB_DIR"

# --- Testing Job Array ---
echo "PBS Job Id is ${PBS_JOBID}"
echo "PBS job array index value is ${PBS_ARRAY_INDEX}"

# --- Environment Setup ---
module load conda
conda activate npl
export HDF5_USE_FILE_LOCKING=FALSE
export PYTHONUNBUFFERED=TRUE

# --- Move PBS .o and .e files into the job directory ---
JobIDClean="${PBS_JOBID%%[*]*}"
echo "Moving PBS output files for Job ${JobIDClean} into ${JOB_DIR}"

mv -v "python_jobarray.o${JobIDClean}"* "${JOB_DIR}/"
mv -v "python_jobarray.e${JobIDClean}"* "${JOB_DIR}/"