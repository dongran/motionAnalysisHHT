# Motion Analysis Using Hilbert-Huang Transform (HHT)

This repository contains a Python implementation for analyzing BVH motion capture data using the Hilbert-Huang Transform (HHT) and Multivariate Empirical Mode Decomposition (MEMD). This approach enables effective frequency and amplitude analysis of complex, non-linear and non-stationary motion data.

## Overview

The Hilbert-Huang Transform (HHT) is a time-frequency analysis method particularly well-suited for analyzing non-linear and non-stationary data. This implementation applies HHT to motion capture data stored in BVH format, allowing researchers and animators to extract meaningful frequency and amplitude information from complex movements.

## Key Features

- **BVH File Handling**: Read and write BVH motion capture files
- **Multivariate Empirical Mode Decomposition (MEMD)**: Decompose motion signals into Intrinsic Mode Functions (IMFs)
- **Hilbert Spectral Analysis**: Extract instantaneous frequency and amplitude information
- **Visualization**: Generate Hilbert spectral plots for selected joints
- **Motion Decomposition**: Output individual IMF components as BVH files for visualization

## Dependencies

- NumPy
- Matplotlib
- Custom modules:
  - `MEMD_all.py`: Multivariate EMD implementation
  - `ht.py`: Hilbert Transform utilities

## Usage

1. Place your BVH files in the `data` directory
2. Edit the file path in `motionAnalysisHHT.py` to point to your BVH file
3. Run the script:

```bash
python motionAnalysisHHT.py
```

4. The script will generate:
   - Hilbert spectrum visualizations in the `visualization` directory
   - Decomposed motion components in the `decomposition` directory

## BVH Joint Selection

The script analyzes specific joints by default:
- Joint 27: RightLeg
- Joint 12: LeftLeg
- Joint 45: Neck
- Joint 78: RightArm
- Joint 57: LeftArm

You can modify the joint selection in the script by editing the `joints` array.

## Example Output

The analysis produces Hilbert spectrum plots showing how frequency components of motion change over time with color-coded amplitude. This helps identify patterns, periodicity, and energy distribution in the motion.

Each IMF component is also exported as a BVH file, allowing you to visualize different frequency components of the motion separately.

## License

This project is available under MIT License. See the LICENSE file for more details.

## Citation

If you use this code in your research, please cite:

```
@misc{motionAnalysisHHT,
  author = {Author},
  title = {Motion Analysis Using Hilbert-Huang Transform},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/username/motionAnalysisHHT}}
}
```

## Contact

For questions or collaboration opportunities, please open an issue in this repository. 
