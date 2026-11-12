# Article Scripts

Scripts that produce every figure and table of the article [Overcoming spectrophotometer measurement limitations](../README.md).

## Contents

- [Overview](#overview)
- [Setup](#setup)
   - [1. Install Python](#1-install-python)
   - [2. Create and Set Up the Virtual Environment](#2-create-and-set-up-the-virtual-environment)
   - [Usage](#usage)
- [Scripts](#scripts)

## Overview

The scripts read the Game Boy Color spectra in `handhelds/Nintendo GBC/[2026-11-09][Pokefan531]/measurements/` (`gbc-all-top.ods`, `gbc-all-middle.ods`, `gbc-all-bottom.ods`). They never modify them.

- Figures are written to [`../img/`](../img/).
- Tables are printed to the console as Markdown.

## Setup

### 1. Install Python

Use Python 3.12 through 3.14. Check whether Python is already installed:

```bash
python3 --version
```

#### Linux

On Debian or Ubuntu, install Python and virtual environment support with:

```bash
sudo apt update
sudo apt install python3 python3-venv
```

On other Linux distributions, install Python 3 and its `venv` support using the distribution's package manager.

#### macOS

Install Python with [Homebrew](https://brew.sh/):

```bash
brew install python
```

Alternatively, use the installer from [python.org](https://www.python.org/downloads/macos/).

### 2. Create and Set Up the Virtual Environment

Open a terminal in the directory containing this README and `requirements.txt`. Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

With the environment active, install the exact dependencies listed in `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

When finished, close the virtual environment with:

```bash
deactivate
```

### Usage

With the virtual environment activated, run the scripts from this directory in order:

```bash
python3 1_spectrum_to_xyz.py
python3 2_noise_floor.py
python3 3_band_below_420.py
python3 4_band_420_440.py
python3 5_evaluate_method.py --method cleaning
python3 5_evaluate_method.py --method truncation
python3 5_evaluate_method.py --method gaussian
python3 5_evaluate_method.py --method hold
python3 6_compare_methods.py
```

Each script prints its tables and lists the figures it saved.

## Scripts

| Script | Article section | Output |
|---|---|---|
| `common.py` | – | Shared code: data loading, spectrum to XYZ (D50, CIE 1931 2°), CAM16-UCS ΔE, tables, swatches |
| `methods.py` | 3, 5 | Cleaning, truncation, Gaussian and hold methods |
| `1_spectrum_to_xyz.py` | 1 | `1_cmfs_d50.png`, `1_white_ramp.png`, share of X, Y, Z below the cutoff and above 700 nm |
| `2_noise_floor.py` | 2.3 | Differences between orientations, Y per orientation, reading-to-reading noise floor |
| `3_band_below_420.py` | 3 | `3_zoom_380_470.png`, negative values per region, baseline statistics |
| `4_band_420_440.py` | 4 | Baseline leak table, zones table, cutoff candidates table, `4_drop_shape.png`, `4_zones.png` |
| `5_evaluate_method.py --method NAME` | 3, 5 | `method_NAME_spectrum.png`, `method_NAME_products.png`, `method_NAME_swatches.png`, reading 31 tables, ramp tables, implied reflectance table |
| `6_compare_methods.py` | 6 | Comparison tables, `6_delta_e.png`, `6_xy.png` |

The cutoff used by sections 5 and 6 is `CUTOFF` in `common.py`.
