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
dataType = "VariableHistograms_Interpolation"

outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
outputPlottingDirectory = DirectoryManager.GetOutputPlottingDirectory(codeType, dataType)


# In[ ]:


#Importing ModelData Class
sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
from CLASSES_ModelData import StructuredModelData_Class, DataOperator_Class


# In[ ]:


#Setup

# Region = "TRACER"; Case = "WET"; spinup_hours = "0"
# Region = "TRACER"; Case = "DIURNAL"; spinup_hours = "-5"

Region = "PRECIP"; Case = "WET"; spinup_hours = "12"
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


# In[106]:


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


# In[107]:


############################
#RUNNING
running = True #keep true when job array is running
# running = False


# In[108]:


def GetFileNamePath(ModelData,varName,t):
    
    # Build file name
    fileName = (
        f"VariableHistograms_{varName}_{ModelData.timeStrings[t]}_{ModelData.region}_"
        f"{ModelData.case}_spinup{ModelData.spinup_hours}hrs.pkl"
    )
    
    # Build directory for radar timeseries
    outputDir = os.path.join(
        DirectoryManager.GetOutputDirectory(codeType, dataType),
        "VariableHistograms",
        f"{ModelData.region}_{ModelData.case}_spinup{ModelData.spinup_hours}hrs",
        varName
    )

    os.makedirs(outputDir, exist_ok=True)
    
    # Full path to the .pkl file
    fileNamePath = os.path.join(outputDir, fileName)
    return fileNamePath


# In[109]:


def RunCalculations(ModelData_NSSL,ModelData_TEMPO,varNames,
                    DirectoryManager,
                    zTarget = None):
    
    # ----------------------------------------------------------
    # 1. SETUP
    # ----------------------------------------------------------
    hist2d_raw_NSSL  = None
    hist2d_raw_TEMPO = None
    
    mask = RadarObservationMask_Class.LoadMaskData(DirectoryManager, ModelData_NSSL)
    
    # Loading zlevels
    z_levels_filePath = "/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project/MPAS_Atmosphere_8.3.1/TRACER/WET/MPAS-Model_8.3.1_56nz/zeta_30km_57levels.txt"
    zlevels = np.loadtxt(z_levels_filePath)/1e3

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

        for varName in varNames:
            #getting data
            _varData_NSSL = GetVarData(data_NSSL, varName)
            _varData_TEMPO = GetVarData(data_TEMPO, varName)
            
            #Interpolating Z levels #*TESTING
            #################################
            _varData_NSSL = ModelData_NSSL.InterpolateVertical(_varData_NSSL,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
            _varData_TEMPO = ModelData_TEMPO.InterpolateVertical(_varData_TEMPO,zGrid_f,zGrid_c,zTarget_f,zTarget_c)
            #################################
            
    
            varData_NSSL  = _varData_NSSL.where(mask)
            varData_TEMPO = _varData_TEMPO.where(mask)

            #altitude information
            if varName == "w":
                (altitude_bins,altitude_levels,altitude_data)=(altitude_bins_w,altitude_levels_w,altitude_data_w)
            else:
                (altitude_bins,altitude_levels,altitude_data)=(altitude_bins_1,altitude_levels_1,altitude_data_1)
        
            # ------------------------------
            # CALCULATING HISTOGRAM
            # ------------------------------

            [hist2d_raw_NSSL,hist2d_raw_TEMPO, field_edges,z_edges] = RunHistogram(varData_NSSL,varData_TEMPO, varName,varBinsDictionary,
                                                                                   altitude_levels,
                                                                                   altitude_data,altitude_bins)
        
            # ----------------------------------------------------------
            # 3. COMBINING INTO DICTIONARY
            # ----------------------------------------------------------
            results = {
                # --- HISTOGRAMS ---
                "hist2d_raw_NSSL":  hist2d_raw_NSSL,
                "hist2d_raw_TEMPO": hist2d_raw_TEMPO,
            
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


# In[110]:


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
        f"VariableHistograms_{varName}_{ModelData.region}_"
        f"{ModelData.case}_spinup{ModelData.spinup_hours}hrs.pkl"
    )
    
    # Build directory for radar timeseries
    outputDir = os.path.join(
        DirectoryManager.GetOutputDirectory(codeType, dataType),
        "VariableHistograms",
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
                results["hist2d_raw_NSSL"]  += stepResults["hist2d_raw_NSSL"]
                results["hist2d_raw_TEMPO"] += stepResults["hist2d_raw_TEMPO"]

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


def MakePlot(
    hist2d_NSSL, hist2d_TEMPO,
    field_edges, z_edges,
    varName, multiplier=1,
    plotType="contour"
):
    """
    Plot CFAD-style 2D histograms for NSSL and TEMPO schemes side-by-side,
    with properly aligned axes and shared colorbar.
    """

    # ------------------------------------------------------
    # 1. Compute bin centers (for contourf)
    # ------------------------------------------------------
    var_centers = 0.5 * (field_edges[:-1] + field_edges[1:])
    z_centers   = 0.5 * (z_edges[:-1] + z_edges[1:])

    # ------------------------------------------------------
    # 2. Define color levels and figure layout
    # ------------------------------------------------------
    vmin, vmax = 0, 100
    levels = np.linspace(vmin, vmax, 40)

    # Use constrained_layout so colorbar doesn’t overlap
    fig = plt.figure(figsize=(15, 6), constrained_layout=True)
    gs = GridSpec(1, 3, figure=fig, width_ratios=[1, 1, 0.05])

    ax1 = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1])

    # ------------------------------------------------------
    # 3a. Shared y-limit and consistent grid style
    # ------------------------------------------------------
    if varName == "w":
        ymin = 0
    else:
        ymin=ModelData_NSSL.zc[0]
    for ax in [ax1, ax2]:
        if varName == "theta":
            ymax = 0.1
        elif varName == "qv":
            ymax = 0.1
        else:
            ymax = 20
        ylabel_units = "km" if ymax > 1 else "m"
        ylabel_multiplier = 1 if ymax > 1 else 1e3
        ax.set_ylim(ylabel_multiplier*ymin, ylabel_multiplier*ymax)

    # ------------------------------------------------------
    # 3b. Limiting Some Variables X Axis
    # ------------------------------------------------------
    for ax in [ax1, ax2]:
        if varName == "theta":
            ax.set_xlim(290,305)


    # ------------------------------------------------------
    # 4. Plot NSSL
    # ------------------------------------------------------
    
    if plotType == "mesh":
        p1 = ax1.pcolormesh(
            multiplier * field_edges, ylabel_multiplier*z_edges,
            hist2d_NSSL.T, cmap="turbo", vmin=vmin, vmax=vmax, shading="auto"
        )
    elif plotType == "contour":
        p1 = ax1.contourf(
            multiplier * var_centers, ylabel_multiplier*z_centers,
            hist2d_NSSL.T, levels=levels, cmap="turbo", extend="both"
        )
    ax1.set_title(f"NSSL", fontsize=13)
    ax1.set_xlabel(f"{varName} values", fontsize=11)
    ax1.set_ylabel(f"Altitude ({ylabel_units})", fontsize=11)
    # ------------------------------------------------------
    # 5. Plot TEMPO
    # ------------------------------------------------------
    
    if plotType == "mesh":
        p2 = ax2.pcolormesh(
            multiplier * field_edges, ylabel_multiplier*z_edges,
            hist2d_TEMPO.T, cmap="turbo", vmin=vmin, vmax=vmax, shading="auto"
        )
    elif plotType == "contour":
        p2 = ax2.contourf(
            multiplier * var_centers, ylabel_multiplier*z_centers,
            hist2d_TEMPO.T, levels=levels, cmap="turbo", extend="both"
        )
    ax2.set_title(f"TEMPO", fontsize=13)
    ax2.set_xlabel(f"{varName} values", fontsize=11)
    ax2.set_ylabel(f"Altitude ({ylabel_units})", fontsize=11)


    # ------------------------------------------------------
    # 6. Shared colorbar (placed in 3rd GridSpec column)
    # ------------------------------------------------------
    cax = fig.add_subplot(gs[2])
    cbar = fig.colorbar(p2, cax=cax)
    cbar.set_label("Normalized Frequency (%)", fontsize=11)

    return fig


# In[ ]:


def PlotSingleVariable(ModelData, varName):

    
    fileNamePath_combined = GetFileNamePath_Combined(ModelData,varName)

    with open(fileNamePath_combined, "rb") as f:
        results = pickle.load(f)


    hist2d_raw_NSSL = results["hist2d_raw_NSSL"]
    hist2d_raw_TEMPO = results["hist2d_raw_TEMPO"]
    hist2d_NSSL = NormalizeHistogram(hist2d_raw_NSSL)
    hist2d_TEMPO = NormalizeHistogram(hist2d_raw_TEMPO)
    field_edges = results["field_edges"]
    z_edges = results["z_edges"]
    
    multiplier = 1e3 if "q" in varName else 1
    fig = MakePlot(hist2d_NSSL, hist2d_TEMPO,
                   field_edges, z_edges,
                   varName=varName,
                   multiplier=multiplier,
                   plotType="contour")

    return fig
    # fig = PlotSingleVariable(ModelData_NSSL,varName)

def PlotMultipleVariable(ModelData, varNames):

    images = []

    for varName in varNames:
        fig = PlotSingleVariable(ModelData, varName)
        img = FigureToImage(fig)
        images.append(img)
        plt.close(fig)   # 🔴 important to avoid memory leaks

    n = len(images)

    fig = plt.figure(figsize=(12, 4 * n))
    gs = GridSpec(n, 1, figure=fig)

    for i, img in enumerate(images):
        ax = fig.add_subplot(gs[i, 0])
        ax.imshow(img)
        ax.axis("off")

    fig.tight_layout()
    return fig

def FigureToImage(fig):
    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    img = img.reshape((height, width, 3))
    return img

def SaveFigure(ModelData, fig,key):
    # --- Define output subdirectory and file path ---
    outputSubDirectory = f"{ModelData.region}_{ModelData.case}_{ModelData.spinup_hours}hrs"
    os.makedirs(os.path.join(outputPlottingDirectory, outputSubDirectory), exist_ok=True)

    outputFile = os.path.join(
        outputPlottingDirectory,
        outputSubDirectory,
        f"VariableHistograms_{key}.png"
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
    
    varNames = ["w","theta","relhum"]
    fig1 = PlotMultipleVariable(ModelData_NSSL, varNames)
    SaveFigure(ModelData_NSSL, fig1,key="1")


# In[ ]:


if plotting == True:
    varNames = ["qv","qc+qi","qg","qr"]
    fig2 = PlotMultipleVariable(ModelData_NSSL, varNames)
    SaveFigure(ModelData_NSSL, fig2,key="2")


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


###########################
#TESTING


# In[ ]:


# #TESTING

# t=60
# data_NSSL = ModelData_NSSL.GetDataTimestep(t, printout=False)
# data_TEMPO = ModelData_TEMPO.GetDataTimestep(t, printout=False)
# varName = 'w'

# altitude_bins,altitude_levels,altitude_data = GetAltitudeThings(ModelData_NSSL,varName)

# varData_NSSL = GetVarData(data_NSSL, varName)
# varData_TEMPO = GetVarData(data_TEMPO, varName)
# [hist2d_raw_NSSL,hist2d_raw_TEMPO, field_edges,z_edges] = RunHistogram(varData_NSSL,varData_TEMPO, varName,varBinsDictionary,
#                                                                        altitude_levels,
#                                                                        altitude_data,altitude_bins)
# hist2d_NSSL = NormalizeHistogram(hist2d_raw_NSSL)
# hist2d_TEMPO = NormalizeHistogram(hist2d_raw_TEMPO)

# fig = MakePlot(
#     hist2d_NSSL, hist2d_TEMPO,
#     field_edges, z_edges,
#     varName="w",
#     multiplier=1,
#     plotType="contour"
# )

