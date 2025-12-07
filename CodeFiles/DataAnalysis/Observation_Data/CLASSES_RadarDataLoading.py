#!/usr/bin/env python
# coding: utf-8

# In[2]:


# ============================================================
# RadarData_MRMS_Class
# ============================================================

#libraries 
import os,re

import xarray as xr
from datetime import datetime 
import pandas as pd
import numpy as np


class RadarData_MRMS_Class:
    def __init__(self, ModelData, fileDirectory):
        #data file reading
        self.fileDirectory = fileDirectory
        self.filePathList,self.fileList = self.GetFilePathList()

    # ------------------------------------------------------------
    # Data Loading Functions
    # ------------------------------------------------------------
    # Internal Use
    def ExtractDateTimeFromFileName(self, path):
        """
        Extract datetime from MRMS-style filename:
        e.g., MRMSReflectivity_CONUS_TRACER_20220702-124438.nc
        """
        fname = os.path.basename(path)
        m = re.search(r"_(\d{8})-(\d{6})\.nc$", fname)
        if m:
            date_str, time_str = m.groups()
            return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        else:
            return datetime.min  # fallback if no match
    
    
    def GetFilePathList(self):
        """Return sorted list of MRMS NetCDF file paths and names."""
        filePathList = [
            os.path.join(self.fileDirectory, f)
            for f in os.listdir(self.fileDirectory)
            if f.endswith(".nc")
        ]
    
        # Sort chronologically using extracted datetimes
        filePathList = sorted(filePathList, key=self.ExtractDateTimeFromFileName)
        fileList = [os.path.basename(p) for p in filePathList]
    
        return filePathList, fileList
    
    # External Use
    def LoadClosestMRMSFile(self, target_time):
        """
        Find and load the MRMS NetCDF file closest to the given time.
        """
        target_time = pd.to_datetime(target_time)
    
        # Build sorted list of files
        filePathList, fileList = self.GetFilePathList()
    
        # Extract datetimes from filenames
        file_times = [
            self.ExtractDateTimeFromFileName(path)
            for path in filePathList
        ]
    
        # Convert to numpy datetime64 for proper subtraction
        file_times_np = np.array(file_times, dtype="datetime64[ns]")
        target_np = np.datetime64(target_time)
    
        # Find index of closest timestamp
        deltas = np.abs(file_times_np - target_np)
        nearest_index = deltas.argmin()
    
        nearest_time = file_times[nearest_index]
        nearest_filePath = filePathList[nearest_index]
    
        print(f"Target time:  {target_time}")
        print(f"Closest file: {os.path.basename(nearest_filePath)} ({nearest_time})")
    
        # Load dataset
        radarData = xr.open_dataset(nearest_filePath)
    
        # Extract variable automatically
        varname = list(radarData.data_vars.keys())[0]
        radarData_t = radarData[varname]
    
        return radarData_t, nearest_filePath

    # ============================================================
    # External Static Functions for Loading 3D MRMS Data
    # ============================================================

    @staticmethod
    def ConvertTimeStringtoDateTime(timeString):
        """
        Converts a time string like '2022-06-30_00.00.00' to a datetime object.
        """
        return datetime.strptime(timeString, '%Y-%m-%d_%H.%M.%S')

    @staticmethod
    def FixLatLon_RadarData(radarData):        
        radarData = radarData.isel(latitude=slice(None, None, -1))
    
        radarData = radarData.assign_coords(
            longitude=((radarData.longitude + 180) % 360) - 180
        )
        return radarData

    @staticmethod
    def ReturnLatLon_RadarData(radarData):
        # Fix latitude order
        radarData_fixed = radarData.isel(latitude=slice(None, None, -1))
    
        # Fix longitude convention
        radarData_fixed = radarData_fixed.assign_coords(
            longitude=radarData.longitude+360
        )
    
        return radarData_fixed

    @staticmethod
    def InterpolateRadarData(radarData,modelData):
        radarData = RadarData_MRMS_Class.FixLatLon_RadarData(radarData)
        
        radarData_interp = radarData.interp(
            latitude=modelData.latitude,
            longitude=modelData.longitude,
            method="linear"
        )
        return radarData_interp

    @staticmethod
    def GetData(DirectoryManager,ModelData, t, RadarObservationLevels_string):
        timeString = ModelData.timeStrings[t]
        timeString_datetime = RadarData_MRMS_Class.ConvertTimeStringtoDateTime(timeString)

        #date string

        #LOADING RADAR CLASS dateString
        if int(ModelData.spinup_hours) <= 0 and ModelData.region == "TRACER":
            if ModelData.case == "WET":
                dateString = '2022-06-30_2022-07-03'
            elif ModelData.case == "DIURNAL":
                dateString = '2022-06-21_2022-06-24'
        else:
            dateString = f"{ModelData.simulationDates[0]}_{ModelData.simulationDates[-1]}"

    
        #Loading Model Data
        modelRadarData_NSSL = ModelData.GetDataTimestep_diag(t)["refl10cm_1km"]
        
        #Loading Observational Radar
        RadarData_MRMS = RadarData_MRMS_Class(ModelData,
                                              fileDirectory=os.path.join(DirectoryManager.dataDirectory,
                                                                         "Observation_Data/TRACER/MRMS_RadarData",
                                                                         dateString,
                                                                         f"MergedReflectivityQC_{RadarObservationLevels_string}"))
        radarData, nearestFilePath = RadarData_MRMS.LoadClosestMRMSFile(target_time=timeString_datetime)
        radarData=radarData.isel(time=0)
        radarData_interp = RadarData_MRMS_Class.InterpolateRadarData(radarData=radarData, modelData=modelRadarData_NSSL)
    
        return radarData_interp

    @staticmethod
    def GetData_AllZLevels(DirectoryManager,ModelData, t, RadarObservationLevels):
    
        # Format MRMS folder strings (e.g., "0000.50", "0001.00")
        RadarObservationLevels_strings = [
            f"0{val:04.2f}" if val < 10 else f"{val:05.2f}"
            for val in RadarObservationLevels
        ]
    
        radarList = []
    
        for k, levelStr in enumerate(RadarObservationLevels_strings):
    
            # Get interpolated (lat,lon) DataArray
            radarData_interp = RadarData_MRMS_Class.GetData(DirectoryManager,ModelData, t, levelStr)
    
            # Store it
            radarList.append(radarData_interp)
    
        # Stack into a single 3D DataArray with "height" dimension
        radarData = xr.concat(radarList, dim="heightAboveSea")
        radarData = radarData.rename(f"MergedReflectivityQC_{RadarObservationLevels_strings[0]}-{RadarObservationLevels_strings[-1]}")
        return radarData


# #Example Loading:
# if int(ModelData_NSSL.spinup_hours) <= 0 and ModelData_NSSL.region == "TRACER":
#     if ModelData_NSSL.case == "WET":
#         dateString = '2022-06-30_2022-07-03'
#     elif ModelData_NSSL.case == "DIURNAL":
#         dateString = '2022-06-21_2022-06-24'
# else:
#     dateString = f"{ModelData_NSSL.simulationDates[0]}_{ModelData_NSSL.simulationDates[-1]}"

# RadarData_MRMS = RadarData_MRMS_Class(ModelData_NSSL,
#                                       fileDirectory=os.path.join(DirectoryManager.dataDirectory,
#                                                                  "Observation_Data/TRACER/MRMS_RadarData",
#                                                                  dateString,
#                                                                  "MergedReflectivityQC_01.00"))


# In[1]:


# ============================================================
# RadarData_PRECIP_Class
# ============================================================

#libraries 
import os,re

import xarray as xr
from datetime import datetime 
import pandas as pd
import numpy as np
import pickle

# from scipy.spatial import Delaunay
# from scipy.interpolate import LinearNDInterpolator
import xesmf as xe


class RadarData_PRECIP_Class:
    def __init__(self, ModelData, folderDirectory):
        #data file reading
        self.folderDirectory = folderDirectory
        self.longitude,self.latitude,self.z_heights = self.GetCoordinates(ModelData)

    # ------------------------------------------------------------
    # Data Loading Functions
    # ------------------------------------------------------------
    # Internal Use
    def ExtractDateTimeFromFileName(self, path):
        """
        Extract datetime from MRMS-style filename:
        e.g., MRMSReflectivity_CONUS_TRACER_20220702-124438.nc
        """
        fname = os.path.basename(path)
        m = re.search(r"_(\d{8})_(\d{6})\.nc$", fname)
        if m:
            date_str, time_str = m.groups()
            return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        else:
            return datetime.min  # fallback if no match

    
    @staticmethod
    def ConvertTimeStringtoDateTime(timeString):
        """
        Converts a time string like '2022-06-30_00.00.00' to a datetime object.
        """
        return datetime.strptime(timeString, '%Y-%m-%d_%H.%M.%S')
    
    def GetFilePathList(self,yearmonthday):
        """Return sorted list of MRMS NetCDF file paths and names."""
        fileDirectory = os.path.join(self.folderDirectory,yearmonthday)
        filePathList = [
            os.path.join(fileDirectory, f)
            for f in os.listdir(fileDirectory)
            if f.endswith(".nc") and f.startswith("ncf")
        ]
    
        # Sort chronologically using extracted datetimes
        filePathList = sorted(filePathList, key=self.ExtractDateTimeFromFileName)
        fileList = [os.path.basename(p) for p in filePathList]
    
        return filePathList, fileList
    
    def LoadClosestMRMSFile(self, timeString):
        """
        Find and load the MRMS NetCDF file closest to the given time.
        """

        target_time = self.ConvertTimeStringtoDateTime(timeString)
        
        yearmonthday = target_time.strftime("%Y%m%d")
        target_time = pd.to_datetime(target_time)
    
        # Build sorted list of files
        filePathList, fileList = self.GetFilePathList(yearmonthday)
    
        # Extract datetimes from filenames
        file_times = [
            self.ExtractDateTimeFromFileName(path)
            for path in filePathList
        ]
    
        # Convert to numpy datetime64 for proper subtraction
        file_times_np = np.array(file_times, dtype="datetime64[ns]")
        target_np = np.datetime64(target_time)
    
        # Find index of closest timestamp
        deltas = np.abs(file_times_np - target_np)
        nearest_index = deltas.argmin()
    
        nearest_time = file_times[nearest_index]
        nearest_filePath = filePathList[nearest_index]
    
        print(f"Target time:  {target_time}")
        print(f"Closest file: {os.path.basename(nearest_filePath)} ({nearest_time})")
    
        # Load dataset
        radarData = xr.open_dataset(nearest_filePath)
    
        # Extract variable automatically
        radarData_t = radarData["DBZ_F_L2"]
    
        return radarData_t, nearest_filePath

    def GetCoordinates(self,ModelData):
        timeString = ModelData.timeStrings[0]
        radarData_t,_ = self.LoadClosestMRMSFile(timeString)
        longitude = radarData_t.lon0.data
        latitude = radarData_t.lat0.data
        z_heights = radarData_t.z0.data
        return longitude,latitude,z_heights

    #============================================================
    # External Static Functions for Loading 3D MRMS Data
    #============================================================
        
    # def InterpolateRadarData(self, radarData_tz, ModelData,DirectoryManager):
    
    #     # --- Setup output folder ---
    #     codeType = os.path.join("DataAnalysis", "Observation_Data")
    #     dataType = "RadarData"
    #     outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
        
    #     interpPath = os.path.join(
    #         outputDirectory, 
    #         "RadarObservationMask",
    #         f"{ModelData.region}_{ModelData.case}_{ModelData.spinup_hours}hrs"
    #     )
    #     os.makedirs(interpPath, exist_ok=True)
    
    #     triPath = os.path.join(interpPath, "triangulation.pkl")
    
    #     # ============================================================
    #     # 1. Load OR Build triangulation based only on (lat0, lon0)
    #     # ============================================================
    #     lat_r = radarData_tz.lat0.values
    #     lon_r = radarData_tz.lon0.values
    #     pts_radar = np.column_stack((lat_r.ravel(), lon_r.ravel()))
    
    #     if os.path.exists(triPath):
    #         print(f"Loading cached triangulation: {triPath}")
    #         with open(triPath, "rb") as f:
    #             tri = pickle.load(f)
    #     else:
    #         print("Building triangulation (slow, one-time)...")
    #         tri = Delaunay(pts_radar)
    #         with open(triPath, "wb") as f:
    #             pickle.dump(tri, f)
    #         print(f"Saved triangulation to {triPath}")
    
    #     # ============================================================
    #     # 2. Build interpolator
    #     # ============================================================
    #     vals_radar = radarData_tz.values.ravel()
    #     interp_func = LinearNDInterpolator(tri, vals_radar) #Linear interpolation over 2D Delaunay triangles
    
    #     # ============================================================
    #     # 3. Interpolate onto model grid
    #     # ============================================================
    #     lat_m_1d = ModelData.latitude
    #     lon_m_1d = ModelData.longitude
    #     lon_m, lat_m = np.meshgrid(lon_m_1d, lat_m_1d)
    
    #     pts_model = np.column_stack((lat_m.ravel(), lon_m.ravel()))
    #     out_vals = interp_func(pts_model).reshape(lat_m.shape) 
    
    #     # Return DataArray
    #     return xr.DataArray(
    #         out_vals,
    #         dims=("y", "x"),
    #         coords={
    #             "y": lat_m_1d,
    #             "x": lon_m_1d,
    #             "latitude": (("y", "x"), lat_m),
    #             "longitude": (("y", "x"), lon_m),
    #         }
    #     )
    def InterpolateRadarData2D(self, radarData_xy, ModelData, DirectoryManager):
        """
        Interpolate a single-level 2D radar field (y, x) onto the MPAS latitude/longitude grid.
        radarData_xy must contain coords lat0(y,x) and lon0(y,x).
        """
    
        # ===============================
        # 1. Build output directory paths
        # ===============================
        codeType = os.path.join("DataAnalysis", "Observation_Data")
        dataType = "RadarData"
        outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
    
        interpPath = os.path.join(
            outputDirectory,
            "RadarObservationMask",
            f"{ModelData.region}_{ModelData.case}_{ModelData.spinup_hours}hrs"
        )
        os.makedirs(interpPath, exist_ok=True)
    
        weightPath = os.path.join(interpPath, "xesmf_weights_2D.nc")
    
        # ===============================
        # 2. Build INPUT grid (2D only)
        # ===============================
        ds_in = xr.Dataset(
            {
                "var": (("y", "x"), radarData_xy.values)
            },
            coords={
                "lat": (("y", "x"), radarData_xy.lat0.values),
                "lon": (("y", "x"), radarData_xy.lon0.values),
            }
        )
    
        # ===============================
        # 3. Build OUTPUT grid (MPAS lat/lon)
        # ===============================
        lat_m = ModelData.latitude
        lon_m = ModelData.longitude
        lat2d, lon2d = np.meshgrid(lat_m, lon_m, indexing="ij")
    
        ds_out = xr.Dataset(
            coords={
                "lat": (("y", "x"), lat2d),
                "lon": (("y", "x"), lon2d),
            }
        )
    
        # ===============================
        # 4. Create or reuse regridder
        # ===============================
        regridder = xe.Regridder(
            ds_in,
            ds_out,
            method="bilinear",
            filename=weightPath,
            reuse_weights=os.path.exists(weightPath),
            unmapped_to_nan=True
        )
    
        # ===============================
        # 5. Interpolate (2D only)
        # ===============================
        out = regridder(ds_in["var"])
    
        # ===============================
        # 6. Return 2D DataArray
        # ===============================
        return xr.DataArray(
            out.values,
            dims=("y", "x"),
            coords={
                "y": lat_m,
                "x": lon_m,
                "latitude": (("y", "x"), lat2d),
                "longitude": (("y", "x"), lon2d),
            }
        )

    
    def InterpolateRadarData3D(self, radarData_tz, ModelData, DirectoryManager):
    
        # ===============================
        # 1. Build output directory paths
        # ===============================
        codeType = os.path.join("DataAnalysis", "Observation_Data")
        dataType = "RadarData"
        outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
    
        interpPath = os.path.join(
            outputDirectory,
            "RadarObservationMask",
            f"{ModelData.region}_{ModelData.case}_{ModelData.spinup_hours}hrs"
        )
        os.makedirs(interpPath, exist_ok=True)
    
        weightPath = os.path.join(interpPath, "xesmf_weights.nc")
    
        # ===============================
        # 2. Build INPUT grid and data
        # radarData_tz is shape (z, y, x)
        # ===============================
        ds_in = xr.Dataset(
            {
                "var": (("z", "y", "x"), radarData_tz.values)
            },
            coords={
                "z": radarData_tz.z0.values if "z0" in radarData_tz.coords else np.arange(radarData_tz.shape[0]),
                "lat": (("y", "x"), radarData_tz.lat0.values),
                "lon": (("y", "x"), radarData_tz.lon0.values),
            }
        )
    
        # ===============================
        # 3. Build OUTPUT grid
        # ===============================
        lat_m = ModelData.latitude
        lon_m = ModelData.longitude
        lat2d, lon2d = np.meshgrid(lat_m, lon_m, indexing="ij")
    
        ds_out = xr.Dataset(
            coords={
                "lat": (("y", "x"), lat2d),
                "lon": (("y", "x"), lon2d),
            }
        )
    
        # ===============================
        # 4. Create or reuse regridder
        # ===============================
        regridder = xe.Regridder(
            ds_in, ds_out, method="bilinear",
            filename=weightPath,
            reuse_weights=os.path.exists(weightPath),
            unmapped_to_nan=True
        )
    
        # ===============================
        # 5. FULLY VECTORIZED regridding
        # xESMF handles the z dimension automatically
        # ===============================
        out = regridder(ds_in["var"])
    
        # ===============================
        # 6. Return 3D DataArray
        # ===============================
        return xr.DataArray(
            out.values,
            dims=("z", "y", "x"),
            coords={
                "z": ds_in.z,
                "y": lat_m,
                "x": lon_m,
                "latitude": (("y", "x"), lat2d),
                "longitude": (("y", "x"), lon2d),
            }
        )
        
    def GetData_AllZLevels(self, DirectoryManager, ModelData, t):
        timeString = ModelData.timeStrings[t]
        timeString_datetime = self.ConvertTimeStringtoDateTime(timeString)
    
        # Load model data
        modelRadarData_NSSL = ModelData.GetDataTimestep_diag(t)["refl10cm_1km"]
    
        # Load closest radar file for this time
        radarData, nearestFilePath = self.LoadClosestMRMSFile(timeString)
        radarData_t = radarData.isel(time=0)
        return radarData_t, nearestFilePath
    
    def GetData(self, DirectoryManager, ModelData, t, z_km=1):
        timeString = ModelData.timeStrings[t]
        timeString_datetime = self.ConvertTimeStringtoDateTime(timeString)
    
        # Load model data
        modelRadarData_NSSL = ModelData.GetDataTimestep_diag(t)["refl10cm_1km"]
    
        # Load closest radar file for this time
        radarData, nearestFilePath = self.LoadClosestMRMSFile(timeString)
        radarData_t = radarData.isel(time=0)

        z_levels = radarData_t.z0
        z_idx = z_levels.to_index().get_indexer([z_km], method="nearest")[0]
        radarData_tz = radarData_t.isel(z0 = z_idx)
        return radarData_tz,z_idx,z_levels, nearestFilePath


# In[ ]:


# ============================================================
# RadarData_ARM_Class
# ============================================================

#libraries 
import os
import re
from datetime import datetime
import pyart
import matplotlib.pyplot as plt
import numpy as np
import netCDF4
import xarray as xr

class RadarData_ARM_Class:
    """
    A helper class for reading, inspecting, and plotting ARM radar data (Ka/X-band).
    """

    def __init__(self, fileDirectory, radarDataType):
        #data file reading
        self.fileDirectory = fileDirectory
        self.radarDataType = radarDataType
        self.filePathList, self.fileList = self.GetFilePathList()

    # ------------------------------------------------------------
    # Data Loading Functions
    # ------------------------------------------------------------
    # Internal Use
    def ExtractDateTimeFromFileName(self, path):
        """Extract datetime from ARM-style filename (e.g., 20220609.140946)."""
        m = re.search(r'\.(\d{8})\.(\d{6})', os.path.basename(path))
        if m:
            date_str, time_str = m.groups()
            return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        else:
            return datetime.min  # fallback if no match
        
    def GetFilePathList(self):
        filePathList = []
        for filename in os.listdir(self.fileDirectory):
            full_path = os.path.join(self.fileDirectory, filename)
            filePathList.append(full_path)

        filePathList = sorted(filePathList, key=self.ExtractDateTimeFromFileName)

        fileList = []
        for filePath in filePathList:
            fileList.append(os.path.basename(filePath))
        
        return filePathList, fileList

    # External Use
    def FindClosestFileIndex(self, fileList, target_datetime):
        """
        Find the index of the file in fileList whose timestamp is closest to target_datetime.
        """
        def extract_datetime_from_filename(fname):
            m = re.search(r'\.(\d{8})\.(\d{6})', fname)
            if m:
                date_str, time_str = m.groups()
                return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            else:
                return None
    
        # Parse all datetimes
        datetimes = [extract_datetime_from_filename(f) for f in fileList]
    
        # Compute absolute time difference
        deltas = [abs((dt - target_datetime).total_seconds()) for dt in datetimes]
        index = deltas.index(min(deltas))
        return index, fileList[index]

    def GetRadarData(self,filePath):
        self.radar = pyart.io.read(filePath, include_fields=['reflectivity']) #can add more fields here
        self.scan_time = netCDF4.num2date(self.radar.time['data'][0], self.radar.time['units'])
        print(f"Loaded radar file at {self.scan_time:%Y-%m-%d %H:%M:%S UTC}")
        return self.radar

    def GetRadarDataSweep(self, radar, field_name="reflectivity", sweep=0):
        self.radarSweep = radar.get_field(sweep, field_name)
        
        self.elev = self.radar.fixed_angle["data"][sweep]
        x, y, z = self.radar.get_gate_x_y_z(sweep, edges=False)
        self.cartesian_coords = (x,y,z)
        return self.radarSweep, self.cartesian_coords

    def GridRadarReflectivity(self, radar,
                              field_name='reflectivity',
                              grid_shape=(56, 500, 500),
                              grid_limits=((0, 2000.0), (-500e3, 500e3), (-500e3, 500e3))):
        """
        Grid radar reflectivity data into a 3-D Cartesian volume.
        """
        
        origin = (radar.latitude['data'][0], radar.longitude['data'][0])
    
        grid = pyart.map.grid_from_radars(
            radar,
            fields=[field_name],
            grid_shape=grid_shape,
            grid_limits=grid_limits,
            grid_origin=origin
        )
    
        data = grid.fields[field_name]['data'].filled(np.nan)
        return grid, data

    # ------------------------------------------------------------
    # Plotting Functions
    # ------------------------------------------------------------
    def PlotReflectivity(self, axis, sweep=0, vmin=-35, vmax=60):
        """Plot PPI reflectivity for the given sweep number."""
        if self.radar is None:
            raise ValueError("No radar data loaded. Run GetRadarData() first.")

        cmap = plt.get_cmap('NWSRef')

        radarSweep, cartesian_coords  = self.GetRadarDataSweep(self.radar)
        radarSweep[radarSweep<=0]=np.nan

        (x,y,z) = cartesian_coords

        # Convert to km
        x_km, y_km = x / 1000.0, y / 1000.0

        # Plot

        cplot = axis.pcolormesh(x_km, y_km, radarSweep, cmap=cmap, vmin=vmin, vmax=vmax)
        axis.set_xlabel("X distance from radar (km)")
        axis.set_ylabel("Y distance from radar (km)")
        axis.set_title(
            f"{self.radarDataType} Reflectivity – {self.scan_time:%Y-%m-%d %H:%M:%S UTC} – Elev {self.elev:.1f}°", fontsize=10
        )
        axis.figure.colorbar(cplot, label="Reflectivity (dBZ)")
        axis.axis("equal")

        # Overlay height contours
        cs = axis.contour(
            x_km,
            y_km,
            z / 1000.0,
            colors="black",
            linestyles="dashed",
            alpha=0.6,
            linewidths=0.7,
        )
        axis.clabel(cs, fmt="%1.1f km", inline=True, fontsize=8)

    def PlotGriddedReflectivity(self, 
                                grid,data,axis, 
                                z_index=4,xlim=(-40,40),ylim=(-40,40)):

        cmap = plt.get_cmap('NWSRef')
        z_height = grid.z['data'][z_index] / 1000.0  # km
        
        cplot =axis.pcolormesh(grid.x['data']/1000, grid.y['data']/1000, data[z_index,:,:],
                       vmin=-35, vmax=60, cmap=cmap)
        axis.set_xlabel('x (km)'); plt.ylabel('y (km)')
        axis.set_title(f"{self.radarDataType} Reflectivity – {self.scan_time:%Y-%m-%d %H:%M:%S UTC} at {z_height*1e3:.1f} km", fontsize=10)
        axis.figure.colorbar(cplot, label='dBZ')
        axis.set_xlim(xlim); axis.set_ylim(ylim)


# In[ ]:


# ============================================================
# RadarObservationMask_Class
# ============================================================

#libraries 
import xarray as xr
import pickle

class RadarObservationMask_Class:
    @staticmethod
    def LoadMaskData(DirectoryManager, ModelData):
        """
        Load a previously saved radar observation mask for timestep t.
        """
    
        codeType = os.path.join("DataAnalysis", "Observation_Data")
        dataType = "RadarData/RadarObservationMask"
        outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
    
        # Rebuild the directory path used in SaveMaskData
        outputPath = os.path.join(
            outputDirectory,
            f"{ModelData.region}_{ModelData.case}_spinup{ModelData.spinup_hours}hrs"
        )
    
        # Filename pattern must match the SaveMaskData naming
        outputFileName = f"RadarObservationMask.nc"
        outputFilePath = os.path.join(outputPath, outputFileName)
    
        # Load mask file
        RadarDataMask = xr.load_dataarray(outputFilePath)
    
        print(f"Loaded mask: {outputFilePath}\n")
    
        return RadarDataMask

    # Alias
    LoadMaskData_MRMS = LoadMaskData

    @staticmethod
    def LoadRadarObservationLevels_MRMS(DirectoryManager, ModelData):
        """
        Load previously saved radar observation levels (pickle version).
        """
    
        codeType = os.path.join("DataAnalysis", "Observation_Data")
        dataType = "RadarData/RadarObservationMask"
        outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
    
        # Rebuild the path used during saving
        outputPath = os.path.join(
            outputDirectory,
            f"{ModelData.region}_{ModelData.case}_spinup{ModelData.spinup_hours}hrs"
        )
    
        outputFileName = "RadarObservationLevels.pkl"
        outputFilePath = os.path.join(outputPath, outputFileName)
    
        # Load pickle
        with open(outputFilePath, "rb") as file:
            RadarObservationLevels = pickle.load(file)
    
        print(f"Loaded mask: {outputFilePath}\n")
    
        return RadarObservationLevels

