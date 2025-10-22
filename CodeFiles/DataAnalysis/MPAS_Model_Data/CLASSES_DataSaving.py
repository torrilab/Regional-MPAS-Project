#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ============================================================
# ArrayDataSaving_Class
# ============================================================

import h5py
import numpy as np

class DataSaving_Class:

    @staticmethod
    def SaveDictionaryToH5(outputDictionary, filePath):
        """
        Save all items in a dictionary to a single HDF5 file as float32 datasets.
        """
        with h5py.File(filePath, 'w') as h5f:
            for varName, data in outputDictionary.items():
                # Convert to float32 numpy array
                data = np.array(data, dtype=np.float32)
                h5f.create_dataset(varName, data=data, dtype='float32')
        print(f"Saved {len(outputDictionary)} variables to {filePath}")

    def LoadDictionaryFromH5(filePath):
        """
        Load all dictionary items back from single HDF5 file.
        """
        outputDictionary = {}
        with h5py.File(filePath, 'r') as h5f:
            for varName in h5f.keys():
                outputDictionary[varName] = np.array(h5f[varName][:], dtype=np.float32)

        print(f"Loaded {len(outputDictionary)} variables from {filePath}")
        return outputDictionary

