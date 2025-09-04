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
Classes_1
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


# In[ ]:


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
            mean_block, _ = Ultimate_AreaAverage(chunk,
                                           dims=('t','z'),
                                           dim_names=('z'),
                                           mode='keep')
            profiles.append(mean_block)

        profiles = np.stack(profiles, axis=0)   # (nblocks, Nz)
        return profiles
    
    def block_vertical_profiles_4D(self, data, block=3):
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
            mean_block = np.mean(chunk, axis=0)   # (z, y, x)
            mean_block, _ = Ultimate_AreaAverage(chunk,
                               dims=('t','z','y','x'),
                               dim_names=('z','y','x'),
                               mode='keep')
    
            profiles.append(mean_block)
    
        profiles = np.stack(profiles, axis=0)     # (nblocks, z, y, x)
        return profiles
            
calculation = Calculation()


# In[1]:


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
    def TZContourPlot(self,numerics, var_data, var_name, var_units, date_string, date_folder, outputFile, colormap):
        #setting up labels
        # pc = np.linspace(1000,1,var_data.shape[1])     # vertical levels
        pc = numerics.P
        times = np.arange(0, var_data.shape[0]*3, 3)  # [0,3,6,9,...]
        labels = [f"{t}-{t+3-1} h" for t in times]
    
        #setting up plot figure
        fig = plt.figure(figsize=(10,4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
    
        #plotting
        ax = fig.add_subplot(gs[0, 0])
        cf = ax.contourf(times, pc, var_data.T, cmap=colormap)
        cbar = fig.colorbar(cf, ax=ax)
        cbar.set_label(f"{var_name} {var_units}")
    
        #inverting yaxis
        ax.invert_yaxis()
    
        #labels
        ax.set_xlabel('Time (hrs)')
        ax.set_ylabel('p ' + r'$(hrs)$')
        # ax.set_ylabel(f"{var_name} {var_units}")
        ax.set_title(f"TZ Contour of {var_name} {var_units} \nERA5 Data on {date_string}")

        #saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_TZContour_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter
        

    #2. TIME SERIES    
    def TimeSeries(self,numerics, var_data, var_name, var_units, date_string, date_folder, outputFile):
        #setting up plot figure
        fig = plt.figure(figsize=(10,4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
    
        #plotting
        ax = fig.add_subplot(gs[0, 0])
        x_data=numerics.time/3600
        ax.plot(x_data, var_data, lw=1.5)

        #fix axises
        #yticks
        ymin = np.floor(np.min(var_data))
        ymax = np.ceil(np.max(var_data))
        ax.set_ylim(ymin, ymax)
        yticks = np.arange(ymin, ymax + 1, 1)
        ax.set_yticks(yticks)

        #xticks
        xmin = np.floor(np.min(x_data))
        xmax = np.ceil(np.max(x_data)+1)
        ax.set_xlim(xmin, xmax)
        xticks = np.arange(xmin, xmax + 1, 1)
        ax.set_xticks(xticks)

        #labels
        ax.set_xlabel('Time (hrs)')
        ax.set_ylabel(f"{var_name} {var_units}")
        ax.set_title(f"Time-series of {var_name} {var_units} \nERA5 Data on {date_string}")
    
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
    def MultiAverage_VerticalProfiles(self,numerics, var_data,var_name,var_units,date_string, date_folder, outputFile):
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
        
        fig.suptitle(f"Vertical Profiles of {var_name} {var_units} \nERA5 Data on {date_string}")

        #saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_VerticalProfiles_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter

    #4. Horizontal Fields
    def MultiAverage_HorizontalFields(self, numerics, var_data, var_name, var_units, date_string, date_folder, plev, outputFile, colormap):
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
        vmin = np.min(var_data[:, pind, :, :])
        vmax = np.max(var_data[:, pind, :, :])
    
        fig = plt.figure(figsize=(2.5*cols, 2.5*rows), constrained_layout=True)
        gs = gridspec.GridSpec(rows, cols, figure=fig, wspace=0.1)
    
        mappable = None  # will store the last contourf object
    
        for i in range(nblocks):
            r = i // cols
            c = i % cols
            ax = fig.add_subplot(gs[r, c], projection=ccrs.PlateCarree())
    
            # horizontal slice at given z index
            field = var_data[i, pind, :, :]
            cf = ax.contourf(xc, yc, field, cmap=colormap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    
            # add coastlines & land
            self.add_land_features(ax)
    
            ax.set_title(labels[i], fontsize=12)
            mappable = cf
    
        # one shared colorbar
        cbar = fig.colorbar(mappable, ax=fig.get_axes(), orientation="vertical", shrink=0.6)
        cbar.set_label(f"{var_name} {var_units}")
    
        fig.suptitle(f"Horizontal Fields of {var_name} {var_units} at p={plev} hPa \nERA5 Data on {date_string}")
    
        # saving plot
        fig.savefig(os.path.join(outputFile, f"{var_name}_HorizontalFields_{date_folder}.jpg"))
        plt.close(fig)


plotting = Plotting()