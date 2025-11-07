#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# ERA5DataLoading_Class 
# ============================================================

#Libraries
import os
import glob
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr


class ERA5DataLoading_Class:
    
    @staticmethod
    def GetERA5FolderName(timeString):
        dt = datetime.strptime(timeString, "%Y-%m-%d_%H.%M.%S")
        year = dt.year
        month = f"{dt.month:02d}"
        folderName = f"{year}{month}"
        return folderName

    @staticmethod
    def GetERA5FilePath(DirectoryManager, timeString, varName='msl'):
        # Generate folder name and full directory path
        folderName = ERA5DataLoading_Class.GetERA5FolderName(timeString)
        ERA5_DataDirectory = os.path.join(
            DirectoryManager.dataDirectory,
            "ERA5_Data/globus_download/d633000/e5.oper.an.sfc",
            folderName
        )
    
        # Build the glob pattern
        fileNamePattern = f"e5.oper.an.sfc.128_151_{varName}.ll025sc.*"
        fullPattern = os.path.join(ERA5_DataDirectory, fileNamePattern)
    
        # Find files
        matching_files = glob.glob(fullPattern)
    
        if not matching_files:
            raise FileNotFoundError(f"No ERA5 file found matching pattern: {fullPattern}")
        
        # If multiple matches, return the first one (or sort if needed)
        return matching_files[0]
        
    @staticmethod
    def SubsetERA5(ERA5Data, ModelData):
        latModel = ModelData.latitude
        lonModel = ModelData.longitude
    
        # Convert model longitudes from -180:180 → 0:360 to match ERA5
        lonModel_360 = (lonModel + 360) % 360
    
        # Determine model bounding box
        lat_min, lat_max = float(latModel.min()), float(latModel.max())
        lon_min, lon_max = float(lonModel_360.min()), float(lonModel_360.max())
    
        # Snap model domain to nearest ERA5 grid points
        lat_bounds = ERA5Data.sel(latitude=[lat_min, lat_max], method="nearest").latitude.values
        lon_bounds = ERA5Data.sel(longitude=[lon_min, lon_max], method="nearest").longitude.values
    
        # Ensure proper slicing order
        lat_start, lat_end = sorted(lat_bounds)[::-1]  # ERA5 latitude is descending
        lon_start, lon_end = sorted(lon_bounds)
    
        # Subset the ERA5 data
        ERA5_subset = ERA5Data.sel(
            latitude=slice(lat_start, lat_end),
            longitude=slice(lon_start, lon_end)
        )
    
        # Convert ERA5 longitudes from 0–360 → -180–180 (in-place update)
        ERA5_subset = ERA5_subset.assign_coords(
            longitude=(((ERA5_subset.longitude + 180) % 360) - 180)
        )
    
        # Sort longitudes to keep increasing order (optional, but helpful for plotting)
        ERA5_subset = ERA5_subset.sortby('longitude')
    
        return ERA5_subset

    @staticmethod
    def LoadERA5Data(timeString, ModelData, DirectoryManager):
        filePath = ERA5DataLoading_Class.GetERA5FilePath(DirectoryManager, timeString, varName='msl')
        ERA5Data = xr.open_dataset(filePath)['MSL']
        ERA5_subset = ERA5DataLoading_Class.SubsetERA5(ERA5Data,ModelData)
        return ERA5_subset
    
    @staticmethod
    def SelectNearestERA5Time(ERA5Data, timeString):
        """
        Selects the nearest ERA5 time slice based on a custom time string.
        """
    
        # Convert custom timeString to pandas Timestamp
        time_dt = pd.to_datetime(timeString.replace('_', ' ').replace('.', ':'))
    
        # Use xarray's nearest selection
        ERA5Data_t = ERA5Data.sel(time=time_dt, method='nearest')
    
        return ERA5Data_t

