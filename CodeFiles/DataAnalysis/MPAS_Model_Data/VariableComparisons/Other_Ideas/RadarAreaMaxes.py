#!/usr/bin/env python
# coding: utf-8

# In[ ]:


####################################
#ENVIRONMENT SETUP


# In[ ]:


#LIBRARIES

#system
import os
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
import sys

#math and array operations
import numpy as np
import math

#plotting
import matplotlib
# matplotlib.use("Agg") #UNCOMMENT IF PLOTTING WITHIN JUPYTER DOCUMENT
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm

import cartopy.crs as ccrs
import cartopy.feature as cfeature

#data classes
import xarray as xr
import h5py
import pickle 

#loading bar
from tqdm import tqdm

#dates
from datetime import datetime


# In[ ]:


#Importing DirectoryManager Class
sys.path.append(os.path.join("/glade/u/home/aroseman/Projects/Regional-MPAS-Project/Code/CodeFiles/","DataAnalysis"))
from CLASSES_Directories import DirectoryManager_Class


# In[ ]:


DirectoryManager = DirectoryManager_Class()

codeType = os.path.join("DataAnalysis", "MPAS_Model_Data", "VariableComparisons")
dataType = "RadarAreaMaxes" #*MAX_TESTING
# dataType = "RadarAreaMaxes_Interpolation" #*TESTING

outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
outputPlottingDirectory = DirectoryManager.GetOutputPlottingDirectory(codeType, dataType)


# In[ ]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
from CLASSES_ModelData import StructuredModelData_Class, DataOperator_Class


# In[ ]:


#Setup

Region = "TRACER"; Case = "WET"; spinup_hours = "0"
# Region = "TRACER"; Case = "DIURNAL"; spinup_hours = "-5"

# Region = "PRECIP"; Case = "WET"; spinup_hours = "12"
# Region = "PRECIP"; Case = "DIURNAL"; spinup_hours = "12"

# Region = "Hawaii"; Case = "WET"; spinup_hours = "12"#;spinup_hours="-16"
# Region = "Hawaii"; Case = "TRADES"; spinup_hours = "24"


# In[ ]:


#Load Model Directory Class
RunType = (Region,Case,"NSSL",spinup_hours)
ModelData = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)

# RunType = (Region,Case,"TEMPO",spinup_hours)
# ModelData_TEMPO = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)


# In[ ]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_DataSaving import DataSaving_Class


# In[ ]:


#Importing PlottingModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
from CLASSES_PlottingModelData import RadarPlotting_Class


# In[ ]:


#Importing Radar Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","Observation_Data"))
from CLASSES_RadarDataLoading import RadarData_MRMS_Class,RadarData_PRECIP_Class, RadarObservationMask_Class

sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_RadarDataPlotting import RadarPlotting_Class


# In[ ]:


###############
#JOB ARRAY SETUP


# In[ ]:


#Importing PlottingModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_JobArray import JobArray_Class


# In[ ]:


#JOB ARRAY SETUP
UsingJobArray=True

def GetNumJobs():
    num_jobs=20
    return num_jobs

num_jobs = GetNumJobs()
JobArray = JobArray_Class(total_elements=ModelData.Ntime, num_jobs=num_jobs, UsingJobArray=UsingJobArray)
start_job = JobArray.start_job; end_job = JobArray.end_job

def GetLoopElements(start_job,end_job):
    loop_elements = np.arange(ModelData.Ntime)[start_job:end_job].tolist()
    return loop_elements
loop_elements = GetLoopElements(start_job,end_job)


# In[ ]:


####################################
#CALCULATION FUNCTIONS


# In[ ]:


if ModelData.region in ["PRECIP"]:
    #LOADING RADAR CLASS
    import xesmf as xe
    
    folderDirectory = os.path.join(
        DirectoryManager.dataDirectory,
        "Observation_Data/PRECIP/Radar",
        ModelData.case
    )
    
    RadarData_PRECIP = RadarData_PRECIP_Class(ModelData, folderDirectory)


# In[ ]:


#Loading Radar Mask
RadarDataMask = RadarObservationMask_Class.LoadMaskData(DirectoryManager, ModelData)
if ModelData.region not in ["PRECIP"]:
    RadarObservationLevels = RadarObservationMask_Class.LoadRadarObservationLevels_MRMS(DirectoryManager, ModelData)
else:
    RadarObservationLevels = RadarData_PRECIP.z_heights


# In[ ]:


def InitiateMatrix(variableSubset, fill_nan=False):
    """
    Initializes an output matrix for a given variable subset.
    """
    if "nVertLevels" in variableSubset.dims:
        shape = (ModelData.Ntime, ModelData.Nzc)

    elif "nVertLevelsP1" in variableSubset.dims:
        shape = (ModelData.Ntime, ModelData.Nzf)

    elif "heightAboveSea" in variableSubset.dims:
        shape = (ModelData.Ntime, len(variableSubset.heightAboveSea))

    elif "z" in variableSubset.dims:
        shape = (ModelData.Ntime, len(variableSubset.z))

    else:  # 2D variable case
        shape = (ModelData.Ntime, 1)

    fill_value = np.nan if fill_nan else 0
    output = np.full(shape, fill_value, dtype=float)

    return output

# def GetMean(variableSubset):
#     if "x" in variableSubset.dims and "y" in variableSubset.dims:
#         # Model-style dims
#         dims = ("y", "x")
#     else:
#         # Radar-style dims
#         dims = ("latitude", "longitude")

#     variableMean = variableSubset.mean(dim=dims, skipna=True).data
#     return variableMean

def GetMean(variableSubset):
    if "x" in variableSubset.dims and "y" in variableSubset.dims:
        # Model-style dims
        dims = ("y", "x")
    else:
        # Radar-style dims
        dims = ("latitude", "longitude")
        
    # #(1/A) times integral of phi dA 
    # #dA is [(R*cos(Lat)dLon)][RdLat] = R^2 cos(Lat)dLatdLon ==> weight is simply cos(Lat)
    # weights = np.cos(np.deg2rad(variableSubset.latitude))
    # variableMean = variableSubset.weighted(weights).mean(dim=dims, skipna=True).data

    variableMean = variableSubset.max(dim=dims, skipna=True).data
    return variableMean


# In[ ]:


def GetVariableSubset_Helper(ModelData, dataSubset, dataSubset_diag, dataSubset_static, varName):
    """
    Retrieves a variable subset from the given model data.
    If varName contains a '+', returns the sum of the two variables.
    """
    if '+' in varName:
        var1, var2 = varName.split('+')
        var1 = var1.strip()
        var2 = var2.strip()

        subset1 = DataOperator_Class.GetData_Variable(ModelData, dataSubset, 
                                                      dataSubset_diag, dataSubset_static, var1)
        subset2 = DataOperator_Class.GetData_Variable(ModelData, dataSubset, 
                                                      dataSubset_diag, dataSubset_static, var2)
        variableSubset = subset1 + subset2
    else:
        variableSubset = DataOperator_Class.GetData_Variable(ModelData, dataSubset, 
                                                             dataSubset_diag, dataSubset_static, varName)

    return variableSubset

def MeanDBZ(variableSubset): #*MAX_TESTING
    # # Convert from dBZ → linear Z (mm^6 m^-3)
    # variableSubset_power = 10 ** (variableSubset / 10.0)

    # # Take mean in linear space
    # variableMean = GetMean(variableSubset_power)

    # # Convert mean Z → back to dBZ
    # variableMean = 10.0 * np.log10(variableMean)

    variableMean = GetMean(variableSubset)
    return variableMean


# In[ ]:


def RunCalculations(ModelData, varNames, loop_elements,zTarget=None):
    outputDictionary={}
    
    for count, t in enumerate(tqdm(loop_elements, desc="Processing timesteps")):
        # if t % 10 == 0: print(f"Currently working on time {t}/{num_times}","\n")
            
        #Loading Data
        [dataSubset,dataSubset_diag,dataSubset_static, lat,lon,zGrid_f,zGrid_c, _, _] = DataOperator_Class.GetData_Subset(ModelData, t)

        for varName in varNames:
            if count == 0: print(f"Running for {varName}")
            #Subsetting Data

            if varName in ['refl10cm']:
                variableSubset= GetVariableSubset_Helper(ModelData, dataSubset, dataSubset_diag, dataSubset_static, varName)
                # #Interpolating Z levels #*TESTING
                # #################################
                # if any(dim.startswith("nVertLevels") for dim in variableSubset.dims):
                #     if zTarget is None:
                #         [zTarget_f, zTarget_c] = ModelData.GetZTarget(zGrid_f, zGrid_c)
                #         zTarget = "loaded"
                #     variableSubset = ModelData.InterpolateVertical(variableSubset,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
                # #################################
                variableSubset = variableSubset.where(variableSubset > 0)

            elif varName in ['MergedReflectivityQC_00.50-19.00']:
                variableSubset = RadarData_MRMS_Class.GetData_AllZLevels(DirectoryManager,ModelData, t, RadarObservationLevels)
                variableSubset = variableSubset.where(variableSubset > 0)

            elif varName in ['PRECIP_Radar']:
                variableSubset, _ = RadarData_PRECIP.GetData_AllZLevels(DirectoryManager,ModelData, t)
                variableSubset = RadarData_PRECIP.InterpolateRadarData3D(variableSubset, ModelData, DirectoryManager)
                variableSubset = variableSubset.where(variableSubset > 0)
                

            #Applying RadarDataMask
            if varName in ["refl10cm"]:
                variableSubset = variableSubset.where(RadarDataMask == True)
            
            #Initializing Output
            if count == 0:
                output = InitiateMatrix(variableSubset, fill_nan=False)
                outputDictionary[varName] = output

            #Taking Mean
            if varName in ['refl10cm','MergedReflectivityQC_00.50-19.00','PRECIP_Radar']:
                variableMean = MeanDBZ(variableSubset)  
            else:
                variableMean = GetMean(variableSubset)
                
            outputDictionary[varName][t] = variableMean

    return outputDictionary

# Notes:
# (1) may need to subset land/water later


# In[ ]:


def RunAreaAverages(ModelData,varNames,name, loop_elements):
    filePath = DataOperator_Class.GetOutputFilePath(ModelData, DirectoryManager, outputDirectory, fileName = f"outputDictionary_{name}_{loop_elements[0]}-{loop_elements[-1]+1}.h5")
    
    #loading back in 
    try:
        outputDictionary = DataSaving_Class.LoadDictionaryFromH5(filePath)
        return outputDictionary
    except Exception as e:
        print(f"Error: {e}")
        
        print("Running Calculation")
        outputDictionary = RunCalculations(ModelData,varNames,loop_elements)
        #saving output
        
        DataSaving_Class.SaveDictionaryToH5(outputDictionary, filePath)
        return outputDictionary


# In[ ]:


####################################
#CALCULATING FUNCTIONS
running = True #keep true when job_array is running
# running = False


# In[ ]:


def GetDictionary_NSSL_MRMS(ModelData, loop_elements):
    #microphysics variables
    varNames = ["refl10cm"]
    if ModelData.region not in ["PRECIP"]:
        varNames += ["MergedReflectivityQC_00.50-19.00"]
    else:
        varNames += ["PRECIP_Radar"]
    
    outputDictionary_1 = RunAreaAverages(ModelData,varNames, "1", loop_elements)
    return outputDictionary_1

def GetDictionary_TEMPO(ModelData, loop_elements):
    #microphysics variables
    varNames = ["refl10cm"]
    
    outputDictionary_1 = RunAreaAverages(ModelData,varNames, "1", loop_elements)
    return outputDictionary_1


# In[ ]:


def RunJob(loop_elements):

    #getting NSSL dictionaries
    RunType = (Region,Case,"NSSL",spinup_hours)
    ModelData = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)
    
    outputDictionary_NSSL_MRMS = GetDictionary_NSSL_MRMS(ModelData, loop_elements)
    
    #getting TEMPO dictionaries
    RunType = (Region,Case,"TEMPO",spinup_hours)
    ModelData = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)
    
    outputDictionary_TEMPO = GetDictionary_TEMPO(ModelData, loop_elements)

    return outputDictionary_NSSL_MRMS,outputDictionary_TEMPO


# In[ ]:


if running:
    [outputDictionary_NSSL_MRMS,outputDictionary_TEMPO] = RunJob(loop_elements)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


####################################
#RECOMBINING
recombining = False #keep false when job_array is running
# recombining = True


# In[ ]:


def AddDictionaries(dictA, dictB):
    """
    Modifies dictA by adding dictB values into it
    """
    for key in dictA:
        dictA[key] += dictB[key]
        
def Recombine():
    for job_id in tqdm(range(1, num_jobs + 1)):
    
        start_job, end_job = JobArray._get_job_range(job_id)
        loop_elements = GetLoopElements(start_job, end_job)
    
        dict_NSSL_MRMS, dict_TEMPO = RunJob(loop_elements)
    
        if job_id == 1:
            dict_NSSL_MRMS_all, dict_TEMPO_all = dict_NSSL_MRMS, dict_TEMPO
        else:
            AddDictionaries(dict_NSSL_MRMS_all,  dict_NSSL_MRMS)
            AddDictionaries(dict_TEMPO_all,  dict_TEMPO)
    return dict_NSSL_MRMS_all,dict_TEMPO_all


# In[ ]:


if recombining:
    [outputDictionary_NSSL_MRMS,outputDictionary_TEMPO] = Recombine()


# In[ ]:


# # *REFLECTIVITY_TESTING

# # #Load Model Directory Class
# # RunType = (Region,Case,"NSSL",spinup_hours)
# # ModelData_NSSL = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)

# # RunType = (Region,Case,"TEMPO",spinup_hours)
# # ModelData_TEMPO = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)



# thresholdValue = 20.0  # dBZ

# fig, axes = plt.subplots(
#     nrows=2, ncols=3,
#     figsize=(15, 8),
#     sharex=True, sharey=True
# )

# # =========================
# # NSSL
# # =========================
# a = ModelData_NSSL.GetDataTimestep_diag(
#     t=72, varName="refl10cm", printout=False
# )

# a_mean = a.mean(dim="latitude")
# # a_max = a.max(dim="latitude")
# a_max = MeanDBZ(a)
# a_thresh = a.where(a > thresholdValue).mean(dim="latitude")

# m0 = a_mean.plot(ax=axes[0, 0], cmap="turbo", add_colorbar=False)
# m1 = a_max.plot(ax=axes[0, 1], cmap="turbo", add_colorbar=False)
# m2 = a_thresh.plot(ax=axes[0, 2], cmap="turbo", add_colorbar=False)

# axes[0, 0].set_title("NSSL – Mean")
# axes[0, 1].set_title("NSSL – Max")
# axes[0, 2].set_title(f"NSSL – Mean (>{thresholdValue:.0f} dBZ)")

# # =========================
# # TEMPO
# # =========================
# a = ModelData_TEMPO.GetDataTimestep_diag(
#     t=72, varName="refl10cm", printout=False
# )

# a_mean = a.mean(dim="latitude")
# # a_max = a.max(dim="latitude")
# a_max = MeanDBZ(a)
# a_thresh = a.where(a > thresholdValue).mean(dim="latitude")

# a_mean.plot(ax=axes[1, 0], cmap="turbo", add_colorbar=False)
# a_max.plot(ax=axes[1, 1], cmap="turbo", add_colorbar=False)
# a_thresh.plot(ax=axes[1, 2], cmap="turbo", add_colorbar=False)

# axes[1, 0].set_title("TEMPO – Mean")
# axes[1, 1].set_title("TEMPO – Max")
# axes[1, 2].set_title(f"TEMPO – Mean (>{thresholdValue:.0f} dBZ)")

# # =========================
# # Column-shared colorbars
# # =========================
# cbar_mean = fig.colorbar(
#     m0, ax=axes[:, 0], fraction=0.046, pad=0.02
# )
# cbar_mean.set_label("Reflectivity (dBZ) – Mean")

# cbar_max = fig.colorbar(
#     m1, ax=axes[:, 1], fraction=0.046, pad=0.02
# )
# cbar_max.set_label("Reflectivity (dBZ) – Max")

# cbar_thresh = fig.colorbar(
#     m2, ax=axes[:, 2], fraction=0.046, pad=0.02
# )
# cbar_thresh.set_label(f"Reflectivity (dBZ) – Mean > {thresholdValue:.0f}")

# fig.suptitle("Reflectivity Composites (Latitude Composite)", fontsize=14)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


####################################
#PLOTTING FUNCTIONS
plotting = False #keep false when job array is running
# plotting = True


# In[ ]:


def GetVerticalCoord(dataSubset):
    pressure_profile = dataSubset['pressure'].mean(dim=("latitude","longitude")).data
    dp = pressure_profile[-1] - pressure_profile[-2]
    p_topface = pressure_profile[-1] + dp  # extrapolate linearly
    pressure_profile_face = np.append(pressure_profile, p_topface)
    return (pressure_profile/100,pressure_profile_face/100)

if plotting:
    [dataSubset,dataSubset_diag,dataSubset_static, lat,lon,zGrid_f,zGrid_c, _, _] = DataOperator_Class.GetData_Subset(ModelData, t=0)
    pressure_profiles = GetVerticalCoord(dataSubset)
    time_strings = ModelData.timeStrings
    time = [datetime.strptime(t, "%Y-%m-%d_%H.%M.%S") for t in time_strings]


# In[ ]:


#Helper Functions

def nansubtract(a, b):
    """
    Element-wise subtraction (a - b) that preserves NaNs.

    If shapes differ, raises a ValueError.
    """
    if a.shape != b.shape:
        raise ValueError(f"Shape mismatch: a{a.shape} != b{b.shape}")

    return np.where(np.isnan(a) | np.isnan(b), np.nan, a - b)

# Example: align datetime x-limits to min/max of your data
def SetXLimitsDatetime(ax, time_array):
    """
    Ensures datetime x-axis starts and ends exactly at the first and last time values.
    Works for both datetime.datetime and np.datetime64 arrays.
    """
    import numpy as np
    from matplotlib.dates import date2num

    # Convert to Matplotlib’s internal float format if needed
    times = np.asarray(time_array)
    if np.issubdtype(times.dtype, np.datetime64):
        times = date2num(times)
    elif isinstance(times[0], (object,)):
        try:
            times = date2num(times)
        except Exception:
            pass

    ax.set_xlim(times.min(), times.max())

def AlignAxesRight(ax_list):
    """
    Aligns the right edges of all axes in ax_list (e.g., contour + line plots),
    so that colorbars don't make some axes narrower.

    It uses the first axis that contains a contour or image
    (typically a contourf plot) as the reference width.
    """

    # Try to find a contour axis (has .collections or .images)
    ref_ax = None
    for ax in ax_list:
        if getattr(ax, "collections", []) or getattr(ax, "images", []):
            ref_ax = ax
            break

    # If no contour axis found, just use the first axis
    if ref_ax is None:
        ref_ax = ax_list[0]

    ref_pos = ref_ax.get_position()

    # Apply its width to all other axes
    for ax in ax_list:
        pos = ax.get_position()
        new_pos = [pos.x0, pos.y0, ref_pos.width, pos.height]
        ax.set_position(new_pos)

    print(f"Aligned {len(ax_list)} axes using reference width from contour axis at {ref_pos.width:.3f}")
# #EXAMPLE USAGE
# fig, axs = plt.subplots(2, 1, figsize=(8, 6))

# # contourf on top, line on bottom
# time = np.arange(24)
# pressure = np.linspace(1000, 100, 25)
# data = np.sin(time / 3)[None, :] * np.exp(-pressure[:, None] / 1000)

# plot = axs[0].contourf(time, pressure, data, cmap="RdBu_r")
# plt.colorbar(plot, ax=axs[0], orientation="vertical", pad=0.02)
# axs[1].plot(time, np.sin(time / 3), color="k")

# # Align both
# AlignAxesRight(axs)

# plt.show()

from matplotlib.ticker import MultipleLocator
def add_minor_white_grid(ax, alpha=0.5, lw=1.0, thickness=1.4, color='lightgray'):
    """
    Add white semi-transparent grid lines halfway between major ticks
    on both x and y axes (for contour plots).
    """
    from matplotlib.ticker import MultipleLocator

    # --- Minor locators at half the major spacing ---
    try:
        major_x = ax.xaxis.get_major_locator()
        step_x = major_x()[1] - major_x()[0]
        ax.xaxis.set_minor_locator(MultipleLocator(step_x / 2))
    except Exception:
        pass

    try:
        major_y = ax.yaxis.get_major_locator()
        step_y = major_y()[1] - major_y()[0]
        ax.yaxis.set_minor_locator(MultipleLocator(step_y / 2))
    except Exception:
        pass

    # --- Grid styling ---
    ax.grid(True, which="major", color=color, alpha=alpha, lw=lw * thickness)
    ax.grid(True, which="minor", color=color, alpha=alpha, lw=lw)

def AdjustLayout(fig,
                 left=0.07, right=0.97, bottom=0.07,
                 wspace=0.35, hspace=0.6,
                 title_space_inches=0.9, 
                 title_y_inches_from_top=0.25):
    """
    Applies a robust manual Matplotlib layout
    to a figure, reserving absolute space for a suptitle.
    """
    
    # Get figure height in inches
    fig_height_inches = fig.get_figheight()
    
    # Calculate the 'top' margin (where plots end) in relative figure coords
    # This leaves 'title_space_inches' at the top.
    top_margin = 1.0 - (title_space_inches / fig_height_inches)
    
    # Calculate the 'y' position for the suptitle
    title_y_relative = 1.0 - (title_y_inches_from_top / fig_height_inches)
    
    # Apply the manual layout
    plt.subplots_adjust(left=left, right=right, bottom=bottom, 
                        top=top_margin, wspace=wspace, hspace=hspace)

    # Return the calculated 'y' coordinate for the suptitle
    return title_y_relative


# In[ ]:


####################################
#PLOTTING FUNCTIONS


# In[ ]:


def PlotReflectivity(axis, zlevels, matrix, title, color_label=False):
    
    cmap, norm, levels, ticks = RadarPlotting_Class.GetReflectivityColormap()
    plot = axis.contourf(time, zlevels, matrix.T,
                         levels=levels, cmap=cmap, norm=norm, extend='both')
    cbar = add_colorbar(axis.figure, plot, axis,
                        label="Reflectivity (dBZ)", ticks=ticks)
    add_minor_white_grid(axis)
    RadarPlotting_Class.FormatReflectivityColorbar(
        cbar, ticks, orientation='vertical', show_labels=False
    )

    if not color_label:
        cbar.set_label("")
    
    # SetXLimitsDatetime(axis, time)
    axis.set_title(title)
    axis.set_ylim(0,maxZLevel)    

# ------------------------------------------------------
#  Helper: Consistent Colorbar Formatting
# ------------------------------------------------------
def add_colorbar(fig, mappable, ax, label, ticks=None, orientation="vertical"):
    """Add a consistently styled, larger colorbar."""
    cbar = fig.colorbar(
        mappable, ax=ax, orientation=orientation,
        fraction=0.12, pad=0.020, aspect=20, shrink=1.15
    )
    cbar.set_label(label, fontsize=11)
    cbar.ax.tick_params(labelsize=8, width=1.1, length=4, pad=2)
    if ticks is not None:
        cbar.set_ticks(ticks)
    # Prevent overcrowding
    if len(cbar.get_ticks()) > 10:
        from matplotlib.ticker import MaxNLocator
        cbar.ax.yaxis.set_major_locator(MaxNLocator(8))
    return cbar


def InterpModelToMRMS(model_matrix, z_model, z_mrms):
    """
    Interpolates a time-height matrix (model_matrix) from model vertical levels
    (z_model) to MRMS vertical levels (z_mrms).
    """

    nt = model_matrix.shape[0]
    nz_mrms = len(z_mrms)

    model_interp = np.zeros((nt, nz_mrms))

    for t in range(nt):
        model_interp[t, :] = np.interp(
            z_mrms,
            z_model,
            model_matrix[t, :]
        )

    return model_interp

def PlotDifference(axis, time, zlevels, diff, title, vlim):
    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad("black")
    axis.set_facecolor("black")
    
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-vlim, vmax=vlim)
    levels = np.linspace(-vlim, vlim, 41)

    plot = axis.contourf(
        time,
        zlevels,
        diff.T,
        cmap=cmap,
        levels=levels,
        norm=norm,
        extend="both"
    )

    axis.set_title(title)
    axis.set_xlabel("Time")
    axis.set_ylim(zlevels[0], zlevels[-1])

    return plot


# In[ ]:


zGrid_f, zGrid_c = ModelData.GetZGrids() #*TESTING
[zTarget_f, zTarget_c] = ModelData.GetZTarget(zGrid_f, zGrid_c) #*TESTING

def MakeReflectivityComparisonPlot_Contour(
    outputDictionary_NSSL_MRMS, #this code also works for PRECIP radar
    outputDictionary_TEMPO,
    time,
    RadarObservationLevels):

    # z_levels_filePath = "/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project/MPAS_Atmosphere_8.3.1/TRACER/WET/MPAS-Model_8.3.1_56nz/zeta_30km_57levels.txt"
    # zlevels = np.loadtxt(z_levels_filePath)/1e3
    # zlevels_plot = 0.5 * (zlevels[:-1] + zlevels[1:])
    zlevels_plot = zTarget_c/1e3
    
    fig = plt.figure(figsize=(15, 8))
    gs = gridspec.GridSpec(nrows=2, ncols=3, hspace=0.45, wspace=0.15)
    
    ###########################################
    # ------------ TOP ROW (3 panels) ---------
    ###########################################
    
    # # (0,0) – NSSL
    axis1 = fig.add_subplot(gs[0, 0])
    matrix = outputDictionary_NSSL_MRMS['refl10cm']
    PlotReflectivity(axis1, zlevels_plot, matrix, title="NSSL")
    axis1.set_ylabel("Altitude (km)")
    
    # # (0,1) – MRMS/PRECIP
    axis2 = fig.add_subplot(gs[0, 1])
    matrix = outputDictionary_NSSL_MRMS[radarVariableName]
    PlotReflectivity(axis2, RadarObservationLevels, matrix, title="MRMS")
    
    # # (0,2) – TEMPO
    axis3 = fig.add_subplot(gs[0, 2])
    matrix = outputDictionary_TEMPO['refl10cm']
    PlotReflectivity(axis3, zlevels_plot, matrix, title="TEMPO", color_label=True)
    
    
    ###########################################
    # ----- SECOND ROW (centered: 2 panels) ---
    ###########################################
    
    model_interp_NSSL = InterpModelToMRMS(outputDictionary_NSSL_MRMS['refl10cm'], z_model=zlevels_plot, z_mrms=RadarObservationLevels)
    MRMS_data = outputDictionary_NSSL_MRMS[radarVariableName]
    model_interp_TEMPO = InterpModelToMRMS(outputDictionary_TEMPO['refl10cm'], z_model=zlevels_plot, z_mrms=RadarObservationLevels)
    
    diff_1 = (MRMS_data-model_interp_NSSL)
    diff_2 = (outputDictionary_NSSL_MRMS['refl10cm']-outputDictionary_TEMPO['refl10cm'])
    diff_3 = (MRMS_data-model_interp_TEMPO)
    
    vlim = np.nanmax([
        np.nanmax(np.abs(diff_1)),
        np.nanmax(np.abs(diff_2)),
        np.nanmax(np.abs(diff_3))
    ])
    # (1,0) – Center-left panel
    axis4 = fig.add_subplot(gs[1, 0])
    plot4 = PlotDifference(axis4, time, RadarObservationLevels, diff_1, title=f"{radarName} - NSSL", vlim=vlim)
    axis4.set_ylabel("Altitude (km)")
    axis4.set_xlabel("Time")

    # (1,1) – Center panel
    axis5 = fig.add_subplot(gs[1, 1])
    plot5 = PlotDifference(axis5, time, zlevels_plot, diff_2, title=f"NSSL - TEMPO", vlim=vlim)
    axis5.set_xlabel("Time")
    
    # (1,2) – Center-right panel
    axis6 = fig.add_subplot(gs[1, 2])
    plot6 = PlotDifference(axis6, time, RadarObservationLevels, diff_3, title=f"{radarName} - TEMPO", vlim=vlim)
    axis6.set_xlabel("Time")

    # Add one shared colorbar on the right
    cbar = fig.colorbar(
        plot6,                           # any returned mappable works
        ax=[axis4, axis5, axis6],        # attach to all bottom-row axes
        orientation="vertical",
        fraction=0.03,
        pad=0.02,
        label="ΔReflectivity (dBZ)"
    )
    
    ###########################################
    # Fix time axis labels
    ###########################################
    main_axes = [axis1, axis2, axis3, axis4, axis5, axis6] 
    for ax in main_axes: # <-- LOOP ONLY OVER THE MAIN PLOT AXES
        ax.tick_params(labelbottom=True)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_ylim(0,maxZLevel)

    ###########################################
    # Suptitle
    ###########################################
    fig.suptitle(
        f"{ModelData.region} {ModelData.case}",
        fontsize=20,
        y=0.95,
        fontweight="bold")

    return fig

def lineplot(axis, time, output, varName, units, color, label):
    axis.plot(time, output.squeeze(), color=color, label=label)
    axis.set_ylabel(f"{varName} " + fr"$({units})$")
    axis.set_xlabel("Time")
    axis.grid(True)
    SetXLimitsDatetime(axis, time)
    
def MakeReflectivityComparisonPlot_Line(outputDictionary_NSSL_MRMS, outputDictionary_TEMPO, time):
    
    varName = "Reflectivity"
    units = "dBZ"
    
    fig = plt.figure(figsize=(12, 5))
    gs = gridspec.GridSpec(nrows=1, ncols=1)
    
    axis = fig.add_subplot(gs[0, 0])
    
    
    a = outputDictionary_NSSL_MRMS['refl10cm']
    output = np.nanmean(a,axis=1)
    color = "blue"; label = "NSSL"
    lineplot(axis, time, output, varName, units, color, label)
    
    a = outputDictionary_NSSL_MRMS[radarVariableName]
    output = np.nanmean(a,axis=1)
    color = "black"; label = radarName
    lineplot(axis, time, output, varName, units, color, label)
    
    a = outputDictionary_TEMPO['refl10cm']
    output = np.nanmean(a,axis=1)
    color = "green"; label = "TEMPO"
    lineplot(axis, time, output, varName, units, color, label)
    
    axis.legend(loc="upper left")
    
    axis.set_ylim(bottom=0, top=40)

    ###########################################
    # Suptitle
    ###########################################
    fig.suptitle(
        f"{ModelData.region} {ModelData.case}",
        fontsize=20,
        y=0.95,
        fontweight="bold")
    
    return fig


# In[ ]:


def MakeReflectivityComparisonPlot_ContourLine_Combined(
    outputDictionary_NSSL_MRMS,
    outputDictionary_TEMPO,
    time,
    RadarObservationLevels):

    zlevels_plot = zTarget_c / 1e3

    fig = plt.figure(figsize=(15, 9))
    gs = gridspec.GridSpec(
        nrows=2, ncols=3,
        height_ratios=[2, 1.4],
        hspace=0.35, wspace=0.15
    )

    ###########################################
    # ------------ TOP ROW (TZ) ---------------
    ###########################################

    ax1 = fig.add_subplot(gs[0, 0])
    PlotReflectivity(ax1, zlevels_plot,
                     outputDictionary_NSSL_MRMS["refl10cm"],
                     title="NSSL")
    ax1.set_ylabel("Altitude (km)")

    ax2 = fig.add_subplot(gs[0, 1])
    PlotReflectivity(ax2, RadarObservationLevels,
                     outputDictionary_NSSL_MRMS[radarVariableName],
                     title=radarName)

    ax3 = fig.add_subplot(gs[0, 2])
    PlotReflectivity(ax3, zlevels_plot,
                     outputDictionary_TEMPO["refl10cm"],
                     title="TEMPO",
                     color_label=True)

    ###########################################
    # -------- BOTTOM ROW (TIMESERIES) --------
    ###########################################

    ax_ts = fig.add_subplot(gs[1, :])  # span all 3 columns

    PlotReflectivityTimeseries(
        ax_ts,
        outputDictionary_NSSL_MRMS,
        outputDictionary_TEMPO,
        time
    )

    ###########################################
    # -------- Formatting ---------------------
    ###########################################

    for ax in [ax1, ax2, ax3]:
        ax.set_ylim(0, maxZLevel)
        ax.tick_params(labelbottom=True)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    plt.setp(ax_ts.get_xticklabels(), rotation=45, ha="right")

    fig.suptitle(
        f"{ModelData.region} {ModelData.case}",
        fontsize=20,
        y=0.95,
        fontweight="bold")

    return fig

def PlotReflectivityTimeseries(axis,
                               outputDictionary_NSSL_MRMS,
                               outputDictionary_TEMPO,
                               time):

    varName = "Reflectivity"
    units   = "dBZ"

    # ---- NSSL
    a = outputDictionary_NSSL_MRMS["refl10cm"]
    output = np.nanmean(a, axis=1)
    lineplot(axis, time, output, varName, units,
             color="blue", label="NSSL")

    # ---- Radar
    a = outputDictionary_NSSL_MRMS[radarVariableName]
    output = np.nanmean(a, axis=1)
    lineplot(axis, time, output, varName, units,
             color="black", label=radarName)

    # ---- TEMPO
    a = outputDictionary_TEMPO["refl10cm"]
    output = np.nanmean(a, axis=1)
    lineplot(axis, time, output, varName, units,
             color="green", label="TEMPO")

    axis.legend(loc="upper left")
    axis.set_ylim(0, 40)


# In[ ]:


def GetOutputFile(ModelData, outputPlottingDirectory):
    outputSubDirectory = f"{ModelData.region}_{ModelData.case}_{ModelData.spinup_hours}hrs"
    
    outputFilePath = os.path.join(
        outputPlottingDirectory,
        outputSubDirectory)
    os.makedirs(outputFilePath, exist_ok=True)
    return outputFilePath

def SaveFigure(ModelData, fig, plotType):
    """
    Saves a figure to corresponding directory.
    """
    # --- Define output subdirectory and file path ---
    outputFilePath = GetOutputFile(ModelData, outputPlottingDirectory)
    outputFile = os.path.join(outputFilePath,f"RadarAreaAverages_{plotType}_NSSLvsMRMSvsTEMPO.png")

    # --- Save figure ---
    fig.savefig(outputFile, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {outputFile}")


# In[ ]:


#Removing Levels Above maxZLevel km from Timeseries Averages
maxZLevel=16
def SubsetAltitude(Dictionary,
                   maxZLevel=16):

    for varName, dataArray in Dictionary.items(): 
        
        #Getting Z Threshold Indexes
        z_levels_filePath = "/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project/MPAS_Atmosphere_8.3.1/TRACER/WET/MPAS-Model_8.3.1_56nz/zeta_30km_57levels.txt"
        zlevels = np.loadtxt(z_levels_filePath)/1e3
        zlevels_center = 0.5 * (zlevels[:-1] + zlevels[1:])
        zc_level = np.where(zlevels_center>maxZLevel)[0][0]
        # zlevels = zTarget_f #*TESTING
        # zlevels_center = zTarget_c #*TESTING
        
        zf_level = np.where(zlevels>maxZLevel)[0][0]
        z_level = zf_level if varName == "w" else zc_level
        
        #Applying Nan to Altitudes Greater than maxZLevel km
        
        Dictionary[varName][:,z_level+1:] = np.nan

    return Dictionary

if plotting:
    outputDictionary_NSSL_MRMS = SubsetAltitude(outputDictionary_NSSL_MRMS, maxZLevel)
    outputDictionary_TEMPO = SubsetAltitude(outputDictionary_TEMPO, maxZLevel)


# In[ ]:


####################################
#PLOTTING


# In[ ]:


if plotting:
    radarVariableName = "PRECIP_Radar" if ModelData.region == "PRECIP" else 'MergedReflectivityQC_00.50-19.00'
    radarName = "PRECIP" if ModelData.region == "PRECIP" else "MRMS"


# In[ ]:


if plotting:
    fig = MakeReflectivityComparisonPlot_Contour(
        outputDictionary_NSSL_MRMS,
        outputDictionary_TEMPO,
        time,
        RadarObservationLevels)
    
    SaveFigure(ModelData, fig, plotType="TZ")


# In[ ]:


if plotting:
    fig = MakeReflectivityComparisonPlot_Line(outputDictionary_NSSL_MRMS, 
                                              outputDictionary_TEMPO, 
                                              time)
    SaveFigure(ModelData, fig, plotType="T")


# In[ ]:


if plotting:
    fig = MakeReflectivityComparisonPlot_ContourLine_Combined(outputDictionary_NSSL_MRMS,
                                                        outputDictionary_TEMPO,
                                                        time,
                                                        RadarObservationLevels)
    
    SaveFigure(ModelData, fig, plotType="TZ_T_Combined")


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


####################################
#PLOTTING ALL SIMULATIONS
plotting = False #keep false when job array is running
# plotting = True


# In[ ]:


def GetFigureFilePath(region,case,spinup_hours,
               extension="png"):
    # --- Define output subdirectory ---
    inputSubDirectory = f"{region}_{case}_{spinup_hours}hrs"
    load_dir = os.path.join(outputPlottingDirectory, inputSubDirectory)
    # --- File path ---
    fileName = f"RadarAreaAverages_TZ_T_Combined_NSSLvsMRMSvsTEMPO"
    inputFilePath = os.path.join(
        load_dir,
        f"{fileName}.{extension}"
    )
    return inputFilePath

def GetFilePaths():
    caseList = ConsolidateFigures_CLASS.GetCaseList()
    filePaths = []
    for region, case, spinup_hours in caseList:
        filePaths.append(GetFigureFilePath(region,case,spinup_hours))
    return filePaths


# In[ ]:


if plotting:
    sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
    from CLASSES_Plotting import ConsolidateFigures_CLASS


# In[ ]:


if plotting:
    filePaths = GetFilePaths()
    
    fig = ConsolidateFigures_CLASS.AssembleImageGrid(filePaths=filePaths,
                                                     nrows=3,ncols=2,
                                                     figsize=(5, 4),
                                                     wspace=0.02,hspace=0.02,
                                                     dpi=600)
    ConsolidateFigures_CLASS.SaveCombinedFigure(fig, saveDirectory=outputPlottingDirectory,fileName=dataType)

