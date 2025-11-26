#!/usr/bin/env python
# coding: utf-8

# In[2]:


# WHEN SAFE, MOVE OUTPUT TO RadarComparison/RadarComparison_MRMS


# In[3]:


####################################
#ENVIRONMENT SETUP


# In[4]:


#LIBRARIES

#system
import os
import sys

#math and array operations
import numpy as np
import math
import pandas as pd

#data classes
import xarray as xr

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


# In[5]:


#Importing DirectoryManager Class
sys.path.append(os.path.join("/glade/u/home/aroseman/Projects/Regional-MPAS-Project/Code/CodeFiles/","DataAnalysis"))
from CLASSES_Directories import DirectoryManager_Class


# In[6]:


DirectoryManager = DirectoryManager_Class()

codeType = os.path.join("DataAnalysis", "Observation_Data")
dataType = "RadarData"

outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
outputPlottingDirectory = DirectoryManager.GetOutputPlottingDirectory(codeType, dataType)


# In[7]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
from CLASSES_ModelData import StructuredModelData_Class, DataOperator_Class


# In[8]:


DirectoryManager.dataDirectory


# In[13]:


def GetSimulationTime(RunType):
    if (RunType[0] == "TRACER") and (RunType[1] == "MOIST"):
        SimulationTime = ("2022-06-30","2022-07-03")
    elif (RunType[0] == "TRACER") and (RunType[1] == "DRY"):
        SimulationTime = ("2022-06-08","2022-06-11")
    return SimulationTime

# spinup_hours = "24"
# spinup_hours = "12"
# spinup_hours = "6"
spinup_hours = "0"

RunType = ("TRACER","MOIST","NSSL",spinup_hours)
# RunType = ("TRACER","DRY","NSSL",spinup_hours)
SimulationTime = GetSimulationTime(RunType)
ModelData_NSSL = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType, SimulationTime)

RunType = ("TRACER","MOIST","TEMPO",spinup_hours)
# RunType = ("TRACER","DRY","TEMPO",spinup_hours)
SimulationTime = GetSimulationTime(RunType)
ModelData_TEMPO = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType, SimulationTime)


# In[14]:


#Importing Radar Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","Observation_Data"))
from CLASSES_RadarDataLoading import RadarData_MRMS_Class

sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_RadarDataPlotting import RadarPlotting_Class


# In[15]:


#Importing ERA5 Data Loading Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","ERA5_Data"))
from CLASSES_ERA5DataLoading import ERA5DataLoading_Class,ERA5DataLoading_Class_gdex


# In[16]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_DataSaving import DataSaving_Class


# In[17]:


###############
#JOB ARRAY SETUP


# In[18]:


#Importing PlottingModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_JobArray import JobArray_Class


# In[19]:


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


# In[20]:


########################
#DATA INFORMATION


# In[21]:


#DATA CITATION
# Atmospheric Radiation Measurement (ARM) user facility. 2021. X-Band Scanning ARM Cloud Radar (XSACRCFRQC), 2022-06-09 to 2022-07-02, ARM Mobile Facility (HOU) Houston, TX; AMF1 (main site for TRACER) (M1). Compiled by Y. Feng, A. Matthews, E. Schuman, K. Johnson, I. Lindenmaier, V. Castro and T. Wendler. ARM Data Center. Data set accessed 2025-11-05 at http://dx.doi.org/10.5439/2001296.

#Globus Download Link
# https://urldefense.com/v3/__https://app.globus.org/file-manager?origin_id=ba87aabe-30f6-433d-b4a5-19434c595e0f&origin_path=*rosemana1*261781*__;Ly8v!!PvDODwlR4mBZyAb0!REKAOzHJNvJk50CY5Pjl135CV83BhArwtdyMDuBM-28KqreBug8Xb5Mc3MLgy_p9PUiWe2uVXq-EfUtLcGdH5w$


# In[22]:


#DATA CITATION
# Atmospheric Radiation Measurement (ARM) user facility. 2021. Ka-Band Scanning ARM Cloud Radar (KASACRCFRQC), 2022-06-08 to 2022-07-02, ARM Mobile Facility (HOU) Houston, TX; AMF1 (main site for TRACER) (M1). Compiled by I. Lindenmaier, K. Johnson, D. Nelson, A. Matthews, T. Wendler, V. Melo de Castro, M. Rocque and Y. Feng. ARM Data Center. Data set accessed 2025-11-05 at http://dx.doi.org/10.5439/1877338.

# https://armgov.svcs.arm.gov/capabilities/instruments/kasacr

#Globus Download Link
#https://urldefense.com/v3/__https://app.globus.org/file-manager?origin_id=ba87aabe-30f6-433d-b4a5-19434c595e0f&origin_path=*rosemana1*261893*__;Ly8v!!PvDODwlR4mBZyAb0!UJrKWg_xaYuaaa_iaY91TCVMB_neSskXsDKHtPPCG7Ix6sEmiEvnngTUrYuV18LudZqxB3eHyTDuCHSZ3o3zrg$


# In[30]:


#LOADING RADAR CLASS
if spinup_hours == "0":
    dateString = '2022-06-30_2022-07-03'
else:
    dateString = f"{ModelData_NSSL.simulationDates[0]}_{ModelData_NSSL.simulationDates[-1]}"

RadarData_MRMS = RadarData_MRMS_Class(ModelData_NSSL,
                                      fileDirectory=os.path.join(DirectoryManager.dataDirectory,
                                                                 "Observation_Data/TRACER/MRMS_RadarData",
                                                                 dateString))


# In[31]:


##########################
#DATA LOADING FUNCTIONS


# In[32]:


##########################
#PLOTTING FUNCTIONS


# In[33]:


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


# In[34]:


#Getting TimeData
def GetData(t):
    timeString = ModelData_NSSL.timeStrings[t]
    timeString_datetime = ConvertTimeStringtoDateTime(timeString)
    
    #Loading Model Radar
    modelRadarData_NSSL = ModelData_NSSL.GetDataTimestep_diag(t)["refl10cm_1km"]
    modelRadarData_TEMPO = ModelData_TEMPO.GetDataTimestep_diag(t)["refl10cm_1km"]
    modelRadarTimeTitle = ConvertTimeStringtoTimeTitle(timeString)
    
    #Loading Observational Radar
    radarData, nearestFilePath = RadarData_MRMS.LoadClosestMRMSFile(target_time=timeString_datetime)
    radarTimeTitle = pd.to_datetime(radarData['time'].data[0]).strftime("%Y-%m-%d %H:%M:%S")
    radarData=radarData.isel(time=0)

    #Getting Model MSLP Data
    mslpData_NSSL = ModelData_NSSL.GetDataTimestep_diag(t)['mslp']/1e2
    mslpData_TEMPO = ModelData_TEMPO.GetDataTimestep_diag(t)['mslp']/1e2

    #Getting ERA5 MSLP Data
    mslp_ERA5_alltimes = ERA5DataLoading_Class_gdex.LoadERA5Data(timeString, ModelData_NSSL, DirectoryManager)
    mslp_ERA5 = ERA5DataLoading_Class_gdex.SelectNearestERA5Time(mslp_ERA5_alltimes, timeString)/1e2
    # mslp_ERA5_alltimes = ERA5DataLoading_Class.LoadERA5Data(DirectoryManager, ModelData_NSSL, variableName='msl',dataType='Surface')
    # mslp_ERA5 = ERA5DataLoading_Class.SelectNearestERA5Time(mslp_ERA5_alltimes, ModelData_NSSL.timeStrings[t])/1e2

    return (
    modelRadarData_NSSL,modelRadarData_TEMPO,modelRadarTimeTitle, 
    radarData,radarTimeTitle, 
    timeString,
        
    mslpData_NSSL,mslpData_TEMPO,mslp_ERA5
    )


# In[35]:


##########################
#PLOTTING FUNCTIONS


# In[36]:


def MakePlot(modelRadarData_NSSL,modelRadarData_TEMPO,modelRadarTimeTitle, 
             radarData,radarTimeTitle,
             mslpData_NSSL,mslpData_TEMPO,mslp_ERA5):
    
    fig, axes = RadarPlotting_Class.CreateMapAxes(nrows=1,ncols=3,
                                                  figsize=(16,8))
    
    #Plotting ModelRadar
    #nssl
    axis = axes[0,0]
    lat = modelRadarData_NSSL['latitude']
    lon = modelRadarData_NSSL['longitude']
    contourPlot = RadarPlotting_Class.PlotReflectivity(axis, lat,lon,modelRadarData_NSSL,dataName="NSSL",timeTitle=modelRadarTimeTitle)

    #Adding MSLP Contours
    cs1 = axis.contour(lon, lat, mslpData_NSSL, 
                       colors='black', levels=10, linewidths=1.0, alpha=0.35, zorder=10)
    labels = axis.clabel(cs1, inline=True, fontsize=8, fmt="%.0f",
                colors='black',zorder=11)
    for label in labels:
        label.set_alpha(1)
    
    #tempo
    axis = axes[0,2]
    lat = modelRadarData_TEMPO['latitude']
    lon = modelRadarData_TEMPO['longitude']
    RadarPlotting_Class.PlotReflectivity(axis, lat,lon,modelRadarData_TEMPO,dataName="TEMPO",timeTitle=modelRadarTimeTitle)

    #Adding MSLP Contours
    cs1 = axis.contour(lon, lat, mslpData_TEMPO, 
                       colors='black', levels=10, alpha=0.35, linewidths=1.0,zorder=10)
    labels = axis.clabel(cs1, inline=True, fontsize=8, fmt="%.0f",
                colors='black',zorder=11)
    for label in labels:
        label.set_alpha(1)
    
    #Plotting Observational Radar
    #mrms data
    axis = axes[0,1]
    lat = radarData['latitude'].data
    lon = radarData['longitude'].data-360
    
    RadarPlotting_Class.PlotReflectivity(axis, lat,lon,radarData,dataName="MRMS",timeTitle=radarTimeTitle)

    #Adding MSLP Contours
    cs1 = axis.contour(mslp_ERA5.longitude, mslp_ERA5.latitude, mslp_ERA5, 
                       colors='black', levels=10, alpha=0.35, linewidths=1.0,zorder=10)
    labels = axis.clabel(cs1, inline=True, fontsize=8, fmt="%.0f",
                colors='black',zorder=11)
    for label in labels:
        label.set_alpha(1)
    
    #Adding Colorbar
    colorBar = RadarPlotting_Class.AddSharedColorbar(fig, contourPlot)


    return fig


# In[ ]:





# In[37]:


def GetOutputFile(ModelData_1,ModelData_2, outputPlottingDirectory):
    outputSubDirectory = f"{ModelData_1.region}_{ModelData_1.case}_{ModelData_1.spinup_hours}hrs"
    os.makedirs(os.path.join(outputPlottingDirectory, outputSubDirectory), exist_ok=True)

    
    outputFilePath = os.path.join(
        outputPlottingDirectory,
        outputSubDirectory)
    return outputFilePath
    
def SaveFigure(fig, ModelData_1,ModelData_2, timeString):
    """
    Saves a figure to corresponding directory.
    """
    # --- Define output subdirectory and file path ---
    outputFilePath = GetOutputFile(ModelData_1,ModelData_2, outputPlottingDirectory)
    outputFile = os.path.join(outputFilePath,f"RadarComparison_{ModelData_1.mpType}vsMRMSvs{ModelData_2.mpType}_{timeString}.png")

    # --- Save figure ---
    fig.savefig(outputFile, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {outputFile}")


# In[38]:


##########################
#PLOTTING


# In[ ]:


for t in tqdm(loop_elements, desc="Processing"):
    [modelRadarData_NSSL,modelRadarData_TEMPO,modelRadarTimeTitle, 
     radarData,radarTimeTitle,
     timeString,
     mslpData_NSSL,mslpData_TEMPO,mslp_ERA5]=GetData(t)
    fig = MakePlot(modelRadarData_NSSL,modelRadarData_TEMPO,modelRadarTimeTitle, 
                   radarData,radarTimeTitle,
                   mslpData_NSSL,mslpData_TEMPO,mslp_ERA5)
    SaveFigure(fig, ModelData_NSSL,ModelData_TEMPO, timeString)


# In[ ]:





# In[40]:


#################
#MAKING ANIMATION
ANIMATE=False #keep false when running with bash code
# ANIMATE=True


# In[41]:


if ANIMATE==True:    
    #Importing AnimationPlotting_Class
    sys.path.append(os.path.join("/glade/u/home/aroseman/Projects/Regional-MPAS-Project/Code/CodeFiles/","DataAnalysis","MPAS_Model_Data"))
    from CLASSES_PlottingModelData import AnimationPlotting_Class


# In[42]:


def GetVariableInputFiles(ModelData_1,ModelData_2, outputPlottingDirectory):
    filePath = GetOutputFile(ModelData_1,ModelData_2, outputPlottingDirectory)
    fileName = f"*.png"
    filePattern = DirectoryManager.GetOutputFile(outputPlottingDirectory, filePath, fileName)
    print(filePattern)
    filePaths = DirectoryManager.GetSortedFileListByTimestamp(filePattern)
    return filePaths

def GetPlottingFileName(ModelData_1,ModelData_2, outputPlottingDirectory, filePaths, extension="mp4"):
    filePath = GetOutputFile(ModelData_1,ModelData_2, outputPlottingDirectory)

    splits = os.path.basename(filePaths[0]).split('_')
    plottingFileName = f"{splits[0]}_{splits[1]}.{extension}"
    
    plottingFilePath = DirectoryManager.GetOutputFile(outputPlottingDirectory, filePath, plottingFileName)
    return plottingFilePath


# In[43]:


# PNGtoMP4 VERSION
if ANIMATE==True:    
    # Setting up output file
    print("getting file information")
    imageFiles = GetVariableInputFiles(ModelData_NSSL,ModelData_TEMPO, outputPlottingDirectory)
    plottingFilePath = GetPlottingFileName(ModelData_NSSL,ModelData_TEMPO, outputPlottingDirectory, imageFiles, extension="mp4")

     # running animation
    fps = AnimationPlotting_Class.CalculateFPS(num_frames=ModelData_NSSL.Ntime, time_interval_minutes=15, desired_duration_min=1)
    AnimationPlotting_Class.PNGsToMP4(imageFiles, plottingFilePath, fps=fps)

