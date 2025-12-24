#!/bin/bash
#PBS -A UHWM0066
#PBS -N python_jobarray
#PBS -q main
#PBS -J 1-20:1
#PBS -l walltime=00:15:00
#PBS -l select=1:ncpus=1:mem=10GB
#PBS -M air673@hawaii.edu
#PBS -m bea

cd $PBS_O_WORKDIR

# --- Setup Variables ---
NOTEBOOK="ComparingCFADs_MRMS.ipynb"
SCRIPT="${NOTEBOOK%.ipynb}.py"
JOB_DIR="job_out/${SCRIPT%.py}"

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

# --- Convert and Run ---
jupyter nbconvert --to script "$NOTEBOOK"
python -u "$SCRIPT" > "${JOB_DIR}/${SCRIPT%.py}-${PBS_JOBID}.out" 2>&1

# --- Move PBS .o and .e files into the job directory ---
BaseJobID=$(echo "$PBS_JOBID" | sed -E 's/\[.*//; s/\..*//')    # e.g. 370036
Index="${PBS_ARRAY_INDEX}"         # e.g. 1

echo "Moving PBS output files into ${JOB_DIR}:"

mv -v "python_jobarray.o${BaseJobID}.${Index}" "${JOB_DIR}/"
mv -v "python_jobarray.e${BaseJobID}.${Index}" "${JOB_DIR}/"
