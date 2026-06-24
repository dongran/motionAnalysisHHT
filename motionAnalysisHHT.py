#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motion Analysis using Hilbert-Huang Transform (HHT)
This script analyzes BVH motion data using Multivariate Empirical Mode Decomposition (MEMD)
and Hilbert-Huang Transform to extract frequency and amplitude information.
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

import bvh as bvh
import ht as hs
from MEMD_all import hhtplot, memd, wafa

# Root X offset between adjacent BVH outputs for side-by-side viewing.
VISUALIZATION_SPACING = 150

# Joint indices to analyze (Z-rotation channel index in euler BVH layout)
JOINTS = [27, 12, 45, 78, 57]
# rightleg: 27 (RightLeg)
# leftleg: 12 (LeftLeg)
# neck: 45 (Neck)
# RightArm: 78 (RightArm)
# LeftArm: 57 (LeftArm)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze BVH motion with MEMD and Hilbert-Huang Transform."
    )
    parser.add_argument(
        "--input",
        default="./data/jump/13_32.bvh",
        help="Path to input BVH file.",
    )
    parser.add_argument(
        "--rotation-mode",
        choices=["euler", "quat"],
        default="euler",
        help="Rotation representation for MEMD: euler or quat.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory root. Defaults to ./visualization and ./decomposition.",
    )
    return parser.parse_args()


def get_output_dirs(rotation_mode, output_dir=None):
    if output_dir:
        visualization_dir = os.path.join(output_dir, "visualization")
        decomposition_dir = os.path.join(output_dir, "decomposition")
    elif rotation_mode == "quat":
        visualization_dir = "./visualization_quat"
        decomposition_dir = "./decomposition_quat"
    else:
        visualization_dir = "./visualization"
        decomposition_dir = "./decomposition"

    os.makedirs(visualization_dir, exist_ok=True)
    os.makedirs(decomposition_dir, exist_ok=True)
    return visualization_dir, decomposition_dir


def analyze_joint_spectrum(
    imf,
    joint_index,
    work_channels,
    dt,
    visualization_dir,
    rotation_mode,
):
    channel_count = len(work_channels)
    result = imf[:, work_channels[0], :]

    m = result.shape[0] - 1
    n = result.shape[1]
    freq, amp = hs.FAhilbert(result, dt)
    freqall = freq
    ampall = amp ** 2

    for channel_offset in range(1, channel_count):
        result = imf[:, work_channels[channel_offset], :]
        freq, amp = hs.FAhilbert(result, dt)
        freqall = freqall + freq
        ampall = ampall + amp ** 2

    freqall = freqall / channel_count
    ampall = np.sqrt(ampall)

    window = 13
    freqall = wafa(freqall, ampall, window)
    ampall = (ampall - np.min(ampall)) / (np.max(ampall) - np.min(ampall))

    t2 = np.zeros((n, m))
    for i in range(m):
        t2[:, i] = np.linspace(0, n * dt, n)

    freqall, ampall = hhtplot(freqall, ampall)

    plt.clf()
    plt.figure(dpi=200, figsize=(16, 9))
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["font.size"] = 30

    for i in range(m):
        plt.scatter(
            t2[:, i],
            freqall[:, i],
            s=100,
            c=ampall[0:n, i],
            cmap="jet",
        )
        plt.clim(0, 1)

    ax = plt.gca()
    ax.set_facecolor([0.0, 0.0, 0.5])
    plt.ylim(0, 10)
    plt.xlabel("time(s)")
    plt.ylabel("frequency(Hz)")
    plt.colorbar()

    suffix = f"_{rotation_mode}" if rotation_mode != "euler" else ""
    plt.savefig(
        os.path.join(
            visualization_dir,
            f"joint_{joint_index}_spectrum{suffix}.png",
        )
    )
    plt.close()


def write_bvh_outputs(
    imf,
    fs,
    text,
    segments,
    rotation_groups,
    rotation_mode,
    decomposition_dir,
    include_trend=True,
):
    def convert_for_bvh(work_data):
        # MEMD stores each component as channels x frames; conversion helpers use
        # frames x channels, which is also the layout expected by bvhoutput.
        euler_data = bvh.from_work_data(work_data.T, rotation_mode, segments)
        if rotation_mode == "euler":
            return bvh.errb(euler_data, 3, 6)
        return bvh.finalize_euler_data(euler_data, rotation_groups)

    for imf_index in range(imf.shape[0] - 1):
        if include_trend:
            work_data = imf[imf_index, :, :] + imf[-1, :, :]
        else:
            work_data = imf[imf_index, :, :]

        work_data = work_data.copy()
        work_data[0, :] = work_data[0, :] + (imf_index + 1) * VISUALIZATION_SPACING

        euler_data = convert_for_bvh(work_data)
        bvh.bvhoutput(
            euler_data,
            fs,
            os.path.join(decomposition_dir, f"IMF{imf_index + 1}"),
            text,
        )

    trend_data = imf[-1, :, :].copy()
    trend_euler = convert_for_bvh(trend_data)
    bvh.bvhoutput(
        trend_euler,
        fs,
        os.path.join(decomposition_dir, "Trend"),
        text,
    )

    reconstructed = np.sum(imf, axis=0).copy()
    # Shift left by one spacing step so original sits opposite IMF1 (+150).
    reconstructed[0, :] = reconstructed[0, :] - VISUALIZATION_SPACING
    reconstructed_euler = convert_for_bvh(reconstructed)
    bvh.bvhoutput(
        reconstructed_euler,
        fs,
        os.path.join(decomposition_dir, "original"),
        text,
    )


def main():
    args = parse_args()
    visualization_dir, decomposition_dir = get_output_dirs(
        args.rotation_mode, args.output_dir
    )

    data, fs, text = bvh.bvhreader(args.input)
    segments, rotation_groups = bvh.parse_channel_layout(text)
    euler_to_work = bvh.build_work_channel_map(segments, args.rotation_mode)

    if args.rotation_mode == "euler":
        data = bvh.errc(data, 3, 6)
    else:
        data = bvh.prepare_euler_data(data, rotation_groups)
    work_data = bvh.to_work_data(data, args.rotation_mode, segments)

    dt = float(fs)
    imf = memd(work_data, work_data.shape[1] * 2)

    for joint_index in JOINTS:
        work_channels = bvh.get_joint_work_channels(joint_index, euler_to_work)
        analyze_joint_spectrum(
            imf,
            joint_index,
            work_channels,
            dt,
            visualization_dir,
            args.rotation_mode,
        )

    write_bvh_outputs(
        imf,
        fs,
        text,
        segments,
        rotation_groups,
        args.rotation_mode,
        decomposition_dir,
        include_trend=True,
    )

    print(f"Rotation mode: {args.rotation_mode}")
    print(f"Input BVH: {args.input}")
    print(f"Visualization output: {visualization_dir}")
    print(f"Decomposition output: {decomposition_dir}")


if __name__ == "__main__":
    main()
