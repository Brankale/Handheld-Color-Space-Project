# Overcoming spectrophotometer measurement limitations

*Reconstructing unreliable spectral regions: a case study with Game Boy Color measurements and an X-Rite ColorMunki Photo*

A reflectance spectrum describes how much light a surface reflects at each wavelength. To measure it, we use a spectrophotometer, but not every part of its reported spectrum is necessarily reliable. In the Game Boy Color measurements examined here, the X-Rite ColorMunki Photo produces unreliable readings below about 440 nm and noisy readings above 700 nm.

The aim of this article is to determine how to reconstruct the unreliable part of these spectra from the usable measurements. We first examine the affected regions and their influence on the colour coordinates calculated from the spectrum. We then compare four approaches, from removing suspect values to extrapolating from reliable bands, and assess their assumptions and limitations. Without an independent reference measurement, this comparison cannot establish the true spectrum.

The article is written for two audiences:

- If you only want the answer, read the **In short** lines at the start of each section and the [Conclusions](#7-conclusions).
- If you want to check or reuse the analysis, every number, table and figure comes from a script you can run yourself.

## Index

- [1 Introduction](#1-introduction)
   - [1.1 From spectrum to XYZ](#11-from-spectrum-to-xyz)
   - [1.2 The problem](#12-the-problem)
   - [1.3 Why it matters](#13-why-it-matters)
   - [1.4 Roadmap](#14-roadmap)
- [2 Data and evaluation](#2-data-and-evaluation)
   - [2.1 Measurements](#21-measurements)
   - [2.2 Metrics](#22-metrics)
   - [2.3 Noise floor](#23-noise-floor)
- [3 The band at or below 420 nm](#3-the-band-at-or-below-420-nm)
   - [3.1 What the data show](#31-what-the-data-show)
   - [3.2 Cleaning](#32-cleaning)
- [4 The band from 420 to 440 nm](#4-the-band-from-420-to-440-nm)
   - [4.1 Baseline leak](#41-baseline-leak)
   - [4.2 Shape of the drop](#42-shape-of-the-drop)
   - [4.3 Reliability zones](#43-reliability-zones)
   - [4.4 Choosing the cutoff](#44-choosing-the-cutoff)
- [5 Reconstructing the region below the cutoff](#5-reconstructing-the-region-below-the-cutoff)
   - [5.1 Truncation](#51-truncation)
   - [5.2 Gaussian extrapolation](#52-gaussian-extrapolation)
   - [5.3 Hold](#53-hold)
- [6 Comparison and choice](#6-comparison-and-choice)
- [7 Conclusions](#7-conclusions)
- [8 Limitations and open questions](#8-limitations-and-open-questions)
- [9 References](#9-references)

## 1 Introduction

> **In short:** unreliable spectral readings also affect the colour coordinates calculated from them. We first explain that calculation, then examine the suspect regions to decide where reconstruction is needed.

### 1.1 From spectrum to XYZ

The instrument measures the **reflectance** $R(\lambda)$ of the screen: the share of light it reflects at each wavelength, in percent. 0 % means nothing is reflected, 100 % means as much as a perfect white. Our data have 106 bands from 380 to 730 nm, one every 3.33 nm.

A spectrum is not yet a colour. We get there in two steps, following the path of the light.

**1. Light hits the screen.** The reflected light depends on what illuminates the screen. For this analysis we choose **CIE D50**, a standard daylight illuminant. Multiplying its power by the reflectance, wavelength by wavelength, gives the light the screen sends back (Figure 1a).

![D50 times the reflectance gives the reflected light](img/1a_reflected_light.png)

*Figure 1a. D50 (left) times the reflectance of the brightest white of the Game Boy Color (centre: reading 31, 0°, raw data) gives the reflected light (right). Produced by `scripts/1_spectrum_to_xyz.py`.*

**2. The eye sees the reflected light.** The **CIE 1931 2° standard observer** describes the eye with three curves, $\bar{x}$, $\bar{y}$ and $\bar{z}$, one per coordinate. Multiplying the reflected light by each curve gives what the eye picks up at each wavelength. The area under each product is X, Y or Z (Figure 1b).

![Reflected light times the colour matching functions gives X, Y and Z](img/1b_light_to_xyz.png)

*Figure 1b. The reflected light of Figure 1a (left) times the CIE 1931 2° colour matching functions (centre). The coloured areas (right) are X, Y and Z. Produced by `scripts/1_spectrum_to_xyz.py`.*

This also tells us where measurement errors hurt most: a reflectance error counts more where both the light and the eye are strong. Z is most sensitive around 450 nm, where $\bar{z}$ peaks and D50 is already high; above 520 nm $\bar{z}$ is almost zero, so Z barely moves.

**Scale.** The areas are multiplied by a constant $k$, chosen so that a **perfect reflector** ($R = 100\ \%$ at every wavelength) has $Y = 100$. This puts XYZ on the same 0–100 scale as the values exported by `spotread`, and makes the perfect reflector the reference white for the colour differences in section 2.2. On this scale the Game Boy Color is very dark: its brightest white reaches only $Y \approx 0.6$–$1.0$ (0.62 in Figure 1b).

<details>
<summary><b>For the maths</b></summary>

With $S(\lambda)$ the illuminant and $\lambda_i$ the band centres:

$$
X = k\sum_i S(\lambda_i)\,R(\lambda_i)\,\bar{x}(\lambda_i),\qquad
Y = k\sum_i S(\lambda_i)\,R(\lambda_i)\,\bar{y}(\lambda_i),\qquad
Z = k\sum_i S(\lambda_i)\,R(\lambda_i)\,\bar{z}(\lambda_i)
$$

$$
k = \frac{1}{\sum_i S(\lambda_i)\,\bar{y}(\lambda_i)}
$$

- **Sensitivity to errors.** In the sum for X, the reflectance $R(\lambda_i)$ is multiplied by $k\,S(\lambda_i)\,\bar{x}(\lambda_i)$. This factor depends only on illuminant and observer, not on the screen: it is how much X changes for each unit of reflectance error in band $i$. The same holds for Y and Z with $\bar{y}$ and $\bar{z}$.
- **Wavelength grid.** D50 is resampled to 1 nm with colour-science, then D50 and the colour matching functions are linearly interpolated to the 106 measured band centres.

</details>

### 1.2 The problem

Figure 2 shows the 32 readings of the white ramp, from the darkest (0) to the brightest (31) level of the Game Boy Color screen.

![White ramp, raw spectra](img/1_white_ramp.png)

*Figure 2. Raw spectra of the white ramp, instrument at 0°. Produced by `scripts/1_spectrum_to_xyz.py`.*

Two regions are clearly wrong:

- **Below 440 nm.** Up to 420 nm every spectrum is a flat line, mostly below zero. A negative reflectance is physically impossible. Between 420 and 440 nm the curves climb steeply from that line to the real signal. Section 3 and section 4 study these two parts separately.
- **Above 700 nm.** The curves become ragged and fan out.

### 1.3 Why it matters

Look again at Figure 1b. The peak of $\bar{z}$ (446 nm) and the small blue lobe of $\bar{x}$ (442 nm) sit right at the edge of the bad region. Table 1 shows how much of each coordinate comes from the two unreliable regions.

*Table 1. Share of X, Y and Z coming from the bands below 440 nm and above 700 nm, reading 31, 0°, raw data. "Perfect reflector" is the theoretical $R = 100\ \%$ surface. Produced by `scripts/1_spectrum_to_xyz.py`.*

| Ramp | X < 440 | Y < 440 | Z < 440 | X > 700 | Y > 700 | Z > 700 |
|---|---:|---:|---:|---:|---:|---:|
| White | 2.2 % | 0.1 % | 11.9 % | 0.10 % | 0.03 % | 0.00 % |
| Red | 1.1 % | 0.1 % | 10.1 % | 0.13 % | 0.06 % | 0.00 % |
| Green | 0.8 % | 0.0 % | 5.3 % | 0.07 % | 0.02 % | 0.00 % |
| Blue | 2.7 % | 0.1 % | 9.3 % | 0.07 % | 0.02 % | 0.00 % |
| Yellow | 1.3 % | 0.1 % | 10.3 % | 0.13 % | 0.05 % | 0.00 % |
| Cyan | 2.5 % | 0.1 % | 10.5 % | 0.11 % | 0.03 % | 0.00 % |
| Magenta | 2.4 % | 0.1 % | 12.6 % | 0.11 % | 0.04 % | 0.00 % |
| Perfect reflector | 3.6 % | 0.1 % | 20.4 % | 0.11 % | 0.04 % | 0.00 % |

The illuminant also matters. The shares below 440 nm increase from D50 to D75, as more of the illuminant's energy lies at short wavelengths relative to the rest of the spectrum.

*Table 1a. Share of X and Z coming from bands below 440 nm under four daylight illuminants, reading 31, 0°, raw data. The perfect reflector has $R = 100\ \%$ at every wavelength. All calculations use the same 106 bands and CIE 1931 2° observer. Produced by `scripts/1_spectrum_to_xyz.py`.*

| Ramp | D50 X < 440 | D50 Z < 440 | D55 X < 440 | D55 Z < 440 | D65 X < 440 | D65 Z < 440 | D75 X < 440 | D75 Z < 440 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 2.2 % | 11.9 % | 2.5 % | 12.5 % | 3.2 % | 13.4 % | 3.8 % | 14.1 % |
| Red | 1.1 % | 10.1 % | 1.3 % | 10.4 % | 1.7 % | 11.0 % | 1.9 % | 11.3 % |
| Green | 0.8 % | 5.3 % | 1.0 % | 5.5 % | 1.2 % | 5.7 % | 1.3 % | 5.9 % |
| Blue | 2.7 % | 9.3 % | 3.1 % | 9.7 % | 3.8 % | 10.2 % | 4.3 % | 10.7 % |
| Yellow | 1.3 % | 10.3 % | 1.5 % | 10.8 % | 2.0 % | 11.5 % | 2.3 % | 12.0 % |
| Cyan | 2.5 % | 10.5 % | 2.9 % | 11.0 % | 3.6 % | 11.9 % | 4.1 % | 12.4 % |
| Magenta | 2.4 % | 12.6 % | 2.8 % | 13.1 % | 3.5 % | 14.0 % | 4.1 % | 14.6 % |
| Perfect reflector | 3.6 % | 20.4 % | 4.2 % | 21.5 % | 5.4 % | 23.1 % | 6.4 % | 24.3 % |

What Table 1 tells us under D50:

- **Below 440 nm matters.** For a surface that reflects evenly, one fifth of Z and 3.6 % of X come from the bands the instrument gets wrong. The measured screens show less, because the raw data are already wrong there. The perfect reflector shows what is at stake.
- **Y is almost unaffected** (0.1 %). Brightness is safe, while chromaticity (the hue and saturation) is not.
- **Above 700 nm does not matter** for colour. All three coordinates get at most 0.13 % from that region. The rest of the article ignores it.

### 1.4 Roadmap

1. Section 2 describes the data and how we judge a method.
2. Section 3 analyses the flat region up to 420 nm and introduces **cleaning**, the first step of every method.
3. Section 4 analyses the steep region from 420 to 440 nm and chooses a **cutoff**: the first band we trust.
4. Section 5 tests three ways to fill the region below the cutoff: **truncation**, **Gaussian extrapolation** and **hold**.
5. Section 6 compares all methods and picks one.

All the figures and tables are produced by the Python scripts in [scripts/](scripts/). See [scripts/README.md](scripts/README.md) to set them up and run them.

## 2 Data and evaluation

> **In short:** 672 spectra of a Game Boy Color, measured in three instrument orientations. We compare each method against the raw data with CAM16-UCS ΔE. After the cleaning described in section 3, five repeated readings per patch from an earlier session provide a historical repeatability reference of ΔE 0.22, not a significance threshold.

### 2.1 Measurements

| Item | Value |
|---|---|
| Handheld | Nintendo Game Boy Color |
| Instrument | X-Rite ColorMunki Photo (spectrophotometer), calibrated |
| Software | ArgyllCMS `spotread` |
| Screen protector | Present, not removed |
| Ramps | White, Red, Green, Blue, Yellow, Cyan, Magenta |
| Readings per ramp | 32 (levels 0 to 31 of the console's 5-bit colour) |
| Orientations | 0°, 90° and 180° (instrument rotated on the screen) |
| Spectral range | 380–730 nm, 106 bands, 3.33 nm step |
| Total | 3 orientations × 7 ramps × 32 readings = 672 spectra |

The raw data are in [`handhelds/Nintendo GBC/[2026-11-09][Pokefan531]/measurements/`](../../handhelds/Nintendo%20GBC/%5B2026-11-09%5D%5BPokefan531%5D/measurements/). The files `gbc-all-top.ods`, `gbc-all-middle.ods` and `gbc-all-bottom.ods` hold the 0°, 90° and 180° orientations.

> [!NOTE]
> **TODO:** add photos of the instrument placed on the screen at 0°, 90° and 180°.

### 2.2 Metrics

Every method changes the spectrum, so it also changes XYZ. We compare the XYZ of each method with the XYZ of the **raw data**, the spectra exactly as the instrument delivered them.

| Metric | What it measures |
|---|---|
| ΔX, ΔY, ΔZ | Signed difference, method minus raw, on the 0–100 scale |
| Δxy | Distance between the two points on the CIE 1931 xy chromaticity diagram |
| ΔE | Perceived colour difference in CAM16-UCS |

- **ΔE settings.** XYZ is used on its 0–100 scale. The reference white is the perfect reflector under D50 ($Y = 100$), computed on the same 106 bands. Every patch of this screen is therefore very dark relative to the reference white. The adapting luminance is $L_A = 318.31$ cd/m², the background is $Y_b = 20$ and the surround is *Average*.
- **Reading ΔE.** As a practical guideline here, differences start to become visible above about ΔE 3. This is not a universal threshold: visibility depends on the colours and viewing conditions.
- **The raw data are not the truth.** They are just the common reference. ΔE tells us how much a method changes the colour. It does not tell us whether the change is correct. We judge correctness separately, with physical plausibility checks.
- **Swatches.** XYZ values calculated under D50 are converted to sRGB. For display only, a fixed exposure maps $Y = 1$ (1 % reflectance) to sRGB white; otherwise every swatch would be almost black. Colours outside sRGB are clipped and marked with `*`.

For each method we report:

- one table per orientation for reading 31, the full-intensity colour;
- one table per ramp summarising all 32 readings.

### 2.3 Noise floor

A measured spectrum varies slightly from one acquisition to the next. To put the changes made by a reconstruction method in context, we estimate **repeatability** from repeated measurements of the same patch under the same acquisition conditions.

The source measurements were acquired on **9 May 2026**, in the report dated 13 May:

- [gbc-gamma1 2026-05-09.txt](../../handhelds/Nintendo%20GBC/%5B2026-05-13%5D%5BPokefan531%5D/measurements/gbc-gamma1%202026-05-09.txt).
- [gbc-gamma2 2026-05-09.txt](../../handhelds/Nintendo%20GBC/%5B2026-05-13%5D%5BPokefan531%5D/measurements/gbc-gamma2%202026-05-09.txt).

The [acquisition notes](../../handhelds/Nintendo%20GBC/%5B2026-05-13%5D%5BPokefan531%5D/measurements/README.md) identify the same physical Game Boy Color, a calibrated ColorMunki Photo and five readings per greyscale patch. Each file contains 32 blocks of five readings. These 320 historical spectra are used only for the repeatability estimate; they are not added to the 672 November spectra evaluated by the reconstruction methods.

**Preprocessing.** Before computing repeatability, we apply the cleaning described in [section 3.2](#32-cleaning) to every repeated spectrum: all bands up to and including **423.333 nm** and all negative reflectance values at any wavelength are set to zero. The first band retained is 426.667 nm, provided its value is non-negative. The source files are not modified.

**Calculation.** We integrate each cleaned reflectance spectrum under D50 with the CIE 1931 2° observer, exactly as in section 1.1. We do not use the XYZ or Lab columns already present in the exports. Each XYZ is converted to CAM16-UCS with the settings in section 2.2. For each file $f$ and patch block $p$, the five readings give ten distinct pairs:

$$
d_{f,p,a,b} = \left\|\mathbf{J}'_{f,p,a}-\mathbf{J}'_{f,p,b}\right\|_2,
\qquad 1 \leq a < b \leq 5
$$

Here $\mathbf{J}'$ denotes the three CAM16-UCS coordinates $(J',a',b')$, not lightness alone. Every comparison stays within one patch block in one file. We report the distances directly, without scaling them to a single-reading standard deviation.

*Table 2. Historical within-patch repeatability after section 3 cleaning. Each patch block contributes ten pairs. Produced by `scripts/2_noise_floor.py` from the two source files linked above.*

| Source | Patch blocks | Readings | Pairs | mean ΔE | p95 ΔE | max ΔE |
|---|---:|---:|---:|---:|---:|---:|
| gbc-gamma1 2026-05-09.txt | 32 | 160 | 320 | 0.10 | 0.21 | 0.36 |
| gbc-gamma2 2026-05-09.txt | 32 | 160 | 320 | 0.10 | 0.22 | 0.37 |
| All | 64 | 320 | 640 | 0.10 | 0.22 | 0.37 |

The pooled empirical 95th percentile is **ΔE = 0.22**. We use it below as a **historical repeatability reference after cleaning**. It describes differences between repeated readings after the bands through 423.333 nm and all negative values have been removed, not the repeatability of the unprocessed data, the uncertainty of a single reading or the accuracy of the instrument. The 640 pairs are not independent observations, because pairs within a block share readings. The method comparisons in sections 3, 5 and 6 remain against the raw November data, as defined in section 2.2; only the repeatability reference uses these cleaned historical spectra.

Repeatability varies by patch, so one pooled value does not describe every colour equally well. A change above 0.22 is larger than most observed historical repeat differences after cleaning; a change below it is not automatically noise. Neither result proves that a reconstruction is correct.

**Limits of this reference.** The repeated measurements cover greyscale patches in May, whereas the reconstruction analysis covers colour ramps in November. Session conditions may have changed, and repeatability for coloured patches is not established by these files. The reference is therefore a scale for comparison, not a verified noise floor for every November reading or a statistical significance threshold. Repeated acquisitions of the November colour patches would be needed to establish that directly.

## 3 The band at or below 420 nm

> **In short:** up to 420 nm the instrument returns a flat, mostly negative line that follows the brightness of the patch. It contains no spectral information, so we set it to zero.

### 3.1 What the data show

![Zoom on 380–470 nm](img/3_zoom_380_470.png)

*Figure 3. Raw spectra between 380 and 470 nm for all ramps at reading 31 (solid) and reading 0 (dotted), one panel per orientation. Produced by `scripts/3_band_below_420.py`.*

*Table 3. Negative reflectance values per region, all ramps and readings. Produced by `scripts/3_band_below_420.py`.*

| Orientation | ≤ 420 nm | 423.3–436.7 nm | 440–700 nm | > 700 nm |
|---|---:|---:|---:|---:|
| 0° | 2834 / 2912 | 97 / 1120 | 0 / 17696 | 0 / 2016 |
| 90° | 2249 / 2912 | 0 / 1120 | 0 / 17696 | 0 / 2016 |
| 180° | 2912 / 2912 | 150 / 1120 | 0 / 17696 | 0 / 2016 |

We call **baseline** the mean of the bands at or below 420 nm in one spectrum.

*Table 4. Baseline statistics per spectrum. "Max spread" is the largest difference between bands inside one baseline. The last two columns are correlations of the baseline with the reflectance at 450 nm and with Y. Produced by `scripts/3_band_below_420.py`.*

| Orientation | Range | Negative spectra | Max spread within baseline | corr(baseline, R450) | corr(baseline, Y) |
|---|---:|---:|---:|---:|---:|
| 0° | -0.417 … +0.037 | 218 / 224 | 0.0044 | 0.83 | 0.68 |
| 90° | -0.266 … +0.200 | 173 / 224 | 0.0044 | 0.94 | 0.75 |
| 180° | -0.370 … -0.011 | 224 / 224 | 0.0040 | 0.67 | 0.52 |

Observations:

- **The baseline is flat.** Inside one spectrum, the 13 bands from 380 to 420 nm differ by at most 0.0044 percentage points. A real surface would show some spectral shape. A flat line means the instrument reports one number repeated across all the bands.
- **It is mostly negative.** 615 of the 672 spectra have a negative baseline, down to −0.417 %. Reflectance cannot be negative.
- **It follows brightness.** The baseline is higher when the patch is brighter (correlation 0.67–0.94 with R450). It behaves like an offset that depends on the signal, not like a measured reflectance.
- **Negatives are confined to the blue end.** Some values between 423 and 437 nm are negative, but not a single band from 440 nm upward is.

### 3.2 Cleaning

#### Idea

The baseline carries no information about the screen. Replace it and the first contaminated transition band at 423.333 nm with zero, and remove every remaining negative value.

#### Technical details

- Bands up to and including 423.333 nm: $R = 0$.
- Every other band: $R = \max(R, 0)$.
- Bands from 426.667 nm upward are otherwise left untouched.

Every method in section 5 starts with this step.

Run `python scripts/5_evaluate_method.py --method cleaning` from this article's directory to regenerate the figures and print the three orientation tables below.

#### Assumptions and limits

- Zero is not a measurement either. It is simply the least harmful value: it adds nothing to XYZ. Section 5 replaces it with better estimates.
- Cleaning leaves the steep region from 426.667 to 436.667 nm in place. Section 4 shows that these bands are still contaminated by the baseline.

#### Spectrum

![Cleaning: implied reflectance](img/method_cleaning_spectrum.png)

*Figure 4. Reflectance after cleaning, reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

#### Reflectance × CMF

![Cleaning: R·x̄ and R·z̄](img/method_cleaning_products.png)

*Figure 5. $R\bar{x}$ and $R\bar{z}$ for White, Red and Blue at reading 31, 0°: raw data and cleaning. The area under these curves is what ends up in X and Z. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

#### All readings

Raw versus cleaned spectra: all 672 measurements, shown separately by instrument orientation. The dashed line is the historical repeatability p95 (0.22), not a significance threshold. All panels use the same scale, from 0 to 2.

![Cleaning: primary ramp colour differences](img/method_cleaning_delta_e_primaries.png)

*Figure 6. CAM16-UCS ΔE across the 32 readings of each primary ramp, separately for 0°, 90° and 180°. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

![Cleaning: secondary ramp and greyscale colour differences](img/method_cleaning_delta_e_secondaries_greyscale.png)

*Figure 7. CAM16-UCS ΔE across the 32 readings of each secondary ramp and the greyscale, separately for 0°, 90° and 180°. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

#### Swatches

![Cleaning: swatches](img/method_cleaning_swatches.png)

*Figure 8. For each ramp, the reading with the largest ΔE: raw data (left) and cleaning (right). Produced by `scripts/5_evaluate_method.py --method cleaning`.*

XYZ values calculated under D50 are converted to sRGB with the fixed display exposure described in section 2.2. Colours outside sRGB are clipped and marked with `*`. No chromatic adaptation or per-ramp brightness normalisation is applied.

#### Observations and verdict

ΔX, ΔY, ΔZ and Δxy refer to the full-level patch (reading #31), not ramp averages. Mean, p95 and max ΔE use all 32 readings of each ramp at the stated orientation; the “All ramps” row pools its 224 measurements. p95 describes the distribution of cleaning-induced changes, not repeatability.

ΔX, ΔY and ΔZ are cleaned minus raw on the `spotread` XYZ scale (perfect-reflector Y = 100). Removing a negative contribution increases Z, giving a positive ΔZ. Δxy is the chromaticity distance for the same patch. Patch deltas are rounded to four decimals; 0.0000 need not mean exactly zero.

*Table 5. Cleaning, 0°. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

| Colour | ΔX | ΔY | ΔZ | Δxy | Mean ΔE | p95 ΔE | Max ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Red | +0.0016 | 0.0000 | +0.0077 | 0.0044 | 0.66 | 1.11 | 1.38 |
| Green | +0.0022 | +0.0001 | +0.0105 | 0.0052 | 0.63 | 1.01 | 1.11 |
| Blue | +0.0013 | 0.0000 | +0.0063 | 0.0030 | 0.63 | 1.50 | 1.63 |
| Yellow | +0.0005 | 0.0000 | +0.0026 | 0.0010 | 0.30 | 0.71 | 0.97 |
| Cyan | -0.0003 | 0.0000 | -0.0013 | 0.0005 | 0.34 | 0.92 | 0.94 |
| Magenta | -0.0001 | 0.0000 | -0.0003 | 0.0001 | 0.22 | 0.56 | 0.66 |
| White | -0.0009 | 0.0000 | -0.0044 | 0.0012 | 0.26 | 0.89 | 1.04 |
| All ramps | N/A | N/A | N/A | N/A | 0.43 | 1.01 | 1.63 |

*Table 6. Cleaning, 90°. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

| Colour | ΔX | ΔY | ΔZ | Δxy | Mean ΔE | p95 ΔE | Max ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Red | +0.0001 | 0.0000 | +0.0006 | 0.0003 | 0.23 | 0.80 | 0.87 |
| Green | +0.0007 | 0.0000 | +0.0032 | 0.0011 | 0.27 | 0.81 | 0.88 |
| Blue | -0.0015 | 0.0000 | -0.0072 | 0.0024 | 0.26 | 0.58 | 0.69 |
| Yellow | -0.0006 | 0.0000 | -0.0027 | 0.0007 | 0.10 | 0.30 | 0.31 |
| Cyan | -0.0021 | -0.0001 | -0.0101 | 0.0023 | 0.24 | 0.66 | 0.73 |
| Magenta | -0.0022 | -0.0001 | -0.0106 | 0.0025 | 0.20 | 0.33 | 0.42 |
| White | -0.0029 | -0.0001 | -0.0139 | 0.0025 | 0.21 | 0.44 | 0.46 |
| All ramps | N/A | N/A | N/A | N/A | 0.22 | 0.64 | 0.88 |

*Table 7. Cleaning, 180°. Produced by `scripts/5_evaluate_method.py --method cleaning`.*

| Colour | ΔX | ΔY | ΔZ | Δxy | Mean ΔE | p95 ΔE | Max ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Red | +0.0019 | +0.0001 | +0.0092 | 0.0062 | 0.69 | 0.85 | 0.96 |
| Green | +0.0013 | 0.0000 | +0.0061 | 0.0033 | 0.69 | 1.13 | 1.30 |
| Blue | +0.0014 | 0.0000 | +0.0065 | 0.0035 | 0.67 | 1.18 | 1.28 |
| Yellow | +0.0009 | 0.0000 | +0.0042 | 0.0017 | 0.50 | 0.74 | 1.09 |
| Cyan | -0.0003 | 0.0000 | -0.0014 | 0.0005 | 0.51 | 0.77 | 0.83 |
| Magenta | -0.0007 | 0.0000 | -0.0032 | 0.0012 | 0.58 | 0.89 | 0.93 |
| White | -0.0005 | 0.0000 | -0.0024 | 0.0007 | 0.36 | 0.75 | 0.81 |
| All ramps | N/A | N/A | N/A | N/A | 0.57 | 0.98 | 1.30 |

- **Small effect overall.** Mean ΔE is 0.41 and the maximum is 1.63 (Blue #4, 0°). At reading 31 the ΔE stays at or below 0.49. Across all readings, 66 % of the spectra change by more than the historical repeatability reference after cleaning of 0.22. This is a comparison of magnitudes, not a significance test.
- **Y does not move.** The magnitude of ΔY stays below 0.0001.
- **Z mostly rises.** Removing a negative baseline adds back what the baseline was subtracting. Removing positive values through 423.333 nm can lower Z instead, for example White #31 at 90°: ΔZ = −0.0139.
- **Dark readings change most.** The largest ΔE values are at readings 0 to 8. There the baseline is large compared to the real signal.
- **Verdict: necessary, not sufficient.** Cleaning zeros bands through 423.333 nm and removes negative values, but it keeps the 426.667–436.667 nm region, which section 4 shows to be contaminated.

## 4 The band from 420 to 440 nm

> **In short:** between 420 and 440 nm the signal is a blend of real reflectance and the baseline. The baseline's share drops below 5 % only from 440 nm. That is our cutoff.

Figure 3 shows a steep climb from the baseline at 420 nm to the real signal around 440 nm. The question is: which of these bands can we trust?

### 4.1 Baseline leak

**Idea.** The baseline changes from reading to reading in a way that has nothing to do with the screen. If a band follows those changes, part of the baseline has *leaked* into it.

**How the leak is measured,** for each band, ramp and orientation:

1. Remove the real brightness trend. Within one ramp, regress the band on the mean of a trusted reference region (446–461 nm) and keep the residuals. Do the same for the baseline.
2. Regress the band residuals on the baseline residuals. The slope is the **leak**: the fraction of the baseline jitter that shows up in the band. 100 % means the band is the baseline; 0 % means the band ignores it.
3. Also record the correlation between the two residuals.

*Table 8. Baseline leak per band. Leak is the mean over the 7 ramps. Correlation is shown as mean (min) over the 7 ramps. The last column counts negative values over all 672 spectra. Produced by `scripts/4_band_420_440.py`.*

| Band (nm) | Leak 0° | Leak 90° | Leak 180° | Corr 0° | Corr 90° | Corr 180° | Negatives / 672 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 420.0 | 100.5 % | 100.5 % | 100.5 % | 1.00 (1.00) | 1.00 (1.00) | 1.00 (1.00) | 615 |
| 423.3 | 37.8 % | 43.2 % | 34.8 % | 0.77 (0.58) | 0.70 (0.53) | 0.81 (0.64) | 247 |
| 426.7 | 13.6 % | 19.3 % | 16.6 % | 0.44 (0.23) | 0.45 (0.26) | 0.49 (-0.07) | 0 |
| 430.0 | 7.9 % | 11.6 % | 13.5 % | 0.46 (0.11) | 0.36 (0.22) | 0.52 (0.05) | 0 |
| 433.3 | 4.1 % | 7.3 % | 7.4 % | 0.39 (-0.16) | 0.26 (0.02) | 0.46 (-0.08) | 0 |
| 436.7 | 2.1 % | 7.0 % | 5.8 % | 0.34 (-0.32) | 0.27 (-0.14) | 0.52 (-0.05) | 0 |
| 440.0 | 0.0 % | 3.5 % | 2.4 % | 0.14 (-0.35) | 0.23 (-0.44) | 0.36 (-0.60) | 0 |
| 443.3 | 0.2 % | 2.3 % | 1.8 % | 0.04 (-0.35) | 0.18 (-0.55) | 0.26 (-0.72) | 0 |
| 446.7 | 0.4 % | 2.2 % | 0.9 % | 0.08 (-0.33) | 0.26 (-0.07) | 0.12 (-0.53) | 0 |
| 450.0 | 0.3 % | 0.7 % | 0.4 % | 0.07 (-0.34) | 0.12 (-0.17) | 0.03 (-0.55) | 0 |

Observations:

- **420 nm is the baseline** (leak 100 %, correlation 1.00).
- **The leak fades over about 15 nm.** 423.3 nm still carries 35–43 % of the baseline jitter and has 247 negative values. By 430 nm the leak is down to 8–14 %, and by 436.7 nm to 2–7 %.
- **From 440 nm the leak is at the level of the reference region.** 446.7 nm overlaps the reference region, so it cannot be contaminated, yet it still shows a leak of up to 2.2 %. That is the background level of this estimate. 440 nm (at most 3.5 %) is in the same range.

### 4.2 Shape of the drop

If the climb from 420 to 440 nm were the real reflectance of the screen, each colour would climb in its own way. Figure 9 divides each spectrum by its value at 450 nm, so only the shape is left.

![Shape of the drop](img/4_drop_shape.png)

*Figure 9. Reflectance divided by reflectance at 450 nm, mean of readings 16–31, one line per ramp and one panel per orientation. Produced by `scripts/4_band_420_440.py`.*

- **Below about 437 nm, all seven ramps collapse onto the same curve.** The shape of the drop does not depend on the colour of the patch.
- **Above 440 nm, the curves separate by colour,** as real reflectance should.

A common shape points to something that affects every colour equally. That is either the instrument itself, such as the edge of its usable range smeared by its optical bandwidth, or a layer common to the whole screen, such as the polarizer or the screen protector. The data cannot tell these apart (see [section 8](#8-limitations-and-open-questions)). Either way, the bands below 437 nm do not tell us anything about the colour of each patch.

### 4.3 Reliability zones

Each band is assigned a zone from its worst leak over the three orientations:

| Zone | Rule |
|---|---|
| baseline | Part of the flat line (≤ 420 nm) |
| invalid | Negative values, or leak ≥ 25 % |
| contaminated | Leak ≥ 10 % |
| grey | Leak ≥ 5 % |
| reliable | Leak < 5 % |

The 5 % threshold sits just above the background level of the estimate (2.2 % at 446.7 nm, section 4.1).

*Table 9. Zone of each band. Produced by `scripts/4_band_420_440.py`.*

| Band (nm) | Max leak | Negatives | Zone |
|---|---:|---:|---:|
| 420.0 | 100.5 % | 615 | baseline |
| 423.3 | 43.2 % | 247 | invalid |
| 426.7 | 19.3 % | 0 | contaminated |
| 430.0 | 13.5 % | 0 | contaminated |
| 433.3 | 7.4 % | 0 | grey |
| 436.7 | 7.0 % | 0 | grey |
| 440.0 | 3.5 % | 0 | reliable |
| 443.3 | 2.3 % | 0 | reliable |
| 446.7 | 2.2 % | 0 | reliable |
| 450.0 | 0.7 % | 0 | reliable |

![Reliability zones](img/4_zones.png)

*Figure 10. Reliability zones over the raw spectra at reading 31, 0°. Produced by `scripts/4_band_420_440.py`.*

### 4.4 Choosing the cutoff

The **cutoff** is the first band we keep. Everything below it is replaced in section 5. Choosing it is a trade-off:

- a lower cutoff keeps more measured data but lets more baseline in;
- a higher cutoff is cleaner but leaves more to reconstruct.

*Table 10. Cutoff candidates. "Worst leak ≥ cutoff" is the highest leak among the bands from the cutoff up to 450 nm. "X below" and "Z below" are the shares of X and Z of a perfect reflector under D50 that lie below the cutoff and must be reconstructed. Produced by `scripts/4_band_420_440.py`.*

| Cutoff (nm) | Zone | Worst leak ≥ cutoff | Negatives ≥ cutoff | X below | Z below |
|---|---:|---:|---:|---:|---:|
| 430.0 | contaminated | 13.5 % | 0 | 1.6 % | 9.1 % |
| 433.3 | grey | 7.4 % | 0 | 2.2 % | 12.2 % |
| 436.7 | grey | 7.0 % | 0 | 2.8 % | 16.0 % |
| 440.0 | reliable | 3.5 % | 0 | 3.6 % | 20.4 % |
| 443.3 | reliable | 2.3 % | 0 | 4.4 % | 25.5 % |

**Decision: cutoff at 440 nm,** the lowest band in the reliable zone. Going lower would keep bands that still carry 7 % or more of the baseline. Going higher would add 5 percentage points of Z to reconstruct without making the data noticeably cleaner.

The price is that 20.4 % of Z and 3.6 % of X of a perfect reflector must be reconstructed.

## 5 Reconstructing the region below the cutoff

> **In short:** we tried three ways to fill the gap below 440 nm. Assuming zero reflectance is too low, and a Gaussian fit invents a violet peak that the measured spectra do not show. Holding the 440 nm value constant is the most plausible choice.

All three methods share the same steps:

1. Clean the spectrum (section 3.2).
2. Keep every band from 440 nm upward unchanged.
3. Replace the bands below 440 nm with an estimate.

They differ only in step 3. To check whether the estimate is physically possible, we compute the **implied reflectance**: the reflectance that the method effectively assumes below 440 nm. A passive screen without fluorescence cannot reflect more light than it receives, so an implied reflectance above 100 % is impossible. This screen reflects about 1 %, so that limit is far away. A stricter check compares the implied reflectance with the highest value measured in the same spectrum from 440 nm upward: a method that exceeds it adds a violet peak that the reliable part of the spectrum gives no sign of.

### 5.1 Truncation

#### Idea

Assume the screen reflects nothing below 440 nm.

#### Technical details

- $R(\lambda) = 0$ for $\lambda < 440$ nm.
- The method adds nothing to X, Y and Z below the cutoff.

#### Assumptions and limits

- The method assumes that the reflectance falls from its 440 nm value (0.3–0.6 % at reading 31, Figure 3) to zero in one step. No real material behaves like that.
- It is a **lower bound**: the true contribution of the region cannot be smaller than zero.

#### Spectrum

![Truncation: implied reflectance](img/method_truncation_spectrum.png)

*Figure 11. Reflectance implied by truncation, reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method truncation`.*

#### Reflectance × CMF

![Truncation: R·x̄ and R·z̄](img/method_truncation_products.png)

*Figure 12. $R\bar{x}$ and $R\bar{z}$ for White, Red and Blue at reading 31, 0°: raw data and truncation. Produced by `scripts/5_evaluate_method.py --method truncation`.*

#### Reading 31

*Table 11. Truncation, reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method truncation`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.5591 | 0.6206 | 0.4485 | -0.0123 | -0.0006 | -0.0604 | 0.0178 | 1.98 |
| Red | 0.3667 | 0.3113 | 0.1853 | -0.0042 | -0.0002 | -0.0208 | 0.0124 | 1.01 |
| Green | 0.3420 | 0.4328 | 0.2582 | -0.0029 | -0.0002 | -0.0146 | 0.0074 | 0.57 |
| Blue | 0.2240 | 0.2718 | 0.3030 | -0.0063 | -0.0003 | -0.0310 | 0.0157 | 1.61 |
| Yellow | 0.5085 | 0.5294 | 0.2908 | -0.0067 | -0.0003 | -0.0333 | 0.0131 | 1.19 |
| Cyan | 0.3817 | 0.5016 | 0.4073 | -0.0097 | -0.0005 | -0.0476 | 0.0172 | 1.68 |
| Magenta | 0.3986 | 0.3828 | 0.3303 | -0.0096 | -0.0005 | -0.0474 | 0.0190 | 2.08 |

*Table 12. Truncation, reading 31, 90°. Produced by `scripts/5_evaluate_method.py --method truncation`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.8999 | 1.0050 | 0.7125 | -0.0203 | -0.0009 | -0.0997 | 0.0183 | 2.25 |
| Red | 0.5192 | 0.4193 | 0.2415 | -0.0079 | -0.0004 | -0.0389 | 0.0170 | 1.49 |
| Green | 0.4718 | 0.6127 | 0.3464 | -0.0064 | -0.0003 | -0.0317 | 0.0118 | 0.96 |
| Blue | 0.2913 | 0.3668 | 0.4420 | -0.0133 | -0.0006 | -0.0652 | 0.0228 | 2.46 |
| Yellow | 0.8088 | 0.8398 | 0.4291 | -0.0113 | -0.0005 | -0.0554 | 0.0142 | 1.44 |
| Cyan | 0.5643 | 0.7793 | 0.6273 | -0.0162 | -0.0007 | -0.0796 | 0.0189 | 1.96 |
| Magenta | 0.6123 | 0.5798 | 0.5233 | -0.0175 | -0.0008 | -0.0857 | 0.0217 | 2.58 |

*Table 13. Truncation, reading 31, 180°. Produced by `scripts/5_evaluate_method.py --method truncation`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.5478 | 0.6051 | 0.4389 | -0.0117 | -0.0006 | -0.0577 | 0.0174 | 1.93 |
| Red | 0.3188 | 0.2655 | 0.1559 | -0.0030 | -0.0002 | -0.0151 | 0.0106 | 0.81 |
| Green | 0.3133 | 0.3889 | 0.2313 | -0.0038 | -0.0002 | -0.0187 | 0.0104 | 0.79 |
| Blue | 0.2106 | 0.2486 | 0.2724 | -0.0060 | -0.0003 | -0.0296 | 0.0165 | 1.69 |
| Yellow | 0.4912 | 0.5093 | 0.2771 | -0.0059 | -0.0003 | -0.0293 | 0.0121 | 1.08 |
| Cyan | 0.3644 | 0.4808 | 0.3894 | -0.0095 | -0.0004 | -0.0467 | 0.0177 | 1.70 |
| Magenta | 0.3938 | 0.3735 | 0.3267 | -0.0105 | -0.0005 | -0.0517 | 0.0209 | 2.22 |

#### All readings

<details>
<summary>Truncation: one table per ramp, readings 0–31 (produced by <code>scripts/5_evaluate_method.py --method truncation</code>)</summary>

**White**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0125 … -0.0009 | -0.0006 … -0.0001 | -0.0613 … -0.0047 | 0.0144 ± 0.0038 | 1.40 ± 0.47 | 1.99 (#30) |
| 90° | -0.0203 … -0.0036 | -0.0009 … -0.0002 | -0.0997 … -0.0178 | 0.0164 ± 0.0015 | 1.77 ± 0.32 | 2.26 (#29) |
| 180° | -0.0117 … -0.0015 | -0.0006 … -0.0001 | -0.0577 … -0.0078 | 0.0123 ± 0.0026 | 1.08 ± 0.37 | 1.94 (#30) |

**Red**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0044 … -0.0001 | -0.0002 … -0.0001 | -0.0219 … -0.0008 | 0.0085 ± 0.0028 | 0.66 ± 0.24 | 1.06 (#29) |
| 90° | -0.0084 … -0.0024 | -0.0004 … -0.0002 | -0.0413 … -0.0119 | 0.0155 ± 0.0026 | 1.34 ± 0.21 | 1.60 (#24) |
| 180° | -0.0031 … -0.0007 | -0.0002 … -0.0001 | -0.0154 … -0.0037 | 0.0070 ± 0.0022 | 0.49 ± 0.17 | 0.84 (#30) |

**Green**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0035 … -0.0005 | -0.0002 … -0.0001 | -0.0177 … -0.0028 | 0.0062 ± 0.0023 | 0.46 ± 0.18 | 0.71 (#24) |
| 90° | -0.0069 … -0.0028 | -0.0003 … -0.0002 | -0.0338 … -0.0140 | 0.0121 ± 0.0007 | 0.98 ± 0.10 | 1.31 (#0) |
| 180° | -0.0038 … +0.0003 | -0.0002 … 0.0000 | -0.0187 … +0.0013 | 0.0061 ± 0.0025 | 0.43 ± 0.19 | 0.79 (#31) |

**Blue**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0068 … -0.0003 | -0.0003 … -0.0001 | -0.0335 … -0.0018 | 0.0118 ± 0.0051 | 1.22 ± 0.54 | 1.73 (#30) |
| 90° | -0.0137 … -0.0032 | -0.0006 … -0.0002 | -0.0674 … -0.0160 | 0.0185 ± 0.0032 | 2.02 ± 0.31 | 2.51 (#29) |
| 180° | -0.0063 … -0.0003 | -0.0003 … -0.0001 | -0.0311 … -0.0019 | 0.0112 ± 0.0043 | 1.18 ± 0.52 | 1.82 (#30) |

**Yellow**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0067 … -0.0015 | -0.0003 … -0.0001 | -0.0333 … -0.0075 | 0.0116 ± 0.0013 | 0.97 ± 0.16 | 1.19 (#31) |
| 90° | -0.0114 … -0.0043 | -0.0005 … -0.0002 | -0.0558 … -0.0213 | 0.0148 ± 0.0009 | 1.39 ± 0.16 | 1.85 (#0) |
| 180° | -0.0059 … -0.0003 | -0.0003 … -0.0001 | -0.0293 … -0.0019 | 0.0078 ± 0.0025 | 0.60 ± 0.22 | 1.08 (#31) |

**Cyan**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0101 … -0.0016 | -0.0005 … -0.0001 | -0.0494 … -0.0084 | 0.0134 ± 0.0031 | 1.23 ± 0.35 | 1.74 (#30) |
| 90° | -0.0165 … -0.0030 | -0.0007 … -0.0002 | -0.0809 … -0.0150 | 0.0162 ± 0.0022 | 1.61 ± 0.24 | 1.98 (#30) |
| 180° | -0.0095 … -0.0011 | -0.0004 … -0.0001 | -0.0467 … -0.0056 | 0.0103 ± 0.0033 | 0.88 ± 0.37 | 1.70 (#31) |

**Magenta**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | -0.0101 … -0.0025 | -0.0005 … -0.0001 | -0.0496 … -0.0125 | 0.0160 ± 0.0025 | 1.67 ± 0.35 | 2.16 (#29) |
| 90° | -0.0176 … -0.0040 | -0.0008 … -0.0002 | -0.0864 … -0.0199 | 0.0192 ± 0.0021 | 2.22 ± 0.30 | 2.61 (#28) |
| 180° | -0.0105 … -0.0013 | -0.0005 … -0.0001 | -0.0517 … -0.0065 | 0.0115 ± 0.0048 | 1.07 ± 0.58 | 2.22 (#31) |

</details>

#### Swatches

![Truncation: swatches](img/method_truncation_swatches.png)

*Figure 13. For each ramp, the reading with the largest ΔE: raw data (left) and truncation (right). Produced by `scripts/5_evaluate_method.py --method truncation`.*

#### Observations and verdict

*Table 14. Truncation, reflectance implied below 440 nm, over all 672 spectra. Produced by `scripts/5_evaluate_method.py --method truncation`.*

| From | Max | Spectra above 100 % | Spectra above own max ≥ 440 nm | Max ratio to own max ≥ 440 nm |
|---|---:|---:|---:|---:|
| R·x̄ | 0.00 % | 0 / 672 | 0 / 672 | 0.00 |
| R·z̄ | 0.00 % | 0 / 672 | 0 / 672 | 0.00 |

- **Z always drops.** ΔZ is negative in almost every spectrum, down to −0.0997 (White #31, 90°). X drops about five times less, and Y barely moves.
- **Colours shift towards yellow.** Less Z means a higher x and y on the chromaticity diagram (see Figure 21).
- **The effect grows with brightness.** The largest ΔE values are mostly at the bright end of the ramps, where the removed signal is largest. Mean ΔE is 1.18 and the maximum is 2.61.
- **Verdict: a lower bound, not an estimate.** Truncation is useful as the lowest possible answer, but its assumption contradicts the data at 440 nm.

### 5.2 Gaussian extrapolation

#### Idea

Just above the cutoff, $R\bar{x}$ and $R\bar{z}$ look like the right half of a bell curve (Figure 15). Fit a Gaussian to that half and use it to draw the missing left half.

#### Technical details

- **Model:** $g(\lambda) = A\,\exp\!\left(-\dfrac{(\lambda-\mu)^2}{2\sigma^2}\right)$.
- **Fit:** least squares (SciPy `curve_fit`) on the 13 bands from 440 to 480 nm.
- **Separate fits:** one for $R\bar{x}$ and one for $R\bar{z}$, for every spectrum.
- **Bounds:** $A \ge 0$, $\mu$ within 440 ± 60 nm, $\sigma$ between 5 and 100 nm.
- **Start:** $A$ at the maximum, $\mu$ at its position, $\sigma = 20$ nm.
- **Below 440 nm:** the contribution to X (or Z) of each band is $g(\lambda)\,k\,S(\lambda)$.
- **Y:** not reconstructed. $R\bar{y}$ below 440 nm stays at zero, as in truncation. It is only 0.1 % of Y (Table 1).
- **Implied reflectance:** $g(\lambda)/\bar{x}(\lambda)$ and $g(\lambda)/\bar{z}(\lambda)$.

#### Assumptions and limits

- **The method assumes the bell is symmetric.** The colour matching functions are not: their left side is steeper than their right side.
  - $\bar{x}$ lobe: peak at 442 nm, half height reached 19 nm to the left and 30 nm to the right.
  - $\bar{z}$: peak at 446 nm, half height reached 23 nm to the left and 32 nm to the right.

  A Gaussian fitted to the gentle right side falls too slowly on the left, so it overestimates the missing area.
- **The two fits are independent,** so they imply two different reflectances for the same surface at the same wavelength (Figure 14).
- Y is left truncated, which is slightly inconsistent with X and Z.

#### Spectrum

![Gaussian: implied reflectance](img/method_gaussian_spectrum.png)

*Figure 14. Reflectance implied by the Gaussian fit to $R\bar{x}$ (solid) and to $R\bar{z}$ (dashed), reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method gaussian`.*

#### Reflectance × CMF

![Gaussian: R·x̄ and R·z̄](img/method_gaussian_products.png)

*Figure 15. $R\bar{x}$ and $R\bar{z}$ for White, Red and Blue at reading 31, 0°: raw data and Gaussian extrapolation. Produced by `scripts/5_evaluate_method.py --method gaussian`.*

#### Reading 31

*Table 15. Gaussian, reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method gaussian`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.5822 | 0.6206 | 0.5747 | +0.0108 | -0.0006 | +0.0658 | 0.0180 | 2.71 |
| Red | 0.3781 | 0.3113 | 0.2465 | +0.0072 | -0.0002 | +0.0404 | 0.0224 | 1.87 |
| Green | 0.3551 | 0.4328 | 0.3335 | +0.0102 | -0.0002 | +0.0608 | 0.0287 | 2.40 |
| Blue | 0.2387 | 0.2718 | 0.3816 | +0.0084 | -0.0003 | +0.0476 | 0.0221 | 2.19 |
| Yellow | 0.5258 | 0.5294 | 0.3876 | +0.0105 | -0.0003 | +0.0635 | 0.0233 | 2.12 |
| Cyan | 0.4009 | 0.5016 | 0.5117 | +0.0095 | -0.0005 | +0.0568 | 0.0189 | 2.01 |
| Magenta | 0.4153 | 0.3828 | 0.4190 | +0.0071 | -0.0005 | +0.0413 | 0.0155 | 1.58 |

*Table 16. Gaussian, reading 31, 90°. Produced by `scripts/5_evaluate_method.py --method gaussian`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.9325 | 1.0050 | 0.8906 | +0.0123 | -0.0009 | +0.0785 | 0.0136 | 2.20 |
| Red | 0.5338 | 0.4193 | 0.3178 | +0.0067 | -0.0004 | +0.0374 | 0.0154 | 1.36 |
| Green | 0.4895 | 0.6127 | 0.4482 | +0.0113 | -0.0003 | +0.0701 | 0.0241 | 2.12 |
| Blue | 0.3111 | 0.3668 | 0.5466 | +0.0065 | -0.0006 | +0.0393 | 0.0127 | 1.31 |
| Yellow | 0.8323 | 0.8398 | 0.5624 | +0.0122 | -0.0005 | +0.0779 | 0.0187 | 1.88 |
| Cyan | 0.5909 | 0.7793 | 0.7722 | +0.0104 | -0.0007 | +0.0652 | 0.0144 | 1.60 |
| Magenta | 0.6382 | 0.5798 | 0.6592 | +0.0084 | -0.0008 | +0.0502 | 0.0120 | 1.31 |

*Table 17. Gaussian, reading 31, 180°. Produced by `scripts/5_evaluate_method.py --method gaussian`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.5708 | 0.6051 | 0.5644 | +0.0112 | -0.0006 | +0.0677 | 0.0189 | 2.87 |
| Red | 0.3285 | 0.2655 | 0.2072 | +0.0067 | -0.0002 | +0.0362 | 0.0237 | 1.88 |
| Green | 0.3253 | 0.3889 | 0.2997 | +0.0082 | -0.0002 | +0.0498 | 0.0258 | 2.13 |
| Blue | 0.2243 | 0.2486 | 0.3451 | +0.0077 | -0.0003 | +0.0430 | 0.0219 | 2.13 |
| Yellow | 0.5075 | 0.5093 | 0.3689 | +0.0104 | -0.0003 | +0.0624 | 0.0239 | 2.14 |
| Cyan | 0.3834 | 0.4808 | 0.4946 | +0.0095 | -0.0004 | +0.0585 | 0.0203 | 2.12 |
| Magenta | 0.4113 | 0.3735 | 0.4188 | +0.0070 | -0.0005 | +0.0403 | 0.0151 | 1.50 |

#### All readings

<details>
<summary>Gaussian: one table per ramp, readings 0–31 (produced by <code>scripts/5_evaluate_method.py --method gaussian</code>)</summary>

**White**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0059 … +0.0109 | -0.0006 … -0.0001 | +0.0331 … +0.0666 | 0.0206 ± 0.0040 | 2.66 ± 0.20 | 3.02 (#6) |
| 90° | +0.0057 … +0.0131 | -0.0009 … -0.0002 | +0.0322 … +0.0822 | 0.0170 ± 0.0034 | 2.26 ± 0.20 | 2.76 (#5) |
| 180° | +0.0050 … +0.0112 | -0.0006 … -0.0001 | +0.0272 … +0.0677 | 0.0224 ± 0.0027 | 2.59 ± 0.16 | 2.92 (#16) |

**Red**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0063 … +0.0077 | -0.0002 … -0.0001 | +0.0350 … +0.0416 | 0.0266 ± 0.0043 | 2.27 ± 0.47 | 3.51 (#0) |
| 90° | +0.0057 … +0.0071 | -0.0004 … -0.0002 | +0.0311 … +0.0386 | 0.0189 ± 0.0046 | 1.73 ± 0.51 | 2.92 (#0) |
| 180° | +0.0045 … +0.0067 | -0.0002 … -0.0001 | +0.0250 … +0.0362 | 0.0265 ± 0.0018 | 2.13 ± 0.21 | 2.79 (#0) |

**Green**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0069 … +0.0103 | -0.0002 … -0.0001 | +0.0400 … +0.0612 | 0.0311 ± 0.0033 | 2.69 ± 0.50 | 3.82 (#3) |
| 90° | +0.0063 … +0.0115 | -0.0003 … -0.0002 | +0.0353 … +0.0716 | 0.0250 ± 0.0017 | 2.29 ± 0.36 | 3.14 (#3) |
| 180° | +0.0054 … +0.0086 | -0.0002 … 0.0000 | +0.0298 … +0.0501 | 0.0306 ± 0.0026 | 2.60 ± 0.26 | 3.15 (#2) |

**Blue**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0065 … +0.0084 | -0.0003 … -0.0001 | +0.0369 … +0.0476 | 0.0247 ± 0.0044 | 2.53 ± 0.50 | 3.59 (#4) |
| 90° | +0.0058 … +0.0069 | -0.0006 … -0.0002 | +0.0334 … +0.0404 | 0.0179 ± 0.0052 | 1.83 ± 0.49 | 2.79 (#1) |
| 180° | +0.0053 … +0.0077 | -0.0003 … -0.0001 | +0.0297 … +0.0430 | 0.0265 ± 0.0045 | 2.51 ± 0.35 | 3.23 (#3) |

**Yellow**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0056 … +0.0106 | -0.0003 … -0.0001 | +0.0327 … +0.0642 | 0.0242 ± 0.0030 | 2.15 ± 0.36 | 3.15 (#0) |
| 90° | +0.0059 … +0.0126 | -0.0005 … -0.0002 | +0.0339 … +0.0812 | 0.0206 ± 0.0021 | 2.01 ± 0.27 | 2.66 (#4) |
| 180° | +0.0045 … +0.0104 | -0.0003 … -0.0001 | +0.0248 … +0.0624 | 0.0264 ± 0.0022 | 2.21 ± 0.16 | 2.88 (#0) |

**Cyan**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0061 … +0.0097 | -0.0005 … -0.0001 | +0.0353 … +0.0579 | 0.0227 ± 0.0038 | 2.36 ± 0.40 | 3.32 (#3) |
| 90° | +0.0064 … +0.0107 | -0.0007 … -0.0002 | +0.0368 … +0.0667 | 0.0186 ± 0.0042 | 1.99 ± 0.44 | 2.95 (#3) |
| 180° | +0.0050 … +0.0095 | -0.0004 … -0.0001 | +0.0272 … +0.0585 | 0.0252 ± 0.0031 | 2.49 ± 0.27 | 3.06 (#9) |

**Magenta**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0054 … +0.0077 | -0.0005 … -0.0001 | +0.0307 … +0.0438 | 0.0198 ± 0.0035 | 1.99 ± 0.33 | 2.68 (#1) |
| 90° | +0.0058 … +0.0085 | -0.0008 … -0.0002 | +0.0324 … +0.0504 | 0.0154 ± 0.0040 | 1.60 ± 0.34 | 2.32 (#3) |
| 180° | +0.0056 … +0.0071 | -0.0005 … -0.0001 | +0.0313 … +0.0403 | 0.0245 ± 0.0059 | 2.31 ± 0.49 | 2.89 (#8) |

</details>

#### Swatches

![Gaussian: swatches](img/method_gaussian_swatches.png)

*Figure 16. For each ramp, the reading with the largest ΔE: raw data (left) and Gaussian extrapolation (right). Produced by `scripts/5_evaluate_method.py --method gaussian`.*

#### Observations and verdict

*Table 18. Gaussian, reflectance implied below 440 nm, over all 672 spectra. Produced by `scripts/5_evaluate_method.py --method gaussian`.*

| From | Max | Spectra above 100 % | Spectra above own max ≥ 440 nm | Max ratio to own max ≥ 440 nm |
|---|---:|---:|---:|---:|
| R·x̄ | 3.19 % | 0 / 672 | 632 / 672 | 4.29 |
| R·z̄ | 9.30 % | 0 / 672 | 672 / 672 | 12.52 |

- **The implied reflectance is implausible.** It never exceeds 100 % (maximum 9.30 %), so it is not physically impossible. However, the $\bar{z}$ fit implies more reflectance below 440 nm than the highest value measured from 440 nm upward in every spectrum (672 of 672), by up to 12.5 times; the $\bar{x}$ fit does so in 632 of 672. Figure 14 shows the White patch climbing above 4 % near 380 nm, while its measured spectrum never exceeds 0.8 %. Nothing in the reliable bands points to such a violet peak.
- **The two fits disagree.** The $\bar{x}$ fit implies much less reflectance than the $\bar{z}$ fit (maximum 3.19 % against 9.30 %).
- **Largest change of all methods.** Mean ΔE is 2.25 and the maximum is 3.82. Z rises in every spectrum, between +0.0248 and +0.0822.
- **Colours shift towards blue.** More Z means a lower x and y (see Figure 21).
- **Verdict: rejected.** The result in XYZ is not far from hold (section 6), but it is reached through implausible spectra. Without a physical constraint on the fit, the method cannot be trusted.

### 5.3 Hold

#### Idea

Assume the reflectance stays at its 440 nm value all the way down to 380 nm.

#### Technical details

- $R(\lambda) = R(440\ \text{nm})$ for $\lambda < 440$ nm.
- The same reflectance is used for X, Y and Z, so all three coordinates stay consistent.
- No free parameters and no fitting.

#### Assumptions and limits

- The method assumes no spectral feature below 440 nm: no peak and no dip.
- If the screen absorbs more strongly below 440 nm, for example in the polarizer, hold **overestimates** the region. Section 4.2 shows a common drop in all colours below 437 nm. If that drop is real and not an instrument artefact, the truth lies between truncation and hold.
- The implied reflectance can never exceed the measured value at 440 nm, so it can never exceed 100 % or the spectrum's own measured maximum.

#### Spectrum

![Hold: implied reflectance](img/method_hold_spectrum.png)

*Figure 17. Reflectance implied by hold, reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method hold`.*

#### Reflectance × CMF

![Hold: R·x̄ and R·z̄](img/method_hold_products.png)

*Figure 18. $R\bar{x}$ and $R\bar{z}$ for White, Red and Blue at reading 31, 0°: raw data and hold. Produced by `scripts/5_evaluate_method.py --method hold`.*

#### Reading 31

*Table 19. Hold, reading 31, 0°. Produced by `scripts/5_evaluate_method.py --method hold`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.5797 | 0.6215 | 0.5485 | +0.0082 | +0.0003 | +0.0397 | 0.0109 | 1.64 |
| Red | 0.3775 | 0.3117 | 0.2377 | +0.0066 | +0.0002 | +0.0316 | 0.0175 | 1.49 |
| Green | 0.3524 | 0.4332 | 0.3090 | +0.0075 | +0.0002 | +0.0363 | 0.0176 | 1.43 |
| Blue | 0.2388 | 0.2724 | 0.3749 | +0.0085 | +0.0003 | +0.0409 | 0.0189 | 1.95 |
| Yellow | 0.5221 | 0.5300 | 0.3572 | +0.0069 | +0.0002 | +0.0331 | 0.0124 | 1.15 |
| Cyan | 0.3989 | 0.5023 | 0.4912 | +0.0075 | +0.0003 | +0.0363 | 0.0122 | 1.30 |
| Magenta | 0.4158 | 0.3835 | 0.4140 | +0.0075 | +0.0002 | +0.0363 | 0.0134 | 1.39 |

*Table 20. Hold, reading 31, 90°. Produced by `scripts/5_evaluate_method.py --method hold`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.9313 | 1.0063 | 0.8654 | +0.0110 | +0.0004 | +0.0533 | 0.0092 | 1.46 |
| Red | 0.5336 | 0.4199 | 0.3118 | +0.0065 | +0.0002 | +0.0314 | 0.0128 | 1.15 |
| Green | 0.4853 | 0.6132 | 0.4123 | +0.0071 | +0.0002 | +0.0343 | 0.0121 | 1.04 |
| Blue | 0.3121 | 0.3676 | 0.5432 | +0.0075 | +0.0002 | +0.0360 | 0.0114 | 1.24 |
| Yellow | 0.8280 | 0.8405 | 0.5224 | +0.0079 | +0.0003 | +0.0379 | 0.0092 | 0.96 |
| Cyan | 0.5899 | 0.7803 | 0.7521 | +0.0094 | +0.0003 | +0.0451 | 0.0100 | 1.12 |
| Magenta | 0.6391 | 0.5809 | 0.6540 | +0.0093 | +0.0003 | +0.0449 | 0.0105 | 1.17 |

*Table 21. Hold, reading 31, 180°. Produced by `scripts/5_evaluate_method.py --method hold`.*

| Ramp | X | Y | Z | ΔX | ΔY | ΔZ | Δxy | ΔE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| White | 0.5681 | 0.6059 | 0.5378 | +0.0085 | +0.0003 | +0.0412 | 0.0116 | 1.77 |
| Red | 0.3284 | 0.2659 | 0.2028 | +0.0066 | +0.0002 | +0.0318 | 0.0207 | 1.66 |
| Green | 0.3230 | 0.3893 | 0.2784 | +0.0059 | +0.0002 | +0.0284 | 0.0151 | 1.21 |
| Blue | 0.2242 | 0.2492 | 0.3384 | +0.0076 | +0.0002 | +0.0364 | 0.0184 | 1.87 |
| Yellow | 0.5041 | 0.5098 | 0.3398 | +0.0069 | +0.0002 | +0.0334 | 0.0130 | 1.19 |
| Cyan | 0.3811 | 0.4815 | 0.4709 | +0.0072 | +0.0002 | +0.0348 | 0.0122 | 1.28 |
| Magenta | 0.4111 | 0.3742 | 0.4111 | +0.0068 | +0.0002 | +0.0326 | 0.0121 | 1.22 |

#### All readings

<details>
<summary>Hold: one table per ramp, readings 0–31 (produced by <code>scripts/5_evaluate_method.py --method hold</code>)</summary>

**White**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0054 … +0.0084 | +0.0002 … +0.0003 | +0.0260 … +0.0404 | 0.0147 ± 0.0045 | 1.87 ± 0.33 | 2.64 (#0) |
| 90° | +0.0050 … +0.0117 | +0.0002 … +0.0004 | +0.0239 … +0.0564 | 0.0124 ± 0.0029 | 1.63 ± 0.22 | 2.27 (#5) |
| 180° | +0.0048 … +0.0085 | +0.0002 … +0.0003 | +0.0231 … +0.0412 | 0.0171 ± 0.0032 | 1.96 ± 0.10 | 2.13 (#2) |

**Red**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0058 … +0.0074 | +0.0002 … +0.0002 | +0.0281 … +0.0358 | 0.0223 ± 0.0036 | 1.92 ± 0.40 | 3.04 (#0) |
| 90° | +0.0055 … +0.0065 | +0.0002 … +0.0002 | +0.0267 … +0.0314 | 0.0158 ± 0.0039 | 1.47 ± 0.44 | 2.46 (#1) |
| 180° | +0.0044 … +0.0068 | +0.0001 … +0.0002 | +0.0213 … +0.0329 | 0.0250 ± 0.0022 | 2.03 ± 0.17 | 2.43 (#0) |

**Green**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0057 … +0.0080 | +0.0002 … +0.0003 | +0.0273 … +0.0384 | 0.0210 ± 0.0038 | 1.79 ± 0.46 | 2.80 (#3) |
| 90° | +0.0057 … +0.0071 | +0.0002 … +0.0002 | +0.0276 … +0.0343 | 0.0153 ± 0.0036 | 1.41 ± 0.50 | 2.54 (#3) |
| 180° | +0.0053 … +0.0066 | +0.0002 … +0.0002 | +0.0254 … +0.0316 | 0.0232 ± 0.0050 | 1.92 ± 0.47 | 2.93 (#2) |

**Blue**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0066 … +0.0086 | +0.0002 … +0.0003 | +0.0317 … +0.0414 | 0.0215 ± 0.0042 | 2.27 ± 0.48 | 3.33 (#4) |
| 90° | +0.0053 … +0.0077 | +0.0002 … +0.0003 | +0.0256 … +0.0370 | 0.0150 ± 0.0029 | 1.62 ± 0.29 | 2.19 (#4) |
| 180° | +0.0049 … +0.0076 | +0.0002 … +0.0002 | +0.0237 … +0.0364 | 0.0215 ± 0.0035 | 2.12 ± 0.26 | 2.70 (#3) |

**Yellow**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0050 … +0.0070 | +0.0002 … +0.0002 | +0.0238 … +0.0337 | 0.0155 ± 0.0032 | 1.41 ± 0.34 | 2.40 (#0) |
| 90° | +0.0045 … +0.0080 | +0.0001 … +0.0003 | +0.0217 … +0.0388 | 0.0119 ± 0.0023 | 1.19 ± 0.25 | 1.84 (#4) |
| 180° | +0.0045 … +0.0075 | +0.0001 … +0.0002 | +0.0218 … +0.0359 | 0.0206 ± 0.0037 | 1.73 ± 0.29 | 2.60 (#0) |

**Cyan**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0054 … +0.0081 | +0.0002 … +0.0003 | +0.0261 … +0.0389 | 0.0165 ± 0.0035 | 1.74 ± 0.39 | 2.58 (#3) |
| 90° | +0.0054 … +0.0095 | +0.0002 … +0.0003 | +0.0261 … +0.0459 | 0.0135 ± 0.0032 | 1.47 ± 0.37 | 2.34 (#3) |
| 180° | +0.0047 … +0.0076 | +0.0002 … +0.0002 | +0.0228 … +0.0367 | 0.0202 ± 0.0039 | 2.00 ± 0.34 | 2.48 (#9) |

**Magenta**

| Orientation | ΔX range | ΔY range | ΔZ range | Δxy mean ± sd | ΔE mean ± sd | ΔE max (reading) |
|---|---:|---:|---:|---:|---:|---:|
| 0° | +0.0046 … +0.0076 | +0.0001 … +0.0002 | +0.0221 … +0.0367 | 0.0158 ± 0.0019 | 1.63 ± 0.20 | 2.08 (#1) |
| 90° | +0.0047 … +0.0094 | +0.0001 … +0.0003 | +0.0227 … +0.0454 | 0.0127 ± 0.0022 | 1.36 ± 0.18 | 1.80 (#3) |
| 180° | +0.0050 … +0.0068 | +0.0002 … +0.0002 | +0.0242 … +0.0326 | 0.0200 ± 0.0042 | 1.92 ± 0.35 | 2.32 (#8) |

</details>

#### Swatches

![Hold: swatches](img/method_hold_swatches.png)

*Figure 19. For each ramp, the reading with the largest ΔE: raw data (left) and hold (right). Produced by `scripts/5_evaluate_method.py --method hold`.*

#### Observations and verdict

*Table 22. Hold, reflectance implied below 440 nm, over all 672 spectra. Produced by `scripts/5_evaluate_method.py --method hold`.*

| From | Max | Spectra above 100 % | Spectra above own max ≥ 440 nm | Max ratio to own max ≥ 440 nm |
|---|---:|---:|---:|---:|
| R·x̄ | 0.91 % | 0 / 672 | 0 / 672 | 0.97 |
| R·z̄ | 0.91 % | 0 / 672 | 0 / 672 | 0.97 |

- **Always physically possible.** The implied reflectance never exceeds 0.91 %, the highest value measured at 440 nm, and never exceeds the spectrum's own maximum from 440 nm upward.
- **Z rises in every spectrum,** between +0.0213 and +0.0564. X rises about five times less and Y by at most 0.0004.
- **Colours shift towards blue,** like the Gaussian method but less (see Figure 21).
- **Dark readings change most in ΔE.** The largest values (up to 3.33, Blue #4, 0°) are mostly at readings 0–9. At those levels a fixed amount of added Z is a larger share of the colour.
- **Verdict: the most plausible estimate.** Hold is simple, consistent across X, Y and Z, and always physically possible. It is an upper bound if the screen absorbs more below 440 nm.

## 6 Comparison and choice

> **In short:** truncation and hold bracket the plausible answer, and the gap between them is the real uncertainty. Hold is the recommended method.

*Table 23. All methods compared with the raw data: 3 orientations × 7 ramps × 32 readings. "mean ΔE #31" is the mean over reading 31 only. Produced by `scripts/6_compare_methods.py`.*

| Method | mean ΔX | mean ΔY | mean ΔZ | mean Δxy | mean ΔE | p95 ΔE | max ΔE | mean ΔE #31 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cleaning | +0.0010 | 0.0000 | +0.0050 | 0.0045 | 0.41 | 0.94 | 1.63 | 0.20 |
| truncation | -0.0053 | -0.0003 | -0.0262 | 0.0124 | 1.18 | 2.19 | 2.61 | 1.59 |
| gaussian | +0.0074 | -0.0003 | +0.0429 | 0.0231 | 2.25 | 3.02 | 3.82 | 1.97 |
| hold | +0.0066 | +0.0002 | +0.0319 | 0.0177 | 1.74 | 2.47 | 3.33 | 1.37 |

*Table 24. Methods compared with each other, all spectra. ΔZ is the second method minus the first. Produced by `scripts/6_compare_methods.py`.*

| Pair | mean ΔZ | mean ΔE | max ΔE |
|---|---:|---:|---:|
| cleaning vs truncation | -0.0312 | 1.53 | 2.31 |
| cleaning vs gaussian | +0.0379 | 1.89 | 2.96 |
| cleaning vs hold | +0.0269 | 1.38 | 1.86 |
| truncation vs gaussian | +0.0691 | 3.42 | 4.79 |
| truncation vs hold | +0.0580 | 2.91 | 3.77 |
| gaussian vs hold | -0.0111 | 0.52 | 1.19 |

*Table 25. Summary of the plausibility checks, compiled from Tables 14, 18 and 22 and the cleaning diagnostics printed by `scripts/5_evaluate_method.py --method cleaning`. Shares above the historical repeatability reference after cleaning (ΔE 0.22, section 2.3) are produced by `scripts/6_compare_methods.py` and also printed by `scripts/5_evaluate_method.py`.*

| Method | Treats the 423–437 nm region | Implied reflectance below 440 nm | Share of spectra changed beyond the historical repeatability reference |
|---|---|---|---:|
| cleaning | Removes 423.333 nm; keeps 426.667–436.667 nm (contaminated) | Measured values, max 0.85 % | 66 % |
| truncation | Replaces it | 0 everywhere | 98 % |
| gaussian | Replaces it | Up to 9.30 %; above own measured maximum in 672 / 672 spectra | 100 % |
| hold | Replaces it | Up to 0.91 %, never above own measured maximum | 100 % |

![Mean and max ΔE per ramp](img/6_delta_e.png)

*Figure 20. Mean ΔE (bars) and max ΔE (ticks) per ramp and method, against the raw data. The dashed line is the historical repeatability p95 after section 3 cleaning (ΔE 0.22), not a significance threshold. Produced by `scripts/6_compare_methods.py`.*

![Chromaticity of reading 31](img/6_xy.png)

*Figure 21. Chromaticity of reading 31 at 0°, one zoomed panel per ramp: raw data (circle) and the four methods. Produced by `scripts/6_compare_methods.py`.*

What the comparison shows:

- **Reconstruction changes are often larger than historical repeat differences after cleaning.** Truncation changes 98 % of spectra by more than the reference of 0.22; Gaussian and hold change all of them by more. This puts the size of the changes in context, without establishing their statistical significance or correctness.
- **The methods move colours in opposite directions** (Figure 21). Truncation moves every colour towards yellow. Gaussian and hold move it towards blue. Cleaning stays close to the raw data, because it keeps the contaminated bands.
- **Truncation and hold set the range.** If the true reflectance below 440 nm lies anywhere between 0 and the value at 440 nm, the true colour lies between these two methods. They are 2.91 ΔE apart on average, about thirteen times the historical repeatability reference after cleaning. **This illustrates reconstruction uncertainty under those assumptions, not a statistical confidence interval.**
- **Gaussian and hold agree in XYZ** (mean ΔE 0.52). They arrive there by very different routes: the Gaussian through an implausible violet peak, hold through a plausible reflectance.

**Choice: hold.** It is the only method that:

1. replaces all the contaminated bands;
2. never implies a reflectance above what the same spectrum shows from 440 nm upward;
3. uses the same reflectance for X, Y and Z;
4. needs no fitting and no free parameters.

Hold sits at the upper end of the plausible range. If future measurements show that the screen absorbs below 440 nm, the true Z will be lower, towards truncation.

## 7 Conclusions

1. **The ColorMunki Photo does not measure below 440 nm on this screen.** Up to 420 nm it returns a flat, mostly negative line that follows the patch brightness. Between 420 and 437 nm that line still leaks into the signal.
2. **The damage is in X and Z, not in Y.** Below 440 nm lies 20.4 % of Z and 3.6 % of X for a uniform reflector under D50, against 0.1 % of Y. Above 700 nm the instrument is noisy, but the region contributes at most 0.13 % and can be ignored.
3. **The cutoff is 440 nm.** It is the lowest band where the baseline leak drops to the background level of the estimate (below 5 %).
4. **Cleaning alone is not enough.** It removes impossible values but keeps contaminated bands.
5. **Truncation is a lower bound.** It assumes the reflectance drops to zero in one step, which no real material does.
6. **Gaussian extrapolation is rejected.** In every spectrum it implies more reflectance below 440 nm than the same spectrum's measured maximum from 440 nm upward, by up to 12.5 times.
7. **Hold is recommended.** It is simple, always physically possible and consistent across X, Y and Z.
8. **The reconstruction uncertainty is large.** Truncation and hold differ by 2.91 ΔE on average, compared with a historical repeatability p95 after cleaning of 0.22. The former describes disagreement between reconstruction assumptions; the latter describes repeated measurements after section 3 cleaning. Neither establishes the true spectrum below 440 nm.
9. **Keep acquisition conditions consistent.** The method results are reported separately for each instrument orientation. Assess a correction within the same acquisition geometry rather than mixing datasets.

## 8 Limitations and open questions

- **No ground truth.** No method can be proven correct without a reference measurement of the same screen below 440 nm, for example with a spectroradiometer or a spectrophotometer whose range covers 380 nm reliably. Such a measurement would also decide where the truth lies between truncation and hold.
- **Polarizer or instrument?** The common drop below 437 nm (section 4.2) could be an instrument artefact or a real absorption in the polarizer or the screen protector. If it is real, hold overestimates Z.
- **Screen protector.** It was not removed. Its transmission below 440 nm is unknown and is included in every measurement.
- **Orientation dependence.** The per-orientation results in sections 3 and 5 differ. It is still open which acquisition geometry, if any, represents how the screen is seen in normal use.
- **Repeatability reference.** The five-reading patch blocks come from May greyscale measurements, not the November colour ramps. Their pooled p95 of 0.22 describes repeatability after section 3 cleaning, not the variability of the raw exports. It is an empirical reference, not a verified noise floor for every patch, a significance test or an accuracy estimate (see [section 2.3](#23-noise-floor)).
- **Zone thresholds.** The 5 %, 10 % and 25 % leak thresholds are judgement calls. The 5 % threshold is anchored to the background level of the estimate. The other two only separate degrees of contamination and do not affect the cutoff.
- **Gaussian method.** Y was not reconstructed. This does not change the verdict, because it accounts for only 0.1 % of Y.
- **Above 700 nm.** The instability was not corrected, because its effect on XYZ is negligible (Table 1). It would matter for observers or illuminants with more weight in the deep red.
- **One console.** The analysis covers a single Game Boy Color. Other handhelds measured with the same instrument share the 440 nm limit, but the size of the effect depends on each screen's blue reflectance.

## 9 References

- CIE 015:2018, *Colorimetry*, 4th edition. Commission Internationale de l'Éclairage, 2018. Colour matching functions, D50 and the computation of XYZ.
- C. Li, Z. Li, Z. Wang, Y. Xu, M. R. Luo, G. Cui, M. Melgosa, M. H. Brill, M. Pointer, "Comprehensive color solutions: CAM16, CAT16, and CAM16-UCS", *Color Research & Application*, 42(6), 703–718, 2017. [doi:10.1002/col.22131](https://doi.org/10.1002/col.22131).
- IEC 61966-2-1:1999, *Multimedia systems and equipment – Colour measurement and management – Part 2-1: Default RGB colour space – sRGB*.
- Colour developers, *Colour*, Python library for colour science, version 0.4.7. [colour-science.org](https://www.colour-science.org/).
- SciPy developers, `scipy.optimize.curve_fit`. [docs.scipy.org](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html).
- G. Gill, *ArgyllCMS*, `spotread`. [argyllcms.com](https://www.argyllcms.com/doc/spotread.html).
