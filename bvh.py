#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 23:28:30 2020

@author: dong
"""
import numpy as np
import io
from scipy.spatial.transform import Rotation as R

def _euler_order_from_channel_names(channel_names):
    axes = []
    for name in channel_names:
        axis = name[0].lower()
        if axis not in "xyz":
            raise ValueError(f"Unsupported rotation channel name: {name}")
        axes.append(axis)
    return "".join(axes)
#BVH import
########################
# =============================================================================

def bvhreader(path):    
    with open(path) as f:
        l = f.readlines()
    
    for i in range(len(l)):
        if l[i].strip() == "MOTION":
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


def _is_rotation_channel(name):
    return "rotation" in name.lower()


def _is_position_channel(name):
    return "position" in name.lower()


def parse_channel_layout(hierarchy_lines):
    """
    Parse BVH hierarchy CHANNELS definitions into ordered segments.

    Returns
    -------
    segments : list of dict
        Each segment is either position (1 channel) or rotation (3 euler channels).
    rotation_groups : list of tuple
        (z_idx, x_idx, y_idx) for every joint rotation triplet in euler layout.
    """
    channel_index = 0
    segments = []
    rotation_groups = []

    for line in hierarchy_lines:
        stripped = line.strip()
        if not stripped.startswith("CHANNELS"):
            continue

        parts = stripped.split()
        channel_names = parts[2:]

        i = 0
        while i < len(channel_names):
            name = channel_names[i]
            if _is_position_channel(name):
                segments.append(
                    {"type": "position", "src_idx": channel_index}
                )
                channel_index += 1
                i += 1
            elif _is_rotation_channel(name):
                rot_names = channel_names[i:i + 3]
                if len(rot_names) != 3 or not all(
                    _is_rotation_channel(rot_name) for rot_name in rot_names
                ):
                    raise ValueError(f"Unexpected rotation channels: {rot_names}")

                z_idx = channel_index
                x_idx = channel_index + 1
                y_idx = channel_index + 2
                rotation_groups.append((z_idx, x_idx, y_idx))
                segments.append(
                    {
                        "type": "rotation",
                        "indices": (z_idx, x_idx, y_idx),
                        "order": _euler_order_from_channel_names(rot_names),
                        "channel_names": tuple(rot_names),
                    }
                )
                channel_index += 3
                i += 3
            else:
                raise ValueError(f"Unsupported BVH channel: {name}")

    return segments, rotation_groups


def build_work_channel_map(segments, rotation_mode):
    """
    Map euler channel indices to working-space channel indices.

    In quaternion mode each rotation triplet becomes 4 quaternion channels.
    """
    euler_to_work = {}
    work_idx = 0

    for segment in segments:
        if segment["type"] == "position":
            work_idx += 1
        elif segment["type"] == "rotation":
            z_idx, x_idx, y_idx = segment["indices"]
            if rotation_mode == "quat":
                work_channels = tuple(range(work_idx, work_idx + 4))
                for euler_idx in segment["indices"]:
                    euler_to_work[euler_idx] = work_channels
                work_idx += 4
            else:
                work_channels = (work_idx, work_idx + 1, work_idx + 2)
                for euler_idx in segment["indices"]:
                    euler_to_work[euler_idx] = work_channels
                work_idx += 3

    return euler_to_work


def errc_rotations(data, rotation_groups):
    """Unwrap all euler rotation channels."""
    data = data.copy()
    for z_idx, x_idx, y_idx in rotation_groups:
        for channel_idx in (z_idx, x_idx, y_idx):
            data = errc(data, channel_idx, channel_idx + 1)
    return data


def errb_rotations(data, rotation_groups):
    """Wrap all euler rotation channels back to [-180, 180]."""
    data = data.copy()
    for z_idx, x_idx, y_idx in rotation_groups:
        for channel_idx in (z_idx, x_idx, y_idx):
            data = errb(data, channel_idx, channel_idx + 1)
    return data


def quat_hemisphere_fix(quats):
    """Keep quaternion sign continuous across frames."""
    fixed = quats.copy()
    for frame_idx in range(1, fixed.shape[0]):
        if np.dot(fixed[frame_idx - 1], fixed[frame_idx]) < 0:
            fixed[frame_idx] = -fixed[frame_idx]
    return fixed


def normalize_quaternions(quats):
    """Normalize quaternion rows for conversion back to euler angles."""
    normalized = quats.copy()
    norms = np.linalg.norm(normalized, axis=1, keepdims=True)
    zero_mask = norms[:, 0] < 1e-8
    norms = np.where(norms < 1e-8, 1.0, norms)
    normalized = normalized / norms
    normalized[zero_mask] = np.array([0.0, 0.0, 0.0, 1.0])
    return normalized


def euler_data_to_quat_data(data, segments):
    """Convert euler rotation channels to quaternion channels (x, y, z, w)."""
    columns = []

    for segment in segments:
        if segment["type"] == "position":
            columns.append(data[:, segment["src_idx"]:segment["src_idx"] + 1])
        elif segment["type"] == "rotation":
            z_idx, x_idx, y_idx = segment["indices"]
            euler = data[:, [z_idx, x_idx, y_idx]]
            quat = R.from_euler(
                segment["order"], euler, degrees=True
            ).as_quat()
            quat = quat_hemisphere_fix(quat)
            columns.append(quat)

    return np.hstack(columns)


def quat_data_to_euler_data(data_quat, segments):
    """Convert quaternion channels back to euler rotation channels."""
    columns = []
    quat_offset = 0

    for segment in segments:
        if segment["type"] == "position":
            columns.append(
                data_quat[:, quat_offset:quat_offset + 1]
            )
            quat_offset += 1
        elif segment["type"] == "rotation":
            quat = data_quat[:, quat_offset:quat_offset + 4]
            quat = normalize_quaternions(quat)
            euler = R.from_quat(quat).as_euler(
                segment["order"], degrees=True
            )
            columns.append(euler)
            quat_offset += 4

    return np.hstack(columns)


def to_work_data(data, rotation_mode, segments):
    """Prepare motion data for MEMD in the selected rotation space."""
    if rotation_mode == "euler":
        return data
    if rotation_mode == "quat":
        return euler_data_to_quat_data(data, segments)
    raise ValueError(f"Unsupported rotation mode: {rotation_mode}")


def from_work_data(data_work, rotation_mode, segments):
    """Convert MEMD results back to euler-channel BVH layout."""
    if rotation_mode == "euler":
        return data_work
    if rotation_mode == "quat":
        return quat_data_to_euler_data(data_work, segments)
    raise ValueError(f"Unsupported rotation mode: {rotation_mode}")


def prepare_euler_data(data, rotation_groups):
    """Unwrap all rotation channels before conversion or MEMD."""
    return errc_rotations(data, rotation_groups)


def finalize_euler_data(data, rotation_groups):
    """Wrap rotation channels before writing BVH files."""
    return errb_rotations(data, rotation_groups)


def get_joint_work_channels(euler_channel_index, euler_to_work):
    """
    Return working-space channels for a joint given its Z-rotation channel index.
    """
    if euler_channel_index not in euler_to_work:
        raise ValueError(
            f"Channel {euler_channel_index} is not a rotation channel index."
        )
    return list(euler_to_work[euler_channel_index])



