#!/usr/bin/env python
# coding: utf-8

# In[ ]:

# ============================================================
# FigurePlotting_Class 
# ============================================================

import matplotlib.pyplot as plt

class FigurePlotting_Class:

    #Figure Outputting
    @staticmethod
    def SaveUniformFigure(fig, outputFilePath, target_size=(1500, 500), dpi=100):
        width_in, height_in = target_size[0]/dpi, target_size[1]/dpi
        fig.set_size_inches(width_in, height_in)
        fig.savefig(outputFilePath, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved uniform image: {outputFilePath}")



# In[ ]:


# ============================================================
# AnimationPlotting_Class 
# (for MPAS Cartesian lat-lon data, converted from original unstructured data using convert_mpas code)
# ============================================================

import os
import numpy as np
import matplotlib.pyplot as plt

class AnimationPlotting_Class:
     
    #ANIMATION FUNCTIONS
    @staticmethod
    def CalculateFPS(num_frames, time_interval_minutes, desired_duration_min=1):
        """
        Calculate a reasonable integer FPS (frames per second) for atmospheric animations.
        """
        if num_frames <= 1:
            raise ValueError("Need at least 2 frames for an animation.")
    
        # Compute raw FPS from desired duration
        fps = num_frames / (desired_duration_min*60)
    
        # Clamp FPS to a practical range
        fps = max(1, min(round(fps), 15))  # between 1 and 15 fps
        return int(fps)

    # #EXAMPLE USAGE
    # fps = AnimationPlotting_Class.CalculateFPS(num_frames=ModelData.Ntime, time_interval_minutes=5, desired_duration_min=1)

    @staticmethod
    def CreateAnimation(ModelData, DirectoryManager,
                        outputDirectory, plottingFilePath, GetVariableOutputFile,
                        varName, start_t, end_t,
                        fps=2):
        """
        Create an animation by loading PNG files (pre-made plots) in sequence.
        """
    
        # --- Create figure ---
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis("off")
    
        # --- Collect image paths ---
        image_files = []
        for t in range(start_t, end_t):
            inputFilePath = GetVariableOutputFile(varName, t, ModelData, outputDirectory)
            if os.path.exists(inputFilePath):
                image_files.append(inputFilePath)
            else:
                print(f"Warning: Missing file {inputFilePath}")
    
        if len(image_files) == 0:
            raise FileNotFoundError("No PNG files found in the specified range.")
    
        # --- Sort images by time order (if filenames not already sorted) ---
        image_files.sort()
    
        # --- Load the first image for display initialization ---
        img = Image.open(image_files[0])
        im_plot = ax.imshow(img)
    
        # --- Update function ---
        def update(i):
            if i % 20 == 0:
                print(f"Frame {i+1}/{len(image_files)}")
            img = Image.open(image_files[i])
            im_plot.set_data(img)
            return [im_plot]
    
        # --- Create animation ---
        ani = FuncAnimation(fig, update, frames=len(image_files), interval=1000/fps, blit=True)
    
        # --- Save as GIF ---
        writer = PillowWriter(fps=fps)
        ani.save(plottingFilePath, writer=writer)
        plt.close(fig)
        print(f"Animation saved to: {plottingFilePath}")
   
    # GIF TO MP4 FUNCTION (MoviePy v2.x compatible)
    @staticmethod
    def convertGIFtoMP4(input_file, output_file, fps, speed=1, bitrate='750k'):
        """
        Convert a GIF to MP4 using moviepy.
        """
        from moviepy import VideoFileClip, vfx ## pip install moviepy
        from moviepy.video.fx import MultiplySpeed
    
        # Load the GIF file
        gif_clip = VideoFileClip(input_file)
    
        # Set the desired framerate if provided
        if fps:
            gif_clip = gif_clip.with_fps(fps)  # <-- updated method name
        if speed != 1.0:
            # gif_clip = gif_clip.fx(vfx.speedx, speed) old version
            gif_clip = MultiplySpeed(speed).apply(gif_clip) # < 1 slower, > 1 faster
    
        # Write the GIF as an MP4 file
        gif_clip.write_videofile(output_file, codec="libx264", bitrate=bitrate)

        gif_clip.close()
    
    @staticmethod
    def PNGsToMP4(imageFiles, outputFile, 
                  fps=2, speed=1.0, bitrate='1500k'):
        """
        ***NEWEST METHOD (RECOMMENDED)***
        Convert a sequence of PNG images directly to a widely compatible MP4,
        automatically resizing and ensuring even frame dimensions.
        """
        import os
        from PIL import Image
        from moviepy import ImageSequenceClip
        from moviepy.video.fx import MultiplySpeed
    
        if not imageFiles:
            raise ValueError("No image files provided for MP4 conversion.")
    
        # --- Get target size from first image ---
        w, h = Image.open(imageFiles[0]).size
    
        # --- Round width and height to even numbers (required by libx264) ---
        if w % 2 != 0:
            w += 1
        if h % 2 != 0:
            h += 1
    
        uniform_images = []
    
        # --- Ensure all images match the even target size ---
        for img_path in imageFiles:
            with Image.open(img_path) as im:
                if im.size != (w, h):
                    resized = im.resize((w, h), Image.Resampling.LANCZOS)
                    tmp_path = img_path.replace(".png", "_tmp.png")
                    resized.save(tmp_path)
                    uniform_images.append(tmp_path)
                else:
                    uniform_images.append(img_path)
    
        # --- Create video clip ---
        clip = ImageSequenceClip(uniform_images, fps=fps)
    
        # --- Adjust playback speed if needed ---
        if speed != 1.0:
            clip = MultiplySpeed(speed).apply(clip)
    
        # --- Export to MP4 ---
        clip.write_videofile(
            outputFile,
            codec="libx264",
            bitrate=bitrate,
            audio=False,
            ffmpeg_params=[
                "-pix_fmt", "yuv420p",
                "-profile:v", "main",
                "-movflags", "+faststart"
            ],
            preset="medium",
            threads=4
        )
        clip.close()
    
        print(f"MP4 saved to: {outputFile} (fps={fps}, speed={speed}, size={w}x{h})")
    
        # --- Clean up temporary resized PNGs ---
        tmp_files = [f for f in uniform_images if f.endswith("_tmp.png")]
        for tmp in tmp_files:
            try:
                os.remove(tmp)
            except Exception as e:
                print(f"Warning: could not remove temp file {tmp}: {e}")

    # #EXAMPLE USAGE
    # AnimationPlotting_Class.PNGsToMP4(imageFiles, outputFile, fps=fps)
   
    # # GIF TO MP4 FUNCTION (MoviePy v2.x compatible)
    # @staticmethod
    # def convertGIFtoMP4(input_file, output_file, fps, speed=1, bitrate='750k'):
    #     """
    #     Convert a GIF to MP4 using moviepy.
    #     """
    #     from moviepy import VideoFileClip, vfx ## pip install moviepy
    #     from moviepy.video.fx import MultiplySpeed
    
    #     # Load the GIF file
    #     gif_clip = VideoFileClip(input_file)
    
    #     # Set the desired framerate if provided
    #     if fps:
    #         gif_clip = gif_clip.with_fps(fps)  # <-- updated method name
    #     if speed != 1.0:
    #         # gif_clip = gif_clip.fx(vfx.speedx, speed) old version
    #         gif_clip = MultiplySpeed(speed).apply(gif_clip) # < 1 slower, > 1 faster
    
    #     # Write the GIF as an MP4 file
    #     gif_clip.write_videofile(output_file, codec="libx264", bitrate=bitrate)

    #     gif_clip.close()

# #EXAMPLE LOADING
# sys.path.append(os.path.join(mainCodeDirectory,"1_Initial_Figures","Animations"))
# import CLASSES_AnimationPlotting
# from CLASSES_AnimationPlotting import AnimationPlotting_Class


# In[ ]:


# ============================================================
# RadarPlotting_Class 
# ============================================================

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

class RadarPlotting_Class:

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

# #EXAMPLE IMPORTING
# #Importing PlottingModelData Class
# sys.path.append(os.path.join(DirectoryManager.mainCodeDirectory,"DataAnalysis","MPAS_Model_Data"))
# from CLASSES_PlottingModelData import RadarPlotting_Class
        
# #EXAMPLE USAGE
# cmap, norm, levels, ticks = RadarPlotting_Class.GetReflectivityColormap()

# plot = axis.contourf(time, pressure_profile, output.T, 
#                     levels=levels, cmap=cmap, norm=norm, 
#                     extend='both') #contour plot
# cbar = axis.figure.colorbar(plot, ax=axis, pad=0.18, orientation='vertical')
# RadarPlotting_Class.FormatReflectivityColorbar(cbar, ticks, orientation='vertical', show_labels=True)

