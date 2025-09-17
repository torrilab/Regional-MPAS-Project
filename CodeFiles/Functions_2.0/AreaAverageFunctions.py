#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
====================================================
AreaAverageFunctions
====================================================
"""


# In[ ]:


#IMPORTING NECESSARY LIBRARIES
import numpy

# In[18]:


import numpy as np

def Ultimate_AreaAverage(data, dims, dim_names, mode="keep"):
    """
    Average a NumPy array over dimensions by name using a mode switch.

    Parameters
    ----------
    data : np.ndarray
        Input array (2D–4D).
    dims : tuple of str
        Names of each axis in order of data.shape, e.g. ('t','z','y','x').
    dim_names : tuple/list/str
        - If mode='remove': dimensions to average over (same as `avg_over`).
        - If mode='keep'  : dimensions to keep (others will be averaged out).
    mode : {'remove','keep'}, default 'remove'
        'remove' -> behave like Ultimate_AreaAverage_remove
        'keep'   -> behave like Ultimate_AreaAverage_keep

    Returns
    -------
    out : np.ndarray
        Array after averaging.
    out_dims : tuple of str
        Remaining dimensions after averaging.
    """
    # normalize dim_names to a tuple (so single strings work too)
    if isinstance(dim_names, str):
        dim_names = (dim_names,)
    else:
        dim_names = tuple(dim_names)

    if mode == "remove":
        # --- EXACT behavior of Ultimate_AreaAverage_remove ---
        # Map dimension names to axis indices
        axes = [dims.index(d) for d in dim_names]

        # String of Remaining dimensions
        out_dims = tuple(d for d in dims if d not in dim_names)

        # Take Area Average
        out = np.nanmean(data, axis=tuple(axes))

        return out, out_dims

    elif mode == "keep":
        # --- EXACT behavior of Ultimate_AreaAverage_keep ---
        # Axes to average over = everything NOT in keep_dims
        axes = [i for i, d in enumerate(dims) if d not in dim_names]

        # Remaining dimensions = the ones we kept
        out_dims = tuple(d for d in dims if d in dim_names)

        # Take Area Average
        out = np.nanmean(data, axis=tuple(axes))

        return out, out_dims

    else:
        raise ValueError("mode must be either 'remove' or 'keep'.")


# #################################
# #TESTING
# import numpy as np 
# arr4d = np.random.rand(10, 11, 12, 13)  # (t,z,y,x)

# # remove mode (same as Ultimate_AreaAverage_remove)
# out, dims_out = Ultimate_AreaAverage(arr4d, ('t','z','y','x'), ('z','y','x'), mode='remove')
# print(out.shape, dims_out)   # (10,) ('t',)

# out, dims_out = Ultimate_AreaAverage(arr4d, ('t','z','y','x'), ('y','x'), mode='remove')
# print(out.shape, dims_out)   # (10, 11) ('t','z')

# out, dims_out = Ultimate_AreaAverage(arr4d, ('t','z','y','x'), 'y', mode='remove')
# print(out.shape, dims_out)   # (10, 11, 13) ('t','z','x')

# # keep mode (same as Ultimate_AreaAverage_keep)
# out, dims_out = Ultimate_AreaAverage(arr4d, ('t','z','y','x'), ('t',), mode='keep')
# print(out.shape, dims_out)   # (10,) ('t',)

# out, dims_out = Ultimate_AreaAverage(arr4d, ('t','z','y','x'), ('z',), mode='keep')
# print(out.shape, dims_out)   # (11,) ('z',)

# out, dims_out = Ultimate_AreaAverage(arr4d, ('t','z','y','x'), ('t','z'), mode='keep')
# print(out.shape, dims_out)   # (10, 11) ('t','z')


# In[ ]:




