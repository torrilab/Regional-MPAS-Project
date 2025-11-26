#!/usr/bin/env python
# coding: utf-8

# In[1]:


####################################
#ENVIRONMENT SETUP


# In[2]:


#LIBRARIES

#system
import os
import sys

#math and array operations
import numpy as np
import math
import pandas as pd
import metpy.calc as mpcalc

#data classes
import xarray as xr
import pickle
import glob

#plotting
import matplotlib
# matplotlib.use("Agg") #UNCOMMENT IF PLOTTING WITHIN JUPYTER DOCUMENT
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

import cartopy.crs as ccrs
import cartopy.feature as cfeature

#loading bar
from tqdm import tqdm

#datetime
from datetime import datetime


# In[3]:


#Importing DirectoryManager Class
sys.path.append(os.path.join("/glade/u/home/aroseman/Projects/Regional-MPAS-Project/Code/CodeFiles/","DataAnalysis"))
from CLASSES_Directories import DirectoryManager_Class


# In[4]:


DirectoryManager = DirectoryManager_Class()

codeType = os.path.join("DataAnalysis", "ERA5_Data")
dataType = "ERA5Comparison"

outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
outputPlottingDirectory = DirectoryManager.GetOutputPlottingDirectory(codeType, dataType)


# In[5]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
from CLASSES_ModelData import StructuredModelData_Class, DataOperator_Class


# In[6]:


spinup_hours = "0"

RunType = ("TRACER","WET","NSSL",spinup_hours)
# RunType = ("TRACER","DRY","NSSL",spinup_hours)
ModelData_NSSL = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)

RunType = ("TRACER","WET","TEMPO",spinup_hours)
# RunType = ("TRACER","DRY","TEMPO",spinup_hours)
ModelData_TEMPO = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)


# In[7]:


#Importing Plotting Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_Plotting import ContourPlotting_Class


# In[8]:


#Importing DataSaving Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_DataSaving import DataSaving_Class


# In[9]:


#Importing ERA5 Data Loading Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","ERA5_Data"))
from CLASSES_ERA5DataLoading import ERA5DataLoading_Class


# In[10]:


###############
#JOB ARRAY SETUP


# In[11]:


#Importing PlottingModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_JobArray import JobArray_Class


# In[12]:


#JOB ARRAY SETUP
UsingJobArray=True

def GetNumJobs():
    num_jobs=20
    return num_jobs

num_jobs = GetNumJobs()
JobArray = JobArray_Class(total_elements=ModelData_NSSL.Ntime, num_jobs=num_jobs, UsingJobArray=UsingJobArray)
start_job = JobArray.start_job; end_job = JobArray.end_job

def GetNumElements():
    num_elements = np.arange(ModelData_NSSL.Ntime)[start_job:end_job].tolist()
    return num_elements
loop_elements = GetNumElements()


# In[13]:


########################
#DATA INFORMATION


# In[14]:


# ERA5 atmospheric surface analysis [netCDF4]
# https://gdex.ucar.edu/datasets/d633000/
# https://gdex.ucar.edu/datasets/d633000/filelist/29/?fl=glade


# In[15]:


##########################
#PLOTTING FUNCTIONS


# In[16]:


#Converting timeStrings
def ConvertTimeStringtoDateTime(timeString):
    """
    Converts a time string like '2022-06-30_00.00.00' to a datetime object.
    """
    return datetime.strptime(timeString, '%Y-%m-%d_%H.%M.%S')
def ConvertTimeStringtoTimeTitle(timeString):
    """
    Converts a time string like '2022-06-30_00.00.00' to a datetime object.
    Formatted for use as a plot title.
    """
    # Parse the custom format to a datetime object
    dt = datetime.strptime(timeString, '%Y-%m-%d_%H.%M.%S')
    # Format it to 'YYYY-MM-DD HH:MM:SS'
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def ConvertDatetime64ToTimeTitle(dt64):
    """
    Converts numpy.datetime64 to 'YYYY-MM-DD HH:MM:SS' format.
    """
    return pd.to_datetime(dt64).strftime('%Y-%m-%d %H:%M:%S')


# In[17]:


variableInfoDictionary = {
    "uReconstructZonal": {
        "era5_name": "u",
        "model_multiplier": 1.0,
        "era5_multiplier": 1.0,
        "units": "m/s",
        "name": "u"
    },
    "uReconstructMeridional": {
        "era5_name": "v",
        "model_multiplier": 1.0,
        "era5_multiplier": 1.0,
        "units": "m/s",
        "name": "v"
    },
    "geopotential": {
        "era5_name": "z",
        "model_multiplier": 1.0,
        "era5_multiplier": 1.0, 
        "units": "m",
        "name": r"$\phi$"
    }
}


# In[18]:


def Convert_P1_to_FullLevels(fP1):
    return 0.5 * (
        fP1.isel(nVertLevelsP1=slice(0, -1)) +
        fP1.isel(nVertLevelsP1=slice(1, None))
    )
def GetModelGeopotential(ModelData):
    g0 = 9.80665 
    output = (ModelData.initData['zgrid']*g0)
    output = Convert_P1_to_FullLevels(output)
    output = output.rename({'nVertLevelsP1': 'nVertLevels'})
    return output

def GetVariablePressureSurface(f, p, targetPressure):
    """
    Interpolate a 3-D field (u) onto a constant pressure surface (targetPressure)
    by applying 1D interpolation along each vertical column.
    """

    def interp_column(f_col, p_col):
        # f_col, p_col are 1D arrays along the vertical dimension
        return np.interp(targetPressure, p_col[::-1], f_col[::-1])
        
    output = xr.apply_ufunc(
        interp_column,
        f,
        p,
        input_core_dims=[["nVertLevels"], ["nVertLevels"]],
        output_core_dims=[[]],
        vectorize=True,
        dask="parallelized"
    )
    return output

def ApplySmoothing(data, n_degree=8):
    # https://unidata.github.io/MetPy/latest/examples/calculations/Smoothing.html
    smooth = mpcalc.smooth_gaussian(data,n_degree)
    # smooth = mpcalc.smooth_n_point(data, 9)
    return smooth

def InterpolateModeltoERA5(model,observation):
    model_interp = model.interp(
        latitude=observation.latitude,
        longitude=observation.longitude,
        method="linear"
    )
    return model_interp


# In[19]:


def GetData(t, modelVariableName, option="two"):
    # Map model variable to ERA5 variable name
    ERA5VariableName = variableInfoDictionary[modelVariableName]["era5_name"]

    # Time formatting
    timeString = ModelData_NSSL.timeStrings[t]
    timeString_datetime = ConvertTimeStringtoDateTime(timeString)
    modelTimeTitle = ConvertTimeStringtoTimeTitle(timeString)

    # ----------------------------------------------------
    # Load model data (NSSL and TEMPO)
    # ----------------------------------------------------
    if modelVariableName not in ["geopotential"]:
        modelData_NSSL = ModelData_NSSL.GetDataTimestep(t)[modelVariableName]
        modelData_TEMPO = ModelData_TEMPO.GetDataTimestep(t)[modelVariableName]
    else:
        modelData_NSSL = GetModelGeopotential(ModelData_NSSL)
        modelData_TEMPO = GetModelGeopotential(ModelData_TEMPO)

    # ----------------------------------------------------
    # Load ERA5 from gdex
    # ----------------------------------------------------
    ERA5Data = ERA5DataLoading_Class.LoadERA5Data_gdex(
        DirectoryManager,
        ModelData_NSSL,
        timeString,
        ERA5VariableName
    )

    ERA5TimeTitle = ConvertDatetime64ToTimeTitle(ERA5Data.time.data)

    # ----------------------------------------------------
    # Getting correct pressure levels
    # ----------------------------------------------------    
    if modelVariableName in ["geopotential"]:
        ERA5Data = ERA5Data.sel(level=500,method='nearest')
        targetPressure = 500e2
    elif modelVariableName in ["uReconstructZonal","uReconstructMeridional"]:
        ERA5Data = ERA5Data.sel(level=250,method='nearest')
        targetPressure = 250e2

    pressure_NSSL = ModelData_NSSL.GetDataTimestep(t,varName = "pressure")
    modelData_NSSL = GetVariablePressureSurface(f = modelData_NSSL, p = pressure_NSSL, targetPressure=targetPressure)
    modelData_TEMPO = GetVariablePressureSurface(f = modelData_TEMPO, p = pressure_NSSL, targetPressure=targetPressure)
    
    # ----------------------------------------------------
    # smoothing data for comparison
    # ----------------------------------------------------   
    if option == "one":
        pass
    elif option == "two":
        modelData_NSSL = ApplySmoothing(modelData_NSSL)
        modelData_TEMPO = ApplySmoothing(modelData_TEMPO)
    elif option == "three":
        modelData_NSSL = InterpolateModeltoERA5(modelData_NSSL,ERA5Data)
        modelData_TEMPO = InterpolateModeltoERA5(modelData_TEMPO,ERA5Data)
    # ----------------------------------------------------
    # Return results
    # ----------------------------------------------------
    return (modelData_NSSL,modelData_TEMPO,modelTimeTitle,
            ERA5Data,ERA5TimeTitle,timeString)


# In[20]:


##########################
#PLOTTING FUNCTIONS


# In[21]:


def ComputeOrLoadClims(ModelData_NSSL, ModelData_TEMPO, GetData, modelVariableName, outFilePath):
    """
    Computes min/max for 3 datasets across all time steps and saves/loads them to/from a .pkl file.
    """

    # If file exists, load and return it
    if os.path.exists(outFilePath):
        with open(outFilePath, "rb") as f:
            clim_dict = pickle.load(f)
        print(f"Loaded cached clim dictionary from: {outFilePath}")
        return clim_dict

    # Otherwise compute it
    mins_nssl, maxs_nssl = [], []
    mins_tempo, maxs_tempo = [], []
    mins_era5, maxs_era5 = [], []

    for t in tqdm(range(ModelData_NSSL.Ntime), desc="Computing clim bounds"):
        modelData_NSSL, modelData_TEMPO, _, ERA5Data, _, _ = GetData(t, modelVariableName)

        # Convert to numpy arrays and flatten
        mins_nssl.append(float(modelData_NSSL.min()))
        maxs_nssl.append(float(modelData_NSSL.max()))

        mins_tempo.append(float(modelData_TEMPO.min()))
        maxs_tempo.append(float(modelData_TEMPO.max()))

        mins_era5.append(float(ERA5Data.min()))
        maxs_era5.append(float(ERA5Data.max()))

    # Create dictionary and save
    clim_dict = {
        'nssl': {'min': mins_nssl, 'max': maxs_nssl},
        'tempo': {'min': mins_tempo, 'max': maxs_tempo},
        'era5': {'min': mins_era5, 'max': maxs_era5},
    }

    with open(outFilePath, "wb") as f:
        pickle.dump(clim_dict, f)
        print(f"Saved clim dictionary to: {outFilePath}")

    return clim_dict

def GetClim(clim_dict):
    # To get global colorbar limits:
    vmin = min(min(clim_dict['nssl']['min']),
               min(clim_dict['tempo']['min']),
               min(clim_dict['era5']['min']))
    
    vmax = max(max(clim_dict['nssl']['max']),
               max(clim_dict['tempo']['max']),
               max(clim_dict['era5']['max']))
    clim = (vmin,vmax)
    return clim


# In[22]:


def MakePlot(modelData_NSSL,modelData_TEMPO,modelTimeTitle,
             ERA5Data, ERA5TimeTitle,
             timeString, modelVariableName,
             clim=(None,None)):
    model_multiplier = variableInfoDictionary[modelVariableName]["model_multiplier"] 
    era5_multiplier = variableInfoDictionary[modelVariableName]["era5_multiplier"] 
    units = variableInfoDictionary[modelVariableName]["units"] 
    name = variableInfoDictionary[modelVariableName]["name"] 

    #Setting up diverging colorbar
    if modelVariableName in ["uReconstructZonal","uReconstructMeridional"]:
        diverging_colorbar=True
    else:
        diverging_colorbar=False

    #Plotting
    
    fig, axes = ContourPlotting_Class.CreateMapAxes(nrows=1,ncols=3,
                                                  figsize=(16,8))
    
    #Plotting ModelRadar
    #nssl
    axis = axes[0,0]
    lat = modelData_NSSL['latitude']
    lon = modelData_NSSL['longitude']
    contourPlot = ContourPlotting_Class.PlotContourPlot(axis,lat,lon,modelData_NSSL,
                                                        dataName="NSSL", timeTitle = modelTimeTitle,
                                                        multiplier = model_multiplier,
                                                        clim=clim,
                                                        diverging_colorbar=diverging_colorbar)

    #tempo
    axis = axes[0,2]
    lat = modelData_TEMPO['latitude']
    lon = modelData_TEMPO['longitude']
    contourPlot = ContourPlotting_Class.PlotContourPlot(axis,lat,lon,modelData_TEMPO,
                                                        dataName="TEMPO", timeTitle = modelTimeTitle,
                                                        multiplier = model_multiplier,
                                                        clim=clim,
                                                        diverging_colorbar=diverging_colorbar)

    
    #Plotting ERA5
    #mrms data
    axis = axes[0,1]
    lat = ERA5Data['latitude'].data
    lon = ERA5Data['longitude'].data    
    contourPlot = ContourPlotting_Class.PlotContourPlot(axis,lat,lon,ERA5Data,
                                                        dataName="ERA5", timeTitle = modelTimeTitle,
                                                        multiplier = era5_multiplier,
                                                        clim=clim,
                                                        diverging_colorbar=diverging_colorbar)


    #Shared Colorbar
    colorbarTitle = f"{name} "+ units
    colorBar = ContourPlotting_Class.AddSharedColorbar(fig, contourPlot, colorbarTitle = colorbarTitle)

    return fig


# In[23]:


def GetOutputFile(ModelData_1,ModelData_2, outputPlottingDirectory):
    outputSubDirectory = f"{ModelData_1.region}_{ModelData_1.case}_{ModelData_1.spinup_hours}hrs"
    os.makedirs(os.path.join(outputPlottingDirectory, outputSubDirectory), exist_ok=True)

    
    outputFilePath = os.path.join(
        outputPlottingDirectory,
        outputSubDirectory)
    return outputFilePath


# In[24]:


def SaveFigure(fig, ModelData_1,ModelData_2,modelVariableName, timeString):
    """
    Saves a figure to corresponding directory.
    """
    # --- Define output subdirectory and file path ---
    outputFilePath = GetOutputFile(ModelData_1,ModelData_2, outputPlottingDirectory)
    outputFilePath = os.path.join(outputFilePath,modelVariableName)
    os.makedirs(outputFilePath, exist_ok=True)
    
    outputFileName = f"ERA5Comparison_{modelVariableName}_{ModelData_1.mpType}vsERA5vs{ModelData_2.mpType}"
    outputFileName += f"_{ModelData_1.spinup_hours}_{timeString}.png"
    outputFile = os.path.join(outputFilePath,outputFileName)

    # --- Save figure ---
    fig.savefig(outputFile, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {outputFile}")


# In[25]:


##########################
#PLOTTING


# In[26]:


modelVariableNames = ["uReconstructZonal","uReconstructMeridional","geopotential"]


# In[27]:


def RunERA5ComparisonClims(ModelData_NSSL, ModelData_TEMPO, GetData, 
                           modelVariableName, outputDirectory):
    """
    Wrapper for generating or loading climatologies for ERA5 comparison.
    This function simply wraps your existing code without modifying it.
    """

    # Construct output filename
    outFileName = (
        f"ERA5Comparison_clims_{ModelData_NSSL.region}_"
        f"{ModelData_NSSL.case}_spinup{ModelData_NSSL.spinup_hours}hrs_"
        f"{modelVariableName}.pkl"
    )
    outFilePath = os.path.join(outputDirectory, outFileName)

    # Compute or load climatologies
    clim_dict = ComputeOrLoadClims(
        ModelData_NSSL, ModelData_TEMPO, GetData, modelVariableName,
        outFilePath=outFilePath
    )

    # Extract the climatology
    clim = GetClim(clim_dict)

    return clim


# In[28]:


#getting clims (first time)
for modelVariableName in modelVariableNames:
    clim = RunERA5ComparisonClims(ModelData_NSSL, ModelData_TEMPO, GetData, 
                           modelVariableName, outputDirectory)


# In[ ]:


#running
for modelVariableName in modelVariableNames:

    #getting clims (second time)
    clim = RunERA5ComparisonClims(ModelData_NSSL, ModelData_TEMPO, GetData, 
                           modelVariableName, outputDirectory)

    for t in tqdm(loop_elements, desc="Processing"):
        [modelData_NSSL,modelData_TEMPO,modelTimeTitle,
         ERA5Data, ERA5TimeTitle,
         timeString]=GetData(t,modelVariableName)
        fig = MakePlot(modelData_NSSL,modelData_TEMPO,modelTimeTitle,
                       ERA5Data, ERA5TimeTitle,
                       timeString, modelVariableName,
                       clim=clim)
        SaveFigure(fig, ModelData_NSSL,ModelData_TEMPO, modelVariableName, timeString)


# In[ ]:





# In[112]:


#################
#MAKING ANIMATION
ANIMATE=False #keep false when running with bash code
# ANIMATE=True


# In[113]:


if ANIMATE==True:    
    #Importing AnimationPlotting_Class
    sys.path.append(os.path.join("/glade/u/home/aroseman/Projects/Regional-MPAS-Project/Code/CodeFiles/","DataAnalysis","MPAS_Model_Data"))
    from CLASSES_PlottingModelData import AnimationPlotting_Class


# In[114]:


def GetVariableInputFiles(ModelData_1, ModelData_2, outputPlottingDirectory, modelVariableName):
    # Folder where PNGs live
    filePath = os.path.join(
        GetOutputFile(ModelData_1, ModelData_2, outputPlottingDirectory),
        modelVariableName
    )

    filePattern = os.path.join(filePath, "*.png")
    print("File pattern:", filePattern)

    filePaths = DirectoryManager.GetSortedFileListByTimestamp(filePattern)
    return filePaths

def GetPlottingFileName(ModelData_1, ModelData_2, outputPlottingDirectory, filePaths,
                        modelVariableName, extension="mp4"):

    filePath = os.path.join(
        GetOutputFile(ModelData_1, ModelData_2, outputPlottingDirectory),
        modelVariableName
    )

    basename = os.path.basename(filePaths[0])
    splits = basename.split('_')

    # ERA5Comparison, variableName, model1 vs ERA5 vs model2
    plottingFileName = f"{splits[0]}_{splits[1]}_{splits[2]}.{extension}"

    plottingFilePath = os.path.join(filePath, plottingFileName)
    return plottingFilePath


# In[115]:


# PNGtoMP4 VERSION
if ANIMATE==True:    

    for modelVariableName in modelVariableNames:
        print(f"working on {modelVariableName}")
        # Setting up output file
        print("getting file information")
        imageFiles = GetVariableInputFiles(ModelData_NSSL,ModelData_TEMPO, outputPlottingDirectory,modelVariableName)
        plottingFilePath = GetPlottingFileName(ModelData_NSSL,ModelData_TEMPO, outputPlottingDirectory, imageFiles, modelVariableName, extension="mp4")
    
         # running animation
        fps = AnimationPlotting_Class.CalculateFPS(num_frames=ModelData_NSSL.Ntime, time_interval_minutes=15, desired_duration_min=1)
        AnimationPlotting_Class.PNGsToMP4(imageFiles, plottingFilePath, fps=fps)


# In[ ]:




