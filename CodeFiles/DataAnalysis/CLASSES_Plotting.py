#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# ContourPlotting_Class 
# ============================================================

import sys,os

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd  
import cartopy.crs as ccrs  
import cartopy.feature as cfeature 
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable

class ContourPlotting_Class:

    COAST = cfeature.COASTLINE.with_scale("50m")
    BORDERS = cfeature.BORDERS.with_scale("50m")
    STATES = cfeature.STATES.with_scale("50m")
    LAND = cfeature.LAND.with_scale("50m")
    LAKES = cfeature.LAKES.with_scale("50m")

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
    def PlotContourPlot(axis, lat,lon,matrix,
                         dataName, timeTitle,
                         multiplier=1,
                         clim = (None,None),
                         diverging_colorbar=False):
        """
        Plots radar data given lat,lon, and radarData_t (a xarray NETCDF object)
        """
        num_levels=19
        if diverging_colorbar == False:
            cmap = 'viridis'
            norm = None
        
            if clim != (None, None):
                vmin, vmax = clim
                levels = multiplier * np.linspace(vmin, vmax, num_levels)
            else:
                levels = num_levels
        
        # Diverging (centered at zero)
        else:
            cmap = "RdBu_r"
        
            # Handle clim or auto-detect
            if clim != (None, None):
                vmin, vmax = clim
            else:
                data_min = float(np.nanmin(multiplier * matrix))
                data_max = float(np.nanmax(multiplier * matrix))
                vmax = max(abs(data_min), abs(data_max))
                vmin = -vmax
        
            # Symmetric levels around zero
            levels = np.linspace(vmin, vmax, num_levels)
        
            # Center colorbar at zero
            norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)
        
        contourPlot = axis.contourf(
            lon, lat, multiplier*matrix,
            levels=levels,
            cmap=cmap,
            norm=norm,
            transform=ccrs.PlateCarree(),
            extend='both'
        ) 
        
        # Add map features
        axis.add_feature(ContourPlotting_Class.COAST, linewidth=1)
        axis.add_feature(ContourPlotting_Class.BORDERS, linewidth=0.8)
        axis.add_feature(ContourPlotting_Class.STATES, linewidth=0.5)
        axis.add_feature(ContourPlotting_Class.LAND, facecolor="lightgray", alpha=0.3)
        axis.add_feature(ContourPlotting_Class.LAKES, edgecolor="k", facecolor="none")
        
        #TICKS
        ContourPlotting_Class.FormatGeoTicks(axis, lon,lat)
        
        #LABELS
        title = f"{dataName} – {timeTitle}"
        axis.set_title(title, fontsize=10);
        return contourPlot

    @staticmethod
    def AddSharedColorbar(fig, contourPlot, orientation='vertical',
                          colorbarTitle="",
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
    
        cax = fig.add_axes(position)
        cbar = fig.colorbar(contourPlot, cax=cax, orientation=orientation)

        # Add label
        if colorbarTitle:
            cbar.set_label(colorbarTitle, fontsize=11)
        return cbar

# #EXAMPLE IMPORTING
# sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis"))
# from CLASSES_Plotting import ContourPlotting_Class
        
# #EXAMPLE USAGE
# contourPlot = ContourPlotting_Class.PlotContourPlot(axis,lat,lon,modelData_NSSL,
#                                                     dataName="NSSL", timeTitle = modelTimeTitle,
#                                                     multiplier = multiplier)
# colorBar = ContourPlotting_Class.AddSharedColorbar(fig, contourPlot, colorbarTitle = colorbarTitle)

