#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
====================================================
PlottingFunctions
====================================================
"""


# In[ ]:


#IMPORTING NECESSARY LIBRARIES
import numpy as np
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.ticker as ticker
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import ScalarFormatter
import matplotlib.gridspec as gridspec


# In[4]:


# # #TESTING
# # ######################################
# dir='/mnt/lustre/koa/koastore/torri_group/air_directory/DCI-Project/'
# data=xr.open_dataset(dir+'../cm1r20.3/run/cm1out_test7tundra-7_062217.nc') #***
# f=data['w'].interp(zf=data['zh']).data


# In[12]:


def VertContour(f, units, xax, ax=None, ny=None, nx=None):
    # Create an axis if one is not provided
    if ax is None:
        fig, ax = plt.subplots()
    if ny is None: ny=2

    # Plot the contour on the specified axis
    if xax=='t':
        c = ax.contourf(f.T);
    else:
        c = ax.contourf(f);

    # Scientific Notation
    if units == "sci":
        from matplotlib.ticker import ScalarFormatter
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((-3, 3))
        ax.xaxis.set_major_formatter(formatter)

    # Set labels
    if xax=='t':
        if nx is None: nx=1
        ax.set_xlabel('time')
    elif xax=='y':
        ax.set_xlabel('y (km)')
    elif xax=='x':
        ax.set_xlabel('x (km)')

    # Fixing Vertical Ticks
    tick_inds = np.arange(0, len(data['zh'].values), ny)
    ax.set_yticks(tick_inds)
    ax.set_yticklabels(np.round(data['zh'].values[tick_inds], 1))

    if xax=='y':
        if nx is None: nx=5
        tick_inds = np.arange(0, len(data['yh'].values), nx)
        ax.set_xticks(tick_inds)
        ax.set_xticklabels(np.round(data['yh'].values[tick_inds], 1))
        
    elif xax=='x':
        if nx is None: nx=60
        tick_inds = np.arange(0, len(data['xh'].values), nx)
        ax.set_xticks(tick_inds)
        ax.set_xticklabels(np.round(data['xh'].values[tick_inds], 1))
        
    # plt.close(fig)
    return ax
        
def HorizContour(f, units, ax=None, nx=None, ny=None):
    # Create an axis if one is not provided
    if ax is None:
        fig, ax = plt.subplots()
    if nx is None: nx=60
    if ny is None: ny=5

    # Plot the contour on the specified axis
    c = ax.contourf(f);

    # Scientific Notation
    if units == "sci":
        from matplotlib.ticker import ScalarFormatter
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((-3, 3))
        ax.xaxis.set_major_formatter(formatter)

    # Set labels
    ax.set_xlabel('x (km)')
    ax.set_ylabel('y (km)')

    # Fixing Horizontal Ticks
    tick_inds = np.arange(0, len(data['xh'].values), nx)
    ax.set_xticks(tick_inds)
    ax.set_xticklabels(np.round(data['xh'].values[tick_inds], 1))
    
    tick_inds = np.arange(0, len(data['yh'].values), ny)
    ax.set_yticks(tick_inds)
    ax.set_yticklabels(np.round(data['yh'].values[tick_inds], 1))
    
    # plt.close(fig)
    return ax


# In[258]:


# #TESTING
# ######################################
# VertContour(f[:,:,10,10], units="sci", xax='t')
# VertContour(f[10,:,:,10], units="sci", xax='y',nx=10)
# VertContour(f[10,:,10,:], units="sci", xax='x')
# HorizContour(f[10,10,:,:], units="sci")


# In[221]:


# #How To Plot Multiple GridSpec Subplots
# fig = plt.figure(figsize=(10, 5))
# gs = gridspec.GridSpec(1, 2, figure=fig)

# # Create first subplot
# ax1 = fig.add_subplot(gs[0, 0])
# VertContour(f[:,:,10,10], units="sci", ax=ax1)

# # Create second subplot
# ax2 = fig.add_subplot(gs[0, 1])
# VertContour(f[:,:,10,10], units="sci", ax=ax2)


# In[258]:


# #TESTING
# ######################################
# VertContour(f[:,:,10,10], units="sci", xax='t')
# VertContour(f[10,:,:,10], units="sci", xax='y',nx=10)
# VertContour(f[10,:,10,:], units="sci", xax='x')
# HorizContour(f[10,10,:,:], units="sci")


# In[221]:


# #How To Plot Multiple GridSpec Subplots
# fig = plt.figure(figsize=(10, 5))
# gs = gridspec.GridSpec(1, 2, figure=fig)

# # Create first subplot
# ax1 = fig.add_subplot(gs[0, 0])
# VertContour(f[:,:,10,10], units="sci", ax=ax1)

# # Create second subplot
# ax2 = fig.add_subplot(gs[0, 1])
# VertContour(f[:,:,10,10], units="sci", ax=ax2)


# In[ ]:


#TIME 00:00:00 Function
#Gets the realtime for the current timestep
def get_time(data,t,init):
    (init_day,init_hour,init_min)=init[0],init[1],init[2]
    times=data['time'].values/(1e9 * 60); time_inc=times.astype(int)[1]-times.astype(int)[0]
    current_min=init_hour*60+init_min+time_inc*t;
    
    days = init_day + (current_min // (24 * 60))
    
    remain_min = (init_min+time_inc*t) % (24 * 60); 
    hours = (init_hour + (remain_min // 60)) % 24
    mins = remain_min % 60

    ##############################################
    days=str(days);hours=str(hours);mins=str(mins)
    if len(days)==1:days='0'+days
    if len(hours)==1:hours='0'+hours
    if len(mins)==1:mins='0'+mins
    ##############################################

    combo=days+":"+hours+":"+mins
    return(days,hours,mins),(combo)


# In[ ]:


#ANIMATION FUNCTION
#MUST CREATE A SINGLE TIME PLOTTING FUNCTION TITLED single_plot(args) 

from matplotlib.animation import FuncAnimation, PillowWriter
def create_animation(start_t, end_t, output_file, vmin_max_values, fps=2):
    # Create a figure each time for the animation
    fig = plt.figure(figsize=(18, 25))

    # Define the update function for the animation
    def update(t):
        plt.clf()  # Clear the current figure
        if np.mod(t, 20) == 0:
            print(f'current t: {t}')
        single_plot(fig, t, vmin_max_values)  # Pass the figure and vmin_max_values to single_plot

    # Create the animation object
    ani = FuncAnimation(fig, update, frames=np.arange(start_t, end_t), repeat=False)

    # Save the animation as a GIF file using PillowWriter
    writer = PillowWriter(fps=fps)
    ani.save(output_file, writer=writer)


# In[ ]:


def convert_gif_to_mp4(input_file, output_file, fps,speed,bitrate='750k'):
    from moviepy.editor import VideoFileClip, vfx
    # Load the GIF file
    gif_clip = VideoFileClip(input_file)

    # Set the desired framerate if provided
    if fps:
        gif_clip = gif_clip.set_fps(fps)
    if speed != 1.0:
        gif_clip = gif_clip.fx(vfx.speedx, speed)

    # Write the GIF as an MP4 file
    gif_clip.write_videofile(output_file, codec="libx264",bitrate=bitrate)

# # Example usage:
# input_filename = dir3+f'Animations/animation.gif'
# output_filename = dir3+f'Animations/animation.mp4'
# convert_gif_to_mp4(input_filename, output_filename, fps=None,speed=2,bitrate='750k')  # Optional fps argument


# In[ ]:





# In[1]:


#USEFUL VERTICAL PROFILE PLOTTING FUNCTIONS
# def apply_scientific_notation(axes, use_math_text=True, power_limits=(-1, 1)): #OLD VERSION
#     #Provide Axises in terms of [ax1,ax2,...]
#     from matplotlib.ticker import ScalarFormatter
#     for axis in axes:
#         formatter = ScalarFormatter(useMathText=use_math_text)
#         formatter.set_scientific(True)
#         formatter.set_powerlimits(power_limits)
#         axis.xaxis.set_major_formatter(formatter)

from matplotlib.ticker import ScalarFormatter
class RoundedScalarFormatter(ScalarFormatter):
    def __init__(self, decimals=2, useMathText=True, powerlimits=(-1, 1), scientific=True):
        super().__init__(useMathText=useMathText)
        self.decimals = decimals
        self.set_scientific(scientific)
        self.set_powerlimits(powerlimits)
        self.set_useOffset(False)

    def _set_format(self):
        self.format = f"%.{self.decimals}f"


def apply_scientific_notation(axes, dim='x', use_math_text=True, power_limits=(-1, 1), decimals=2, scientific=True):
    """
    Apply scientific notation with mantissas rounded to a fixed number of decimals.
    """
    for axis in axes:
        formatter = RoundedScalarFormatter(
            decimals=decimals,
            useMathText=use_math_text,
            powerlimits=power_limits,
            scientific=scientific
        )
        if dim == 'x':
            axis.xaxis.set_major_formatter(formatter)
        elif dim == 'y':
            axis.yaxis.set_major_formatter(formatter)

# def apply_scientific_notation_colorbar(cbars):
#     from matplotlib.ticker import ScalarFormatter
#     formatter = ScalarFormatter(useMathText=True)
#     formatter.set_powerlimits((-2, 2))  # Adjust the range for scientific notation
#     for cbar in cbars:  # These must be Colorbar instances
#         cbar.formatter = formatter
#         cbar.update_ticks()

def apply_scientific_notation_colorbar(cbars, 
                                       use_math_text=True, 
                                       power_limits=(-2, 2), decimals=2, scientific=True):
    for cbar in cbars:
        formatter = RoundedScalarFormatter(
            decimals=decimals,
            useMathText=use_math_text,
            powerlimits=power_limits,
            scientific=scientific
        )
        cbar.formatter = formatter
        cbar.update_ticks()

#Makes ticks flush to figure boundaries (recommended)
def SnapLimitsToTicks(axes, dim="x"):
    from matplotlib.ticker import AutoLocator
    """
    Snap axis limits to the nearest ticks that enclose the visible data.
    Ignores helper lines (axhline, axvline, etc.) by ignoring lines with <= 2 points (better to run helper lines afterwards). 
    """
    for ax in axes:
        if dim == "x":
            ymin, ymax = ax.get_ylim()
            xs = []
            for line in ax.get_lines():
                xdata = np.asarray(line.get_xdata())
                ydata = np.asarray(line.get_ydata())
                # Skip constant or very short lines (axvline, etc.)
                if len(np.unique(xdata)) <= 2 or len(np.unique(ydata)) <= 2:
                    continue
                mask = (ydata >= ymin) & (ydata <= ymax)
                xs.extend(xdata[mask])
            # --- include fill_betweenx (PolyCollection) data ---
            for coll in ax.collections:
                for path in coll.get_paths():
                    coords = path.vertices
                    ymask = (coords[:, 1] >= ymin) & (coords[:, 1] <= ymax)
                    xs.extend(coords[:, 0][ymask])

            lo, hi = (min(xs), max(xs)) if xs else ax.dataLim.intervalx
     
            locator = AutoLocator()
            ticks = locator.tick_values(lo, hi)

            lo_tick = ticks[ticks <= lo][-1]
            hi_tick = ticks[ticks >= hi][0]
            ax.set_xlim(lo_tick, hi_tick)

        else:  # y case
            xmin, xmax = ax.get_xlim()
            ys = []
            for line in ax.get_lines():
                xdata = np.asarray(line.get_xdata())
                ydata = np.asarray(line.get_ydata())
                if len(np.unique(xdata)) <= 2 or len(np.unique(ydata)) <= 2:
                    continue
                mask = (xdata >= xmin) & (xdata <= xmax)
                ys.extend(ydata[mask])
            # --- include fill_betweenx (PolyCollection) data ---  
            for coll in ax.collections:
                for path in coll.get_paths():
                    coords = path.vertices
                    xmask = (coords[:, 0] >= xmin) & (coords[:, 0] <= xmax)
                    ys.extend(coords[:, 1][xmask])
            lo, hi = (min(ys), max(ys)) if ys else ax.dataLim.intervaly

            locator = AutoLocator()
            ticks = locator.tick_values(lo, hi)

            lo_tick = ticks[ticks <= lo][-1]
            hi_tick = ticks[ticks >= hi][0]
            ax.set_ylim(lo_tick, hi_tick)

def SetEvenTicks(axes, dim="x", n_ticks=4, decimals=1, pad_frac=0.05):
    """
    Set evenly spaced ticks spanning current axis limits.
    Ensures at least two distinct ticks even for near-zero ranges.
    """
    if not isinstance(axes, (list, tuple, np.ndarray)):
        axes = [axes]

    for ax in axes:
        if dim == "x":
            lo, hi = ax.get_xlim()
        else:
            lo, hi = ax.get_ylim()

        # --- handle flat or extremely narrow ranges ---
        span = hi - lo
        if np.isclose(span, 0) or span < 1e-12:
            pad = max(abs(lo) * pad_frac, pad_frac)
            lo, hi = lo - pad, hi + pad
            span = hi - lo

        # --- compute ticks without rounding first ---
        ticks = np.linspace(lo, hi, n_ticks)

        # avoid collapse after rounding
        ticks_rounded = np.round(ticks, decimals)
        if len(np.unique(ticks_rounded)) < 2:
            # fallback to higher precision if all identical after rounding
            ticks_rounded = np.round(ticks, decimals + 2)

        if dim == "x":
            ax.set_xticks(ticks_rounded)
        else:
            ax.set_yticks(ticks_rounded)


# In[3]:


def fix_tick_labels(axises, data, data_dim, tick_axis, d_xtick, d_ytick, cell_loc, round, meters):
    """
    inputs:
    axises: [ax] or [ax1,ax2,...]
    data: NC datafile (function needs to edited for different data variable conventions)

    data_dim: which dimension is the ticks for ('x','y', or 'z')
    tick_axis: which figure axis is the ticks for ('x','y', or 'z')
    
    d_xtick, d_ytick: controls the spacing between each tick (only one needs to be set at a time)
    
    cell_loc: is the variable stored on cell centers ('center') or cell face ('face')
    round: how many decimal points to round to
    meters: if (True), all ticks are multiplied by 1000 (km ==> m)
    
    """
    
    # PLOT MUST BE IN AXIS FORM
    # AXISES MUST BE STORED IN A LIST []
    for axis in axises:  # ex: axises=[ax1, ax2, ax3, ax4, ax5, ax6]

        # #if data on cell face
        if data_dim == 'x':
            if cell_loc=='center':
                zh = (data['xh']-data['xh'][0]).values
            elif cell_loc=='face':
                zh = (data['xf']-data['xf'][0]).values
        elif data_dim == 'y':
            if cell_loc=='center':
                zh = data['yh'].values
            elif cell_loc=='face':
                zh = data['yf'].values
        elif data_dim == 'z':
            if cell_loc=='center':
                zh = data['zh'].values
            elif cell_loc=='face':
                zh = data['zf'].values
        elif data_dim == 't':
            zh = data['time'].values.astype('timedelta64[m]').astype(int)
        
        # Set tick locator to control number of ticks
        if tick_axis == 'x': 
            # num_xticks=len(zh)/d_xtick
            x_min = min(zh); x_max = max(zh)
            num_xticks = int((x_max - x_min) / 100) + 1
            # axis.xaxis.set_major_locator(ticker.MaxNLocator(nbins=num_xticks))
            axis.xaxis.set_major_locator(ticker.LinearLocator(int(num_xticks)))  # Ensures exact number of ticks
        elif tick_axis == 'y':
            num_yticks=len(zh)/d_ytick
            # axis.yaxis.set_major_locator(ticker.MaxNLocator(nbins=num_yticks))
            axis.yaxis.set_major_locator(ticker.LinearLocator(int(num_yticks)))  # Ensures exact number of ticks

        ticks = axis.get_xticks() if tick_axis == 'x' else axis.get_yticks()

        # Convert tick positions to integer indices

        tick_indices = ticks.astype(int)
        valid_mask = (tick_indices >= 0) & (tick_indices < len(zh))
    
        # Filter valid tick positions and corresponding labels
        filtered_ticks = ticks[valid_mask]

        if meters==True:
            filtered_tick_labels = [f'{zh[i]*1000:.{round}f}' for i in tick_indices[valid_mask]]
        elif meters==False:
            filtered_tick_labels = [f'{zh[i]:.{round}f}' for i in tick_indices[valid_mask]]
    
        # Apply only valid ticks and labels
        if tick_axis == 'x':
            axis.set_xticks(filtered_ticks)
            axis.set_xticklabels(filtered_tick_labels)
        elif tick_axis == 'y':
            axis.set_yticks(filtered_ticks)
            axis.set_yticklabels(filtered_tick_labels)
        elif tick_axis == 'z':
            axis.set_yticks(filtered_ticks)
            axis.set_yticklabels(filtered_tick_labels)
# # # EXAMPLE RUN
# # FOR X TICKS
# ax = plt.gca()
# fix_tick_labels([ax], data, data_dim='x', tick_axis='x', d_xtick=32, d_ytick=20, cell_loc='center',round=1,meters=False)  # apply 
# # FOR Z TICKS
# ax = plt.gca()
# fix_tick_labels([ax], data, data_dim='z', tick_axis='y', d_xtick=10, d_ytick=2, cell_loc='center',round=2,meters=False)  # apply 


# In[ ]:


def fix_x_limits(axes):
    #Bounds all plots by min and max of the current xlims, so all subplots match
    #Provide Axises in terms of [ax1,ax2,...]
    
    # Collect x-limits from all axes
    xlims = [axis.get_xlim() for axis in axes]
    mins = [xlim[0] for xlim in xlims]
    maxes = [xlim[1] for xlim in xlims]
    
    # Find the total min and max
    total_min = min(mins)
    total_max = max(maxes)
    result = (total_min, total_max)
    print(result)
    
    # Set the same x-limits for all axes
    for axis in axes:
        axis.set_xlim(result)

def fix_y_limits(axes):
    #Bounds all plots by min and max of the current ylims, so all subplots match
    #Provide Axises in terms of [ax1,ax2,...]
    
    # Collect x-limits from all axes
    xlims = [axis.get_ylim() for axis in axes]
    mins = [xlim[0] for xlim in xlims]
    maxes = [xlim[1] for xlim in xlims]
    
    # Find the total min and max
    total_min = min(mins)
    total_max = max(maxes)
    result = (total_min, total_max)
    print(result)
    
    # Set the same x-limits for all axes
    for axis in axes:
        axis.set_ylim(result)
        
def MatchAxisLimits(axes, dim='x'):
    """
    Find the axis whose tick bounds span all others,
    then copy its ticks and limits to every axis in the list.
    """
    lo_vals, hi_vals = [], []

    # Collect bounds
    for ax in axes:
        ticks = ax.get_xticks() if dim == 'x' else ax.get_yticks()
        if len(ticks) > 1:
            lo_vals.append(ticks[0])
            hi_vals.append(ticks[-1])

    if not lo_vals or not hi_vals:
        return None

    lo, hi = min(lo_vals), max(hi_vals)

    # Find reference axis
    ref_ax = next(
        (ax for ax in axes
         if len((ticks := (ax.get_xticks() if dim == 'x' else ax.get_yticks()))) > 1
         and ticks[0] == lo and ticks[-1] == hi),
        None
    )
    if ref_ax is None:
        return None  # no reference axis found

    # Extract ticks and limits from reference
    ref_ticks = ref_ax.get_xticks() if dim == 'x' else ref_ax.get_yticks()
    ref_lim   = ref_ax.get_xlim() if dim == 'x' else ref_ax.get_ylim()

    # Apply to all axes
    for ax in axes:
        if dim == 'x':
            ax.set_xlim(ref_lim)
            ax.set_xticks(ref_ticks)
        else:
            ax.set_ylim(ref_lim)
            ax.set_yticks(ref_ticks)

    return ref_ax


# In[3]:


# ## Converts all figures to PDF
# ######################################################################################################################################################
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from PIL import Image
# import os

# def jpg_to_pdf(input_folder, output_pdf):
#     # Get a list of all JPG files in the input folder
#     jpg_files = [file for file in os.listdir(input_folder) if file.endswith('.jpg')]
#     jpg_files = ['domain_config.jpg','convergence.jpg','verticalu.jpg',
#                  'verticaltheta.jpg','verticalprspert.jpg','verticaltheta.jpg',
#                  'verticalwatervapor.jpg','horizontalw-u.jpg'] #***
    
#     # Create a PDF canvas
#     c = canvas.Canvas(output_pdf, pagesize=letter)

#     # Loop through each JPG file and add it to the PDF
#     for jpg_file in jpg_files:
#         # Open the JPG image using PIL
#         img = Image.open(os.path.join(input_folder, jpg_file))

#         # Calculate the aspect ratio to maintain image proportions
#         width, height = img.size
#         aspect_ratio = width / height

#         # Add the image to the PDF
#         c.setPageSize((width, height))
#         c.drawInlineImage(os.path.join(input_folder, jpg_file), 0, 0, width=width, height=height)

#         # Add a new page for the next image
#         c.showPage()

#     # Save the PDF
#     c.save()

# # # Example usage:
# # input_folder = folder_path
# # output_pdf = folder_path + f'figures_062217_{res}.pdf'
# # jpg_to_pdf(input_folder, output_pdf)


# In[2]:


import numpy as np
import matplotlib.pyplot as plt

# === Function ===
def UltimateContourPlot(
    ax, PlotData, xTickLabels, yTickLabels,
    contour_type=None,
    num_xticks=None, round_xticks=None, xTickInterval=None,
    num_yticks=None, round_yticks=None, yTickInterval=None,
    add_colorbar=False, fig=None, colorbar_label=None, colorbar_label_rotation=90,
    xlabel=None, ylabel=None, 
    solid_contour_labels=None,solid_contour_round=None,
    xtick_rotation=None,ytick_rotation=None,cbar_rotation=None,
    save_path=None, save_dpi=300,
    colorbar_kwargs=None,
    **kwargs,
):
    
    if contour_type=='line':
        contour = ax.contour(xTickLabels, yTickLabels, PlotData, **kwargs)
        if solid_contour_labels==True:
            fmt_num = solid_contour_round if solid_contour_round is not None else 1
            plt.clabel(contour, inline=True, fontsize=8, fmt=f"%.{fmt_num}f")
    elif contour_type=='fill':
        contour = ax.contourf(xTickLabels, yTickLabels, PlotData, **kwargs)
    # Colorbar
    cbar=None
    if add_colorbar and fig is not None:
        if colorbar_kwargs is None:
            colorbar_kwargs = {}
        cbar = fig.colorbar(contour, ax=ax, **colorbar_kwargs)
        if colorbar_label:
            cbar.set_label(colorbar_label)
            cbar.ax.yaxis.label.set_rotation(colorbar_label_rotation)
        if cbar_rotation is not None:
            for tick in cbar.ax.get_yticklabels():
                tick.set_rotation(cbar_rotatizon)

    # X-ticks
    if num_xticks is not None:
        if xTickInterval is not None:
            xticks = np.arange(0, x.max()+1, xTickInterval)
        else:
            xticks = np.linspace(xTickLabels.min(), xTickLabels.max(), num_xticks)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticks)
        if round_xticks is not None:
            ax.set_xticklabels([f"{tick:.{round_xticks}f}" for tick in xticks])

    # Y-ticks
    if num_yticks is not None:
        if yTickInterval is not None:
            yticks = np.arange(0, y.max()+1, yTickInterval)
        else:
            yticks = np.linspace(yTickLabels.min(), yTickLabels.max(), num_yticks)
        ax.set_yticks(yticks)
        if round_yticks is not None:
            ax.set_yticklabels([f"{tick:.{round_yticks}f}" for tick in yticks])

    # Axis labels
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    # Tick Rotation
    if xtick_rotation is not None:
        plt.setp(ax.get_xticklabels(), rotation=xtick_rotation)
    if ytick_rotation is not None:
        plt.setp(ax.get_yticklabels(), rotation=ytick_rotation)
        
    # Single Figure Saving
    if save_path is not None:
        if fig is None:
            fig = ax.figure
        fig.savefig(save_path, dpi=save_dpi)
    return contour,cbar


# In[ ]:


# #ADVANCED EXAMPLE (data not available)

# #NEW PLOTTING METHOD


# ######
# cmap1 = plt.cm.viridis
# cmap2 = plt.cm.seismic 
# n_levels=29
# ######

# ######
# vmax_shared = np.max([np.max(profile_array_e), np.max(profile_array_d)])
# norm_shared = mcolors.Normalize(vmin=0, vmax=vmax_shared)
# norm_shared = None #COMMENT OUT IF COLORBARS SHOULD BE SHARED
# ######

# # === Create figure and subplots ===
# # fig, axs = plt.subplots(2, 2, figsize=(15, 10))
# fig = plt.figure(figsize=(10, 8))
# from matplotlib.gridspec import GridSpec
# gs = GridSpec(2, 2, figure=fig)
# ax1 = fig.add_subplot(gs[0, 0])
# ax2 = fig.add_subplot(gs[0, 1])
# ax3 = fig.add_subplot(gs[1, 0])

# # === Base Plot configuration parameters ===
# plot_kwargs = {
#     'PlotData': None, #THIS MUST BE SET SOMEWHERE
#     'xTickLabels': None, 'yTickLabels': None, #THESE MUST BE SET SOMEWHERE
#     'contour_type': 'fill',
#     'num_xticks': 10,'round_xticks': 0, 'xTickInterval': 100,
#     'num_yticks': 15,'round_yticks': 2, 'yTickInterval': None,
#     'add_colorbar': True,'fig': fig, 'levels': 29, 'colorbar_label_rotation': 0, 'colorbar_label': None,
#     'xlabel': "t (timesteps)", 'ylabel': "z (km)",
#     'solid_contour_labels': True, 'solid_contour_round': None,
#     'xtick_rotation': 0, 'ytick_rotation': 0, 'cbar_rotation': 0,
#     'save_path': None, 'save_dpi': 300,
#     'colorbar_kwargs': {
#             'extend': 'both'
#         },

#     'norm': norm_shared
# }

# # === Plot 1 ===
# plot_data1 = profile_array_e.copy().T
# plot_data1[plot_data1==0]=np.nan
# y = data['zh'].data  # len 95
# x = np.arange(profile_array_e.shape[0])  # len 661
# plot_kwargs['xTickLabels'] = x
# plot_kwargs['yTickLabels'] = y

# plot_kwargs1 = plot_kwargs.copy()
# plot_kwargs1['PlotData'] = plot_data1
# plot_kwargs1['cmap'] = cmap1
# [contour1,cbar1]=UltimateContourPlot(ax1, **plot_kwargs1)
# ax1.set_ylim(0,20)
# ax1.set_title('Entrainment')

# # # === Plot 2 ===
# plot_data2 = profile_array_d.copy().T

# plot_data2[plot_data2==0]=np.nan
# plot_kwargs2 = plot_kwargs.copy()
# plot_kwargs2['PlotData'] = plot_data2
# plot_kwargs2['cmap'] = cmap1
# [contour2,cbar2]=UltimateContourPlot(ax2, **plot_kwargs2)
# ax2.set_ylim(0,20)
# ax2.set_title('Detrainment')

# # # === Plot 3 ===
# plot_data3 = profile_array_net.copy().T
# #######################################
# vmin=-np.max(abs(profile_array_net))/2; vmax=+np.max(abs(profile_array_net))
# percentile_vminmax=False
# if percentile_vminmax==True:
#     ####
#     vmin = np.percentile(profile_array_net[profile_array_net<0], 1)
#     vmax = np.percentile(profile_array_net[profile_array_net>0], 99)
#     ####    
# levels = np.linspace(vmin, vmax, n_levels)
# norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=256)
# #######################################

# plot_data3[plot_data3==0]=np.nan
# plot_kwargs3 = plot_kwargs.copy()
# plot_kwargs3['PlotData'] = plot_data3
# plot_kwargs3['cmap'] = cmap2
# plot_kwargs3['norm'] = norm
# plot_kwargs3['levels'] = levels
# [contour3,cbar3]=UltimateContourPlot(ax3, **plot_kwargs3)
# ax3.set_ylim(0,20)
# ax3.set_title('Net Entrainment')



# ################################################################################
# #TIGHT PLOTTING LAYOUT
# plt.tight_layout()
# #APPLY SCIENTIFIC NOTATION
# def apply_scientific_notation_colorbar(cbars):
#     from matplotlib.ticker import ScalarFormatter
#     formatter = ScalarFormatter(useMathText=True)
#     formatter.set_powerlimits((-2, 2))  # Adjust the range for scientific notation
#     for cbar in cbars:  # These must be Colorbar instances
#         cbar.formatter = formatter
#         cbar.update_ticks()
# apply_scientific_notation_colorbar([cbar1,cbar2,cbar3])

