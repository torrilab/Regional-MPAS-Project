# ============================================================
# Functions for use in Python Data Analysis (Last Updated Python Version 3.11.8)
# Author: Abraham Roseman
# Copyright © 2024-Current Abraham Roseman. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to use
the Software for personal or non-commercial purposes only, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
The Software may not be modified, reproduced, distributed, sublicensed, or used for
commercial purposes without explicit prior written permission from the copyright holder. 
The modification or reproduction is permitted for research purposes. 
The copyright holder will continue to maintain all rights to the software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
THE SOFTWARE.

# Description:
#   This folder contains modular Python functions for scientific
#   computation and analysis, including:
#     - Area averaging and dimensional reductions
#     - Numerical computations and derivatives
#     - Data handling and preprocessing
#     - Plotting and visualization routines
#     - Statistical analysis tools
#
# ============================================================


#HOW TO IMPORT FUNCTIONS

# --- Add your Functions folder to sys.path ---
import sys
path = mainDirectory + '/Functions_2.0/'
sys.path.append(path)

# --- Import all your function modules ---
import AreaAverageFunctions
from AreaAverageFunctions import *

import ComputationFunctions
from ComputationFunctions import *

import DataFunctions
from DataFunctions import *

import DerivativeFunctions
from DerivativeFunctions import *

import PlottingFunctions
from PlottingFunctions import *

import StatisticalFunctions
from StatisticalFunctions import *

import Classes
from Classes import *

OR

# --- Add your Functions folder to sys.path ---
import sys
path = mainDirectory + '/Functions_2.0/'
sys.path.append(path)

# --- Import all your function modules ---
import importlib
modules = [
    "AreaAverageFunctions",
    "ComputationFunctions",
    "DataFunctions",
    "DerivativeFunctions",
    "PlottingFunctions",
    "StatisticalFunctions",
    "Classes",
]

for mod in modules:
    globals()[mod] = importlib.import_module(mod)        # import module itself
    globals().update(vars(globals()[mod]))              # import all functions into global namespace