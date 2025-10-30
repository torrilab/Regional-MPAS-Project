#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# DirectoryManager_Class
# ============================================================

import os 
import glob
from datetime import datetime

class DirectoryManager_Class:
    """
    Handles directory paths and output management for the Regional-MPAS-Project.
    Keeps naming conventions consistent with Abraham's original code.
    """

    def __init__(self):
        # MAIN DIRECTORIES
        self.mainDirectory = '/glade/u/home/aroseman/Projects/Regional-MPAS-Project'
        self.mainWorkDirectory = '/glade/work/aroseman/Projects/Regional-MPAS-Project'
        self.mainScratchDirectory = '/glade/derecho/scratch/aroseman/Projects/Regional-MPAS-Project'
        self.scratchDirectory = os.path.join(self.mainScratchDirectory, "MPAS_Atmosphere_8.3.0")

        self.dataDirectory = os.path.join(self.mainWorkDirectory, "Code", "DATA")
        self.mainOutputDirectory = os.path.join(self.mainDirectory, "Code", "OUTPUT")
        self.mainOutputPlottingDirectory = os.path.join(self.mainDirectory, "Code", "PLOTTING")
        self.mainCodeDirectory = os.path.join(self.mainDirectory, "Code", "CodeFiles")
        self.codeDirectory = os.getcwd()

        # Print a summary when initialized
        self.Summary()

    def GetDataDirectory(self, dataClass, ModelData, dataName, directory=None):
        """
        Retrieves data directory path
        """
        if directory is None:
            directory = self.dataDirectory
        #e.g. dataClass = "Observation_Data"
        dataDirectory = os.path.join(directory, dataClass,ModelData.region,f"{ModelData.region}_{ModelData.case}", dataName)
        return dataDirectory
        # Example: DirectoryManager_Class.GetDataDirectory(dataClass="Observation_Data", 
        #                                                  ModelData=ModelData_NSSL,
        #                                                  dataType=dataType)
                                                         

    def GetOutputDirectory(self, codeType, dataType, directory=None):
        """
        Creates (if needed) and returns an output directory path
        for a given codeType and dataType.
        """
        if directory is None:
            directory = self.mainOutputDirectory

        outputDirectory = os.path.join(directory, codeType, dataType)
        os.makedirs(outputDirectory, exist_ok=True)
        return outputDirectory

    def GetOutputPlottingDirectory(self, plottingType, dataType, directory=None):
        """
        Creates (if needed) and returns an output directory path
        for a given plottingType and dataType within the plotting directory.
        """
        if directory is None:
            directory = self.mainOutputPlottingDirectory

        plottingDirectory = os.path.join(directory, plottingType, dataType)
        os.makedirs(plottingDirectory, exist_ok=True)
        return plottingDirectory

    def GetOutputFilePath(self, outputDirectory, folderName):
        """
        Returns the full path for an output file in the given directory.
        """
        filePath = os.path.join(outputDirectory, folderName)
        os.makedirs(filePath, exist_ok=True)
        return filePath

    def GetOutputFile(self, outputDirectory, folderName, fileName):
        """
        Returns the full path for an output file inside a given folder.
        Ensures that the directory exists before returning the file path.
        """
        filePath = self.GetOutputFilePath(outputDirectory, folderName)
        outputFile = os.path.join(filePath, fileName)
        return outputFile

    def ListFiles(self, directory):
        """
        Returns a list of all files in the specified directory.
        """
        if not os.path.exists(directory):
            print(f"Directory does not exist: {directory}")
            return []
        
        fileList =  sorted([
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ])

        filePathList = sorted([
            os.path.join(directory, f) for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ])
        
        return fileList, filePathList

    # def GetSortedFileListByTimestamp(self, filePattern):
    #     """
    #     Given a wildcard path like '.../u10_*.png', return list of full file paths
    #     sorted by the timestamp encoded in the filename.
    #     """
    #     # Match files
    #     matched_files = glob.glob(filePattern)
    
    #     # Extract timestamp from filename and sort
    #     def extract_time(path):
    #         filename = os.path.basename(path)
    #         timestamp_str = filename.split('_', 1)[-1].replace('.png', '')
    #         return datetime.strptime(timestamp_str, "%Y-%m-%d_%H.%M.%S")
    
    #     # Return sorted list
    #     return sorted(matched_files, key=extract_time)

    def GetSortedFileListByTimestamp(self, filePattern):
        import glob, os
        from datetime import datetime
    
        matched_files = glob.glob(filePattern)
    
        def extract_time(path):
            filename = os.path.basename(path).replace(".png", "")
            # ✅ Split from the right — handles extra underscores in varName
            parts = filename.split("_")
            # Expect something like: ["refl10cm", "1km", "2022-07-02", "01.30.00"]
            timestamp_str = "_".join(parts[-2:])  # "2022-07-02_01.30.00"
            return datetime.strptime(timestamp_str, "%Y-%m-%d_%H.%M.%S")
    
        return sorted(matched_files, key=extract_time)

    def Summary(self):
        """
        Prints a formatted summary of the main directory paths.
        """
        print("============================================================")
        print(" DirectoryManager_Class Summary")
        print("============================================================")
        print(f" Main Directory:           {self.mainDirectory}")
        print(f" Main Scratch Directory:   {self.mainScratchDirectory}")
        print(f" Scratch Directory:        {self.scratchDirectory}")

        print(f" Data Directory:           {self.dataDirectory}")
        print(f" Main Output Directory:    {self.mainOutputDirectory}")
        print(f" Main Output Plotting Directory:    {self.mainOutputPlottingDirectory}")
        print(f" Main Code Directory:      {self.mainCodeDirectory}")
        print(f" Current Code Directory:   {self.codeDirectory}")
        print("============================================================\n")
# Example Importing
        
        
# #Example USAGE

# DirectoryManager = DirectoryManager_CLASS()

# codeType = os.path.join("DataAnalysis", "MPAS_Model_Data", "InitialFigures")
# dataType = "SurfaceVariableAnimations_Unstructured"

# outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)
# outputDirectory = DirectoryManager.GetOutputDirectory(codeType, dataType)

