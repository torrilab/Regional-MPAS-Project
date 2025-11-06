#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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
        radarData = xr.load_dataset(nearest_filePath)
    
        # Extract variable automatically
        varname = list(radarData.data_vars.keys())[0]
        radarData_t = radarData[varname]
    
        return radarData_t, nearest_filePath


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
    def PlotReflectivity(self, axis, sweep=0, vmin=-35, vmax=60, cmap = plt.get_cmap('NWSRef')):
        """Plot PPI reflectivity for the given sweep number."""
        if self.radar is None:
            raise ValueError("No radar data loaded. Run GetRadarData() first.")

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
                                z_index=4,xlim=(-40,40),ylim=(-40,40),
                                cmap = plt.get_cmap('NWSRef')):
        
        z_height = grid.z['data'][z_index] / 1000.0  # km
        
        cplot =axis.pcolormesh(grid.x['data']/1000, grid.y['data']/1000, data[z_index,:,:],
                       vmin=-35, vmax=60, cmap=cmap)
        axis.set_xlabel('x (km)'); plt.ylabel('y (km)')
        axis.set_title(f"{self.radarDataType} Reflectivity – {self.scan_time:%Y-%m-%d %H:%M:%S UTC} at {z_height*1e3:.1f} km", fontsize=10)
        axis.figure.colorbar(cplot, label='dBZ')
        axis.set_xlim(xlim); axis.set_ylim(ylim)

