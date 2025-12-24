#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ============================================================
# StructuredModelData_Class 
# (for MPAS Cartesian lat-lon data, converted from original unstructured data using convert_mpas code)
# ============================================================

import os
import re
import glob
from datetime import datetime, timedelta
import xarray as xr

class StructuredModelData_Class():
    def __init__(self, mainDirectory, scratchDirectory, RunType, printSummary=True):#, SimulationTime):
        # DIRECTORIES
        self.mainDirectory = mainDirectory
        self.scratchDirectory = scratchDirectory

        # SIMULATION INFO
        (self.region, self.case, self.mpType, self.spinup_hours) = RunType

        # === DATA DIRECTORIES ===
        (self.dataDirectory,
         self.fileList,
         self.Resolution,
         self.tResolution) = self.GetDataDirectories()

        self.fileList_diag = self.GetDataDirectories_diag()

        # SIMULATION INFO
        # self.SimulationTime = SimulationTime
        self.SimulationTime = self.GetSimulationTime(self.fileList)

        # === STATIC DATA ===
        (self.staticData,
         self.staticDataFilePath,
         self.staticVariables) = self.GetStaticData(self.dataDirectory)

        # === INIT DATA ===
        (self.initData, 
         _, 
         self.initVariables) = self.GetInitData(self.dataDirectory)

        # === TIME STRINGS ===
        self.timeStrings, self.Ntime = self.GetTimeStrings(self.SimulationTime, self.tResolution)
        self.simulationDates = sorted(set(t.split("_")[0] for t in self.timeStrings))

        # === COORDINATES ===
        self.GetCoordinates()
        (self.z_levels_filePath,self.zf,self.zc) = self.GetZLevels()

        # === COORDINATES ===
        self.unitsDictionary = self.GetUnits(self.GetDataTimestep(t=0))
        self.unitsDictionary_diag = self.GetUnits(self.GetDataTimestep_diag(t=0))
        self.unitsDictionary_static = self.GetUnits(self.staticData)

        # === SUMMARY ===
        if printSummary:
            self.Summary()

    # ============================================================
    # Data Loading and Paths
    # ============================================================

    def GetSimulationTime(self,fileList):
        """
        Extracts simulation start and end dates (YYYY-MM-DD)
        """
    
        dates = []
    
        for path in fileList:
            filename = os.path.basename(path)
    
            # Extract just the YYYY-MM-DD part
            match = re.search(r"\d{4}-\d{2}-\d{2}", filename)
            if match:
                dates.append(match.group())
    
        if len(dates) == 0:
            raise ValueError("No dates found in fileList.")
    
        # Convert to datetime.date
        date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
    
        # Get min and max
        startDate = min(date_objs)
        endDate   = max(date_objs)
    
        return (
            startDate.strftime("%Y-%m-%d"),
            endDate.strftime("%Y-%m-%d")
        )

    def GetDataDirectories(self):
        """Return main directory and list of history files."""
        dataDirectory = os.path.join(self.scratchDirectory, self.region, 
                                     self.case, f"MPAS-Model_{self.mpType}", f"model_run_spinup{self.spinup_hours}hrs")
        Resolution, tResolution = '20-1km', '15mins'

        filePattern = os.path.join(dataDirectory,
                                   "history_cartesian", "history.*.latlon.nc")
        fileList = sorted(glob.glob(filePattern))

        return dataDirectory, fileList, Resolution, tResolution

    def GetDataDirectories_diag(self):
        filePattern = os.path.join(self.dataDirectory,
                                   "diag_cartesian", "diag.*.latlon.nc")
        return sorted(glob.glob(filePattern))
        
    def GetStaticData(self, dataDirectory):
        """Open static data using xarray."""
        filePattern = os.path.join(dataDirectory,
                                   "history_cartesian", "static_data", f"{self.region}_*.static.latlon.nc")
        staticDataFilePath = glob.glob(filePattern)[0]
        staticData = xr.open_dataset(staticDataFilePath, engine="netcdf4")
        staticVariables = list(staticData.data_vars)
        return staticData, staticDataFilePath, staticVariables

    def GetInitData(self, dataDirectory):
        """Open static data using xarray."""
        filePattern = os.path.join(dataDirectory,
                                   "history_cartesian", "init_data", f"{self.region}_*.init.latlon.nc")
        staticDataFilePath = glob.glob(filePattern)[0]
        initData = xr.open_dataset(staticDataFilePath, engine="netcdf4")
        initVariables = list(initData.data_vars)
        return initData, staticDataFilePath, initVariables

    def GetVariableNames(self): 
        first_file = self.fileList[0]
        with xr.open_dataset(first_file, engine="netcdf4") as ds:
            dataVariables = list(ds.data_vars.keys())

        first_file = self.fileList_diag[0]
        with xr.open_dataset(first_file, engine="netcdf4") as ds:
            dataVariables_diag = list(ds.data_vars.keys())
            
        return dataVariables, dataVariables_diag

    # ============================================================
    # Coordinates
    # ============================================================
    def GetCoordinates(self):
        first_file = self.fileList[0]
        with xr.open_dataset(first_file, engine="netcdf4") as ds:
            self.latitude= ds['latitude'].data
            self.longitude = ds['longitude'].data
            self.nVertLevels = ds['nVertLevels'].data
            self.nVertLevelsP1 = ds['nVertLevelsP1'].data

            # self.Nlon #not sure if these vary for each variable
            # self.Nlat
            self.Nzc=len(self.nVertLevels)
            self.Nzf=len(self.nVertLevelsP1)
            
        self.coordinateList = ["latitude", "longitude", "nVertLevels", "nVertLevelsP1"]
        
    def GetZLevels(self):
        z_levels_filePath = "/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project/MPAS_Atmosphere_8.3.1/TRACER/WET/MPAS-Model_8.3.1_56nz/zeta_30km_57levels.txt"
        zf = np.loadtxt(z_levels_filePath)/1e3
        zc = 0.5 * (zf[:-1] + zf[1:])
        return z_levels_filePath,zf,zc

    def GetZGrids(self):
        zGrid_f = self.initData.zgrid
        zGrid_c = 0.5 * (
            zGrid_f.isel(nVertLevelsP1=slice(0, -1)) +
            zGrid_f.isel(nVertLevelsP1=slice(1, None))
        ); zGrid_c = zGrid_c.rename({"nVertLevelsP1": "nVertLevels"})
    
        return zGrid_f,zGrid_c
    
    def GetZTarget(self, zGrid_f,zGrid_c):
        """
        Return target vertical coordinates for both interface and center grids.
        """
    
        # -------------------------------
        # Interface grid (nVertLevelsP1)
        # -------------------------------
        zGrid0_f = zGrid_f.isel(nVertLevelsP1=0)
    
        idx_f = zGrid0_f.argmin(dim=("latitude", "longitude"))
    
        zTarget_f = zGrid_f.isel(
            latitude=idx_f["latitude"],
            longitude=idx_f["longitude"]
        ).data
    
        # -------------------------------
        # Center grid (nVertLevels)
        # -------------------------------
        zGrid0_c = zGrid_c.isel(nVertLevels=0)
    
        idx_c = zGrid0_c.argmin(dim=("latitude", "longitude"))
    
        zTarget_c = zGrid_c.isel(
            latitude=idx_c["latitude"],
            longitude=idx_c["longitude"]
        ).data
    
        return zTarget_f, zTarget_c
        
    def InterpolateVertical(self,variableSubset,zGrid_f,zGrid_c,zTarget_f,zTarget_c):
        """
        Column-wise vertical interpolation to fixed height levels.
        """
    
        # def interpColumn(varCol, zCol, zTarget):
        #     valid = np.isfinite(varCol) & np.isfinite(zCol)
        #     if valid.sum() < 2:
        #         return np.full(len(zTarget), np.nan)
    
        #     return np.interp(
        #         zTarget,
        #         zCol[valid],
        #         varCol[valid],
        #         left=np.nan,
        #         right=np.nan
        #     )

        def interpColumn(varCol, zCol, zTarget):
            return np.interp(
                zTarget,
                zCol,
                varCol,
                left=np.nan,
                right=np.nan
            )

        if "nVertLevelsP1" in variableSubset.dims:
            zGrid = zGrid_f
            zDim = "nVertLevelsP1"
            zTarget = zTarget_f
        elif "nVertLevels" in variableSubset.dims:
            zGrid = zGrid_c
            zDim = "nVertLevels"
            zTarget = zTarget_c
            
    
        varInterp = xr.apply_ufunc(
            interpColumn,
            variableSubset,
            zGrid,
            input_core_dims=[[zDim], [zDim]],
            output_core_dims=[["z"]],
            vectorize=True,
            kwargs={"zTarget": zTarget},
            output_dtypes=[variableSubset.dtype],
        )
    
        varInterp = varInterp.assign_coords(
            z=("z", zTarget),
            latitude=variableSubset.latitude,
            longitude=variableSubset.longitude,
        )
    
        varInterp.name = variableSubset.name
        varInterp = varInterp.rename({"z": zDim})
        return varInterp
        
    def GetUnits(self, data):
        """
        Return a dictionary {varName: units} for all variables in an xarray Dataset.
        """
        unitsDictionary = {}
        for var in data.data_vars:
            attrs = data[var].attrs
            unitsDictionary[var] = attrs.get("units", "—")
        return unitsDictionary

    def GetUnits_Specific(self, varName):
        """
        Return the units string for a specific variable name.
        """
        # If variable name includes '+', use the first component
        if "+" in varName:
            varName = varName.split("+")[0].strip()
        
        # Search through the available unit dictionaries
        for d in (self.unitsDictionary,
                  self.unitsDictionary_diag,
                  self.unitsDictionary_static):
            if varName in d:
                return d[varName]
        # Not found
        return None


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

        # Filter only those with matching files
        available_times = []
        available_files = []
        for time_str in times:
            # construct search pattern
            pattern = f"history.{time_str}.latlon.nc"
            matches = [f for f in self.fileList if pattern in f]
            if matches:
                available_times.append(time_str)
                available_files.append(matches[0])
    
        print(f"Found {len(available_files)}/{len(times)} files matching expected times.")
        return available_times, len(available_times)

    # ============================================================
    # Data Access
    # ============================================================

    def GetDataTimestep(self, t, varName=None, printout=True):
        """Load one timestep (index or string)."""
        if isinstance(t, int):
            filePath = self.fileList[t]
        elif isinstance(t, str):
            fileIndex = self.timeStrings.index(t)
            filePath = self.fileList[fileIndex]
        else:
            raise ValueError("t must be int (index) or str (time string).")

        data = xr.open_dataset(filePath, engine="netcdf4", decode_times=False)

        if printout==True:
            print(f"Opened history file: {filePath}")

        if varName:
            return data[varName].isel(Time=0)
        else:
            return data.isel(Time=0)

    def GetDataTimestep_diag(self, t, varName=None, printout=True):
        if isinstance(t, int):
            filePath = self.fileList_diag[t]
        elif isinstance(t, str):
            fileIndex = self.timeStrings.index(t)
            filePath = self.fileList_diag[fileIndex]
        else:
            raise ValueError("t must be int (index) or str (time string).")

        data = xr.open_dataset(filePath, engine="netcdf4", decode_times=False)

        if printout==True:
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
## def GetSimulationTime(RunType):
##     if (RunType[0] == "TRACER") and (RunType[1] == "MOIST"):
##         SimulationTime = ("2022-06-30","2022-07-03")
##     elif (RunType[0] == "TRACER") and (RunType[1] == "DRY"):
##         SimulationTime = ("2022-06-08","2022-06-11")
##     return SimulationTime

# mainDirectory='/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
# mainScratchDirectory='/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
# scratchDirectory = os.path.join(mainScratchDirectory,"MPAS_Atmosphere_8.3.0")

# RunType = ("TRACER","MOIST","NSSL","24")
# SimulationTime = GetSimulationTime(RunType)
# ModelData = StructuredModelData_Class(mainDirectory, scratchDirectory, RunType)#, SimulationTime)

# ################
# #Example Usage
# ################
# [dataVariables, dataVariables_diag] = ModelData.GetVariableNames()
# ModelData.GetDataTimestep(t=100)
# # ModelData.GetDataTimestep(t=100,varName='w')
# ModelData.GetDataTimestep_diag(t=100)
# # ModelData.GetDataTimestep_diag(t=100,varName='refl10cm')


# In[1]:


# ============================================================
# DataOperator_Class
# ============================================================

import math
import xarray as xr
import numpy as np

class DataOperator_Class:

    @staticmethod
    def LatLonBoundingBox_Center(region="TRACER"): 
        if region == "TRACER":
            (latCenter, lonCenter) = 29.67, -95.059
        elif region == "PRECIP":
            (latCenter, lonCenter) = 24.82, 120.91
        elif region == "Hawaii":
            (latCenter, lonCenter) = 21.133, -157.180 
        return latCenter,lonCenter

    @staticmethod
    def LatLonBoundingBox_Calculation(latCenter, lonCenter, radius_km=500): 
        # Earth radius in km
        R = 6371.0
    
        # Convert degrees to radians
        latRadians = math.radians(latCenter)
    
        # Calculate degree offsets
        dLat = (radius_km / R) * (180.0 / math.pi)
        dLon = (radius_km / (R * math.cos(latRadians))) * (180.0 / math.pi)
    
        # Bounding box
        latMin = latCenter - dLat
        latMax = latCenter + dLat
        lonMin = lonCenter - dLon
        lonMax = lonCenter + dLon
    
        latBounds = (latMin, latMax)
        lonBounds = (lonMin, lonMax)
        return latBounds, lonBounds

    @staticmethod
    def LatLonBoundingBox_Subset(data, latBounds, lonBounds): 
        """
        Subset a structured (lat-lon) xarray DataArray or Dataset
        to a given latitude/longitude bounding box.
        """
        # Determine coordinate names (support latitude/lat, longitude/lon)
        lat_name = "latitude" #if "latitude" in data.coords else "lat"
        lon_name = "longitude" #if "longitude" in data.coords else "lon"
    
        # Handle reversed latitude (if decreasing)
        lat_vals = data[lat_name].values
        if lat_vals[0] > lat_vals[-1]:
            lat_slice = slice(latBounds[1], latBounds[0])
        else:
            lat_slice = slice(latBounds[0], latBounds[1])
    
        lon_slice = slice(lonBounds[0], lonBounds[1])
    
        # Perform subset
        dataSubset = data.sel({lat_name: lat_slice, lon_name: lon_slice})
    
        # Extract matching lat/lon arrays
        lat = dataSubset[lat_name].values
        lon = dataSubset[lon_name].values
    
        # print(f"Subset region: lat={latBounds}, lon={lonBounds}")
        # print(f"Subset shape: {dataSubset[lat_name].shape} × {variableSubset[lon_name].shape}")
    
        return dataSubset, lat, lon

    @staticmethod
    def GetData_Variable(ModelData, data, data_diag, data_static, varName):
        if varName in ModelData.unitsDictionary:
            return data[varName]
        elif varName in ModelData.unitsDictionary_diag:
            return data_diag[varName]
        elif varName == "greenfrac":
            return data_static[varName].isel(nMonths=6)

    @staticmethod
    def GetVariable_Subset(ModelData, data, data_diag, data_static, varName):  
        variable = DataOperator_Class.GetData_Variable(ModelData, data, data_diag, data_static, varName)
        [latCenter,lonCenter] = DataOperator_Class.LatLonBoundingBox_Center(region=ModelData.region)
        [latBounds, lonBounds] = DataOperator_Class.LatLonBoundingBox_Calculation(latCenter, lonCenter, radius_km=500)
        variableSubset, lat, lon = DataOperator_Class.LatLonBoundingBox_Subset(variable,latBounds, lonBounds)
    
        # Lon, Lat = np.meshgrid(lon, lat) #not actually needed to plot
        return variableSubset, lat, lon

    @staticmethod
    def GetVariable_Subset2(ModelData, variable):
        [latCenter,lonCenter] = DataOperator_Class.LatLonBoundingBox_Center(region=ModelData.region)
        [latBounds, lonBounds] = DataOperator_Class.LatLonBoundingBox_Calculation(latCenter, lonCenter, radius_km=500)
        variableSubset, lat, lon = DataOperator_Class.LatLonBoundingBox_Subset(variable,latBounds, lonBounds)

        return variableSubset, lat, lon

    @staticmethod
    def GetData_Subset(ModelData,t):  
        data = ModelData.GetDataTimestep(t,printout=False)
        data_diag = ModelData.GetDataTimestep_diag(t,printout=False)
    
        [latCenter,lonCenter] = DataOperator_Class.LatLonBoundingBox_Center(region=ModelData.region)
        [latBounds, lonBounds] = DataOperator_Class.LatLonBoundingBox_Calculation(latCenter, lonCenter, radius_km=500)
        
        dataSubset, lat, lon = DataOperator_Class.LatLonBoundingBox_Subset(data,latBounds, lonBounds)
        dataSubset_diag, _, _ = DataOperator_Class.LatLonBoundingBox_Subset(data_diag,latBounds, lonBounds)
        dataSubset_static, _, _ = DataOperator_Class.LatLonBoundingBox_Subset(ModelData.staticData,latBounds, lonBounds)

        [zGrid_f,zGrid_c] = ModelData.GetZGrids()
        zGrid_f, _, _ = DataOperator_Class.LatLonBoundingBox_Subset(zGrid_f,latBounds, lonBounds)
        zGrid_c, _, _ = DataOperator_Class.LatLonBoundingBox_Subset(zGrid_c,latBounds, lonBounds)
    
        return dataSubset,dataSubset_diag,dataSubset_static, lat,lon,zGrid_f,zGrid_c, data,data_diag

    @staticmethod
    def GetOutputFilePath(ModelData, DirectoryManager, outputDirectory, fileName):
        folderName = f"{ModelData.region}_{ModelData.case}_{ModelData.mpType}_{ModelData.spinup_hours}hrs"    
        filePath = DirectoryManager.GetOutputFile(outputDirectory, folderName, fileName)
        return filePath


# In[1]:


# # ============================================================
# # UnstructuredModelData_Class
# # ============================================================

# #Libraries
# import os
# import glob
# from datetime import datetime, timedelta

# import xarray as xr
# import uxarray as ux

# class UnstructuredModelData_Class:
#     def __init__(self, mainDirectory, scratchDirectory, RunType, SimulationTime):
#         #DIRECTORIES
#         self.mainDirectory = mainDirectory
#         self.scratchDirectory = scratchDirectory

#         #SIMULATION INFO
#         self.region, self.case, self.mpType = RunType
#         self.SimulationTime = SimulationTime
        

#         #GET DATA
#         # Initialize directories and metadata
#         [self.dataDirectory, 
#          self.fileList, 
#          self.Resolution, 
#          self.tResolution] = self.GetDataDirectories()

#         # Get diagnostic data
#         self.fileList_diag = self.GetDataDirectories_diag()

#         # Get Grid and Static Data
#         self.gridData = self.GetGridData(self.dataDirectory)
#         [self.staticData, self.staticDataFilePath, self.staticVariables] = self.GetStaticData(self.dataDirectory)

#         # Get timeStrings
#         self.timeStrings = self.GetTimeStrings(self.SimulationTime,self.tResolution)

#         # # Load Variable Names
#         # self.dataVariables,self.dataVariables_diag = self.GetVariableNames()

#         # Load Coordinates
#         self.GetCoordinates()

#         # Print summary
#         self.Summary()

#     # ============================================================
#     # ========== Data Loading Functions ==========
#     # ============================================================

#     def GetDataDirectories(self):
#         """Return directory paths and metadata based on simulation number."""
#         dataDirectory = os.path.join(self.scratchDirectory, self.region, 
#                                  self.case, "MPAS-Model_"+self.mpType)
#         Resolution, tResolution= '20-1km', '15mins'

#         filePattern =  os.path.join(dataDirectory, "backup_20-1km_56nz", "history.*.nc")
#         fileList = sorted(glob.glob(filePattern))

#         return dataDirectory, fileList, Resolution, tResolution

#     def GetDataDirectories_diag(self):
#         """Return directory paths and metadata based on simulation number."""
#         dataDirectory = os.path.join(self.scratchDirectory, self.region, 
#                                  self.case, "MPAS-Model_"+self.mpType)
#         Resolution, tResolution= '20-1km', '15mins'

#         filePattern =  os.path.join(dataDirectory, "backup_20-1km_56nz", "diag.*.nc")
#         fileList_diag = sorted(glob.glob(filePattern))

#         return fileList_diag

#     def GetGridData(self, dataDirectory):
#         filePattern = os.path.join(dataDirectory,"*.static.nc")
#         staticDataFilePath = glob.glob(filePattern)[0]
#         gridData = ux.open_grid(staticDataFilePath, use_dual=True)
#         return gridData

#     def GetStaticData(self, dataDirectory):
#         filePattern = os.path.join(dataDirectory,"*.static.nc")
#         staticDataFilePath = glob.glob(filePattern)[0]
#         staticData = ux.open_mfdataset(grid_filename_or_obj=staticDataFilePath,
#                                  paths=[staticDataFilePath], parallel=True)
#         staticVariables = list(staticData.data_vars)
#         return staticData, staticDataFilePath, staticVariables

#     def GetTimeStrings(self, SimulationTime,tResolution):
#         fmt_date = "%Y-%m-%d"
#         start = datetime.strptime(SimulationTime[0], fmt_date)
#         end = datetime.strptime(SimulationTime[1], fmt_date)
    
#         # Determine time delta
#         if "min" in tResolution:
#             minutes = int(tResolution.replace("mins", "").replace("min", ""))
#             delta = timedelta(minutes=minutes)
#         elif "hr" in tResolution:
#             hours = int(tResolution.replace("hrs", "").replace("hr", ""))
#             delta = timedelta(hours=hours)
#         else:
#             raise ValueError(f"Unsupported tResolution format: {tResolution}")
    
#         # Generate sequence of times
#         fmt_out = "%Y-%m-%d_%H.%M.%S"
#         times = []
#         t = start
#         while t <= end:
#             times.append(t.strftime(fmt_out))
#             t += delta
    
#         return times

#     def GetVariableNames(self):
#         first_file = self.fileList[0]
    
#         with xr.open_dataset(first_file, engine="netcdf4", decode_times=False, chunks={}) as ds:
#             dataVariables = list(ds.data_vars.keys())


#         first_file_diag = self.fileList_diag[0]
#         with xr.open_dataset(first_file_diag, engine="netcdf4", decode_times=False, chunks={}) as ds:
#             dataVariables_diag = list(ds.data_vars.keys())
#         return dataVariables, dataVariables_diag

#     # ============================================================
#     # === Coordinates ========================================
#     # ============================================================

#     def GetCoordinates(self):
#         """Calculate basic model coordinates."""
#         self.NTime = len(self.timeStrings)
#         print(f"Calculated coordinate: NTime = {self.NTime}")
    
#     # # ============================================================
#     # # ========== On-demand Variable Access ==========
#     # # ============================================================

#     def LoadCombinedData(self): #can take a while, better to load timestep by timestep
#         data = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
#                                  paths=self.fileList, parallel=True)
#         print(f"Opened combined data file for all times")
#         return data

#     def LoadCombinedData_diag(self): #can take a while, better to load timestep by timestep
#         data = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
#                                  paths=self.fileList_diag, parallel=True)
#         print(f"Opened combined data file for all times")
#         return data

#     def GetDataTimestep(self, t, varName=None):
#         if isinstance(t,int):
#             filePath = self.fileList[t]
#         elif isinstance(t,str):
#             fileIndex = self.timeStrings.index(target)
#             filePath = self.fileList[fileIndex]
#         #loading data
#         data = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
#                                paths=[filePath])
#         print(f"Opened data from {filePath}")

#         if varName is not None:
#             return data[varName]
#         else: 
#             return data

#     def GetDataTimestep_diag(self, t, varName=None):
#         if isinstance(t,int):
#             filePath = self.fileList_diag[t]
#         elif isinstance(t,str):
#             fileIndex = self.timeStrings.index(target)
#             filePath = self.fileList_diag[fileIndex]
#         #loading data
#         data_diag = ux.open_mfdataset(grid_filename_or_obj=self.staticDataFilePath,
#                                paths=[filePath])
#         print(f"Opened data from {filePath}")

#         if varName is not None:
#             return data_diag[varName]
#         else: 
#             return data_diag
    
#     # ============================================================
#     # === Information ========================================
#     # ============================================================
    
#     def Summary(self):
#         """Print a clear summary of the MPAS unstructured model configuration."""
#         print("\n=== MPAS Unstructured Model Data Summary ===")
#         print(f" Region:         {self.region}")
#         print(f" Case:           {self.case}")
#         print(f" Microphysics:   {self.mpType}")
#         print(f" Resolution:     {self.Resolution}")
#         print(f" Time Step:      {self.tResolution}")
#         print(f" Time Range:     {self.SimulationTime[0]} to {self.SimulationTime[1]}")
#         print(f" # Time Steps:   {len(self.timeStrings)}")
#         print(f" # History Files:{len(self.fileList)}")
    
#         print(f"\nData Directory:")
#         print(f"   {self.dataDirectory}")
#         print(f"   Static File:  {os.path.basename(self.staticDataFilePath)}")
#         print("=========================","\n")

# # # ##############
# # # #Example Run
# # # ##############

# # #MAIN DIRECTORIES
# # mainDirectory='/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
# # mainScratchDirectory='/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
# # scratchDirectory = os.path.join(mainScratchDirectory,"MPAS_Atmosphere_8.3.0")

# # RunType = ("TRACER","MOIST","NSSL")
# # SimulationTime = ("2022-06-30","2022-07-03")
# # ModelData = UnstructuredModelData_Class(mainDirectory, scratchDirectory, RunType, SimulationTime)

# # # ################
# # # #Example Usage
# # # ################
# # # [dataVariables, dataVariables_diag] = ModelData.GetVariableNames()
# # # # ModelData.LoadCombinedData()
# # # # ModelData.LoadCombinedData_diag()
# # # ModelData.GetDataTimestep(t=100)
# # # ModelData.GetDataTimestep(t=100,varName='w')
# # # ModelData.GetDataTimestep_diag(t=100)
# # # ModelData.GetDataTimestep_diag(t=100,varName='refl10cm')

