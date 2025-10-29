#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# DirectoryManager_Class
# ============================================================

import os 

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

    def GetDataDirectory(self, dataClass, ModelData, dataType, directory=None):
        """
        Retrieves data directory path
        """
        if directory is None:
            directory = self.dataDirectory
        #e.g. dataClass = "Observation_Data"
        dataDirectory = os.path.join(directory, dataClass,ModelData.region,f"{ModelData_NSSL.region}_{MoistData.case}", dataType)
        return dataDirectory

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
# ============================================================
# DirectoryManager_Class
# ============================================================

import os 

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

