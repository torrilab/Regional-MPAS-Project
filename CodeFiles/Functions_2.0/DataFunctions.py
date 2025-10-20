#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
====================================================
DataFunction
====================================================
"""


# In[ ]:


#IMPORTING NECESSARY LIBRARIES
import numpy


# In[2]:


#INITIALIZE DATA FUNCTION
###############################################################
def initiate_array_2D(out_file,vars,t_chunk_size,z_chunk_size,t_size=None,z_size=None):
    # Define array dimensions (adjust based on your data)

    if t_size==None:
        t_size = len(data['time'])  # Number of timesteps
    if z_size==None:
        z_size = len(data['zh'])    # Number of vertical levels
    
    with h5py.File(out_file, 'w') as f: 
        # Check if the dataset 'theta_e' already exists
        for var_name in vars:
            if var_name not in f:
                # Create a dataset with the full size for all time steps (initially empty)
                f.create_dataset(var_name, 
                                 (t_size, z_size),  # Full size for all timesteps
                                 chunks=(t_chunk_size, z_chunk_size))  # Chunks for time axis to allow resizing

#INITIALIZE DATA FUNCTION
###############################################################
def initiate_array_4D(out_file,vars,t_chunk_size,z_chunk_size,y_chunk_size,x_chunk_size,t_size=None,z_size=None,y_size=None,x_size=None):
    # Define array dimensions (adjust based on your data)

    if t_size==None:
        t_size = len(data['time'])  # Number of timesteps
    if z_size==None:
        z_size = len(data['zh'])    # Number of vertical levels
    if y_size==None:
        y_size = len(data['yh'])    # Number of vertical levels
    if x_size==None:
        x_size = len(data['xh'])    # Number of vertical levels
    
    with h5py.File(out_file, 'w') as f: 
        # Check if the dataset 'theta_e' already exists
        for var_name in vars:
            if var_name not in f:
                # Create a dataset with the full size for all time steps (initially empty)
                f.create_dataset(var_name, 
                                 (t_size, z_size, y_size, x_size),  # Full size for all timesteps
                                 chunks=(t_chunk_size, z_chunk_size, y_chunk_size, x_chunk_size))  # Chunks for time axis to allow resizing

