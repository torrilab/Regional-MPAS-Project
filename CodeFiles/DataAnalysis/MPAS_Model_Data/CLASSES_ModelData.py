#!/usr/bin/env python
# coding: utf-8

# In[11]:


# ============================================================
# UnstructuredModelData_Class
# ============================================================

#Libraries
import os
import glob
from datetime import datetime, timedelta

import xarray as xr
import uxarray as ux

class UnstructuredModelData_Class:
    def __init__(self, mainDirectory, scratchDirectory, RunType, SimulationTime):
        #DIRECTORIES
        self.mainDirectory = mainDirectory
        self.scratchDirectory = scratchDirectory

        #SIMULATION INFO
        self.region, self.case, self.mpType = RunType
        self.SimulationTime = SimulationTime
        

        #GET DATA
        # Initialize directories and metadata
        [self.dataDirectory, 
         self.fileList, 
         self.Resolution, 
         self.tResolution] = self.GetDataDirectories()

        # Get diagnostic data
        self.fileList_diag = self.GetDataDirectories_diag()

        # Get Grid and Static Data
        self.gridData = self.GetGridData(self.dataDirectory)
        [self.staticData, self.staticDataFilePath, self.staticVariables] = self.GetStaticData(self.dataDirectory)

        # Get timeStrings
        self.timeStrings = self.GetTimeStrings(self.SimulationTime,self.tResolution)

        # # Load Variable Names
        # self.dataVariables,self.dataVariables_diag = self.GetVariableNames()

        # Load Coordinates
        self.GetCoordinates()

        # Print summary
        self.Summary()

    # ============================================================
    # ========== Data Loading Functions ==========
    # ============================================================

    def GetDataDirectories(self):
        """Return directory paths and metadata based on simulation number."""
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                 self.case, "MPAS-Model_"+self.mpType)
        Resolution, tResolution= '20-1km', '15mins'

        filePattern =  os.path.join(dataDirectory, "backup_RESTART2", "history.*.nc")
        fileList = sorted(glob.glob(filePattern))

        return dataDirectory, fileList, Resolution, tResolution

    def GetDataDirectories_diag(self):
        """Return directory paths and metadata based on simulation number."""
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                 self.case, "MPAS-Model_"+self.mpType)
        Resolution, tResolution= '20-1km', '15mins'

        filePattern =  os.path.join(dataDirectory, "backup_RESTART2", "diag.*.nc")
        fileList_diag = sorted(glob.glob(filePattern))

        return fileList_diag

    def GetGridData(self, dataDirectory):
        filePattern = os.path.join(dataDirectory,"*.static.nc")
        staticDataFilePath = glob.glob(filePattern)[0]
        gridData = ux.open_grid(staticDataFilePath, use_dual=True)
        return gridData

    def GetStaticData(self, dataDirectory):
        filePattern = os.path.join(dataDirectory,"*.static.nc")
        staticDataFilePath = glob.glob(filePattern)[0]
        staticData = ux.open_mfdataset(grid_filename_or_obj=staticDataFilePath,
                                 paths=[staticDataFilePath], parallel=True)
        staticVariables = list(staticData.data_vars)
        return staticData, staticDataFilePath, staticVariables

    def GetTimeStrings(self, SimulationTime,tResolution):
        fmt_date = "%Y-%m-%d"
        start = datetime.strptime(SimulationTime[0], fmt_date)
        end = datetime.strptime(SimulationTime[1], fmt_date)
    
        # Determine time delta
        if "min" in tResolution:
            minutes = int(tResolution.replace("mins", "").replace("min", ""))
            delta = timedelta(minutes=minutes)
        elif "hr" in tResolution:
            hours = int(tResolution.replace("hrs", "").replace("hr", ""))
            delta = timedelta(hours=hours)
        else:
            raise ValueError(f"Unsupported tResolution format: {tResolution}")
    
        # Generate sequence of times
        fmt_out = "%Y-%m-%d_%H.%M.%S"
        times = []
        t = start
        while t <= end:
            times.append(t.strftime(fmt_out))
            t += delta
    
        return times

    def GetVariableNames(self):
        first_file = self.fileList[0]
    
        with xr.open_dataset(first_file, engine="netcdf4", decode_times=False, chunks={}) as ds:
            dataVariables = list(ds.data_vars.keys())


        first_file_diag = self.fileList_diag[0]
        with xr.open_dataset(first_file_diag, engine="netcdf4", decode_times=False, chunks={}) as ds:
            dataVariables_diag = list(ds.data_vars.keys())
        return dataVariables, dataVariables_diag

    # ============================================================
    # === Coordinates ========================================
    # ============================================================

    def GetCoordinates(self):
        """Calculate basic model coordinates."""
        self.NTime = len(self.timeStrings)
        print(f"Calculated coordinate: NTime = {self.NTime}")
    
    # # ============================================================
    # # ========== On-demand Variable Access ==========
    # # ============================================================

    def LoadCombinedData(self): #can take a while, better to load timestep by timestep
        data = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
                                 paths=self.fileList, parallel=True)
        print(f"Opened combined data file for all times")
        return data

    def LoadCombinedData_diag(self): #can take a while, better to load timestep by timestep
        data = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
                                 paths=self.fileList_diag, parallel=True)
        print(f"Opened combined data file for all times")
        return data

    def GetDataTimestep(self, t, varName=None):
        if isinstance(t,int):
            filePath = self.fileList[t]
        elif isinstance(t,str):
            fileIndex = self.timeStrings.index(target)
            filePath = self.fileList[fileIndex]
        #loading data
        data = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
                               paths=[filePath])
        print(f"Opened data from {filePath}")

        if varName is not None:
            return data[varName]
        else: 
            return data

    def GetDataTimestep_diag(self, t, varName=None):
        if isinstance(t,int):
            filePath = self.fileList_diag[t]
        elif isinstance(t,str):
            fileIndex = self.timeStrings.index(target)
            filePath = self.fileList_diag[fileIndex]
        #loading data
        data_diag = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
                               paths=[filePath])
        print(f"Opened data from {filePath}")

        if varName is not None:
            return data_diag[varName]
        else: 
            return data_diag
    
    # ============================================================
    # === Information ========================================
    # ============================================================
    
    def Summary(self):
        """Print a clear summary of the MPAS unstructured model configuration."""
        print("\n=== MPAS Unstructured Model Data Summary ===")
        print(f" Region:         {self.region}")
        print(f" Case:           {self.case}")
        print(f" Microphysics:   {self.mpType}")
        print(f" Resolution:     {self.Resolution}")
        print(f" Time Step:      {self.tResolution}")
        print(f" Time Range:     {self.SimulationTime[0]} to {self.SimulationTime[1]}")
        print(f" # Time Steps:   {len(self.timeStrings)}")
        print(f" # History Files:{len(self.fileList)}")
    
        print(f"\nData Directory:")
        print(f"   {self.dataDirectory}")
        print(f"   Static File:  {os.path.basename(self.staticDataFilePath)}")
        print("=========================","\n")

# # ##############
# # #Example Run
# # ##############

# #MAIN DIRECTORIES
# mainDirectory='/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
# mainScratchDirectory='/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
# scratchDirectory = os.path.join(mainScratchDirectory,"MPAS_Atmosphere_8.3.0")

# RunType = ("TRACER","MOIST","NSSL")
# SimulationTime = ("2022-06-30","2022-07-03")
# ModelData = UnstructuredModelData_Class(mainDirectory, scratchDirectory, RunType, SimulationTime)

# # ################
# # #Example Usage
# # ################
# # [dataVariables, dataVariables_diag] = ModelData.GetVariableNames()
# # # ModelData.LoadCombinedData()
# # # ModelData.LoadCombinedData_diag()
# # ModelData.GetDataTimestep(t=100)
# # ModelData.GetDataTimestep(t=100,varName='w')
# # ModelData.GetDataTimestep_diag(t=100)
# # ModelData.GetDataTimestep_diag(t=100,varName='refl10cm')


# In[47]:


# ============================================================
# StructuredModelData_Class 
# (for MPAS Cartesian lat-lon data, converted from original unstructured data using convert_mpas code)
# ============================================================

import os
import glob
from datetime import datetime, timedelta
import xarray as xr

class StructuredModelData_Class:
    def __init__(self, mainDirectory, scratchDirectory, RunType, SimulationTime):
        # DIRECTORIES
        self.mainDirectory = mainDirectory
        self.scratchDirectory = scratchDirectory

        # SIMULATION INFO
        self.region, self.case, self.mpType = RunType
        self.SimulationTime = SimulationTime

        # === DATA DIRECTORIES ===
        (self.dataDirectory,
         self.fileList,
         self.Resolution,
         self.tResolution) = self.GetDataDirectories()

        self.fileList_diag = self.GetDataDirectories_diag()

        # === STATIC DATA ===
        (self.staticData,
         self.staticDataFilePath,
         self.staticVariables) = self.GetStaticData(self.dataDirectory)

        # === TIME STRINGS ===
        self.timeStrings = self.GetTimeStrings(self.SimulationTime, self.tResolution)

        # === COORDINATES ===
        self.GetCoordinates()

        # === SUMMARY ===
        self.Summary()

    # ============================================================
    # Data Loading and Paths
    # ============================================================

    def GetDataDirectories(self):
        """Return main directory and list of history files."""
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                     self.case, f"MPAS-Model_{self.mpType}")
        Resolution, tResolution = '20-1km', '15mins'

        filePattern = os.path.join(dataDirectory, "backup_RESTART2",
                                   "history_cartesian", "history.*.latlon.nc")
        fileList = sorted(glob.glob(filePattern))

        return dataDirectory, fileList, Resolution, tResolution

    def GetDataDirectories_diag(self):
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                     self.case, f"MPAS-Model_{self.mpType}")
        filePattern = os.path.join(dataDirectory, "backup_RESTART2",
                                   "diag_cartesian", "diag.*.latlon.nc")
        return sorted(glob.glob(filePattern))
        
    def GetStaticData(self, dataDirectory):
        """Open static data using xarray."""
        filePattern = os.path.join(dataDirectory, "backup_RESTART2",
                                   "history_cartesian", "TRACER_regional5250_scaled3_x20.835586.static.latlon.nc")
        staticDataFilePath = glob.glob(filePattern)[0]
        staticData = xr.open_dataset(staticDataFilePath, engine="netcdf4")
        staticVariables = list(staticData.data_vars)
        return staticData, staticDataFilePath, staticVariables

    def GetVariableNames(self): 
        first_file = self.fileList[0]
        with xr.open_dataset(first_file, engine="netcdf4") as ds:
            dataVariables = list(ds.data_vars.keys())

        first_file = self.fileList_diag[0]
        with xr.open_dataset(first_file, engine="netcdf4") as ds:
            dataVariables_diag = list(ds.data_vars.keys())
            
        return dataVariables, dataVariables_diag

    def GetCoordinates(self):
        first_file = self.fileList[0]
        with xr.open_dataset(first_file, engine="netcdf4") as ds:
            self.latitude= ds['latitude'].data
            self.longitude = ds['longitude'].data
            self.nVertLevels = ds['nVertLevels'].data
            self.nVertLevelsP1 = ds['nVertLevelsP1'].data
            self.nSoilLevels = ds['nSoilLevels'].data
            
        self.coordinateList = ["latitude", "longitude", "nVertLevels", "nVertLevelsP1", "nSoilLevels"]

    # ============================================================
    # Time Control
    # ============================================================

    def GetTimeStrings(self, SimulationTime, tResolution):
        fmt_date = "%Y-%m-%d"
        start = datetime.strptime(SimulationTime[0], fmt_date)
        end = datetime.strptime(SimulationTime[1], fmt_date)

        if "min" in tResolution:
            delta = timedelta(minutes=int(tResolution.replace("mins", "").replace("min", "")))
        elif "hr" in tResolution:
            delta = timedelta(hours=int(tResolution.replace("hrs", "").replace("hr", "")))
        else:
            raise ValueError(f"Unsupported tResolution format: {tResolution}")

        fmt_out = "%Y-%m-%d_%H.%M.%S"
        times = []
        t = start
        while t <= end:
            times.append(t.strftime(fmt_out))
            t += delta
        return times

    # ============================================================
    # Data Access
    # ============================================================

    def GetDataTimestep(self, t, varName=None):
        """Load one timestep (index or string)."""
        if isinstance(t, int):
            filePath = self.fileList[t]
        elif isinstance(t, str):
            fileIndex = self.timeStrings.index(t)
            filePath = self.fileList[fileIndex]
        else:
            raise ValueError("t must be int (index) or str (time string).")

        data = xr.open_dataset(filePath, engine="netcdf4", decode_times=False)
        print(f"Opened history file: {filePath}")

        if varName:
            return data[varName].isel(Time=0)
        else:
            return data.isel(Time=0)

    def GetDataTimestep_diag(self, t, varName=None):
        if isinstance(t, int):
            filePath = self.fileList_diag[t]
        elif isinstance(t, str):
            fileIndex = self.timeStrings.index(t)
            filePath = self.fileList_diag[fileIndex]
        else:
            raise ValueError("t must be int (index) or str (time string).")

        data = xr.open_dataset(filePath, engine="netcdf4", decode_times=False)
        print(f"Opened diag file: {filePath}")

        if varName:
            return data[varName].isel(Time=0)
        else:
            return data.isel(Time=0)

    # ============================================================
    # Summary
    # ============================================================

    def Summary(self):
        print("\n=== MPAS Structured (lat-lon) Model Data Summary ===")
        print(f" Region:         {self.region}")
        print(f" Case:           {self.case}")
        print(f" Microphysics:   {self.mpType}")
        print(f" Resolution:     {self.Resolution}")
        print(f" Time Step:      {self.tResolution}")
        print(f" Time Range:     {self.SimulationTime[0]} to {self.SimulationTime[1]}")
        print(f" Coordinates:    {self.coordinateList}")
        print(f" # History Files:{len(self.fileList)}")
        print(f" # Diag Files:   {len(self.fileList_diag)}")
        print(f" # Time Steps:   {len(self.timeStrings)}")
        print(f" Data Directory: {self.dataDirectory}")
        print(f" Static File:    {os.path.basename(self.staticDataFilePath)}")
        print("=============================================\n")

# ##############
# #Example Run
# ##############

# #MAIN DIRECTORIES

# mainDirectory='/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
# mainScratchDirectory='/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
# scratchDirectory = os.path.join(mainScratchDirectory,"MPAS_Atmosphere_8.3.0")

# RunType = ("TRACER","MOIST","NSSL")
# SimulationTime = ("2022-06-30","2022-07-03")
# ModelData = StructuredModelData_Class(mainDirectory, scratchDirectory, RunType, SimulationTime)

# # ################
# # #Example Usage
# # ################
# # [dataVariables, dataVariables_diag] = ModelData.GetVariableNames()
# # ModelData.GetDataTimestep(t=100)
# # ModelData.GetDataTimestep(t=100,varName='w')
# # ModelData.GetDataTimestep_diag(t=100)
# # ModelData.GetDataTimestep_diag(t=100,varName='refl10cm')

