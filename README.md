# Motion Analysis Using Hilbert-Huang Transform (HHT)

This repository contains a Python implementation for analyzing BVH motion capture data using the Hilbert-Huang Transform (HHT) and Multivariate Empirical Mode Decomposition (MEMD). This approach enables effective frequency and amplitude analysis of complex, non-linear and non-stationary motion data.

## Demo Video

Watch a demonstration of this analysis on YouTube:  
[![Watch the video](https://img.youtube.com/vi/PGP5-PKgoi4/0.jpg)](https://www.youtube.com/watch?v=PGP5-PKgoi4)


## Overview

The Hilbert-Huang Transform (HHT) is a time-frequency analysis method particularly well-suited for analyzing non-linear and non-stationary data. This implementation applies HHT to motion capture data stored in BVH format, allowing researchers and animators to extract meaningful frequency and amplitude information from complex movements.

## Key Features

- **BVH File Handling**: Read and write BVH motion capture files
- **Two Rotation Modes**: Decompose motion in Euler-angle space or quaternion space
- **Multivariate Empirical Mode Decomposition (MEMD)**: Decompose motion signals into Intrinsic Mode Functions (IMFs)
- **Hilbert Spectral Analysis**: Extract instantaneous frequency and amplitude information
- **Visualization**: Generate Hilbert spectral plots for selected joints
- **Motion Decomposition**: Export individual IMF components as BVH files for side-by-side viewing

## Dependencies

- Python 3.10+ (3.11 recommended)
- NumPy
- Matplotlib
- SciPy (quaternion conversion via `scipy.spatial.transform.Rotation`)
- Custom modules:
  - `MEMD_all.py`: Multivariate EMD implementation
  - `ht.py`: Hilbert Transform utilities
  - `bvh.py`: BVH I/O and rotation conversion helpers

Install dependencies:

```bash
pip install -r requirements.txt
```

### Conda environment (recommended)

Use Miniconda/Anaconda instead of the system Python (e.g. Python 2.7 on some Windows setups):

```bash
conda create -n motion-hht python=3.11 -y
conda activate motion-hht
pip install -r requirements.txt
```

## Usage

The main entry point is `motionAnalysisHHT.py`. Sample BVH files are provided under `data/` (e.g. `data/jump/13_32.bvh`, `data/golf/cmuGolf.bvh`).

### Euler-angle mode (default)

Decompose BVH Euler rotation channels directly. This matches the original pipeline.

```bash
python motionAnalysisHHT.py --rotation-mode euler
```

### Quaternion mode

Convert each joint's Euler angles to quaternions (via SciPy), run MEMD in quaternion space, then convert IMF outputs back to Euler angles for BVH export.

```bash
python motionAnalysisHHT.py --rotation-mode quat
```

### Custom input and output

```bash
python motionAnalysisHHT.py --input ./data/golf/cmuGolf.bvh --rotation-mode quat
python motionAnalysisHHT.py --input ./data/jump/13_32.bvh --rotation-mode euler --output-dir ./my_run
```

### Command-line options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | `./data/jump/13_32.bvh` | Path to input BVH file |
| `--rotation-mode` | `euler` | `euler` or `quat` |
| `--output-dir` | mode-specific (see below) | Root directory for outputs |

### Output directories

| Mode | Spectra (PNG) | Decomposed BVH |
|------|---------------|----------------|
| `euler` | `visualization/` | `decomposition/` |
| `quat` | `visualization_quat/` | `decomposition_quat/` |

If `--output-dir` is set (e.g. `./my_run`), files are written to `my_run/visualization/` and `my_run/decomposition/` regardless of mode.

Each run produces:

- Hilbert spectrum plots for selected joints (`joint_<channel>_spectrum.png`, or `joint_<channel>_spectrum_quat.png` in quaternion mode)
- BVH files: `IMF1.bvh` … `IMF<n-1>.bvh`, `Trend.bvh`, `original.bvh`

## Rotation Modes

### Euler mode

- MEMD operates on the raw BVH channel layout (positions + Euler angles).
- Root rotation channels are unwrapped before decomposition (`errc` on channels 3–6).
- Suitable for direct comparison with the original published workflow.

### Quaternion mode

- Each rotation triplet is converted to four quaternion components (`x, y, z, w`) using the Euler order declared in the BVH hierarchy (e.g. `zxy` for CMU golf data, `zyx` for some jump mocap files).
- Quaternion sign is kept continuous across frames before MEMD.
- Root translation channels are included in MEMD unchanged.
- IMF results are normalized and converted back to Euler angles before writing BVH files.

Both modes use the same MEMD + Hilbert visualization pipeline; only the working representation for rotation channels differs.

## BVH Joint Selection

The script analyzes specific joints by default (first rotation channel index in the Euler BVH layout):

| Channel index | Joint (example skeleton) |
|---------------|-------------------------|
| 27 | RightLeg |
| 12 | LeftLeg |
| 45 | Neck |
| 78 | RightArm |
| 57 | LeftArm |

Edit the `JOINTS` list in `motionAnalysisHHT.py` to change which joints are plotted.

## Hilbert Spectrum Visualization

For each selected joint, instantaneous frequency and amplitude are computed per IMF layer, then aggregated across rotation channels:

- **Euler mode**: 3 channels — arithmetic mean of frequency; RMS of amplitude (√(mean of squared amplitudes)).
- **Quaternion mode**: 4 channels — same aggregation over `x, y, z, w`.

This is a practical visualization heuristic for comparing Euler vs quaternion MEMD pipelines. It is not a strict SO(3) spectral measure.

## BVH Output Layout (viewer offsets)

Exported IMF BVH files are shifted along the root **X position** so multiple clips can be viewed side by side in a BVH player:

- `IMF1` … `IMF7`: `+150`, `+300`, … along X (`VISUALIZATION_SPACING` in `motionAnalysisHHT.py`)
- `original.bvh`: `-150` (opposite `IMF1`)
- `Trend.bvh`: no offset

These offsets affect display position only, not joint rotations. To compare `original.bvh` numerically with the input file, add `150` to the root X channel.

## Example Output

The analysis produces Hilbert spectrum plots showing how frequency components of motion change over time with color-coded amplitude. This helps identify patterns, periodicity, and energy distribution in the motion.

Each IMF component is also exported as a BVH file, allowing you to visualize different frequency components of the motion separately.

## License

This project is available under MIT License. See the LICENSE file for more details.

## Citation

If you use this code in your research, please cite:

```
@article{dong2020motion,
  title={Motion capture data analysis in the instantaneous frequency-domain using hilbert-huang transform},
  author={Dong, Ran and Cai, Dongsheng and Ikuno, Soichiro},
  journal={Sensors},
  volume={20},
  number={22},
  pages={6534},
  year={2020},
  publisher={MDPI},
  doi={10.3390/s20226534}
}

@article{dong2023biomechanical,
  title={Biomechanical analysis of golf swing motion using hilbert--huang transform},
  author={Dong, Ran and Ikuno, Soichiro},
  journal={Sensors},
  volume={23},
  number={15},
  pages={6698},
  year={2023},
  publisher={MDPI},
  doi={10.3390/s23156698}
}
```

## Contact

For questions or collaboration opportunities, please open an issue in this repository.
