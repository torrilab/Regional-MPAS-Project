#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

# ##############
# #Example Run
# ##############

# #MAIN DIRECTORIES
# def GetDirectories():
#     mainDirectory='/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
#     mainScratchDirectory='/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
#     scratchDirectory = os.path.join(mainScratchDirectory,"MPAS_Atmosphere_8.3.0")
    
#     mainCodeDirectory=os.path.join(mainDirectory,"Code/CodeFiles/")
#     codeDirectory=os.getcwd()
#     return mainDirectory,mainCodeDirectory,scratchDirectory,codeDirectory

# [mainDirectory,mainCodeDirectory,scratchDirectory,codeDirectory] = GetDirectories()

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
# # ModelData.GetDataTimestep(t=100)
# # ModelData.GetDataTimestep(t=100,varName='w')
# # ModelData.GetDataTimestep_diag(t=100)
# # ModelData.GetDataTimestep_diag(t=100,varName='refl10cm')


# In[ ]:


# ============================================================
# StructuredModelData_Class
# ============================================================

#Libraries
import os
from datetime import datetime, timedelta

import xarray as xr
import uxarray as ux

class StructuredModelData_Class:
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
         self.filePath, 
         self.Resolution, 
         self.tResolution] = self.GetDataFilePath()

        # Get diagnostic data
        self.filePath_diag = self.GetDataFilePath_diag()

        # Get timeStrings
        self.timeStrings = self.GetTimeStrings(self.SimulationTime,self.tResolution)

        # # Load Variable Names
        # self.dataVariables,self.dataVariables_diag = self.GetVariableNames()

        # Print summary
        self.Summary()

    # ============================================================
    # ========== Data Loading Functions ==========
    # ============================================================

    def GetDataFilePath(self):
        """Return directory paths and metadata based on simulation number."""
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                 self.case, "MPAS-Model_"+self.mpType)
        Resolution, tResolution= '20-1km', '15mins'

        filePath =  os.path.join(dataDirectory, "backup_RESTART2", "history_cartesian", "history.latlon.nc")
        return dataDirectory, filePath, Resolution, tResolution

    def GetDataFilePath_diag(self):
        """Return directory paths and metadata based on simulation number."""
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                 self.case, "MPAS-Model_"+self.mpType)
        Resolution, tResolution= '20-1km', '15mins'

        filePath_diag =  os.path.join(dataDirectory, "backup_RESTART2", "diag_cartesian", "diag.latlon.nc")

        return filePath_diag

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
        first_file = self.filePath
    
        with xr.open_dataset(first_file, engine="netcdf4", decode_times=False, chunks={}) as ds:
            dataVariables = list(ds.data_vars.keys())


        first_file_diag = self.filePath_diag
        with xr.open_dataset(first_file_diag, engine="netcdf4", decode_times=False, chunks={}) as ds:
            dataVariables_diag = list(ds.data_vars.keys())
        return dataVariables, dataVariables_diag
    
    # # ============================================================
    # # ========== On-demand Variable Access ==========
    # # ============================================================

    def GetData(self, t=None, varName=None):
        data = xr.open_dataset(self.filePath, engine="netcdf4", decode_times=False, chunks={})
        print(f"Opened data from {self.filePath}")

        if t is not None:
            data = data.isel(time=t)
            print(f"Getting time {self.timeStrings[t]}")
        if varName is not None:
            print(f"Getting variable {varName}")
            return data[varName]
        else: 
            return data

    def GetData_diag(self, t=None, varName=None):
        data = xr.open_dataset(self.filePath_diag, engine="netcdf4", decode_times=False, chunks={})
        print(f"Opened data from {self.filePath_diag}")

        if t is not None:
            data = data.isel(time=t)
            print(f"Getting time {self.timeStrings[t]}")
        if varName is not None:
            print(f"Getting variable {varName}")
            return data[varName]
        else: 
            return data
    
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
        print(f"   History File:  {self.filePath}")
        print(f"   Diagnostic File:  {self.filePath_diag}")
        print("=========================","\n")

# ##############
# #Example Run
# ##############

# #MAIN DIRECTORIES
# def GetDirectories():
#     mainDirectory='/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
#     mainScratchDirectory='/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
#     scratchDirectory = os.path.join(mainScratchDirectory,"MPAS_Atmosphere_8.3.0")
    
#     mainCodeDirectory=os.path.join(mainDirectory,"Code/CodeFiles/")
#     codeDirectory=os.getcwd()
#     return mainDirectory,mainCodeDirectory,scratchDirectory,codeDirectory

# [mainDirectory,mainCodeDirectory,scratchDirectory,codeDirectory] = GetDirectories()

# RunType = ("TRACER","MOIST","NSSL")
# SimulationTime = ("2022-06-30","2022-07-03")
# ModelData = StructuredModelData_Class(mainDirectory, scratchDirectory, RunType, SimulationTime)

# # ################
# # #Example Usage
# # ################
# # [dataVariables, dataVariables_diag] = ModelData.GetVariableNames()
# # ModelData.GetData()
# # ModelData.GetData(t=100)
# # ModelData.GetData(t=100,varName='w')
# # ModelData.GetData_diag()
# # ModelData.GetData_diag(t=100)
# # ModelData.GetData_diag(t=100,varName='refl10cm')

