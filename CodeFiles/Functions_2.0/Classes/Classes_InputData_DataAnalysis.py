#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# #IMPORT CLASSES
# # --- Add your Functions folder to sys.path ---
# import sys
# path = mainDirectory + '/Functions_2.0/'
# sys.path.append(path)

# # --- Import all your function modules ---
# import importlib
# modules = [
#     "Classes",
# ]

# for mod in modules:
#     globals()[mod] = importlib.import_module(mod)        # import module itself
#     globals().update(vars(globals()[mod]))              # import all functions into global namespace


# In[ ]:


"""
====================================================
Classes_InputData_DataAnalysis
Used for DownloadERA5Data and InputData_AreaAverages (so far)
====================================================
"""


# In[ ]:


# classes = ["Coordinates", "Strings", "Calculation", "Plotting"]
# print("Importing Classes:\n" + ", ".join(classes))


# In[ ]:


#######################
#DIRECTORIES


# In[ ]:


# #SETTING UP DIRECTORIES
mainDirectory = '/mnt/lustre/koa/koastore/torri_group/air_directory/Projects/Regional-MPAS-Project/'


# In[ ]:


#################################
#IMPORTING LIBRARIES

#If libraries below are not installed, used "pip install library_name" 
#or install with Conda or Mamba in terminal (https://www.anaconda.com/docs/tools/working-with-conda/packages/install-packages)

#arrays
import numpy as np
import math

#plotting
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import ScalarFormatter
import matplotlib.gridspec as gridspec
from matplotlib.colors import BoundaryNorm

#Map Contours for Plotting
import cartopy.crs as ccrs
import cartopy.feature as cfeature

#system
import sys; import os; import time


# In[ ]:


#IMPORT FUNCTIONS
# --- Add your Functions folder to sys.path ---
import sys
path = mainDirectory + 'Functions_2.0/'
sys.path.append(path)

# --- Import all your function modules ---
import importlib
modules = [
    "AreaAverageFunctions",
    "ComputationFunctions",
    "DataFunctions",
    "DerivativeFunctions",
    "PlottingFunctions",
    "StatisticalFunctions",
]
for mod in modules:
    globals()[mod] = importlib.import_module(mod)        # import module itself
    globals().update(vars(globals()[mod]))              # import all functions into global namespace


# In[ ]:


#################################
#CLASSES


# In[ ]:


#NUMERICS
class Numerics:
    def __init__(self, Nt,Np,Nlat,Nlon, dt,
                 TIME,P,LAT,LON):
        # store base values
        self.dt = dt #seconds

        self.Nt = Nt   # number of time steps (from your data array)
        self.Np = Np   # number of time steps (from your data array)
        self.Nlat = Nlat   # number of time steps (from your data array)
        self.Nlon = Nlon   # number of time steps (from your data array)

        #dimension arrays
        self.TIME = TIME
        self.P = P
        self.LAT = LAT
        self.LON = LON

        # derived arrays
        self.time = np.arange(0, Nt*dt, dt)  # seconds

        # time units
        self.second = 1
        self.minute = 60
        self.hour = 60**2
        self.day = 24*(60**2)
        self.minute_index = np.argmin(np.abs(self.time - self.minute))
        self.hour_index = np.argmin(np.abs(self.time - self.hour))
        self.day_index = np.argmin(np.abs(self.time - self.day))


# In[ ]:


class Coordinates:
    def __init__(self):
        pass

    def DMSToDecimal(self, deg, minutes, seconds, hemisphere):
        """
        Convert degrees, minutes, seconds to decimal degrees.

        Parameters
        ----------
        deg : int or float
            Degrees
        minutes : int or float
            Minutes
        seconds : int or float
            Seconds
        hemisphere : str
            'N', 'S', 'E', or 'W'

        Returns
        -------
        float
            Decimal degrees
        """
        decimal = deg + minutes/60 + seconds/3600
        if hemisphere.upper() in ['S', 'W']:
            decimal = -decimal
        return decimal
        
        
    def dxTOdlon(self, dx_m, lat_deg):
        """
        Convert a zonal distance (dx) at a given latitude to degrees of longitude.
        Equation: dx = Rcos(lat)dlon
        
        Parameters
        ----------
        dx_m : float
            Distance in meters (east-west).
        lat_deg : float
            Central latitude in degrees.
        
        Returns
        -------
        dlon_deg : float
            Longitude offset in degrees.
        """
        R = 6_371_000  # Earth radius in meters
        phi = math.radians(lat_deg)
        dlon_rad = dx_m / (R * math.cos(phi))
        return math.degrees(dlon_rad)
    
    
    def dyTOdlat(self, dy_m):
        """
        Convert a meridional distance (dy) to degrees of latitude.
        Equation: dy = Rdlat
        
        Parameters
        ----------
        dy_m : float
            Distance in meters (north-south).
        
        Returns
        -------
        dlat_deg : float
            Latitude offset in degrees.
        """
        R = 6_371_000  # Earth radius in meters
        dlat_rad = dy_m / R
        return math.degrees(dlat_rad)

coordinates=Coordinates()


# In[ ]:


class Strings:
    def __init__(self):
        pass

    def DateString(self, date_string):
        date_folder = (
            date_string
            .replace("/", "-")   # slashes not allowed in folder names
            .replace(" ", "_")   # replace spaces with underscore
            .replace("(", "")    # remove (
            .replace(")", "")    # remove )
        )
        return date_folder
        
strings=Strings()


# In[1]:


#CALCULATION FUNCTIONS
class Calculation:
    def __init__(self):
        pass
    
    def block_vertical_profiles_2D(self, data, block):
        """
        Compute block-averaged vertical profiles from a 2D array (t,z).
        
        Parameters
        ----------
        data : np.ndarray
            Input array with shape (t,z).
        block : int, optional
            Number of timesteps per block (default=3).
        
        Returns
        -------
        profiles : np.ndarray
            Vertical profiles with shape (Nz, nblocks).
        """
        Nt, Nz = data.shape
        profiles = []

        for t0 in range(0, Nt - block + 1, block):
            # slice block of timesteps
            chunk = data[t0:t0+block, :]   # (block, z, y, x)

            # average over (t,y,x) → (z,)
            # mean_block = np.nanmean(chunk, axis=0)
            mean_block, _ = Ultimate_AreaAverage(chunk,
                                           dims=('t','z'),
                                           dim_names=('z'),
                                           mode='keep')
            profiles.append(mean_block)

        profiles = np.stack(profiles, axis=0)   # (nblocks, Nz)
        return profiles
    
    def block_vertical_profiles_4D(self, data, block):
        """
        Compute block-averaged 3D fields from a 4D array (t,z,y,x),
        by averaging over t in blocks.
        
        Parameters
        ----------
        data : np.ndarray
            Input array with shape (t,z,y,x).
        block : int, optional
            Number of timesteps per block (default=3).
        
        Returns
        -------
        profiles : np.ndarray
            Block-averaged fields with shape (nblocks, z, y, x).
            Each block is the average over `block` timesteps.
        """
        Nt, Nz, Ny, Nx = data.shape
        profiles = []
    
        for t0 in range(0, Nt - block + 1, block):
            # slice block of timesteps (block, z, y, x)
            chunk = data[t0:t0+block, :, :, :]
    
            # average over time axis only
            # mean_block = np.nanmean(chunk, axis=0)
            mean_block, _ = Ultimate_AreaAverage(chunk,
                               dims=('t','z','y','x'),
                               dim_names=('z','y','x'),
                               mode='keep')
    
            profiles.append(mean_block)
    
        profiles = np.stack(profiles, axis=0)     # (nblocks, z, y, x)
        return profiles
    
    def block_vertical_profiles_3D(self, data, block):
            """
            Compute block-averaged 2D fields from a 3D array (t,y,x),
            by averaging over t in blocks.
    
            Parameters
            ----------
            data : np.ndarray
                Input array with shape (t,y,x).
            block : int, optional
                Number of timesteps per block (default=3).
    
            Returns
            -------
            profiles : np.ndarray
                Block-averaged fields with shape (nblocks, y, x).
                Each block is the average over `block` timesteps.
            """
            Nt, Ny, Nx = data.shape
            profiles = []
    
            for t0 in range(0, Nt - block + 1, block):
                # slice block of timesteps (block, y, x)
                chunk = data[t0:t0+block, :, :]
    
                # average over time axis only
                # mean_block = np.nanmean(chunk, axis=0)
                mean_block, _ = Ultimate_AreaAverage(
                    chunk,
                    dims=('t','y','x'),
                    dim_names=('y','x'),
                    mode='keep'
                )
    
                profiles.append(mean_block)
    
            profiles = np.stack(profiles, axis=0)   # (nblocks, y, x)
            return profiles
            
calculation = Calculation()


# In[4]:


#PLOTTING FUNCTIONS

#1. (T,Z) Contour Plot
class Plotting:
    def __init__(self):
        pass

    # def add_land_features(self, ax):
    #     """
    #     Add coastlines, borders, and land features to a Cartopy axis.
    #     """
    #     ax.coastlines(resolution="10m", linewidth=0.5)
    #     ax.add_feature(cfeature.BORDERS, linewidth=0.3)
    #     ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.5)
    #     ax.add_feature(cfeature.OCEAN, facecolor="lightblue", alpha=0.3)

    def add_land_features(self, ax):
        """
        Add coastlines, borders, land, ocean, and labeled gridlines to a Cartopy axis.
        """
        # Coastlines and borders
        ax.coastlines(resolution="10m", linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3)
        
        # Land and ocean shading
        ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.5)
        ax.add_feature(cfeature.OCEAN, facecolor="lightblue", alpha=0.3)

        # Gridlines with labels
        gl = ax.gridlines(
            draw_labels=True, linewidth=0.3, color="gray", alpha=0.5, linestyle="--"
        )
        gl.top_labels = False    # remove top labels
        gl.right_labels = False  # remove right labels
        gl.xlabel_style = {"size": 8}
        gl.ylabel_style = {"size": 8}

    #1. (T,Z) Contour Plot
    def TZContourPlot(self,numerics, var_data, var_name, var_units, date_string, date_folder, outputFile, colormap,data_lim, center_contour, UTC_offset):
        #setting up labels
        # pc = np.linspace(1000,1,var_data.shape[1])     # vertical levels
        pc = numerics.P
        times = np.arange(0, var_data.shape[0]*1, 1)  # [0,3,6,9,...]
    
        #setting up plot figure
        fig = plt.figure(figsize=(10,4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
    
        #plotting
        ax = fig.add_subplot(gs[0, 0])
        if data_lim != "NaN":  # user-specified range
            vmin, vmax = data_lim
        else:  # fallback to data range
            vmin, vmax = np.nanmin(var_data), np.nanmax(var_data)

        # ----- TwoSlopeNorm setup -----
        # if center_contour != "NaN":
        #     levels=15
        #     norm = TwoSlopeNorm(vmin=vmin, vcenter=center_contour, vmax=vmax)
        # else:
        #     levels = np.linspace(vmin, vmax, num=15)
        #     norm = None

        # ----- BoundaryNorm setup -----
        if center_contour != "NaN":
            # symmetric limits around the center so the colorbar is balanced
            lim = max(center_contour - vmin, vmax - center_contour)
            vmin, vmax = center_contour - lim, center_contour + lim
    
            levels = np.linspace(vmin, vmax, 15)
            if not np.any(np.isclose(levels, center_contour)):
                levels = np.sort(np.r_[levels, center_contour])  # force a bin edge at the center
            norm = BoundaryNorm(levels, ncolors=plt.get_cmap(colormap).N)
        else:
            levels = np.linspace(vmin, vmax, 15)
            norm = BoundaryNorm(levels, ncolors=plt.get_cmap(colormap).N)
   
        cf = ax.contourf(times, pc, var_data.T, levels=levels, cmap=colormap, norm=norm, extend="both")

        cbar = fig.colorbar(cf, ax=ax)
        cbar.set_label(f"{var_name} {var_units}")

        #inverting yaxis
        ax.invert_yaxis()
    
        #labels
        ax.set_xlabel('Time (hrs)')
        ax.set_ylabel('p ' + r'$(hrs)$')
        # ax.set_ylabel(f"{var_name} {var_units}")
        ax.set_title(f"TZ Contour of {var_name} {var_units} \nERA5 Data on {date_string} UTC{UTC_offset}")

        #saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_TZContour_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter
        

    #2. TIME SERIES    
    def TimeSeries(self,numerics, var_data, var_name, var_units, date_string, date_folder, outputFile, data_lim, UTC_offset):
        #setting up plot figure
        fig = plt.figure(figsize=(10,4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
    
        #plotting
        ax = fig.add_subplot(gs[0, 0])
        x_data=numerics.time/3600
        ax.plot(x_data, var_data, lw=1.5)

        #fix axises
        #yticks
        if data_lim == "NaN":
            ymin = np.nanmin(var_data)
            ymax = np.nanmax(var_data)
            ax.set_ylim(ymin, ymax)
            # yticks = np.arange(ymin, ymax + 1, 1)
            # ax.set_yticks(yticks)
        elif data_lim != "NaN": #data lim
            ax.set_ylim(data_lim)

        #xticks
        xmin = np.floor(np.nanmin(x_data))
        xmax = np.ceil(np.nanmax(x_data)+1)
        ax.set_xlim(xmin, xmax)
        xticks = np.arange(xmin, xmax + 1, 1)
        ax.set_xticks(xticks)

        #labels
        ax.set_xlabel('Time (hrs)')
        ax.set_ylabel(f"{var_name} {var_units}")
        ax.set_title(f"Time-series of {var_name} {var_units} \nERA5 Data on {date_string} UTC{UTC_offset}")
    
        # Set xticks every 3 hours
        max_hours = numerics.time[-1]/3600
        ax.set_xticks(np.arange(0, max_hours+1, 3))
    
        #vertical lines
        ndays=3; vline_xinds = np.insert(np.arange(24, 24*ndays+1, 24) - 1, 0, 0) # e.g. every 24 hrs
        for x in vline_xinds:
            ax.axvline(x, color='k', linestyle='--', alpha=0.7)
        ax.axvline(24-18-1,color='blue', linestyle='--', alpha=0.7, label='model start-time')

        
        
        #other
        fig.tight_layout()
        fig.legend()

        #saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_TimeSeries_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter
    
    #3. VERTICAL PROFILES
    def MultiAverage_VerticalProfiles(self,numerics, var_data,var_name,var_units,date_string, date_folder, outputFile, vline,data_lim, UTC_offset):
        #setting up labels
        times = np.arange(0, var_data.shape[0]*3, 3)  # [0,3,6,9,...]
        labels = [f"{t}-{t+3-1} h" for t in times]
        
        #setting up number of plots
        nplots = var_data.shape[0]
        cols = 8                                      # 8 profiles per row
        rows = int(np.ceil(nplots / cols))            # number of rows needed
        
        #setting up plot figure
        fig = plt.figure(figsize=(2*cols, 3*rows), constrained_layout=True)   # scale fig size to rows/cols
        gs = gridspec.GridSpec(rows, cols, figure=fig, wspace=0.1)
        
        axes = []
        for i, t in enumerate(times):
            r = i // cols   # row index
            c = i % cols    # column index
            ax = fig.add_subplot(gs[r, c])
            ax.plot(var_data[i, :], numerics.P)
    
            #fixing yaxis
            ax.set_ylim(bottom=numerics.P.min(),top=numerics.P.max())
            ax.invert_yaxis()

            #adding vline
            if vline != "NaN":
                ax.axvline(vline,linestyle='dashed',color='gray')            
            
            #labels
            ax.set_title(labels[i], fontsize=12)
            ax.set_xlabel(f"{var_name} {var_units}",fontsize=9)
            if c == 0:
                ax.set_ylabel("p (hPa)")
            else:
                ax.set_yticklabels([])  # hide y tick labels except first col
            # axes.append(ax)
        
        #fixing xlims
        axes = fig.get_axes()
        MatchAxisLimits(axes, dim='x')

        #data lim
        if data_lim != "NaN":
            for ax in axes:
                ax.set_xlim(data_lim)
        
        fig.suptitle(f"Vertical Profiles of {var_name} {var_units} \nERA5 Data on {date_string} UTC{UTC_offset}")

        #saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_VerticalProfiles_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter

    #4. Horizontal Fields 
    def MultiAverage_HorizontalFields(self, numerics, var_data, var_name, var_units,
                                      date_string, date_folder, plev, outputFile,
                                      colormap, data_lim, line_contour, center_contour, UTC_offset):
        """
        Plot horizontal contour maps at a given pressure level for each block in var_data,
        with a single consistent colorbar.
        """
        nblocks, Nz, Ny, Nx = var_data.shape
        times = np.arange(0, nblocks*3, 3)  # hours (assuming 3h blocks)
        labels = [f"{t}-{t+3-1} h" for t in times]
    
        # pressure coords
        pc = numerics.P
        pind = np.argmin(np.abs(pc - plev))  # nearest index
        yc = numerics.LAT
        xc = numerics.LON
    
        # layout
        cols = 8
        rows = int(np.ceil(nblocks / cols))
    
        # global color limits
        if data_lim != "NaN":  # user-specified range
            vmin, vmax = data_lim
        else:  # fallback to data range
            vmin = np.nanmin(var_data[:, pind, :, :])
            vmax = np.nanmax(var_data[:, pind, :, :])
    
        if np.isclose(vmin, vmax):  # correction for if vmin==vmax
            vmin = vmax - 1e-6

        # ----- TwoSlopeNorm setup -----
        # if center_contour != "NaN":
        #     norm   = TwoSlopeNorm(vmin=vmin, vcenter=center_contour, vmax=vmax)
        #     levels = np.linspace(vmin, vmax, num=15)   # <- fixed array, not an int
        # else:
        #     norm   = None
        #     levels = np.linspace(vmin, vmax, num=15)

        # ----- BoundaryNorm setup -----
        if center_contour != "NaN":
            lim    = max(center_contour - vmin, vmax - center_contour)
            edges  = np.linspace(center_contour - lim, center_contour + lim, 15)
            if not np.any(np.isclose(edges, center_contour)):
                edges = np.sort(np.r_[edges, center_contour])  # force a boundary at the center
            norm   = BoundaryNorm(edges, ncolors=plt.get_cmap(colormap).N, clip=True)
            levels = edges
        else:
            levels = np.linspace(vmin, vmax, 15)
            norm   = BoundaryNorm(levels, ncolors=plt.get_cmap(colormap).N, clip=True)
        
        fig = plt.figure(figsize=(2.5*cols, 2.5*rows), constrained_layout=True)
        gs = gridspec.GridSpec(rows, cols, figure=fig, wspace=0.1)
    
        mappable = None  # for the colorbar
    
        for i in range(nblocks):
            r = i // cols
            c = i % cols
            ax = fig.add_subplot(gs[r, c], projection=ccrs.PlateCarree())
    
            # horizontal slice at given z index
            field = var_data[i, pind, :, :]
    
            cf = ax.contourf(
                xc, yc, field,
                levels=levels,                 # <- fixed global boundaries
                cmap=colormap,
                norm=norm,                     # <- shared norm (TwoSlope or None)
                extend="both",
                transform=ccrs.PlateCarree()
            )
    
            if line_contour == "T":
                ax.contour(
                    xc, yc, field,
                    levels=levels,             # <- same fixed levels for lines
                    colors="k",
                    linewidths=0.8,
                    transform=ccrs.PlateCarree(),
                    zorder=10
                )

            #             # # build 2D coordinate grids
            # X, Y = np.meshgrid(xc, yc)
            
            # # grab 2D slices of winds at time i (already averaged over vertical levels)
            # U = np.mean(calculation_results_temp1['u_component_of_wind']['tzyx_3h'], axis=1)[i]
            # V = np.mean(calculation_results_temp2['v_component_of_wind']['tzyx_3h'], axis=1)[i]
            
            # # plot quiver
            # step = 1
            # speed = np.sqrt(U**2 + V**2)
            # Q = ax.quiver(
            #     X[::step, ::step], Y[::step, ::step],
            #     U[::step, ::step], V[::step, ::step],
            #     speed[::step, ::step],              # color map by speed
            #     transform=ccrs.PlateCarree(),
            #     scale=5, scale_units="xy", pivot="middle",
            #     cmap="plasma", zorder=15
            # )  # plot every 3rd point
            # ########## #*##* quiver

    
            self.add_land_features(ax)
            ax.set_title(labels[i], fontsize=12)
    
            # ---- KEY FIX 2: set the mappable ONCE (don’t overwrite with last panel)
            if mappable is None:
                mappable = cf
    
        # ---- Colorbar from the chosen QuadContourSet (cf)
        cbar = fig.colorbar(mappable, ax=fig.get_axes(), orientation="vertical", shrink=0.6)
        cbar.set_label(f"{var_name} {var_units}")
    
        fig.suptitle(
            f"Horizontal Fields of {var_name} {var_units} at p={plev} hPa \n"
            f"ERA5 Data on {date_string} UTC{UTC_offset}"
        )
    
        fig.savefig(os.path.join(outputFile, f"{var_name}_HorizontalFields_{date_folder}.jpg"))
        plt.close(fig)

    #4.5. Horizontal Fields (For Surface Variables)
    def MultiAverage_HorizontalFields_Surface(self, numerics, var_data, var_name, var_units,
                                      date_string, date_folder, plev, outputFile,
                                      colormap, data_lim, line_contour, center_contour, UTC_offset):
        """
        Plot horizontal contour maps at a given pressure level for each block in var_data,
        with a single consistent colorbar.
        """
        nblocks, Ny, Nx = var_data.shape
        times = np.arange(0, nblocks*3, 3)  # hours (assuming 3h blocks)
        labels = [f"{t}-{t+3-1} h" for t in times]
    
        # pressure coords
        pc = numerics.P
        # pind = np.argmin(np.abs(pc - plev))  # nearest index
        yc = numerics.LAT
        xc = numerics.LON
    
        # layout
        cols = 8
        rows = int(np.ceil(nblocks / cols))
    
        # global color limits
        if data_lim != "NaN":  # user-specified range
            vmin, vmax = data_lim
        else:  # fallback to data range
            vmin = np.nanmin(var_data[:, :, :])
            vmax = np.nanmax(var_data[:, :, :])
    
        if np.isclose(vmin, vmax):  # correction for if vmin==vmax
            vmin = vmax - 1e-6

        # ----- TwoSlopeNorm setup -----
        # if center_contour != "NaN":
        #     norm   = TwoSlopeNorm(vmin=vmin, vcenter=center_contour, vmax=vmax)
        #     levels = np.linspace(vmin, vmax, num=15)   # <- fixed array, not an int
        # else:
        #     norm   = None
        #     levels = np.linspace(vmin, vmax, num=15)

        # ----- BoundaryNorm setup -----
        if center_contour != "NaN":
            lim    = max(center_contour - vmin, vmax - center_contour)
            edges  = np.linspace(center_contour - lim, center_contour + lim, 15)
            if not np.any(np.isclose(edges, center_contour)):
                edges = np.sort(np.r_[edges, center_contour])  # force a boundary at the center
            norm   = BoundaryNorm(edges, ncolors=plt.get_cmap(colormap).N, clip=True)
            levels = edges
        else:
            levels = np.linspace(vmin, vmax, 15)
            norm   = BoundaryNorm(levels, ncolors=plt.get_cmap(colormap).N, clip=True)
        
        fig = plt.figure(figsize=(2.5*cols, 2.5*rows), constrained_layout=True)
        gs = gridspec.GridSpec(rows, cols, figure=fig, wspace=0.1)
    
        mappable = None  # for the colorbar
    
        for i in range(nblocks):
            r = i // cols
            c = i % cols
            ax = fig.add_subplot(gs[r, c], projection=ccrs.PlateCarree())
    
            # horizontal slice at given z index
            field = var_data[i, :, :]
    
            cf = ax.contourf(
                xc, yc, field,
                levels=levels,                 # <- fixed global boundaries
                cmap=colormap,
                norm=norm,                     # <- shared norm (TwoSlope or None)
                extend="both",
                transform=ccrs.PlateCarree()
            )
    
            if line_contour == "T":
                ax.contour(
                    xc, yc, field,
                    levels=levels,             # <- same fixed levels for lines
                    colors="k",
                    linewidths=0.8,
                    transform=ccrs.PlateCarree(),
                    zorder=10
                )

            #             # # build 2D coordinate grids
            # X, Y = np.meshgrid(xc, yc)
            
            # # grab 2D slices of winds at time i (already averaged over vertical levels)
            # U = np.mean(calculation_results_temp1['u_component_of_wind']['tzyx_3h'], axis=1)[i]
            # V = np.mean(calculation_results_temp2['v_component_of_wind']['tzyx_3h'], axis=1)[i]
            
            # # plot quiver
            # step = 1
            # speed = np.sqrt(U**2 + V**2)
            # Q = ax.quiver(
            #     X[::step, ::step], Y[::step, ::step],
            #     U[::step, ::step], V[::step, ::step],
            #     speed[::step, ::step],              # color map by speed
            #     transform=ccrs.PlateCarree(),
            #     scale=5, scale_units="xy", pivot="middle",
            #     cmap="plasma", zorder=15
            # )  # plot every 3rd point
            # ########## #*##* quiver

    
            self.add_land_features(ax)
            ax.set_title(labels[i], fontsize=12)
    
            # ---- KEY FIX 2: set the mappable ONCE (don’t overwrite with last panel)
            if mappable is None:
                mappable = cf
    
        # ---- Colorbar from the chosen QuadContourSet (cf)
        cbar = fig.colorbar(mappable, ax=fig.get_axes(), orientation="vertical", shrink=0.6)
        cbar.set_label(f"{var_name} {var_units}")
    
        fig.suptitle(
            f"Horizontal Fields of {var_name} {var_units} at p={plev} hPa \n"
            f"ERA5 Data on {date_string} UTC{UTC_offset}"
        )
    
        fig.savefig(os.path.join(outputFile, f"{var_name}_HorizontalFields_{date_folder}.jpg"))
        plt.close(fig)

        
    #5. Horizontal Fields (Vertical Average)
    def MultiAverage_HorizontalFields_VerticalAvg(self, numerics, var_data, var_name, var_units, date_string, date_folder, outputFile, colormap,data_lim, line_contour, center_contour, UTC_offset):
        """
        Plot horizontal contour maps at a given pressure level for each block in var_data,
        with a single consistent colorbar.
        """
        nblocks, Nz, Ny, Nx = var_data.shape
        times = np.arange(0, nblocks*3, 3)  # hours (assuming 3h blocks)
        labels = [f"{t}-{t+3-1} h" for t in times]
    
        # pressure coords
        pc = numerics.P
        yc = numerics.LAT
        xc = numerics.LON
    
        # layout
        cols = 8
        rows = int(np.ceil(nblocks / cols))
    
        # global color limits
        if data_lim != "NaN":  # user-specified range
            vmin, vmax = data_lim
        else:  # fallback to data range
            vmin, vmax = np.nanmin( np.mean(var_data,axis=1) ), np.nanmax( np.mean(var_data,axis=1) )
        if np.isclose(vmin, vmax): #correction for if vmin=vmax
            vmin = vmax - 1e-6

        # ----- TwoSlopeNorm setup -----
        # if center_contour != "NaN":
        #     levels=15
        #     norm = TwoSlopeNorm(vmin=vmin, vcenter=center_contour, vmax=vmax)
        # else:
        #     levels = np.linspace(vmin, vmax, num=15)
        #     norm = None

        # ----- BoundaryNorm setup -----
        if center_contour != "NaN":
            lim    = max(center_contour - vmin, vmax - center_contour)
            edges  = np.linspace(center_contour - lim, center_contour + lim, 15)
            if not np.any(np.isclose(edges, center_contour)):
                edges = np.sort(np.r_[edges, center_contour])  # force a boundary at the center
            norm   = BoundaryNorm(edges, ncolors=plt.get_cmap(colormap).N, clip=True)
            levels = edges
        else:
            levels = np.linspace(vmin, vmax, 15)
            norm   = BoundaryNorm(levels, ncolors=plt.get_cmap(colormap).N, clip=True)
    
        fig = plt.figure(figsize=(2.5*cols, 2.5*rows), constrained_layout=True)
        gs = gridspec.GridSpec(rows, cols, figure=fig, wspace=0.1)
    
        mappable = None  # will store the last contourf object
    
        for i in range(nblocks):
            r = i // cols
            c = i % cols
            ax = fig.add_subplot(gs[r, c], projection=ccrs.PlateCarree())
    
            # horizontal slice at given z index
            field = np.mean(var_data, axis=1)[i]
            cf = ax.contourf(
                    xc, yc, field,
                    levels=levels,
                    cmap=colormap,
                    norm=norm,
                    extend="both",
                    transform=ccrs.PlateCarree()
                )
            if line_contour == "T":
                cs = ax.contour(
                    xc, yc, field,
                    levels=levels,
                    colors="k",        # fixed black lines
                    linewidths=0.8,
                    transform=ccrs.PlateCarree(),
                    zorder=10
                )       
                
            # add coastlines & land
            self.add_land_features(ax)
    
            ax.set_title(labels[i], fontsize=12)
            mappable = cf
    
        # one shared colorbar
        cbar = fig.colorbar(mappable, ax=fig.get_axes(), orientation="vertical", shrink=0.6)
        cbar.set_label(f"{var_name} {var_units}")
    
        fig.suptitle(f"Horizontal Fields of {var_name} {var_units} at All Levels \nERA5 Data on {date_string} UTC{UTC_offset}")
    
        # saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_HorizontalFields_VerticalAvg_{date_folder}.jpg"))
        plt.close(fig)


plotting = Plotting()

