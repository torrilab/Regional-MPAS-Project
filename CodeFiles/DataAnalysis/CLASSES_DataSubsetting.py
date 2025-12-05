#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ============================================================
# DataSubsetting_Class
# ============================================================

import xarray as xr

class DataSubsetting_Class:
   
    # @staticmethod
    # def SubsetDataRegion(data, ModelData):
    #     """
    #     Subset an xarray DataArray to a given lat/lon region.
    #     """
    #     lat_range = (ModelData.latitude.min(),ModelData.latitude.max())
    #     lon_range = (ModelData.longitude.min(),ModelData.longitude.max())
        
    #     # Convert longitudes to 0–360 range if dataset uses that convention
    #     if data.longitude.max() > 180:
    #         lon_min_target = 360 + lon_range[0] if lon_range[0] < 0 else lon_range[0]
    #         lon_max_target = 360 + lon_range[1] if lon_range[1] < 0 else lon_range[1]
    #     else:
    #         lon_min_target, lon_max_target = lon_range
    
    #     lat_min_target, lat_max_target = lat_range
    
    #     # Get nearest actual grid points
    #     lat_min = float(data.latitude.sel(latitude=lat_min_target, method='nearest'))
    #     lat_max = float(data.latitude.sel(latitude=lat_max_target, method='nearest'))
    #     lon_min = float(data.longitude.sel(longitude=lon_min_target, method='nearest'))
    #     lon_max = float(data.longitude.sel(longitude=lon_max_target, method='nearest'))
    
    #     # Apply slicing (note reversed latitude order if data is descending)
    #     subset = data.sel(latitude=slice(lat_max, lat_min),
    #                       longitude=slice(lon_min, lon_max))
    
    #     return subset

    @staticmethod
    def SubsetDataRegion(data, ModelData):
        """
        Subset an xarray DataArray to the lat/lon region of ModelData.
        Automatically handles ('lat','lon') or ('latitude','longitude').
        """

        # Detect coordinate names on the target dataset
        if "latitude" in data.coords:
            latName = "latitude"
        elif "lat" in data.coords:
            latName = "lat"
        else:
            raise KeyError("No latitude coordinate found (expected 'lat' or 'latitude').")

        if "longitude" in data.coords:
            lonName = "longitude"
        elif "lon" in data.coords:
            lonName = "lon"
        else:
            raise KeyError("No longitude coordinate found (expected 'lon' or 'longitude').")

        # ModelData always uses full names
        lat_range = (ModelData.latitude.min(), ModelData.latitude.max())
        lon_range = (ModelData.longitude.min(), ModelData.longitude.max())

        # Handle 0–360 longitudes if necessary
        if data[lonName].max() > 180:
            lon_min_target = 360 + lon_range[0] if lon_range[0] < 0 else lon_range[0]
            lon_max_target = 360 + lon_range[1] if lon_range[1] < 0 else lon_range[1]
        else:
            lon_min_target, lon_max_target = lon_range

        lat_min_target, lat_max_target = lat_range

        # Nearest valid points on grid
        lat_min = float(data[latName].sel(**{latName: lat_min_target}, method="nearest"))
        lat_max = float(data[latName].sel(**{latName: lat_max_target}, method="nearest"))
        lon_min = float(data[lonName].sel(**{lonName: lon_min_target}, method="nearest"))
        lon_max = float(data[lonName].sel(**{lonName: lon_max_target}, method="nearest"))

        # -----------------------------------------------------
        # Detect ascending or descending coordinate direction
        # -----------------------------------------------------
        latAscending = data[latName][0] < data[latName][-1]
        lonAscending = data[lonName][0] < data[lonName][-1]

        # Latitude slice
        if latAscending:
            latSlice = slice(lat_min, lat_max)
        else:
            latSlice = slice(lat_max, lat_min)

        # Longitude slice
        if lonAscending:
            lonSlice = slice(lon_min, lon_max)
        else:
            lonSlice = slice(lon_max, lon_min)

        # Apply slicing
        subset = data.sel(
            **{
                latName: latSlice,
                lonName: lonSlice,
            }
        )

        return subset
        
    @staticmethod
    def SubsetDataRegion_Curvilinear(data, ModelData):
        """
        Subset an xarray DataArray or Dataset using 2-D curvilinear latitude/longitude grids.
        Works for Stage IV, ST2, ST4, MRMS, etc.
        """
    
        # -------------------------------
        # 1. Identify coordinate names
        # -------------------------------
        if "latitude" in data.coords:
            lat_name = "latitude"
        elif "lat" in data.coords:
            lat_name = "lat"
        else:
            raise KeyError("Curvilinear subset: No 'latitude' coordinate found.")
    
        if "longitude" in data.coords:
            lon_name = "longitude"
        elif "lon" in data.coords:
            lon_name = "lon"
        else:
            raise KeyError("Curvilinear subset: No 'longitude' coordinate found.")
    
        lat2d = data[lat_name].values
        lon2d = data[lon_name].values
    
        # -------------------------------
        # 2. Target bounding box
        # -------------------------------
        lat_min = float(ModelData.latitude.min())
        lat_max = float(ModelData.latitude.max())
        lon_min = float(ModelData.longitude.min())
        lon_max = float(ModelData.longitude.max())
    
        # 0–360 longitude fix
        if lon2d.max() > 180:
            if lon_min < 0: lon_min += 360
            if lon_max < 0: lon_max += 360
    
        # -------------------------------
        # 3. Build mask (NumPy)
        # -------------------------------
        mask_np = (
            (lat2d >= lat_min) & (lat2d <= lat_max) &
            (lon2d >= lon_min) & (lon2d <= lon_max)
        )
    
        # -------------------------------
        # 4. Convert mask to DataArray
        # -------------------------------
        mask_xr = xr.DataArray(
            mask_np,
            dims=data[lat_name].dims,
            coords=data[lat_name].coords
        )
    
        # -------------------------------
        # 5. Apply mask
        # -------------------------------
        subset = data.where(mask_xr, drop=True)
    
        return subset

