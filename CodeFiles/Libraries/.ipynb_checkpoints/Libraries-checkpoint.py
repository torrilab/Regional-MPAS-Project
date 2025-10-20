#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# #IMPORT LIBRARIES
# # --- Add your Functions folder to sys.path ---
# import sys
# mainDirectory = '/mnt/lustre/koa/koastore/torri_group/air_directory/Projects/Regional-MPAS-Project/'
# path = mainDirectory + '/Libraries/'
# sys.path.append(path)


# # --- Import all your function modules ---
# import importlib
# modules = [
#     "Libraries",
# ]

# for mod in modules:
#     globals()[mod] = importlib.import_module(mod)        # import module itself
#     globals().update(vars(globals()[mod]))              # import all functions into global namespace


# In[ ]:


#################################


# In[ ]:


#################################
#IMPORTING LIBRARIES

#arrays
import numpy as np
import math

#plotting
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import ScalarFormatter
import matplotlib.gridspec as gridspec
()

#system
import sys; import os; import time

#loading bar
from tqdm import tqdm
