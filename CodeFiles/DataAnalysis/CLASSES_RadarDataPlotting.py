#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ============================================================
# RadarPlotting_Class 
# ============================================================

import sys,os

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd  # <-- MISSING
import cartopy.crs as ccrs  # <-- MISSING
import cartopy.feature as cfeature  # <-- MISSING
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable

class RadarPlotting_Class:

    COAST = cfeature.COASTLINE.with_scale("50m")
    BORDERS = cfeature.BORDERS.with_scale("50m")
    STATES = cfeature.STATES.with_scale("50m")
    LAND = cfeature.LAND.with_scale("50m")
    LAKES = cfeature.LAKES.with_scale("50m")

    @staticmethod
    def GetReflectivityColormap(show=False):
        #colormap based on colorbar included here: https://www.noaa.gov/jetstream/reflectivity
        
        # Reflectivity bins (dBZ)
        bounds = [-35, 0, 20, 40, 50, 65, 85]
        
        # Define color transitions (light→dark within each range)
        segment_colors = [
            ("#f7f7f7", "#a8a8a8"),   # -35–0  grey
            ("#b3caff", "#0033cc"),   # 0–20   blue
            ("#99ff99", "#006600"),   # 20–40  green
            ("#ffe680", "#ff9900"),   # 40–50  yellow–orange
            ("#ff6666", "#990000"),   # 50–65  red
            ("#e6b3ff", "#660066"),   # 65–85  purple
        ]
        
        # --- Corrected logic for building the continuous colormap ---
        
        # Normalize the bounds to the 0-1 range
        normalized_bounds = (np.array(bounds) - bounds[0]) / (bounds[-1] - bounds[0])
        
        # Initialize the dictionary for LinearSegmentedColormap
        cdict = {'red': [], 'green': [], 'blue': []}
        
        # Build the segment dictionary
        for i, (c1_hex, c2_hex) in enumerate(segment_colors):
            # Convert hex colors to RGB tuples
            c1_rgb = mcolors.to_rgb(c1_hex)
            c2_rgb = mcolors.to_rgb(c2_hex)
            
            # Get the normalized start and end points for this segment
            x_start = normalized_bounds[i]
            x_end = normalized_bounds[i+1]
            
            # Define the red, green, and blue transitions for this segment
            cdict['red'].extend([(x_start, c1_rgb[0], c1_rgb[0]), (x_end, c2_rgb[0], c2_rgb[0])])
            cdict['green'].extend([(x_start, c1_rgb[1], c1_rgb[1]), (x_end, c2_rgb[1], c2_rgb[1])])
            cdict['blue'].extend([(x_start, c1_rgb[2], c1_rgb[2]), (x_end, c2_rgb[2], c2_rgb[2])])
        
        # Create the continuous gradient colormap
        cmap = mcolors.LinearSegmentedColormap("radar_reflectivity", cdict)
        norm = mcolors.Normalize(vmin=bounds[0], vmax=bounds[-1]+2)
        levels=np.linspace(-35, 85, 200)
        ticks = np.arange(-35, 85+1, 5)   # from -35 to 85 inclusive
        
        if show:
            # --- Plotting the result ---
            
            # Create dummy data for demonstration
            # Replace this with your actual data 'a'
            a = np.linspace(bounds[0], bounds[-1], 256).reshape(16, 16)
            
            plt.figure(figsize=(8, 2))
            # The `imshow` function is typically better for showing a colormap directly,
            # as `contourf` can introduce artificial banding depending on `levels`.
            im = plt.imshow(a, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')
            
            cbar = plt.colorbar(im, ticks=bounds, orientation='horizontal', label='Reflectivity (dBZ)')
            cbar.ax.set_xticklabels(['-35', '0', '20', '40', '50', '65', '85'])
            plt.title('Radar Reflectivity Colorbar with Smooth Transitions')
            plt.show()
    
        return cmap, norm, levels, ticks
    
    @staticmethod
    def FormatReflectivityColorbar(cbar, ticks, orientation='vertical', show_labels=False):
        """
        Format a WSR-88D-style reflectivity colorbar with optional category labels.
        """
        # Main reflectivity category edges and text
        category_edges = [-35, 0, 20, 40, 50, 65, 85]
        category_labels = [
            "Extremely light\n(drizzle/snow)",
            "Very light\nprecip/clutter",
            "Light\nprecipitation",
            "Moderate\nprecipitation",
            "Heavy\nprecip/some hail",
            "Extremely heavy\n(water-coated hail)"
        ]
    
        # Set ticks and numeric labels
        cbar.set_ticks(ticks)
        if orientation == 'vertical':
            cbar.ax.set_yticklabels([str(t) for t in ticks])
        else:
            cbar.ax.set_xticklabels([str(t) for t in ticks])
    
        # Add descriptive category labels (to the left of colorbar)
        if show_labels:
            ax = cbar.ax
            for i, label in enumerate(category_labels):
                if orientation == 'vertical':
                    # Place text slightly to the *left* of the colorbar
                    ax.text(-0.4, (category_edges[i] + category_edges[i + 1]) / 2,
                            label,
                            transform=ax.get_yaxis_transform(),
                            fontsize=7.5,
                            va='center',
                            ha='right')
                else:
                    ax.text((category_edges[i] + category_edges[i + 1]) / 2, -0.2,
                            label,
                            transform=ax.get_xaxis_transform(),
                            fontsize=7.5,
                            va='top',
                            ha='center')
    
        # Add main label (reflectivity units)
        cbar.set_label("Reflectivity (dBZ)", fontsize=10)

    @staticmethod
    def CreateMapAxes(nrows=1, ncols=1,
                      figsize=None,
                      projection=ccrs.PlateCarree(),
                      wspace=0.2, hspace=0.2,
                      width_ratios=None, height_ratios=None):
        """
        Create a flexible grid of Cartopy map subplots.
        """
    
        if figsize is None:
            figsize = (5 * ncols, 4 * nrows)
    
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(
            nrows=nrows, ncols=ncols,
            wspace=wspace, hspace=hspace,
            width_ratios=width_ratios,
            height_ratios=height_ratios
        )
    
        axes = np.empty((nrows, ncols), dtype=object)
        for r in range(nrows):
            for c in range(ncols):
                axes[r, c] = fig.add_subplot(gs[r, c], projection=projection)
        return fig, axes
    
    @staticmethod
    def FormatGeoTicks(axis, lon,lat, 
                       n_ticks=5, decimal_points=3,
                       tick_fontsize=9,
                       formatters=True):
        # Set extent to your data range (forces lat/lon ticks)
        axis.set_extent([min(lon), max(lon), min(lat), max(lat)], crs=ccrs.PlateCarree())
        
        #Add lat/lon ticks with degrees
        axis.set_xticks(np.round(np.linspace(lon.min(), lon.max(), n_ticks), decimal_points), 
                        crs=ccrs.PlateCarree())
        axis.set_yticks(np.round(np.linspace(lat.min(), lat.max(), n_ticks), decimal_points), 
                        crs=ccrs.PlateCarree())
        
        # Format tick labels as degrees
        if formatters == True:
            lon_formatter = LongitudeFormatter()
            lat_formatter = LatitudeFormatter()
            axis.xaxis.set_major_formatter(lon_formatter)
            axis.yaxis.set_major_formatter(lat_formatter)
        else:
            axis.set_xlabel("Longitude (°E)")
            axis.set_ylabel("Latitude (°N)")
    
        #setting fontsize
        axis.tick_params(axis="both", which="major", labelsize=tick_fontsize)

    @staticmethod
    def PlotReflectivity(axis, lat,lon,radarData_t,
                         dataName, timeTitle,
                         clim = (None,None)):
        """
        Plots radar data given lat,lon, and radarData_t (a xarray NETCDF object)
        """
    
        num_levels=19
        if clim != (None,None):
            levels = multiplier*np.linspace(clim[0],clim[1],num_levels)
        else:
            levels=num_levels
    
        cmap, norm, levels, ticks = RadarPlotting_Class.GetReflectivityColormap()
        radarData_t = radarData_t.where(radarData_t > 0)
        
        contourPlot = axis.contourf(
            lon, lat, radarData_t,
            levels=levels,
            cmap=cmap,
            norm=norm,
            transform=ccrs.PlateCarree(),
            extend='both'
        ) 
        
        # Add map features
        axis.add_feature(RadarPlotting_Class.COAST, linewidth=1)
        axis.add_feature(RadarPlotting_Class.BORDERS, linewidth=0.8)
        axis.add_feature(RadarPlotting_Class.STATES, linewidth=0.5)
        axis.add_feature(RadarPlotting_Class.LAND, facecolor="lightgray", alpha=0.3)
        axis.add_feature(RadarPlotting_Class.LAKES, edgecolor="k", facecolor="none")
        
        #TICKS
        RadarPlotting_Class.FormatGeoTicks(axis, lon,lat)
        
        #LABELS
        title = f"{dataName} – {timeTitle} – 1 km"
        axis.set_title(title, fontsize=10);
        return contourPlot

    @staticmethod
    def AddSharedColorbar(fig, contourPlot, orientation='vertical',
                          position=None,
                          show_labels=False):
        """
        Add a shared colorbar to the figure, positioned manually with `position`.
    
        Parameters:
            fig (Figure): Matplotlib figure
            contourPlot (QuadContourSet): Returned by contourf
            orientation (str): 'vertical' or 'horizontal'
            position (list): [left, bottom, width, height] (in figure coords)
            show_labels (bool): Whether to show category labels
        """
        # Default positions
        if position is None:
            if orientation == 'vertical':
                position = [0.92, 0.2, 0.02, 0.6]  # right side
            else:
                position = [0.25, 0.1, 0.5, 0.03]  # bottom
    
        _, _, _, ticks = RadarPlotting_Class.GetReflectivityColormap()
    
        cax = fig.add_axes(position)
        cbar = fig.colorbar(contourPlot, cax=cax, orientation=orientation)
        RadarPlotting_Class.FormatReflectivityColorbar(cbar, ticks, orientation, show_labels)
        return cbar

# #EXAMPLE IMPORTING
# #Importing PlottingModelData Class
# sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
# from CLASSES_PlottingModelData import RadarPlotting_Class
        
# #EXAMPLE USAGE
# fig, axes = RadarPlotting_Class.CreateMapAxes(nrows=1,ncols=1,
#                                               figsize=(12,6))
# axis = axes[0,0]
# lat = radarData_t['latitude'].data
# lon = radarData_t['longitude'].data-360
# RadarPlotting_Class.PlotReflectivity(axis, lat,lon,radarData_t,dataName="MRMS")