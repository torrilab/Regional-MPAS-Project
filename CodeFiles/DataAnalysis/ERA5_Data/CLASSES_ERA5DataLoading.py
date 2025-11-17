#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ============================================================
# ERA5DataLoading_Class 
# ============================================================

#Libraries
import os
import glob
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr

from tqdm import tqdm

import cdsapi 

class ERA5DataLoading_Class:

    @staticmethod
    def GetERA5FileName_PressureLevels(ERA5FilePath, variable):
        fileName = f"ERA5Surface_{variable}.nc"
        ERA5FileName = os.path.join(ERA5FilePath, fileName)
        return ERA5FileName

    @staticmethod
    def GetERA5FileName_Surface(ERA5FilePath, variable):
        fileName = f"ERA5Surface_{variable}.nc"
        ERA5FileName = os.path.join(ERA5FilePath, fileName)
        return ERA5FileName
        
    @staticmethod
    def DownloadERA5_PressureLevels(variables, date, area, ERA5FilePath):
        """
        # DOWNLOADING ERA5 (Pressure Levels)
        # Code Inspired from "Download_ERA5_with_python" by github.com/joaohenry23 at https://github.com/joaohenry23/Download_ERA5_with_python
        
        #PRELIMINARY STEPS
        #(1) go to https://cds.climate.copernicus.eu/how-to-api
        #(2) make file in main user directory called .cdsapirc
        #(3) copy the following into file: 
        #    url: https://cds.climate.copernicus.eu/api
        #    key: 6d55399f-dbc5-48bd-848c-31168fc0b133 (key will be different for you based on your account)
        #(4) pip install "cdsapi>=0.7.4"
        """
        c = cdsapi.Client()
        for variable in tqdm(variables, desc="Downloading ERA5 variables"):
            print(f"Downloading {variable}", "\n")
            
            ERA5FileName = ERA5DataLoading_Class.GetERA5FileName_PressureLevels(ERA5FilePath, variable)
            print(f'Saving file to {ERA5FileName}')
            
            c.retrieve(
                "reanalysis-era5-pressure-levels",
                {
                    "product_type": "reanalysis",
                    "format": "netcdf",
                    "variable": variable,
                    # "pressure_level": ['100', '250', '500', '750', '1000'], #LOW-RES
                    "pressure_level": [
                        '10', '20', '30', '50', '70', 
                        '100', '125', '150', '175', '200', '225',
                        '250', '300', '350', '400', '450', '500',
                        '550', '600', '650', '700', '750', '775',
                        '800', '825', '850', '875', '900', '925',
                        '950', '975', '1000',
                    ],
    
                    "date": date,
                    "time": [f"{h:02d}:00" for h in range(24)],
                    "area": area,
                    "grid": [0.25, 0.25],
                },
                ERA5FileName
            )

    @staticmethod
    def DownloadERA5_Surface(variables, date, area, ERA5FilePath):
        """
        #PRELIMINARY STEPS
        #(1) go to https://cds.climate.copernicus.eu/how-to-api
        #(2) make file in main user directory called .cdsapirc
        #(3) copy the following into file: 
        #    url: https://cds.climate.copernicus.eu/api
        #    key: 6d55399f-dbc5-48bd-848c-31168fc0b133 (key will be different for you based on your account)
        #(4) pip install "cdsapi>=0.7.4"
        """
        c = cdsapi.Client()
        for variable in tqdm(variables, desc="Downloading ERA5 surface variables"):
            print(f"Downloading {variable}", "\n")
    
            ERA5FileName = ERA5DataLoading_Class.GetERA5FileName_Surface(ERA5FilePath, variable)
            print(f'Saving file to {ERA5FileName}')
            
            c.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "format": "netcdf",
                    "variable": variable,
                    "date": date,  # e.g. "2022-06-08/2022-06-10"
                    "time": [f"{h:02d}:00" for h in range(24)],  # every hour
                    "area": area,  # [north, west, south, east]
                    "grid": [0.25, 0.25],
                },
                ERA5FileName
            )
        
    @staticmethod
    def GetVariableNames_PressureLevels():
        variables = [
            "u_component_of_wind",
            "v_component_of_wind",
            "vertical_velocity",
            "divergence",
            "vorticity",
            "temperature",
            "specific_humidity",
            "specific_cloud_liquid_water_content",
            "specific_cloud_ice_water_content",
            "specific_rain_water_content",
            "relative_humidity",
            "geopotential",
        ]
        return variables

    @staticmethod
    def GetVariableNames_Surface():
        """
        #for list of variables:
        # https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download
        """
        variables = ["msl",
                     "total_precipitation",
                     "2m_temperature",
                     "surface_sensible_heat_flux",
                     "surface_latent_heat_flux"]
        return variables
    
    @staticmethod
    def GetERA5FolderName(timeString):
        dt = datetime.strptime(timeString, "%Y-%m-%d_%H.%M.%S")
        year = dt.year
        month = f"{dt.month:02d}"
        folderName = f"{year}{month}"
        return folderName

    @staticmethod
    def GetERA5Date(dateTuple):
        startDate, endDate = dateTuple
    
        # convert endDate string → datetime
        end = datetime.strptime(endDate, "%Y-%m-%d")
    
        # subtract one day because ERA5 uses inclusive ranges
        realEnd = (end - timedelta(days=1)).strftime("%Y-%m-%d")
    
        # return ERA5 format
        return f"{startDate}/{realEnd}"

    @staticmethod
    def GetERA5Area(lat, lon):
        """
        lat, lon can be 1D or 2D arrays from ModelData_NSSL.
        Returns area in ERA5 format: [N, W, S, E].
        """
        lon360 = lon+360
        
        north = float(np.max(lat))
        south = float(np.min(lat))
        east  = float(np.max(lon360))
        west  = float(np.min(lon360))
    
        return [north, west, south, east]

    @staticmethod
    def GetERA5FilePath(DirectoryManager,ModelData):
        ERA5FilePath = os.path.join(DirectoryManager.dataDirectory,
                                      "ERA5_Data",
                                      ModelData.region,
                                      ModelData.case)
        os.makedirs(ERA5FilePath, exist_ok=True)
        return ERA5FilePath
        
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
    def LoadERA5Data(DirectoryManager, ModelData, variableName, dataType = "Surface"):
        ERA5FilePath = ERA5DataLoading_Class.GetERA5FilePath(DirectoryManager,ModelData)
        if dataType == "Surface":
            ERA5FileName = ERA5DataLoading_Class.GetERA5FileName_Surface(ERA5FilePath, variableName)
            print(ERA5FileName)
        elif dataType == "PressureLevels":
            ERA5FileName = ERA5DataLoading_Class.GetERA5FileName_PressureLevels(ERA5FilePath, variableName)
        
        ERA5_NAME_MAP = {
            "total_precipitation": "tp",
            "2m_temperature": "t2m",
            "surface_sensible_heat_flux": "sshf",
            "surface_latent_heat_flux": "slhf",
            "msl": "msl",  # already matching
        }
        ERA5variableName = ERA5_NAME_MAP.get(variableName, variableName)
        
        ERA5Data = xr.open_dataset(ERA5FileName)[ERA5variableName]
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
        ERA5Data_t = ERA5Data.sel(valid_time=time_dt, method='nearest')
    
        return ERA5Data_t


# In[ ]:


# ============================================================
# ERA5DataLoading_Class_gdex 
# ============================================================

#Libraries
import os
import glob
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr


class ERA5DataLoading_Class_gdex:
    
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
        filePath = ERA5DataLoading_Class_gdex.GetERA5FilePath(DirectoryManager, timeString, varName='msl')
        ERA5Data = xr.open_dataset(filePath)['MSL']
        ERA5_subset = ERA5DataLoading_Class_gdex.SubsetERA5(ERA5Data,ModelData)
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

