#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
====================================================
ComputationFunctions
====================================================
"""


# In[ ]:


#IMPORTING NECESSARY LIBRARIES
import numpy


# In[ ]:


# def check_memory():
#     ipython_vars = ["In", "Out", "exit", "quit", "get_ipython", "ipython_vars"]
#     print("Top 10 objects with highest memory usage")
#     # Get a sorted list of the objects and their sizes
#     mem = {
#         key: round(value/1e6,2)
#         for key, value in sorted(
#             [
#                 (x, sys.getsizeof(globals().get(x)))
#                 for x in globals()
#                 if not x.startswith("_") and x not in sys.modules and x not in ipython_vars
#             ],
#             key=lambda x: x[1],
#             reverse=True)[:10]
#     }
#     print({key:f"{value} MB" for key,value in mem.items()})
#     print(f"\n{round(sum(mem.values()),2)/1000} GB in use overall")

# check_memory()

def check_memory(namespace):
    ipython_vars = ["In", "Out", "exit", "quit", "get_ipython", "ipython_vars"]
    print("Top 10 objects with highest memory usage")
    # Get a sorted list of the objects and their sizes
    mem = {
        key: round(value/1e6, 2)
        for key, value in sorted(
            [
                (x, sys.getsizeof(namespace.get(x)))
                for x in namespace
                if not x.startswith("_") and x not in sys.modules and x not in ipython_vars
            ],
            key=lambda x: x[1],
            reverse=True)[:10]
    }
    print({key: f"{value} MB" for key, value in mem.items()})
    print(f"\n{round(sum(mem.values()), 2)/1000} GB in use overall")

