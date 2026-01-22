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
from matplotlib.gridspec import GridSpec
from matplotlib.colors import TwoSlopeNorm
import matplotlib.colors as mcolors

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
# dataType = "UpdraftVariableHistograms"
dataType = "UpdraftVariableHistograms_Interpolation" #*TESTING

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

# Region = "Hawaii"; Case = "WET"; spinup_hours = "12";
# Region = "Hawaii"; Case = "TRADES"; spinup_hours = "24"


# In[ ]:


#Load Model Directory Class
RunType = (Region,Case,"NSSL",spinup_hours)
ModelData_NSSL = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)

RunType = (Region,Case,"TEMPO",spinup_hours)
ModelData_TEMPO = StructuredModelData_Class(DirectoryManager.mainDirectory, DirectoryManager.scratchDirectory, RunType)


# In[ ]:


#Importing Radar Classes
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","Observation_Data"))
from CLASSES_RadarDataLoading import RadarData_MRMS_Class, RadarObservationMask_Class

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
JobArray = JobArray_Class(total_elements=ModelData_NSSL.Ntime, num_jobs=num_jobs, UsingJobArray=UsingJobArray)
start_job = JobArray.start_job; end_job = JobArray.end_job

def GetLoopElements(start_job,end_job):
    loop_elements = np.arange(ModelData_NSSL.Ntime)[start_job:end_job].tolist()
    return loop_elements
loop_elements = GetLoopElements(start_job,end_job)


# In[ ]:


####################################
#CALCULATION FUNCTIONS


# In[ ]:


def GetVarData(data, varName):
    if varName == "qc+qi":
        varName_split = varName.split("+")
        varData = data[varName_split[0]] + data[varName_split[1]]
    else:
        varData = data[varName]

    return varData


# In[ ]:


def MakeHistogram(varData, varBins, altitude_levels,altitude_data, altitude_bins):
    """
    Simple fast 2-D histogram generator for gridded data (CFAD-style),
    matching orientation and behavior of the original version.
    """
    # Mask invalid values (NaN or inf)
    field_data = np.ma.masked_invalid(np.asarray(varData))

    # Broadcast altitude levels to 3D grid shape
    if altitude_data is None:
        nz, ny, nx = field_data.shape
        altitude_data = np.repeat(altitude_levels[:, None, None], ny, axis=1)
        altitude_data = np.repeat(altitude_data, nx, axis=2)

    # Apply the same mask to altitude data
    altitude_data = np.ma.masked_where(field_data.mask, altitude_data)

    # Match the original orientation: X = variable, Y = altitude
    hist2d_raw, var_edges, z_edges = np.histogram2d(
        field_data.compressed(),      # variable values first
        altitude_data.compressed(),   # altitude values second
        bins=[varBins, altitude_bins] # same order as original
    )
    return hist2d_raw, var_edges, z_edges
    
def NormalizeHistogram(hist2d_raw):
    level_sums = hist2d_raw.sum(axis=1, keepdims=True)
    level_sums[level_sums == 0] = 1
    hist2d_norm = hist2d_raw / level_sums
    return hist2d_norm * 100


# In[ ]:


def RunHistogram(varData_NSSL,varData_TEMPO, varName,varBinsDictionary,
                 altitude_levels,
                 altitude_data,altitude_bins):
    
    #Getting Histogram Bins for Variable
    varBins = varBinsDictionary[varName]
    
    #Running
    [hist2d_raw_NSSL, field_edges,z_edges] = MakeHistogram(varData_NSSL,varBins, 
                                                           altitude_levels,
                                                           altitude_data,altitude_bins)
    [hist2d_raw_TEMPO, _,_] = MakeHistogram(varData_TEMPO,varBins, 
                                            altitude_levels,
                                            altitude_data,altitude_bins)

    return hist2d_raw_NSSL,hist2d_raw_TEMPO, field_edges,z_edges


# In[ ]:


# #GetAltitudeThings

zGrid_f, zGrid_c = ModelData_NSSL.GetZGrids() #*TESTING
[zTarget_f, zTarget_c] = ModelData_NSSL.GetZTarget(zGrid_f, zGrid_c) #*TESTING

def GetAltitudeThings(ModelData,varName):
    
    #Get Altitude Bins
    if varName == "w":
        # altitude_levels = ModelData.zf
        # altitude_bins   = ModelData.zc

        altitude_levels = zTarget_f #*TESTING
        altitude_bins   = zTarget_c #*TESTING
    else:
        # altitude_levels = ModelData.zc
        # altitude_bins   = ModelData.zf

        altitude_levels = zTarget_c #*TESTING
        altitude_bins   = zTarget_f #*TESTING
    
    ny, nx = len(ModelData.latitude),len(ModelData.longitude)
    altitude_data = np.repeat(altitude_levels[:, None, None], ny, axis=1)
    altitude_data = np.repeat(altitude_data, nx, axis=2)

    return altitude_bins,altitude_levels,altitude_data


# In[ ]:


############################
#RUNNING
running = True #keep true when job array is running
# running = False


# In[ ]:


def GetFileNamePath(ModelData,varName,t):
    
    # Build file name
    fileName = (
        f"{dataType}_{varName}_{ModelData.timeStrings[t]}_{ModelData.region}_"
        f"{ModelData.case}_spinup{ModelData.spinup_hours}hrs.pkl"
    )
    
    # Build directory for radar timeseries
    outputDir = os.path.join(
        DirectoryManager.GetOutputDirectory(codeType, dataType),
        f"{dataType}",
        f"{ModelData.region}_{ModelData.case}_spinup{ModelData.spinup_hours}hrs",
        varName
    )

    os.makedirs(outputDir, exist_ok=True)
    
    # Full path to the .pkl file
    fileNamePath = os.path.join(outputDir, fileName)
    return fileNamePath

def InterpolateWToCenters(wData):
    wData_center = 0.5 * (
        wData.isel(nVertLevelsP1=slice(0, -1)) +
        wData.isel(nVertLevelsP1=slice(1, None))
    )
    wData_center = wData_center.rename({"nVertLevelsP1": "nVertLevels"})
    return wData_center


# In[ ]:


def RunCalculations(ModelData_NSSL,ModelData_TEMPO,varNames,
                    DirectoryManager,
                    zTarget = None):
    wthresh_updraft = 0.1; wthresh_downdraft = -0.1 #*NEW
    
    # ----------------------------------------------------------
    # 1. SETUP
    # ----------------------------------------------------------
    hist2d_raw_NSSL_updraft  = None
    hist2d_raw_TEMPO_updraft = None
    hist2d_raw_NSSL_downdraft  = None
    hist2d_raw_TEMPO_downdraft = None
    
    mask = RadarObservationMask_Class.LoadMaskData(DirectoryManager, ModelData_NSSL)
    
    # Altitude Setup
    altitude_bins_w,altitude_levels_w,altitude_data_w = GetAltitudeThings(ModelData_NSSL,"w")
    altitude_bins_1,altitude_levels_1,altitude_data_1 = GetAltitudeThings(ModelData_NSSL,"theta")
    
    # ----------------------------------------------------------
    # 2. LOOP OVER TIME
    # ----------------------------------------------------------
    for t in tqdm(loop_elements, desc="Computing"):
        # ------------------------------
        # LOAD DATA
        # ------------------------------
        data_NSSL = ModelData_NSSL.GetDataTimestep(t, printout=False)
        data_TEMPO = ModelData_TEMPO.GetDataTimestep(t, printout=False)

        #Loading W for Later Subsetting
        wSubset_f_NSSL = data_NSSL['w'] #*NEW
        wSubset_f_TEMPO = data_TEMPO['w'] #*NEW
        wSubset_c_NSSL = InterpolateWToCenters(wSubset_f_NSSL) #*NEW
        wSubset_c_TEMPO = InterpolateWToCenters(wSubset_f_TEMPO) #*NEW
        #Interpolating Z levels #*TESTING
        #################################
        wSubset_f_NSSL = ModelData_NSSL.InterpolateVertical(wSubset_f_NSSL,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
        wSubset_f_TEMPO = ModelData_NSSL.InterpolateVertical(wSubset_f_TEMPO,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
        wSubset_c_NSSL = ModelData_NSSL.InterpolateVertical(wSubset_c_NSSL,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
        wSubset_c_TEMPO = ModelData_NSSL.InterpolateVertical(wSubset_c_TEMPO,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
        ################################# 
        wSubset_f_NSSL = wSubset_f_NSSL.where(mask) #*NEW
        wSubset_f_TEMPO = wSubset_f_TEMPO.where(mask) #*NEW
        wSubset_c_NSSL = wSubset_c_NSSL.where(mask) #*NEW
        wSubset_c_TEMPO = wSubset_c_TEMPO.where(mask) #*NEW

        for varName in varNames:
            #getting data
            _varData_NSSL = GetVarData(data_NSSL, varName)
            _varData_TEMPO = GetVarData(data_TEMPO, varName)
            
            #Interpolating Z levels #*TESTING
            #################################
            _varData_NSSL = ModelData_NSSL.InterpolateVertical(_varData_NSSL,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
            _varData_TEMPO = ModelData_TEMPO.InterpolateVertical(_varData_TEMPO,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
            #################################  

            #Applying RadarDataMask
            varData_NSSL  = _varData_NSSL.where(mask)
            varData_TEMPO = _varData_TEMPO.where(mask)

            #Applying Updraft/Downdraft Thresholds #*NEW
            wSubset_NSSL = wSubset_f_NSSL if varName in ["w"] else wSubset_c_NSSL
            wSubset_TEMPO = wSubset_f_TEMPO if varName in ["w"] else wSubset_c_TEMPO
            varData_NSSL_updraft = varData_NSSL.where(wSubset_NSSL > wthresh_updraft)
            varData_TEMPO_updraft = varData_TEMPO.where(wSubset_TEMPO > wthresh_updraft)
            varData_NSSL_downdraft = varData_NSSL.where(wSubset_NSSL < wthresh_downdraft)
            varData_TEMPO_downdraft = varData_TEMPO.where(wSubset_TEMPO < wthresh_downdraft)
            
            #altitude information
            if varName == "w":
                (altitude_bins,altitude_levels,altitude_data)=(altitude_bins_w,altitude_levels_w,altitude_data_w)
            else:
                (altitude_bins,altitude_levels,altitude_data)=(altitude_bins_1,altitude_levels_1,altitude_data_1)
        
            # ------------------------------
            # CALCULATING HISTOGRAM
            # ------------------------------

            [hist2d_raw_NSSL_updraft,hist2d_raw_TEMPO_updraft, field_edges,z_edges] = RunHistogram(varData_NSSL_updraft,varData_TEMPO_updraft, varName,varBinsDictionary,
                                                                                   altitude_levels,
                                                                                   altitude_data,altitude_bins) #*NEW
            [hist2d_raw_NSSL_downdraft,hist2d_raw_TEMPO_downdraft, field_edges,z_edges] = RunHistogram(varData_NSSL_downdraft,varData_TEMPO_downdraft, varName,varBinsDictionary,
                                                                                   altitude_levels,
                                                                                   altitude_data,altitude_bins) #*NEW
        
            # ----------------------------------------------------------
            # 3. COMBINING INTO DICTIONARY
            # ----------------------------------------------------------
            results = {
                # --- HISTOGRAMS ---
                "hist2d_raw_NSSL_updraft":  hist2d_raw_NSSL_updraft, #*NEW
                "hist2d_raw_TEMPO_updraft": hist2d_raw_TEMPO_updraft, #*NEW
                "hist2d_raw_NSSL_downdraft":  hist2d_raw_NSSL_downdraft, #*NEW
                "hist2d_raw_TEMPO_downdraft": hist2d_raw_TEMPO_downdraft, #*NEW
            
                # --- AXES ---
                "field_edges": field_edges,
                "z_edges": z_edges}
            
            # ----------------------------------------------------------
            # SAVE TO PKL
            # ----------------------------------------------------------
            fileNamePath = GetFileNamePath(ModelData_NSSL,varName,t)
            with open(fileNamePath, "wb") as f:
                pickle.dump(results, f)
            
            print(f"Saved histogram to: {fileNamePath}")
            del _varData_NSSL, _varData_TEMPO
            del varData_NSSL, varData_TEMPO
        del data_NSSL, data_TEMPO


# In[ ]:


numBins = 500 + 1
varBinsDictionary = {"w": np.linspace(-25,50,numBins),
                     "theta": np.linspace(280,360,numBins),
                     "relhum": np.linspace(0,110,numBins),
                     "qv": np.linspace(0,25/1e3,numBins), 
                     "qc+qi": np.linspace(0,15/1e3,numBins),
                     "qg": np.linspace(0,20/1e3,numBins),
                     "qr": np.linspace(0,15/1e3,numBins)}

varNames = ["w","theta","relhum","qv","qc+qi","qg","qr"]


# In[ ]:


if running == True:
    
    RunCalculations(ModelData_NSSL,ModelData_TEMPO,varNames,
                              DirectoryManager)


# In[ ]:





# In[ ]:


############################
#RECOMBINING ALL TIMESTEPS
recombining = False
# recombining = True


# In[ ]:


def GetFileNamePath_Combined(ModelData,varName):
    
    # Build file name
    fileName = (
        f"{dataType}_{varName}_{ModelData.region}_"
        f"{ModelData.case}_spinup{ModelData.spinup_hours}hrs.pkl"
    )
    
    # Build directory for radar timeseries
    outputDir = os.path.join(
        DirectoryManager.GetOutputDirectory(codeType, dataType),
        f"{dataType}",
        f"{ModelData.region}_{ModelData.case}_spinup{ModelData.spinup_hours}hrs",
        varName
    )

    os.makedirs(outputDir, exist_ok=True)
    
    # Full path to the .pkl file
    fileNamePath_combined = os.path.join(outputDir, fileName)
    return fileNamePath_combined


# In[ ]:


def CombineAllTimeSteps(ModelData, mode="combine"):

    for varName in varNames:

        fileNamePath_combined = GetFileNamePath_Combined(ModelData, varName)

        # --- Check once ---
        exists = os.path.exists(fileNamePath_combined)

        # -------------------
        # DELETE MODE
        # -------------------
        if exists and mode == "delete":
            print(f"Deleting combined file: {fileNamePath_combined}")
            os.remove(fileNamePath_combined)
            continue

        # -------------------
        # COMBINE MODE
        # -------------------
        if exists:
            print(f"Combined file exists: {fileNamePath_combined}")
            continue

        print(f"Combined file not found, computing: {varName}")

        results = None

        for t in tqdm(range(ModelData.Ntime), desc=f"Processing {varName}"):

            fileNamePath = GetFileNamePath(ModelData, varName, t)

            if not os.path.exists(fileNamePath):
                continue

            with open(fileNamePath, "rb") as f:
                stepResults = pickle.load(f)

            if results is None:
                results = stepResults
            else:
                results["hist2d_raw_NSSL_updraft"]  += stepResults["hist2d_raw_NSSL_updraft"]
                results["hist2d_raw_TEMPO_updraft"] += stepResults["hist2d_raw_TEMPO_updraft"]
                results["hist2d_raw_NSSL_downdraft"]  += stepResults["hist2d_raw_NSSL_downdraft"]
                results["hist2d_raw_TEMPO_downdraft"] += stepResults["hist2d_raw_TEMPO_downdraft"]

            del stepResults

        with open(fileNamePath_combined, "wb") as f:
            pickle.dump(results, f)

        del results


# In[ ]:


if recombining == True:
    CombineAllTimeSteps(ModelData_NSSL,mode="combine")


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


###########################
#PLOTTING FUNCTIONS


# In[ ]:


def GetHistogramColormap():

    # ---------------------------------------
    # 1. Define the LOG bin boundaries
    #    (you can adjust these if needed)
    # ---------------------------------------
    log_bins = np.array([1e-3, 1e-2, 1e-1, 1e0, 1e1, 1e2])

    # ---------------------------------------
    # 2. Define colors for each log interval
    #    (10 colors per log bin)
    # ---------------------------------------
    n_per_group = 10   # number of colors per log interval

    # These are the target group colors:
    grey     = np.array([0.60, 0.60, 0.60])
    green    = np.array([0.20, 0.70, 0.20])
    blue     = np.array([0.20, 0.40, 0.90])
    yellow   = np.array([0.95, 0.85, 0.20])
    orange   = np.array([1.00, 0.50, 0.05])
    red      = np.array([0.90, 0.10, 0.10])
    darkred  = np.array([0.60, 0.00, 0.00])

    # Ordered from low → high intensity
    group_colors = [grey, green, blue, yellow, orange, red, darkred]

    # ---------------------------------------
    # 3. Interpolate each group into 10 steps
    # ---------------------------------------
    colors_per_bin = []
    for i in range(len(group_colors)-1):
        start = group_colors[i]
        end   = group_colors[i+1]

        # generate gradient between two colors
        grad = np.linspace(start, end, n_per_group)
        colors_per_bin.append([tuple(c) for c in grad])

    # Flatten color list
    all_colors = [c for group in colors_per_bin for c in group]

    # ---------------------------------------
    # 4. Expand the log bins into sub-bins
    #    (10 subdivisions per decade)
    # ---------------------------------------
    expanded_bins = []
    for low, high in zip(log_bins[:-1], log_bins[1:]):
        sub = np.logspace(np.log10(low), np.log10(high), n_per_group + 1)
        expanded_bins.extend(sub[:-1])
    expanded_bins.append(log_bins[-1])
    expanded_bins = np.array(expanded_bins)

    # ---------------------------------------
    # 5. Build the colormap + norm
    # ---------------------------------------
    cmap = mcolors.ListedColormap(all_colors)
    norm = mcolors.BoundaryNorm(expanded_bins, len(all_colors))

    return cmap, norm


# In[ ]:


def MakePlot(
    hist2d_NSSL, hist2d_TEMPO,
    field_edges, z_edges,
    varName, multiplier=1,
    plotType="contour",
    cmap="turbo",
    norm=None,
    normalize=True,
    ax1=None, ax2=None, cax=None
):
    """
    Draw CFAD-style histograms into provided axes.
    """

    if ax1 is None or ax2 is None or cax is None:
        raise ValueError("ax1, ax2, and cax must be provided")

    # ------------------------------------------------------
    # 1. Bin centers
    # ------------------------------------------------------
    var_centers = 0.5 * (field_edges[:-1] + field_edges[1:])
    z_centers   = 0.5 * (z_edges[:-1] + z_edges[1:])

    # ------------------------------------------------------
    # 2. Levels
    # ------------------------------------------------------
    if not normalize:
        norm = None

    levels = norm.boundaries if norm is not None else 40

    # ------------------------------------------------------
    # 3. Y-axis limits
    # ------------------------------------------------------
    ymin = 0 if varName == "w" else ModelData_NSSL.zc[0]

    if varName in ["theta", "qv"]:
        ymax = 0.5
    else:
        ymax = 20

    ylabel_units = "km" if ymax > 1 else "m"
    ylabel_multiplier = 1 if ymax > 1 else 1e3

    for ax in (ax1, ax2):
        ax.set_ylim(ylabel_multiplier * ymin,
                    ylabel_multiplier * ymax)

    if varName == "theta":
        ax1.set_xlim(290, 320)
        ax2.set_xlim(290, 320)

    # ------------------------------------------------------
    # 4. Plot NSSL
    # ------------------------------------------------------
    p1 = ax1.contourf(
        multiplier * var_centers,
        ylabel_multiplier * z_centers,
        hist2d_NSSL.T,
        levels=levels,
        cmap=cmap,
        norm=norm,
        extend="both"
    )

    ax1.set_title("NSSL")
    ax1.set_xlabel(f"{varName} values")
    ax1.set_ylabel(f"Altitude ({ylabel_units})")

    # ------------------------------------------------------
    # 5. Plot TEMPO
    # ------------------------------------------------------
    p2 = ax2.contourf(
        multiplier * var_centers,
        ylabel_multiplier * z_centers,
        hist2d_TEMPO.T,
        levels=levels,
        cmap=cmap,
        norm=norm,
        extend="both"
    )

    ax2.set_title("TEMPO")
    ax2.set_xlabel(f"{varName} values")
    ax2.set_ylabel(f"Altitude ({ylabel_units})")

    # ------------------------------------------------------
    # 6. Colorbar
    # ------------------------------------------------------
    cbar = plt.colorbar(p2, cax=cax, extend="both")

    if norm is not None:
        ticks = [1e-3, 1e-2, 1e-1, 1, 10, 100]
        cbar.set_ticks(ticks)
        cbar.set_ticklabels(['1e−3','1e−2','1e−1','1','10','100'])

    cbar.set_label("Normalized Frequency (%)" if normalize else "Count")


# In[ ]:


def PlotSingleVariable(ModelData, varName,
                       cmap="turbo", norm=None,
                       normalize=True,
                       updowndraft="updraft"):

    filePath = GetFileNamePath_Combined(ModelData, varName)
    with open(filePath, "rb") as f:
        results = pickle.load(f)

    hist2d_raw_NSSL  = results[f"hist2d_raw_NSSL_{updowndraft}"]
    hist2d_raw_TEMPO = results[f"hist2d_raw_TEMPO_{updowndraft}"]

    hist2d_NSSL  = NormalizeHistogram(hist2d_raw_NSSL)
    hist2d_TEMPO = NormalizeHistogram(hist2d_raw_TEMPO)

    field_edges = results["field_edges"]
    z_edges     = results["z_edges"]

    multiplier = 1e3 if "q" in varName else 1

    fig = plt.figure(figsize=(20, 6))
    gs  = GridSpec(1, 3, figure=fig, width_ratios=[1, 1, 0.05])

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    cax = fig.add_subplot(gs[2])

    MakePlot(
        hist2d_NSSL, hist2d_TEMPO,
        field_edges, z_edges,
        varName=varName,
        multiplier=multiplier,
        cmap=cmap,
        norm=norm,
        normalize=normalize,
        ax1=ax1, ax2=ax2, cax=cax
    )

    # Remove y-axis ticks/label from the second panel
    ax2.set_yticks([])
    ax2.set_ylabel("")

    return fig

from matplotlib.gridspec import GridSpecFromSubplotSpec
def PlotMultipleVariable_V1(ModelData, varNames, normalize=True,
                            updowndraft="updraft"):

    custom_cmap, custom_norm = GetHistogramColormap()

    n = len(varNames)
    fig = plt.figure(figsize=(15, 4 * n))

    outer = GridSpec(n, 1, figure=fig, hspace=0.25)

    for i, varName in enumerate(varNames):

        inner = GridSpecFromSubplotSpec(
            1, 3,
            subplot_spec=outer[i, 0],
            width_ratios=[1, 1, 0.05],
        )

        ax1 = fig.add_subplot(inner[0])
        ax2 = fig.add_subplot(inner[1])
        cax = fig.add_subplot(inner[2])

        filePath = GetFileNamePath_Combined(ModelData, varName)
        with open(filePath, "rb") as f:
            results = pickle.load(f)

        hist2d_NSSL  = NormalizeHistogram(results[f"hist2d_raw_NSSL_{updowndraft}"])
        hist2d_TEMPO = NormalizeHistogram(results[f"hist2d_raw_TEMPO_{updowndraft}"])

        multiplier = 1e3 if "q" in varName else 1

        MakePlot(
            hist2d_NSSL, hist2d_TEMPO,
            results["field_edges"],
            results["z_edges"],
            varName=varName,
            multiplier=multiplier,
            cmap=custom_cmap,
            norm=custom_norm,
            normalize=normalize,
            ax1=ax1, ax2=ax2, cax=cax
        )
        # Remove y-axis ticks/label from the second panel
        ax2.set_yticks([])
        ax2.set_ylabel("")
    return fig

def PlotMultipleVariable_V2(ModelData, varNames, normalize=True,
                            updowndraft="updraft"):

    nvars = len(varNames)
    ncols = 2
    nrows = int(np.ceil(nvars / ncols))

    # Increase height per row so things don’t feel cramped
    fig = plt.figure(figsize=(25, 4.5 * nrows))

    # ---- OUTER GRID: variables ----
    outer = GridSpec(
        nrows, ncols,
        figure=fig,
        hspace=0.30,   # vertical spacing between variable rows
        wspace=0.25    # horizontal spacing between variable columns
    )

    for i, varName in enumerate(varNames):
        custom_cmap, custom_norm = GetHistogramColormap()

        row = i // ncols
        col = i % ncols

        # ---- INNER GRID: NSSL | TEMPO | colorbar ----
        inner = GridSpecFromSubplotSpec(
            1, 3,
            subplot_spec=outer[row, col],
            width_ratios=[1, 1, 0.05],
            wspace=0.1
        )

        ax1 = fig.add_subplot(inner[0])
        ax2 = fig.add_subplot(inner[1])
        cax = fig.add_subplot(inner[2])

        # ---- Load data ----
        filePath = GetFileNamePath_Combined(ModelData, varName)
        with open(filePath, "rb") as f:
            results = pickle.load(f)

        hist2d_NSSL  = NormalizeHistogram(results[f"hist2d_raw_NSSL_{updowndraft}"])
        hist2d_TEMPO = NormalizeHistogram(results[f"hist2d_raw_TEMPO_{updowndraft}"])

        multiplier = 1e3 if "q" in varName else 1

        # ---- Draw CFADs ----
        MakePlot(
            hist2d_NSSL, hist2d_TEMPO,
            results["field_edges"],
            results["z_edges"],
            varName=varName,
            multiplier=multiplier,
            cmap=custom_cmap,
            norm=custom_norm,
            normalize=normalize,
            ax1=ax1, ax2=ax2, cax=cax
        )
        # Remove y-axis ticks/label from the second panel
        ax2.set_yticks([])
        ax2.set_ylabel("")

    return fig


# In[ ]:


def SaveFigure(ModelData, fig,key, normalize=True):
    # --- Define output subdirectory and file path ---
    outputSubDirectory = f"{ModelData.region}_{ModelData.case}_{ModelData.spinup_hours}hrs"
    os.makedirs(os.path.join(outputPlottingDirectory, outputSubDirectory), exist_ok=True)

    if normalize == False:
        key += "_NotNormalized"
    outputFile = os.path.join(
        outputPlottingDirectory,
        outputSubDirectory,
        f"UpdraftVariableHistograms_{key}.png"
    )

    # --- Save figure ---
    fig.savefig(outputFile, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {outputFile}")


# In[ ]:


###########################
#PLOTTING
plotting = False
# plotting = True


# In[ ]:


if plotting == True:
    
    varNames = ["w","theta","qv","qc+qi","qg","qr"]
    fig = PlotMultipleVariable_V2(ModelData_NSSL, varNames, normalize=True,
                                  updowndraft='updraft')
    SaveFigure(ModelData_NSSL, fig,key="1_updraft", normalize=True)


# In[ ]:


if plotting == True:
    
    varNames = ["w","theta","qv","qc+qi","qg","qr"]
    fig = PlotMultipleVariable_V2(ModelData_NSSL, varNames, normalize=True,
                                  updowndraft='downdraft')
    SaveFigure(ModelData_NSSL, fig,key="1_downdraft", normalize=True)

