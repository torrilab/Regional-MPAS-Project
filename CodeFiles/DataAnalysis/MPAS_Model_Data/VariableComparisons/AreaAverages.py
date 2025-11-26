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
matplotlib.use("Agg") #UNCOMMENT IF PLOTTING WITHIN JUPYTER DOCUMENT
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
dataType = "AreaAverages"

outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
outputPlottingDirectory = DirectoryManager.GetOutputPlottingDirectory(codeType, dataType)


# In[ ]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
from CLASSES_ModelData import StructuredModelData_Class, DataOperator_Class


# In[ ]:


spinup_hours = "0"

RunType = ("TRACER","WET","NSSL",spinup_hours)
# RunType = ("TRACER","WET","TEMPO",spinup_hours)

# RunType = ("TRACER","DRY","NSSL",spinup_hours)
# RunType = ("TRACER","DRY","TEMPO",spinup_hours)
ModelData = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)


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
from CLASSES_RadarDataLoading import RadarData_MRMS_Class, RadarObservationMask_Class

sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
from CLASSES_RadarDataPlotting import RadarPlotting_Class


# In[ ]:


####################################
#CALCULATION FUNCTIONS


# In[ ]:


def InitiateMatrix(variableSubset, fill_nan=False):
    """
    Initializes an output matrix for a given variable subset.
    """
    if "nVertLevels" in variableSubset.dims:
        shape = (ModelData.Ntime, ModelData.Nzc)

    elif "nVertLevelsP1" in variableSubset.dims:
        shape = (ModelData.Ntime, ModelData.Nzf)

    else:  # 2D variable case
        shape = (ModelData.Ntime, 1)

    fill_value = np.nan if fill_nan else 0
    output = np.full(shape, fill_value, dtype=float)

    return output


def GetMean(variableSubset):
    variableMean = variableSubset.mean(dim=("latitude","longitude"), skipna=True).data
    return variableMean


# In[ ]:


#Loading Radar Mask
RadarDataMask = RadarObservationMask_Class.LoadMaskData_MRMS(DirectoryManager, ModelData)


# In[ ]:


####################################
#CALCULATION FUNCTIONS


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

def MeanDBZ(variableSubset):
    # Convert from dBZ → linear Z (mm^6 m^-3)
    variableSubset_power = 10 ** (variableSubset / 10.0)

    # Take mean in linear space
    variableMean = GetMean(variableSubset_power)

    # Convert mean Z → back to dBZ
    variableMean = 10.0 * np.log10(variableMean)

    return variableMean

def RunCalculations(varNames):
    outputDictionary={}
    
    num_times = ModelData.Ntime
    for count, t in enumerate(tqdm(range(num_times), desc="Processing timesteps")):
        # if t % 10 == 0: print(f"Currently working on time {t}/{num_times}","\n")
            
        #Loading Data
        [dataSubset, dataSubset_diag, dataSubset_static, lat, lon, _, _] = DataOperator_Class.GetData_Subset(ModelData, t)

        for varName in varNames:
            if count == 0: print(f"Running for {varName}")
            #Subsetting Data

            variableSubset= GetVariableSubset_Helper(ModelData, dataSubset, dataSubset_diag, dataSubset_static, varName)

            if varName in ['refl10cm','refl10cm_1km']:
                variableSubset = variableSubset.where(variableSubset > 0)

            #Applying RadarDataMask
            variableSubset = variableSubset.where(RadarDataMask == True)
            
            #Initializing Output
            if count == 0:
                output = InitiateMatrix(variableSubset, fill_nan=False)
                outputDictionary[varName] = output

            #Taking Mean
            if varName in ['refl10cm','refl10cm_1km']:
                variableMean = MeanDBZ(variableSubset)  
            else:
                variableMean = GetMean(variableSubset)
                
            outputDictionary[varName][t] = variableMean

    return outputDictionary

# Notes:
# (1) may need to subset land/water later


# In[ ]:


def RunAreaAverages(ModelData,varNames,name):
    filePath = DataOperator_Class.GetOutputFilePath(ModelData, DirectoryManager, outputDirectory, fileName = f"outputDictionary_{name}.h5")
    
    #loading back in 
    try:
        outputDictionary = DataSaving_Class.LoadDictionaryFromH5(filePath)
        return outputDictionary
    except Exception as e:
        print(f"Error: {e}")
        
        print("Running Calculation")
        outputDictionary = RunCalculations(varNames) #takes about 10 minutes
        #saving output
        
        DataSaving_Class.SaveDictionaryToH5(outputDictionary, filePath)
        return outputDictionary


# In[ ]:


###############
#Loading in MRMS RadarTimeseries
###############

def LoadRadarTimeseries(ModelData):
    """
    Build the time-series filename using ModelData and load the .pkl file.
    Creates output directory if needed.
    """

    # Build file name
    fileName = (
        f"RadarTimeseries_{ModelData.region}_"
        f"{ModelData.case}_spinup{ModelData.spinup_hours}hrs.pkl"
    )

    # Build directory for radar timeseries
    outputDir = os.path.join(
        DirectoryManager.GetOutputDirectory(codeType='DataAnalysis/Observation_Data', dataType='RadarComparison'),
        "RadarTimeseries"
    )
    os.makedirs(outputDir, exist_ok=True)

    # Full path to the .pkl file
    fullFilePath = os.path.join(outputDir, fileName)

    # Try to load existing file
    if os.path.exists(fullFilePath):
        print(f"Loading existing file: {fullFilePath}")
        with open(fullFilePath, "rb") as f:
            return fullFilePath, pickle.load(f)

    # No file found
    return fullFilePath, None

def Add_MRMS_RadarTimeSeries_Plot(ax, loc='lower right'):
    ax.plot([datetime.strptime(t, "%Y-%m-%d_%H.%M.%S") for t in ModelData.timeStrings], MRMS_RadarTimeseries, color='black',label='MRMS')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, frameon=True, fontsize=9, loc=loc)

fileName, list_array = LoadRadarTimeseries(ModelData)
if list_array is not None:
    MRMS_RadarTimeseries = list_array[:,2]


# In[ ]:


####################################
#CALCULATING


# In[ ]:


#running
def GetDictionary_1(ModelData):
    #2D Variables (12 vars)
    #surface variables
    varNames = ["u10", "v10", "q2", "t2m", "th2m",
                "hfx", "qfx", "lh"]
    #microphysics variables
    varNames += ["refl10cm_1km","rainnc+rainc"]
    #convection variables
    varNames += ["cape", "cin"]
    outputDictionary_1 = RunAreaAverages(ModelData,varNames, "1")
    return outputDictionary_1


# In[ ]:


#running
def GetDictionary_2(ModelData):
    #3D Variables (9 vars)
    #microphysics variables
    varNames = ["refl10cm","qv", "qc+qi", "qr", "qg", "relhum"]
    #convection variables
    varNames += ["w", "theta", "divergence"]
    
    outputDictionary_2 = RunAreaAverages(ModelData,varNames, "2")
    return outputDictionary_2


# In[ ]:


####################################
#PLOTTING FUNCTIONS


# In[ ]:


def GetVerticalCoord(dataSubset):
    pressure_profile = dataSubset['pressure'].mean(dim=("latitude","longitude")).data
    dp = pressure_profile[-1] - pressure_profile[-2]
    p_topface = pressure_profile[-1] + dp  # extrapolate linearly
    pressure_profile_face = np.append(pressure_profile, p_topface)
    return (pressure_profile/100,pressure_profile_face/100)

[dataSubset, dataSubset_diag, dataSubset_static, lat, lon, _, _] = DataOperator_Class.GetData_Subset(ModelData, t=0)
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


def SaveFigure(fig, combinedDict, key,label_text):
    """
    Saves a figure to the appropriate directory based on the models in combinedDict.
    """
    # --- Define output subdirectory and file path ---
    outputSubDirectory = f"{ModelData.region}_{ModelData.case}_{label_text}_{ModelData.spinup_hours}hrs"
    os.makedirs(os.path.join(outputPlottingDirectory, outputSubDirectory), exist_ok=True)

    outputFile = os.path.join(
        outputPlottingDirectory,
        outputSubDirectory,
        f"CombinedPlot_{key}.png"
    )

    # --- Save figure ---
    fig.savefig(outputFile, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {outputFile}")


# In[ ]:


def PlotSingle(axis, outputDictionarys, varName, time, pressure_profiles, labels,
               plottype="TZ", clim=None,num_levels=21):
    """
    Plot one variable on a given Matplotlib axis.
    Supports either:
      - A single dictionary (for single-model plots)
      - Two dictionaries (for model comparisons or line overlays)
    clim: tuple (vmin, vmax) for consistent color scaling (ignored for reflectivity)
    """

    # ------------------------------------------------------
    #  Helper: Line Plot
    # ------------------------------------------------------
    def lineplot(time, output, varName, units, color, label):
        axis.plot(time, output.squeeze(), color=color, label=label)
        axis.set_ylabel(f"{varName} " + fr"$({units})$")
        axis.set_xlabel("Time")
        axis.grid(True)
        SetXLimitsDatetime(axis, time)

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

    # ------------------------------------------------------
    #  Units and scaling
    # ------------------------------------------------------
    units = ModelData.GetUnits_Specific(varName).replace(" ", r"\ ")
    axisTitle = varName.replace("divergence", "convergence")
    if varName in ["qv", "qc", "qi", "qr", "qg", "q2", "qfx"]:
        multiplier = 1e3
        units = units.replace('kg', 'g', 1)
    elif varName == "divergence": #*#*
        multiplier = 1
    else:
        multiplier = 1

    # ------------------------------------------------------
    #  Select pressure profile
    # ------------------------------------------------------
    sample_dict = outputDictionarys[0]
    output_sample = sample_dict[varName]
    pressure_profile = (
        pressure_profiles[0]
        if output_sample.shape[1] == pressure_profiles[0].shape[0]
        else pressure_profiles[1]
    )

    # ------------------------------------------------------
    #  Case 1: Single-model plotting
    # ------------------------------------------------------
    if len(outputDictionarys) == 1:
        output = multiplier * outputDictionarys[0][varName]

        # Choose color setup
        if varName in ["w", "divergence"]:
            cmap = "RdBu_r"
        elif varName in ["refl10cm", "refl10cm_1km"]:
            cmap = None  # handled separately
        else:
            cmap = "viridis"

        # --- Line plot ---
        if output.ndim == 1 or output.shape[1] == 1:
            color = "k"
            label = labels[0] if labels else None
            lineplot(time, output, axisTitle, units, color, label)

        # --- Contour plot ---
        else:
            if plottype == "TZ" and varName not in ["refl10cm", "refl10cm_1km"]:
                # Apply shared clim via levels
                if clim is not None:
                    levels = multiplier*np.linspace(clim[0], clim[1], num_levels)
                else:
                    levels = num_levels

                # Symmetric norm for diverging fields
                if varName in ["w", "divergence"]:
                    norm = TwoSlopeNorm(vcenter=0.0, vmin=clim[0] if clim else np.nanmin(output),
                                        vmax=clim[1] if clim else np.nanmax(output))
                else:
                    norm = None

                plot = axis.contourf(time, pressure_profile, output.T, cmap=cmap,
                                     levels=levels, norm=norm, extend="both")
                add_colorbar(axis.figure, plot, axis,
                             label=f"{axisTitle} " + fr"$({units})$")
                add_minor_white_grid(axis)
                axis.set_ylabel("Pressure (hPa)")
                axis.set_xlabel("Time")
                axis.invert_yaxis()

            elif plottype == "TZ" and varName in ["refl10cm", "refl10cm_1km"]:
                cmap, norm, levels, ticks = RadarPlotting_Class.GetReflectivityColormap()
                plot = axis.contourf(time, pressure_profile, output.T,
                                     levels=levels, cmap=cmap, norm=norm, extend='both')
                cbar = add_colorbar(axis.figure, plot, axis,
                                    label="Reflectivity (dBZ)", ticks=ticks)
                add_minor_white_grid(axis)
                RadarPlotting_Class.FormatReflectivityColorbar(
                    cbar, ticks, orientation='vertical', show_labels=False
                )
                axis.set_ylabel("Pressure (hPa)")
                axis.set_xlabel("Time")
                axis.invert_yaxis()

            elif plottype == "T":
                mean_output = np.nanmean(output, axis=1)
                color = "k"
                label = labels[0] if labels else None
                lineplot(time, mean_output, axisTitle, units, color, label)

    # ------------------------------------------------------
    #  Case 2: Two-model plotting
    # ------------------------------------------------------
    else:
        output1 = multiplier * outputDictionarys[0][varName]
        output2 = multiplier * outputDictionarys[1][varName]
        label1, label2 = labels

        is_line = (
            output1.ndim == 1 and output2.ndim == 1
            or output1.shape[1] == 1 and output2.shape[1] == 1
        )

        if is_line:
            with np.errstate(invalid="ignore"):
                mean1 = np.nanmean(output1, axis=1) if output1.ndim > 1 else output1
                mean2 = np.nanmean(output2, axis=1) if output2.ndim > 1 else output2
            lineplot(time, mean1, axisTitle, units, "blue", label1)
            lineplot(time, mean2, axisTitle, units, "green", label2)
            axis.legend(loc="upper left")

        else:
            if plottype == "TZ":
                diff = nansubtract(output1, output2)
                cmap = "RdBu_r"
                vlim = np.nanmax(np.abs(diff))
                norm = TwoSlopeNorm(vcenter=0.0, vmin=-vlim, vmax=vlim)
                plot = axis.contourf(time, pressure_profile, diff.T, cmap=cmap,
                                     levels=np.linspace(-vlim, vlim, 40),
                                     norm=norm, extend="both")
                add_colorbar(axis.figure, plot, axis,
                             label=f"Δ{axisTitle} " + fr"$({units})$")
                axis.set_ylabel("Pressure (hPa)")
                axis.set_xlabel("Time")
                axis.invert_yaxis()

            elif plottype == "T":
                with np.errstate(invalid="ignore"):
                    mean1 = np.nanmean(output1, axis=1)
                    mean2 = np.nanmean(output2, axis=1)
                lineplot(time, mean1, axisTitle, units, "blue", label1)
                lineplot(time, mean2, axisTitle, units, "green", label2)
                axis.legend(loc="upper left")

    # ------------------------------------------------------
    #  Title and finish
    # ------------------------------------------------------
    axis.set_title(axisTitle, fontsize=11)


# In[ ]:


def MakeCombinedPlot(combinedDict, key, plottype):
    """
    Creates a combined plot from a model-comparison dictionary:
    combinedDict = {"NSSL": {...}, "TEMPO": {...}, ...}

    For two models and TZ plots:
      Each row = variable
      Columns = [Model1, Model2, Difference]
    For T plots:
      Both models are overlaid on the same axes with distinct colors.
    """

    # --- Extract model and variable structure ---
    combinedDict2 = combinedDict[key]
    modelLabels = list(combinedDict2.keys())  # e.g. ["NSSL", "TEMPO"]
    first_model = modelLabels[0]
    varNames = list(combinedDict2[first_model].keys())
    n_vars = len(varNames)

    # --- Layout logic ---
    if len(modelLabels) == 2 and plottype == "TZ":
        n_cols = 3  # Model1, Model2, Difference
        n_rows = n_vars
        layout_mode = "comparison"
    else:
        n_cols = 3
        n_rows = int(np.ceil(n_vars / n_cols))
        layout_mode = "overlay"

    fig = plt.figure(figsize=(5.5 * n_cols, 3.5 * n_rows))
    gs = gridspec.GridSpec(n_rows, n_cols, figure=fig, wspace=0.3, hspace=0.6)

    # --- Loop through variables ---
    
    for i, varName in enumerate(varNames):
        axisTitle = varName.replace("divergence","convergence")
        # ============================================================
        # TZ layout: 3 columns per variable (Model1, Model2, Δ)
        # ============================================================
        if layout_mode == "comparison":
            row = i

            # --- Compute shared clim for both models ---
            if varName not in ["refl10cm", "refl10cm_1km"]:
                out1 = combinedDict2[modelLabels[0]][varName]
                out2 = combinedDict2[modelLabels[1]][varName]
                vmin = np.nanmin([np.nanmin(out1), np.nanmin(out2)])
                vmax = np.nanmax([np.nanmax(out1), np.nanmax(out2)])
                if varName in ["w","divergence"]: #w
                    vlim = np.nanmax(np.abs([vmin, vmax]))
                    clim = (-vlim, vlim)
                else:
                    clim = (vmin, vmax)
            else:
                clim = None

            # --- Column 1: Model 1 ---
            ax1 = fig.add_subplot(gs[row, 0])
            PlotSingle(ax1, [combinedDict2[modelLabels[0]]], varName, time, pressure_profiles,
                       labels=[modelLabels[0]], plottype="TZ", clim=clim)
            ax1.set_title(f"{modelLabels[0]} {axisTitle}", fontsize=11)

            # --- Column 2: Model 2 ---
            ax2 = fig.add_subplot(gs[row, 1])
            PlotSingle(ax2, [combinedDict2[modelLabels[1]]], varName, time, pressure_profiles,
                       labels=[modelLabels[1]], plottype="TZ", clim=clim)
            ax2.set_title(f"{modelLabels[1]} {axisTitle}", fontsize=11)

            # --- Column 3: Difference ---
            ax3 = fig.add_subplot(gs[row, 2])
            PlotSingle(ax3, [combinedDict2[modelLabels[0]], combinedDict2[modelLabels[1]]],
                       varName, time, pressure_profiles,
                       labels=modelLabels, plottype="TZ")
            ax3.set_title(f"Δ({modelLabels[0]} - {modelLabels[1]}) {axisTitle}", fontsize=11)

        # ============================================================
        # T layout: overlay both models on same axes (line plots)
        # ============================================================
        elif layout_mode == "overlay":
            row, col = divmod(i, n_cols)
            ax = fig.add_subplot(gs[row, col])

            # define consistent colors for models
            model_colors = {"NSSL": "blue", "TEMPO": "green"}

            # plot both models on same axis
            for label in modelLabels:
                dataDictionary = combinedDict2[label]

                # track existing lines to only recolor new ones
                existing_lines = len(ax.get_lines())
                PlotSingle(ax, [dataDictionary], varName, time, pressure_profiles,
                           labels=[label], plottype="T")
                new_lines = ax.get_lines()[existing_lines:]

                for line in new_lines:
                    line.set_color(model_colors.get(label, "k"))
                    line.set_label(label)

            ax.legend(loc="upper left", fontsize=9)
            ax.set_title(axisTitle, fontsize=11)

    # ============================================================
    # Format axes and layout
    # ============================================================
    for ax in fig.get_axes():
        ax.tick_params(labelbottom=True)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    title_y_relative = AdjustLayout(fig)

    # global title
    label_text = " vs ".join(modelLabels)
    plt.suptitle(f"{ModelData.region}_{ModelData.case} {label_text}",
                 fontsize=16, fontweight="bold", y=title_y_relative)

    # ============================================================
    # Saving Figure
    # ============================================================
    # save figure
    label_text = label_text.replace(" ", "")
    return fig, combinedDict2, key, label_text


# In[ ]:


####################################
#CALCULATING


# In[ ]:


#getting NSSL dictionaries
RunType = ("TRACER","WET","NSSL",spinup_hours)
# RunType = ("TRACER","DRY","NSSL",spinup_hours)
ModelData = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)

outputDictionary_2D_NSSL = GetDictionary_1(ModelData)
outputDictionary_3D_NSSL = GetDictionary_2(ModelData)

#getting TEMPO dictionaries
RunType = ("TRACER","WET","TEMPO",spinup_hours)
# RunType = ("TRACER","DRY","TEMPO",spinup_hours)
ModelData = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)

outputDictionary_2D_TEMPO = GetDictionary_1(ModelData)
outputDictionary_3D_TEMPO = GetDictionary_2(ModelData)

#extrapolating th2m for time 0 
for a in [outputDictionary_2D_NSSL,outputDictionary_2D_TEMPO]:
    a['th2m'][0] = 2 * a['th2m'][1] - a['th2m'][2]


# In[ ]:


####################################
#PLOTTING


# In[ ]:


# setting up dictionaries for plotting
labels = ("NSSL", "TEMPO")

# variable groups
print('varGroups')
varGroups = {
    "T_1": outputDictionary_2D_NSSL.keys(),
    "T_2": outputDictionary_3D_NSSL.keys(),
    "TZ_1": ["refl10cm", "qv", "qc+qi", "qr", "qg", "relhum"],
    "TZ_2": ["w", "theta", "divergence"]
}

# model source dictionaries
print('modelDicts')
modelDicts = {
    "NSSL": [outputDictionary_2D_NSSL, outputDictionary_3D_NSSL],
    "TEMPO": [outputDictionary_2D_TEMPO, outputDictionary_3D_TEMPO],
}

# --- function ---
def GetCombinedDictionary(varNames, dicts):
    """Get varName: value from the first dict in `dicts` that contains it."""
    return {v: next((d[v] for d in dicts if v in d), None) for v in varNames}

# --- build labeled combined structure ---
print('combinedDictionary')
combinedDictionary = {
    group: {
        label: GetCombinedDictionary(varNames, modelDicts[label])
        for label in labels
    }
    for group, varNames in varGroups.items()
}

#Format of combinedDictionary
# Combined[key] = { "NSSL": {...}, "TEMPO": {...} }


# In[ ]:


#2D Variable Plots
[fig, combinedDict2, key, label_text] = MakeCombinedPlot(combinedDictionary, key = "T_1", plottype="T")
axes = fig.get_axes()

#adding MRMS timeseries
Add_MRMS_RadarTimeSeries_Plot(axes[8])

SaveFigure(fig, combinedDict2, key, label_text)


# In[ ]:


[fig, combinedDict2, key, label_text] = MakeCombinedPlot(combinedDictionary, key = "T_2", plottype="T")
SaveFigure(fig, combinedDict2, key, label_text)


# In[ ]:


#3D Variable Plots
[fig, combinedDict2, key, label_text] = MakeCombinedPlot(combinedDictionary, key = "TZ_1", plottype="TZ")
SaveFigure(fig, combinedDict2, key, label_text)


# In[ ]:


[fig, combinedDict2, key, label_text] = MakeCombinedPlot(combinedDictionary, key = "TZ_2", plottype="TZ")
SaveFigure(fig, combinedDict2, key, label_text)

