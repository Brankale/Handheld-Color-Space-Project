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

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install numpy colour-science
```

**Required packages:**
- `numpy` - numerical computing library
- `colour-science` - comprehensive color science library

## Usage

Run either script directly from the command line:

```bash
python gamma.py
```

```bash
python conversion_matrices.py
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


