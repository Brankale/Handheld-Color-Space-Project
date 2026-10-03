# Color Analysis Scripts

This directory contains Python scripts for analyzing and characterizing handheld console display colorspaces based on colorimeter measurements.

## Overview

These scripts perform color science calculations to understand how handheld console displays reproduce colors. They use measured XYZ tristimulus values (standard color measurements) to compute:

- **Display gamma curves** - how the display responds to different input levels
- **Color transformation matrices** - mathematical conversions between the display's color space and standard color spaces
- **Chromatic adaptation** - adjustments needed to account for the display's white point

## Scripts

### `gamma.py`

Calculates the **local gamma** for each RGB channel across different brightness levels.

**What it does:**
- Takes colorimeter measurements of the display at different gray levels (from black to white)
- Computes how each RGB channel responds to input values
- Returns gamma values that describe the display's brightness curve

**Input data:**
- `R_XYZ`, `G_XYZ`, `B_XYZ` - XYZ measurements of red, green, and blue primaries at full intensity (RGB 255)
- `GREYSCALE_XYZ` - XYZ measurements of neutral gray at multiple levels from black to white (number of measurements depends on the display's bit depth or measurement granularity)

**Output:**
- Array of local gamma values for each gray level and each RGB channel

### `conversion_matrices.py`

Generates **color transformation matrices** for converting between the handheld display colorspace and standard color spaces.

**What it does:**
- Normalizes raw XYZ measurements (removes black point artifacts, scales to white point)
- Creates a custom RGB colorspace definition based on the display's primaries
- Computes the RGB→XYZ transformation matrix
- Calculates chromatic adaptation transform (CAT) using the Bradford method to adapt to D65 illuminant

**Input data:**
- `HANDHELD_R/G/B_XYZ_RAW` - XYZ measurements of RGB primaries at maximum intensity
- `HANDHELD_BLACK_XYZ_RAW` - XYZ measurement of the display at RGB(0,0,0)
- `HANDHELD_WHITE_XYZ_RAW` - XYZ measurement of the display at RGB(255,255,255)

**Output:**
- RGB→XYZ conversion matrix
- Bradford chromatic adaptation transform matrices (with and without black level correction)

## Installation

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

## Usage

With the virtual environment activated, run a script from this directory:

```bash
python3 gamma.py
```

```bash
python3 conversion_matrices.py
```

Each script will print its calculated results to the console.

## Using the Output in RetroArch Shaders

The matrices and gamma values calculated by these scripts can be directly integrated into RetroArch's color correction shaders to accurately reproduce the original handheld console display characteristics on modern screens.

## Modifying Measurement Data

To analyze a different display:

1. **Measure your display** with a colorimeter:
   - RGB primaries at maximum intensity: (255,0,0), (0,255,0), (0,0,255)
   - Black level: (0,0,0)
   - White level: (255,255,255)
   - Grayscale ramp: evenly spaced levels from 0 to 255

2. **Replace the XYZ values** at the top of each script with your measurements

3. **Run the script** to generate results for your display


