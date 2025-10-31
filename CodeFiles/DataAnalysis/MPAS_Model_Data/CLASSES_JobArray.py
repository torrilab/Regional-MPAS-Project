#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# SlurmJobArray_Class
# ============================================================

import os
import numpy as np

class JobArray_Class:
    def __init__(self, total_elements, 
                 num_jobs, UsingJobArray,
                 custom_job_id=None, supercomputer="PBS"):
        self.total_elements = total_elements
        self.num_jobs = num_jobs
        self.UsingJobArray = UsingJobArray
        
        # Get job ID (default = 1 if not running under Slurm)
        if custom_job_id is None:
            if supercomputer=="SLURM":
                self.job_id = int(os.environ.get('SLURM_ARRAY_TASK_ID', 0))
            elif supercomputer=="PBS":
                self.job_id = int(os.environ.get('PBS_ARRAY_INDEX', 0))
            if self.job_id == 0:
                self.job_id = 1
        elif custom_job_id is not None:
            self.job_id = custom_job_id
        
        # Precompute range info
        self.job_range = total_elements // num_jobs
        self.remaining = total_elements % num_jobs
        
        # Compute job range for this job
        self.start_job, self.end_job = self._get_job_range(self.job_id)

        # Print summary
        self.Summary()

    # ------------------------------------------------------------
    def _get_job_range(self, job_id):
        if self.UsingJobArray == True:
            """Compute start and end indices for this job."""
            job_id -= 1
            start_job = job_id * self.job_range + min(job_id, self.remaining)
            end_job = start_job + self.job_range + (1 if job_id < self.remaining else 0)
            if job_id == self.num_jobs - 1:
                end_job = self.total_elements
        elif self.UsingJobArray == False:
            start_job, end_job = 0, self.total_elements
        return start_job, end_job

    # ------------------------------------------------------------
    def TESTING(self):
        """Print start/end for all jobs to verify chunking logic."""
        start, end = [], []
        for job_id in range(1, self.num_jobs + 1):
            s, e = self._get_job_range(job_id)
            print(f"Job {job_id}: {s} → {e}")
            start.append(s)
            end.append(e)
        print("Unique starts:", len(np.unique(start)) == len(start))
        print("Unique ends:", len(np.unique(end)) == len(end))
        print("No zero-length ranges:", np.all(np.array(start) != np.array(end)))

    def Summary(self):
        print(f"Running timesteps from {self.start_job}:{self.end_job-1}","\n")

