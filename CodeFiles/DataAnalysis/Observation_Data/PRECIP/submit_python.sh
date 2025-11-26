#!/bin/bash
#PBS -A UHWM0066
#PBS -N aroseman_python
#PBS -q main
#PBS -l job_priority=economy
#PBS -l walltime=03:00:00
#PBS -l select=1:ncpus=1:mem=10GB

# Email notifications
#PBS -M air673@hawaii.edu
#PBS -m ea

# Temporary Directory
export TMPDIR=${SCRATCH}/tmp
mkdir -p ${TMPDIR}

### Load Conda/Python module and activate NPL environment
module load conda
conda activate npl

### Run the Python script
echo "Code File directory is: $(pwd)"
python SPolRadar_Data.py
