# Color Analysis Scripts

This directory contains Python scripts for analyzing and characterizing handheld console display colorspaces based on display measurements.

## Contents

- [Overview](#overview)
- [Setup](#setup)
   - [1. Install Python](#1-install-python)
   - [2. Create and Set Up the Virtual Environment](#2-create-and-set-up-the-virtual-environment)
   - [Usage](#usage)
- [Scripts](#scripts)
   - [`gamma.py`](#gammapy)
   - [`conversion_matrices.py`](#conversionmatricespy)
- [CHC File Parser Library](#chc-file-parser-library)

## Overview

These scripts perform color science calculations to understand how handheld console displays reproduce colors. They use measured display data to compute:

- **Display gamma curves** - how the display responds to different input levels
- **Color transformation matrices** - mathematical conversions between the display's color space and standard color spaces
- **Chromatic adaptation** - adjustments needed to account for the display's white point

The matrices and gamma values calculated by these scripts can be directly integrated into RetroArch's color correction shaders to accurately reproduce the original handheld console display characteristics on modern screens.

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

With the virtual environment activated, run a script from this directory:

```bash
python3 gamma.py
```

```bash
python3 conversion_matrices.py
```

Each script will print its calculated results to the console.

## Scripts

### `gamma.py`

Calculates the **local gamma** for each RGB channel across different brightness levels.

**What it does:**
- Uses XYZ measurements of the display at different gray levels (from black to white)
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

## CHC File Parser

[chc.py](chc.py) extracts measurements directly from HCFR `.chc` files for analysis without installing HCFR, enabling users to perform analysis on Linux and macOS where the program is not available.

Compared with HCFR's built-in XLS export, this parser provides additional stored data useful for analysis in this project, including:

- **All stored spectra**, with wavelength metadata and original samples, including grayscale, saturation sweeps and free measurements when available. HCFR's XLS export includes spectra only for the primaries and on/off white.
- **Saturation-patch measurements** for red, green, blue, yellow, cyan and magenta sweeps, including stored XYZ and spectra when available.

The parser is distributed under **GPL v2**, with the complete license included in [chc.py](chc.py). Its format reference is the [HCFR SourceForge repository](https://sourceforge.net/p/hcfr/code/) (`https://git.code.sf.net/p/hcfr/code`).

> [!WARNING]
> This script was developed entirely using AI. Only its output was reviewed while the implementation was not reviewed.

Supported layout:

- Document version: **3**
- Measurement version: **17**
- Color record versions: **1 through 6**
- Spectrum and matrix version: **1**
- Verified binary layout: **Win32 little-endian**

### Usage

From the repository root:

```python
from scripts.chc import read_chc

measurements = read_chc("report.chc")
red_xyz = measurements.primaries["R"].xyz
first_gray = measurements.grayscale[0]
if first_gray.spectrum is not None:
      samples = first_gray.spectrum.samples
```

`read_chc(path)` reads a CHC file and returns its measurements as a read-only `ChcMeasurements` object. From a script in this directory, import it with `from chc import read_chc`.

### Raw Data Contract

- `grayscale`, `near_black`, `near_white`, and `free_measurements` preserve
   record order. `saturations` has separate `R`, `G`, `B`, `Y`, `C`, `M` groups.
- `primaries` contains `R`, `G`, `B`; `secondaries` contains `Y`, `C`, `M`.
- `user_black`, `on_off_black`, `on_off_white`, `ansi_black`, `ansi_white`,
   and `prime_white` are separate records. No fallback or black substitution
   from HCFR's application loader is applied.
- Each `ColorMeasurement` exposes original `xyz`, optional `lux`, optional
   `spectrum`, its record `version`, and document-relative `file_offset`.
   Values retain the precision of stored doubles. No normalization, black
   subtraction, correction, matrix transform, interpolation, or rounding is
   performed. "Raw" means stored in the CHC file; the measuring software or
   device may already have processed the values before saving them.
- `is_valid` reports HCFR's criterion: all three XYZ components are strictly
   greater than `-1`. Invalid records, including the `-99999.99` no-data
   sentinel, are preserved. This property is not a physical plausibility check.
- `color_checker` and `color_checker_master` preserve their declared slot
   counts and stored indices. `None` denotes a slot not serialized by HCFR;
   no synthetic XYZ are created. Stored invalid records remain accessible.
- `Spectrum` retains `band_count`, `wavelength_min`, `wavelength_max`,
   `bandwidth`, sample tuple, serialization `version`, and `samples_offset`.
   Bandwidth remains an integer in old color records 2/4 and a double in 5/6.
   No derived wavelength grid or colorimetric integration is performed.
- `settings` retains all serialized measurement settings as named raw numeric
   values: BT.2390 parameters, luminance targets, tone-map/override flags,
   near-white clipping, white target, ColorChecker mode, color standard,
   DeltaE/gamma settings, manual chromaticities, and black override.
   Flags and enums remain stored integers; they do not modify measurements.
   `ire_scale_mode` is the final stored integer flag. Array indices alone
   must not be treated as exact stimulus percentages or RGB code values.
- `notes` is a `RawString` with original `data` bytes and `is_unicode`.
   Unicode-marked strings can use `notes.decode()` (strict UTF-16LE).
   Multibyte strings require an explicit encoding, for example
   `notes.decode("cp1252")` **only if that code page is known**. The CHC string
   does not identify its original multibyte code page. There is no automatic
   UTF-8 fallback or replacement of undecodable characters.
