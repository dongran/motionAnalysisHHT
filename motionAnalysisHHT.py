#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motion Analysis using Hilbert-Huang Transform (HHT)
This script analyzes BVH motion data using Multivariate Empirical Mode Decomposition (MEMD)
and Hilbert-Huang Transform to extract frequency and amplitude information.
"""

import numpy as np
import bvh as bvh
import matplotlib.pyplot as plt
from MEMD_all import memd
from MEMD_all import wafa
from MEMD_all import hhtplot
import ht as hs
import os

# Create output directories if they don't exist
os.makedirs('./visualization', exist_ok=True)
os.makedirs('./decomposition', exist_ok=True)

# Load BVH file
path = './data/jump/13_32.bvh'
[data, fs, text] = bvh.bvhreader(path)

# Error correction for the data
data = bvh.errc(data, 3, 6)

# Time step calculation
dt = float(fs)

# Perform Multivariate Empirical Mode Decomposition
imf = memd(data, data.shape[1] * 2)
# Alternative decomposition ranges:
#imf = memd(data[80:])
#imf = memd(data[281 * 4: 400 * 4])

# Joint indices to analyze
joints = [27, 12, 45, 78, 57]
# Joint descriptions:
# rightleg: 27 (RightLeg)
# leftleg: 12 (LeftLeg)
# neck: 45 (Neck)
# RightArm: 78 (RightArm)
# LeftArm: 57 (LeftArm)

# Analyze each selected joint
for j in range(len(joints)):
    index = joints[j]
    
    # Extract IMF data for the current joint
    result = imf[:, index, :] 
    N = result.shape[0] + 1
    n = result.shape[1]
    t = np.linspace(0, dt*n, n)
    
    # Calculate instantaneous frequency and amplitude
    m = result.shape[0]-1
    n = result.shape[1]
    freq, amp = hs.FAhilbert(result, dt)
    freqall = freq
    ampall = amp ** 2
    
    # Add frequency and amplitude from additional IMF components
    for i in range(2):
        result = imf[:, i + index, :]
        freq, amp = hs.FAhilbert(result, dt)
        freqall = freqall + freq
        ampall = ampall + amp ** 2
    
    # Average and normalize
    freqall = freqall / 3
    ampall = np.sqrt(ampall)
    
    # Apply WAFA smoothing
    window = 13
    freqall = wafa(freqall, ampall, window)
    ampall = (ampall - np.min(ampall)) / (np.max(ampall) - np.min(ampall))
    
    # Prepare time data for Hilbert spectrum plot
    t2 = np.zeros((n, m))
    for i in range(m):
        t2[:, i] = np.linspace(0, n * dt, n)
    
    # Arrange IMFs by amplitude
    freqall, ampall = hhtplot(freqall, ampall)
    
    # Create Hilbert spectrum plot
    plt.clf()
    plt.figure(dpi=200, figsize=(16, 9))
    
    plt.rcParams["font.family"] = "Times New Roman" 
    plt.rcParams["font.size"] = 30
    
    # Plot spectrum
    for i in range(m):
        plt.scatter(t2[:, i], freqall[:, i], s=100, c=ampall[0:n, i], cmap='jet')
        plt.clim(0, 1)
    
    ax = plt.gca()
    ax.set_facecolor([0.0, 0.0, 0.5])
    
    plt.ylim(0, 10)
    plt.xlabel('time(s)')
    plt.ylabel('frequency(Hz)')
    plt.colorbar()
    
    # Save the plot instead of displaying it
    plt.savefig(f'./visualization/joint_{index}_spectrum.png')
    plt.close()

# Flag to include trend component (residue)
flag = 1  # 0 = no trend

# Output individual IMF components as BVH files
for i in range(imf.shape[0]-1):
    if flag == 0:
        out = imf[i, :, :]
    else:
        out = imf[i, :, :] + imf[-1, :, :]
    
    out[0, :] = out[0, :] + (i+1)*150
    bvh.bvhoutput(bvh.errb(out.T, 3, 6), fs, f"./decomposition/IMF{i+1}", text)

# Output trend component
out = imf[-1, :, :]
out[0, :] = out[0, :] + imf.shape[0]*150
bvh.bvhoutput(bvh.errb(imf[-1, :, :].T, 3, 6), fs, "./decomposition/Trend", text)

# Output original reconstructed motion
out2 = np.sum(imf, axis=0) 
out2[0, :] = out2[0, :] - imf.shape[0] * 150
bvh.bvhoutput(bvh.errb(out2.T, 3, 6), fs, "./decomposition/original", text)

# Alternative low frequency component extraction (commented out)
# for i in range(3):
#     out = np.sum(imf[-(i+2):, :, :], axis=0)
#     out[0, :] = out[0, :] + (-i + 3)*150
#     bvh.bvhoutput(bvh.errb(out.T, 3, 6), fs, f"./decomposition/{i+1}", text)
