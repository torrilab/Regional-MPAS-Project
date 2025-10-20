#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
====================================================
StatisticalFunctions
====================================================
"""


# In[ ]:


#IMPORTING NECESSARY LIBRARIES
import numpy as np


# In[2]:


def VectorMean(vec):
    N=len(vec)
    out=np.sum(vec)/N
    return out
# #TESTING
# vec=np.array([1,2,3])
# VectorMean(vec)


# In[3]:


def VectorVariance(vec,method):
    N=len(vec)
    if method==1:
        mean=VectorMean(vec)
        out=np.sum((vec-mean)**2)/N
    elif method==2: #this method has numerical inaccuracy for close large numbers
        out=VectorMean(vec**2)-VectorMean(vec)**2
    return out   
# #TESTING
# vec=[1,2,3]
# print(VectorVariance(vec,method=2)) 

def VectorStd(vec,method):
    variance=VectorVariance(vec,method)
    out=variance**(0.5)
    return out   
# #TESTING
# vec=np.array([1,2,3])
# VectorStd(vec,method=1)


# In[27]:


def VectorSampleVariance(vec,method):
    N=len(vec)
    variance=VectorVariance(vec,method)
    out=variance*(N/(N-1))
    return out
# #TESTING
# vec=np.array([1,2,3])
# print(VectorSampleVariance(vec,method=2))

def VectorStandardError1(vec,method):
    N=len(vec)
    out=VectorMean(vec**2)-VectorMean(vec)**2
    out/=(N-1)
    out**=(0.5)
    return out
# #TESTING
# vec=np.array([1,2,3])
# print(VectorStandardError1(vec,method=2))

def VectorStandardError2(vec,method):
    N=len(vec)
    sample_variance=VectorSampleVariance(vec,method)
    out=sample_variance/(N)
    out**=(0.5)
    return out
# #TESTING
# vec=np.array([1,2,3])
# VectorStandardError2(vec,method=2)


# In[ ]:


#SAME BUT FOR BINNED PROFILES
################################


# In[109]:


def ProfileMean(profile): 
    #Input Requires Three Column Array 
    #with Sum in 1st Column, Count in 2nd Column, and Index in 3rd Column
    #Returns 1st and 3rd Column (removing zero rows)
    
    #gets rid of rows that have no data
    profile_mean=profile[ (profile[:, 1] > 1)]; 
    #divides the data column by the counter column
    profile_mean=np.array([profile_mean[:, 0] / profile_mean[:, 1], profile_mean[:, 2]]).T 
    return profile_mean

# #TESTING
# profile=np.zeros((10,3))
# profile[:,0]=np.arange(1,profile.shape[0]+1)
# profile[:,1]=np.random.randint(1, 101, size=profile.shape[0])
# profile[:,2]=np.arange(1,profile.shape[0]+1)
# ProfileMean(profile)


# In[186]:


def ProfileVariance(profile,squares_profile): 
    #Input Requires Three Column Array 
    #with Sum in 1st Column, Count in 2nd Column, and Index in 3rd Column
    #Returns 1st and 3rd Column (removing zero rows)

    #MEAN OF SQUARES
    #gets rid of rows that have no data
    profile_mean1=squares_profile[ (squares_profile[:, 1] > 1)]; N=profile_mean1[:,1]
    #divides the data column by the counter column
    profile_mean1=np.array([profile_mean1[:, 0] / profile_mean1[:, 1], profile_mean1[:, 2]]).T 
    # print(f"Mean of Squares Profile is \n{profile_mean1}") #TESTING

    #SQUARE OF MEAN
    #gets rid of rows that have no data
    profile_mean2=profile[ (profile[:, 1] > 1)]; 
    #divides the data column by the counter column
    profile_mean2=np.array([profile_mean2[:, 0] / profile_mean2[:, 1], profile_mean2[:, 2]]).T 
    profile_mean2[:,0]**=2
    # print(f"Mean Profile Squared is \n{profile_mean2}") #TESTING

    #SUBTRACTING THE TWO
    profile_mean=profile_mean1.copy()
    profile_mean[:,0]-=profile_mean2[:,0]
    # print(f"Variance Profile is \n{profile_mean}") #TESTING
    return profile_mean,N
    
def ProfileStandardDeviation(profile,squares_profile): 
    [variance,N]=ProfileVariance(profile,squares_profile)
    standard_deviation=variance.copy()
    standard_deviation[:,0]**=(0.5)
    return standard_deviation
    
def ProfileStandardError(profile,squares_profile): 
    [variance,N]=ProfileVariance(profile,squares_profile)
    standard_error=variance.copy()
    standard_error[:,0]/=(N-1)
    standard_error[:,0]**=(0.5)

    # standard_error2=variance.copy()
    # standard_error2[:,0]*=N/(N-1)/N
    # standard_error2[:,0]**=(0.5)
    # print(standard_error2==standard_error)
    return standard_error

# #TESTING
# ####################################################################################################
# # (0) Set up profile so we collect half of the profile value twice
# # (1) For the first row, i counted the data point 0.5 twice, so the SUM = 1 and the MEAN = 1/2 = 0.5
# # (2) And SQUARE OF MEAN = 0.5^2 = 0.25
# # (3) But SUM OF SQUARES = 0.5^2 + 0.5^2 = 0.5, and MEAN(SUM OF SQUARES) = 0.5/2 = 0.25
# # (4) ==> So when i subtract (MEAN OF SQUARES minus SQUARE OF MEANS), we get 0

# profile=np.zeros((10,3))
# profile[:,0]=np.arange(1,profile.shape[0]+1)
# profile[:,1]=np.ones(profile.shape[0])*2
# profile[:,2]=np.arange(1,profile.shape[0]+1)
# print(f"Sum Profile is \n{profile}")

# squares_profile=profile.copy()
# squares_profile[:,0]=2*((profile[:,0]/2)**2)
# print(f"Sum of Squares Profile is \n{squares_profile}")

# profile_mean=ProfileMean(profile)
# profile_SE=ProfileStandardError(profile,squares_profile)
# import matplotlib.pyplot as plt
# plt.plot(profile_mean[:,0],profile_mean[:,1],label='mean')
# plt.plot(profile_SE[:,0]*1.96,profile_SE[:,1],label='SE')
# # plt.fill_betweenx(profile_mean[:, 1], profile_mean[:, 0] - 1.96*profile_SE[:,0], profile_mean[:, 0] + 1.96*profile_SE[:,0], color='black', alpha=0.1) #***
# plt.legend()

