#!/usr/bin/env python
# coding: utf-8

# In[ ]:

# #IMPORT CLASSES
# # --- Add your Functions folder to sys.path ---
# import sys
# path = workingDirectory
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

classes = ["Coordinates", "Strings", "Calculation", "Plotting"]
print("Importing Classes:\n" + ", ".join(classes))

# In[ ]:


#################################
#CLASSES


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


# In[ ]:


#PLOTTING FUNCTIONS

#1. (T,Z) Contour Plot
class Plotting:
    def __init__(self):
        pass

    #1. (T,Z) Contour Plot
    def TZContourPlot(self, var_data, var_name, var_units, date_string):
        #setting up labels
        pc = np.linspace(1000,1,var_data.shape[1])     # vertical levels
        times = np.arange(0, var_data.shape[0]*3, 3)  # [0,3,6,9,...]
        labels = [f"{t}-{t+3-1} h" for t in times]
    
        #setting up plot figure
        fig = plt.figure(figsize=(10,4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
    
        #plotting
        ax = fig.add_subplot(gs[0, 0])
        ax.contourf(times,pc,var_data.T)    
    
        #inverting yaxis
        ax.set_ylim(1000, 1) 
    
        #labels
        ax.set_xlabel('Time (hrs)')
        ax.set_ylabel('p ' + r'$(hrs)$')
        # ax.set_ylabel(f"{var_name} {var_units}")
        ax.set_title(f"TZ Contour of {var_name} {var_units} \nERA5 Data on {date_string}")

        #saving plot
        #adding date_string to output folder
        date_folder=strings.DateString(date_string)
        subdir = os.path.join(outputDirectory, date_folder, var_name)
        os.makedirs(subdir, exist_ok=True)
        #saving
        fig.savefig(os.path.join(subdir, f"{var_name}_TZContour_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter
        

    #2. TIME SERIES    
    def TimeSeries(self, var_data, var_name, var_units, date_string):
        #setting up plot figure
        fig = plt.figure(figsize=(10,4))
        gs = gridspec.GridSpec(1, 1, figure=fig)
    
        #plotting
        ax = fig.add_subplot(gs[0, 0])
        ax.plot(numerics.time/3600, var_data, lw=1.5)
    
        #labels
        ax.set_xlabel('Time (hrs)')
        ax.set_ylabel(f"{var_name} {var_units}")
        ax.set_title(f"Time-series of {var_name} {var_units} \nERA5 Data on {date_string}")
    
        # Set xticks every 3 hours
        max_hours = numerics.time[-1]/3600
        ax.set_xticks(np.arange(0, max_hours+1, 3))
    
        #vertical lines
        vline_xinds = np.arange(0, 24*3+1, 24)  # e.g. every 24 hrs
        for x in vline_xinds:
            ax.axvline(x, color='k', linestyle='--', alpha=0.7)
        ax.axvline(24-18,color='blue', linestyle='--', alpha=0.7, label='model start-time')
        
        #other
        fig.tight_layout()
        fig.legend()

        #saving plot
        #adding date_string to output folder
        date_folder=strings.DateString(date_string)
        subdir = os.path.join(outputDirectory, date_folder, var_name)
        os.makedirs(subdir, exist_ok=True)
        #saving
        fig.savefig(os.path.join(subdir, f"{var_name}_TimeSeries_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter
    
    #3. VERTICAL PROFILES
    def MultiAverage_VerticalProfiles(self, var_data,var_name,var_units,date_string):
        #setting up labels
        pc = np.linspace(1000,1,var_data.shape[1])     # vertical levels
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
            ax.plot(var_data[i, :], pc)
    
            #inverting yaxis
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
        #adding date_string to output folder
        date_folder=strings.DateString(date_string)
        subdir = os.path.join(outputDirectory, date_folder, var_name)
        os.makedirs(subdir, exist_ok=True)
        #saving
        fig.savefig(os.path.join(subdir, f"{var_name}_VerticalProfiles_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter

    #4. Horizontal Fields
    def MultiAverage_HorizontalFields(self, var_data, var_name, var_units, date_string, plev, cmap="RdBu_r"):
        """
        Plot horizontal contour maps at a given pressure level for each block in var_data,
        with a single consistent colorbar.
        """
        nblocks, Nz, Ny, Nx = var_data.shape
        pc = np.linspace(1000, 1, Nz)       # pressure coords
        yc = np.arange(0,Ny,1)
        xc = np.arange(0,Nx,1)
        pind = np.argmin(np.abs(pc - plev)) # nearest index
        times = np.arange(0, nblocks*3, 3)  # hours (assuming 3h blocks)
        labels = [f"{t}-{t+3-1} h" for t in times]
    
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
            ax = fig.add_subplot(gs[r, c])
    
            # horizontal slice at given z index
            field = var_data[i, pind, :, :]   # (Ny, Nx)
            cf = ax.contourf(xc,yc,field, cmap=cmap, vmin=vmin, vmax=vmax)
    
            ax.set_title(labels[i], fontsize=12)
            mappable = cf
    
        # one shared colorbar
        cbar = fig.colorbar(mappable, ax=fig.get_axes(), orientation="vertical", shrink=0.6)
        cbar.set_label(f"{var_name} {var_units}")
    
        fig.suptitle(f"Horizontal Fields of {var_name} {var_units} at p={plev} hPa \nERA5 Data on {date_string}")

        #saving plot
        #adding date_string to output folder
        date_folder=strings.DateString(date_string)
        subdir = os.path.join(outputDirectory, date_folder, var_name)
        os.makedirs(subdir, exist_ok=True)
        #saving
        fig.savefig(os.path.join(subdir, f"{var_name}_HorizontalFields_{date_folder}.jpg"))
        plt.close(fig)   # ensures it won’t show up in Jupyter

plotting = Plotting()

