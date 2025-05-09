#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 23:28:30 2020

@author: dong
"""
import numpy as np
import io
#BVH import
########################
# =============================================================================

def bvhreader(path):    
    with open(path) as f:
        l = f.readlines()
    
    for i in range(len(l)):
        if l[i]== "MOTION\n":
            datanum=i
            break
    
    fs=l[datanum+2]
    fs=fs[12:]
    
    # Read data directly from string without creating intermediate files
    motion_data = ''.join(l[datanum+3:])
    a = np.loadtxt(io.StringIO(motion_data))

    return(a, fs, l[:datanum+1])
# =============================================================================

#BVH output
########################
# =============================================================================

def bvhoutput(data, fs, name, l):   
    path_w = name + '.bvh'
    
    # Prepare motion data
    n = data.shape[0]
    
    # Use StringIO to create memory buffer
    motion_buffer = io.StringIO()
    np.savetxt(motion_buffer, data, fmt='%g', delimiter=' ')
    motion_buffer.seek(0)
    motion_lines = motion_buffer.readlines()
    
    # Prepare frame information
    tmp1 = f"Frames: {n}\n"
    tmp2 = f"Frame Time: {fs}"
    
    # Combine all parts
    output_lines = l + [tmp1, tmp2] + motion_lines
    
    # Write directly to file
    with open(path_w, mode='w') as f:
        f.writelines(output_lines)
    
# =============================================================================
#Error change
########################

def errc(data,strt,end):   
    
    n=data.shape[0]
    for j in range(strt, end):
        for i in range(n-1):
            if data[i,j]-data[i+1,j]<-350:
               data[i+1:,j]=data[i+1:,j]-360
            if data[i,j]-data[i+1,j]>350:
               data[i+1:,j]=data[i+1:,j]+360
    return(data)


def errb(data,strt,end):
    
    n=data.shape[0]
    for j in range(strt, end):
        for i in range(n):
            if data[i,j]<-180:
               data[i:,j]=data[i:,j]+360
            if data[i,j]>180:
               data[i:,j]=data[i:,j]-360

    return(data)



