#!/usr/bin/env python
# coding: utf-8

# In[1]:


# ============================================================
# AnimationPlotting_Class 
# (for MPAS Cartesian lat-lon data, converted from original unstructured data using convert_mpas code)
# ============================================================

import os
import numpy as np
import matplotlib.pyplot as plt

class AnimationPlotting_Class:
     
    # ANIMATION FUNCTIONS
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
    # fps = AnimationPlotting_Class.CalculateFPS(num_frames=ModelData.Ntime, time_interval_minutes=15, desired_duration_min=1)

    # @staticmethod
    # def CreateAnimation(ModelData, DirectoryManager,
    #                     outputDirectory, plottingFilePath, GetVariableOutputFile,
    #                     varName, start_t, end_t,
    #                     fps=2): #VERY SLOW
    #     """
    #     Create an animation by loading PNG files (pre-made plots) in sequence.
    #     """
    
    #     # --- Create figure ---
    #     fig, ax = plt.subplots(figsize=(12, 8))
    #     ax.axis("off")
    
    #     # --- Collect image paths ---
    #     image_files = []
    #     for t in range(start_t, end_t):
    #         inputFilePath = GetVariableOutputFile(varName, t, ModelData, outputDirectory)
    #         if os.path.exists(inputFilePath):
    #             image_files.append(inputFilePath)
    #         else:
    #             print(f"Warning: Missing file {inputFilePath}")
    
    #     if len(image_files) == 0:
    #         raise FileNotFoundError("No PNG files found in the specified range.")
    
    #     # --- Sort images by time order (if filenames not already sorted) ---
    #     image_files.sort()
    
    #     # --- Load the first image for display initialization ---
    #     img = Image.open(image_files[0])
    #     im_plot = ax.imshow(img)
    
    #     # --- Update function ---
    #     def update(i):
    #         if i % 20 == 0:
    #             print(f"Frame {i+1}/{len(image_files)}")
    #         img = Image.open(image_files[i])
    #         im_plot.set_data(img)
    #         return [im_plot]
    
    #     # --- Create animation ---
    #     ani = FuncAnimation(fig, update, frames=len(image_files), interval=1000/fps, blit=True)
    
    #     # --- Save as GIF ---
    #     writer = PillowWriter(fps=fps)
    #     ani.save(plottingFilePath, writer=writer)
    #     plt.close(fig)
    #     print(f"Animation saved to: {plottingFilePath}")

    # @staticmethod
    # def PNGsToGIF(image_files, outputFilePath, fps=2, duration_override=None): #VERY SLOW
    #     """
    #     Create a GIF from a list of PNG images using Pillow with minimal memory usage.
        
    #     Uses a generator to avoid loading all images into memory.
    #     """
    #     from PIL import Image
    #     import os
    
    #     if len(image_files) == 0:
    #         raise ValueError("No image files provided for GIF creation.")
    
    #     image_files.sort()
    
    #     # Duration per frame in milliseconds
    #     duration = duration_override if duration_override is not None else int(1000 / fps)
    
    #     # Open the first image
    #     with Image.open(image_files[0]) as im:
    #         im = im.convert("RGB")  # Ensure proper format
            
    #         def frame_generator():
    #             for img_path in image_files[1:]:
    #                 with Image.open(img_path) as frame:
    #                     yield frame.convert("RGB")
    
    #         # Save GIF with streamed frames
    #         im.save(
    #             outputFilePath,
    #             save_all=True,
    #             append_images=frame_generator(),
    #             duration=duration,
    #             loop=0,
    #             optimize=False  # Optimize uses more memory
    #         )
    
    #     print(f"GIF saved to: {outputFilePath} (fps={fps}, duration={duration} ms)")

    # # GIF TO MP4 FUNCTION (MoviePy v2.x compatible)
    # @staticmethod
    # def convertGIFtoMP4(input_file, output_file, fps, speed=1, bitrate='750k'):
    #     """
    #     Convert a GIF to MP4 using moviepy.
    #     """
    
    #     # Load the GIF file
    #     gif_clip = VideoFileClip(input_file)
    
    #     # Set the desired framerate if provided
    #     if fps:
    #         gif_clip = gif_clip.with_fps(fps)  # <-- updated method name
    #     if speed != 1.0:
    #         gif_clip = gif_clip.fx(vfx.speedx, speed)  # < 1 slower, > 1 faster
    
    #     # Write the GIF as an MP4 file
    #     gif_clip.write_videofile(output_file, codec="libx264", bitrate=bitrate)
    
    @staticmethod
    def SaveUniformFigure(fig, outputFilePath, target_size=(1500, 500), dpi=100):
        width_in, height_in = target_size[0]/dpi, target_size[1]/dpi
        fig.set_size_inches(width_in, height_in)
        fig.savefig(outputFilePath, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved uniform image: {outputFilePath}")
    
    @staticmethod
    def PNGsToMP4(imageFiles, outputFile, 
                  fps=2, speed=1.0, bitrate='1500k', resize=False):
        """
        Convert a sequence of PNG images directly to a widely compatible MP4.
        
        Make sure to choose image resolution when outputting png images using SaveUniformFigure.
        If there is an error, use resize = True
        """
        import os
        from PIL import Image
        
        # --- Use the import paths from your original code ---
        from moviepy import ImageSequenceClip
        from moviepy.video.fx import MultiplySpeed 

        if not imageFiles:
            raise ValueError("No image files provided for MP4 conversion.")

        # We'll default to using the original files
        clip_input = imageFiles
        # This list will hold the paths to the temp files we create
        temp_files_to_clean = [] 

        if resize == True:
            print("Resizing images via temporary files...")
            with Image.open(imageFiles[0]) as im:
                w, h = im.size
            
            # --- Round width and height UP to even numbers ---
            if w % 2 != 0:
                w += 1
            if h % 2 != 0:
                h += 1
            
            target_size = (w, h)
            
            # This list will hold the final paths (original or temp)
            uniform_images = [] 
            
            # --- Ensure all images match the even target size ---
            for img_path in imageFiles:
                with Image.open(img_path) as im:
                    if im.size != target_size:
                        # Create and save a temporary resized file
                        resized = im.resize(target_size, Image.Resampling.LANCZOS)
                        tmp_path = img_path.replace(".png", "_tmp.png")
                        resized.save(tmp_path)
                        
                        uniform_images.append(tmp_path)
                        temp_files_to_clean.append(tmp_path) # Add to cleanup list
                    else:
                        # Use the original file path
                        uniform_images.append(img_path)
            
            # Point the clip generator to our list of uniform-sized images
            clip_input = uniform_images
            print("Temporary file resizing complete.")

        else:
            clip_input = imageFiles


        # --- Create video clip ---
        # This will use the paths in 'clip_input'
        clip = ImageSequenceClip(clip_input, fps=fps)

        # --- Adjust playback speed if needed ---
        if speed != 1.0:
            clip = MultiplySpeed(speed).apply(clip)

        # --- FFMPEG Parameters ---
        ffmpeg_params = [
            "-pix_fmt", "yuv420p",
            "-profile:v", "main",
            "-movflags", "+faststart"
        ]

        # # If we didn't resize, add the padding filter to prevent the BrokenPipeError
        # if resize == False:
        #     ffmpeg_params.extend(["-vf", "pad='iw:ceil(ih/2)*2'"])

        # --- Export to MP4 ---
        clip.write_videofile(
            outputFile,
            codec="libx264",
            bitrate=bitrate,
            audio=False,
            ffmpeg_params=ffmpeg_params,
            preset="medium",
            threads=4
        )
        clip.close()

        print(f"MP4 saved to: {outputFile} (fps={fps}, speed={speed})")
        
        # --- Clean up temporary resized PNGs ---
        if temp_files_to_clean:
            print(f"Cleaning up {len(temp_files_to_clean)} temporary files...")
            for tmp in temp_files_to_clean:
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




