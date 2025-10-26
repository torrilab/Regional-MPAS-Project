#!/usr/bin/env python
# coding: utf-8

# In[2]:


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
    def PNGsToMP4(imageFiles, outputFile, 
                  fps=2, speed=1.0, bitrate='1500k'):
        """
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




