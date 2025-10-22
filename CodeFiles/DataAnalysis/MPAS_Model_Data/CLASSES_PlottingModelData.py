#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# AnimationPlotting_Class 
# (for MPAS Cartesian lat-lon data, converted from original unstructured data using convert_mpas code)
# ============================================================

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from PIL import Image
from moviepy import VideoFileClip, vfx ## pip install moviepy

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
    
        # Load the GIF file
        gif_clip = VideoFileClip(input_file)
    
        # Set the desired framerate if provided
        if fps:
            gif_clip = gif_clip.with_fps(fps)  # <-- updated method name
        if speed != 1.0:
            gif_clip = gif_clip.fx(vfx.speedx, speed)  # < 1 slower, > 1 faster
    
        # Write the GIF as an MP4 file
        gif_clip.write_videofile(output_file, codec="libx264", bitrate=bitrate)

