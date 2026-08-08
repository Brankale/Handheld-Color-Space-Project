# Index

- [Displays types](#displays-types)
   - [Measurements tools](#measurements-tools) 
- [Do the measurements](#do-the-measurements)
   - [Introduction](#introduction)
   - [Measurements guide for emissive displays](#measurements-guide-for-emissive-displays)
   - [Measurements guide for reflective displays (Work in Progress)](#measurements-guide-for-reflective-displays-work-in-progress)
   - [Measurements report (template)](#measurements-report-template)
- [Measurements Validation](#measurements-validation)
- [Technical notes for reflective displays](#technical-notes-for-reflective-displays)
  - [Spectral reflectance and XYZ calculation](#spectral-reflectance-and-xyz-calculation)
  - [Instrumental spectral limitations](#instrumental-spectral-limitations)
  - [XYZ additivity and gamma extraction](#xyz-additivity-and-gamma-extraction)


# Displays types

- `Emissive`: the display **emits its own light** (no external illumination needed).
- `Transmissive`: the display uses a separate backlight and modulates the light passing through the panel. A backlit LCD is therefore transmissive, whereas an OLED is emissive. Although the physical principles differ, both are measured from the viewing side using an instrument's emissive/display measurement mode.
- `Reflective`: the display **does not emit light**; it reflects ambient light. Pixels modulate reflection, rather than emitting light.
- `Transflective`: **hybrid** of transmissive and reflective. A backlight is present, but the display can also use ambient light (via a partially reflective layer).

## Measurements tools

Depending on the display type, you must use an instrument that supports the required measurement mode. Here is a summary table:

| Meter  | Emissive | Reflective | Transflective |
| ------------- | :-------------: | :-------------: | :-------------: | 
| Colorimeter        | ✅ good accuracy | ❌ | ❓ |
| Spectroradiometer  | ✅ highest accuracy | ❓ | ❓ |
| Spectrophotometer  | ⚠️ not recommended (1) | ✅ | ✅ (only with backlit turned off) |

(1) A spectrophotometer primarily measures reflected light from surfaces. Some models have an “emissive mode,” but they’re generally slower, less sensitive at low light, and not ideal for bright HDR peaks or very dark near-black, common in emissive displays.

# Do the measurements

## Introduction

Handheld LCD screens present several challenges:
- color variations depending on the **viewing angle** (especially on TN panels).
- variation in **color tint/brightness/gamma** caused by the 'screen lottery' phenomenon in certain handhelds (e.g. the 3DS), where manufacturing tolerances cause units with the same nominal display model to exhibit distinct color characteristics. 
- different **screen manufacturers**: some handhelds have different screen manufacturers (e.g. NDS Lite has LCD screens coming from Hitachi and Sharp (1)(2)) which can cause color variations across different units of the same handheld.
- **screen protectors and touchscreens** (aka screen digitizers) can affect color accuracy, especially if they are old and have been exposed to sunlight, which can degrade the plastic and cause a yellowish tint.

The goal is to **measure the best possible scenario**, removing all the factors which can degrade image quality.

> [!IMPORTANT]
> Measurements of mods (e.g., IPS and OLED panel replacements) are allowed, but only if clearly documented.

### Examples of "screen lottery"

<img width="600" alt="chromatic adaptation" src="https://github.com/user-attachments/assets/5c68e899-6484-4fdb-a915-a40d6258efcb"/>

GameBoy Advance SP AGS-??? by Pica200 ([libretro post link](https://forums.libretro.com/t/real-gba-and-ds-phat-colors/1540/295))

<img width="600" alt="chromatic adaptation" src="https://github.com/user-attachments/assets/94e169b0-469c-4f04-81e3-cea470034200"/>

GameBoy Advance SP AGS-001 by mckimiaklopa ([libretro post link](https://forums.libretro.com/t/real-gba-and-ds-phat-colors/1540/271))

## Measurements guide for emissive displays

### Environment setup

To achieve reproducible and accurate measurements, you must:

* **Let the screen warm up**:
  * Measuring too early can produce non-reproducible results and will not reflect the true visual experience. Leave the screen on and wait for the luminance and chromaticity to stabilize before recording the measurements. Depending on the screen type, this process can take anywhere from 5 to 30 minutes.
* **Remove external light sources**:
  * Avoid sunlight, lamps, and any other external light sources. Even small reflections or stray light can affect measurement accuracy.
  * For multiple screens (e.g., NDS family), cover the screens not being measured to prevent light leakage.
* **Plug in the charger for certain handhelds**:
  * Some devices (e.g., PSP-1000) require charging to reach maximum screen luminance.
* **Use appropriate color-patch sizes**:
  * Full-screen patches are appropriate for LCD handhelds without automatic brightness limiting (ABL). This requires homebrew software on modded handhelds, hardware modifications, or special cartridges.
  * For emissive displays affected by Automatic Brightness Limiting (ABL), such as the Nintendo Switch OLED, use window patches covering no more than 10% of the screen area and document the chosen size. This reduces the likelihood that ABL alters the measurements.
* **Remove protective layers and touch digitizers when practical**:
  * Screen protectors and touch digitizers can deteriorate or yellow over time, altering the measured color independently of the display panel. Removing them is therefore recommended when the goal is to characterize the panel itself.
  * Removal is especially recommended for reflective displays, where thick plastic layers can substantially attenuate the limited reflected light and reduce measurement reliability.
  * Removal is not always necessary. If a protective layer is clear, undamaged and does not significantly attenuate or alter the measured light, it can remain in place. For example, removing the cover from the top screen of a Nintendo DS may provide little practical benefit.
  * Because removing these layers requires disassembling the console and may not be practical or desirable, measurements of a fully assembled console are also accepted. Always document which protective layers and digitizers were present or removed so that the measurement conditions can be interpreted and reproduced.
* **Colorimeter usage**:
  * **With screen protector**: Place the sensor in contact with the protector to keep it perpendicular, reduce light leakage, and minimize external light influence.
  * **Without screen protector**: Place the sensor directly on the screen but avoid pressing too hard to prevent distortion or Newton rings. Alternatively, position the meter very close to the screen, ensuring perpendicular alignment—small viewing angle changes can significantly affect color and brightness on TN panels.

### What to Measure

To reproduce the display's color space, use one of the following presets according to the desired compromise between fidelity and measurement time:

| Level | Measurements | Patches | Result and limitations |
| ------------- | ------------- | :-------------: | ------------- |
| **Complete** | CIE XYZ coordinates for the full Red, Green, Blue, Yellow, Cyan, Magenta and Greyscale ramps. | $7N = 224$ | Provides direct measurements of all primary, secondary and greyscale response curves. |
| **Recommended** | CIE XYZ coordinates for the full Red, Green and Blue ramps, plus Black, White, Yellow, Cyan and Magenta. | $3N + 5 = 101$ | Produces results that are practically equivalent to the Complete preset for emissive and transmissive displays, with substantially fewer measurements. |
| **Bare minimum** | CIE XYZ coordinates for the full Greyscale ramp, plus Red, Green, Blue, Yellow, Cyan and Magenta. | $N + 6 = 38$ | The primary gamma curves must be calculated rather than measured directly and may be slightly less accurate because measurement errors can be amplified by the mathematical extraction steps. |

> [!NOTE]
> The counts assume a 5-bit signal depth: $N = 2^5 = 32$ levels per full ramp. For emissive and transmissive displays, is not necessary to measure more than 32 patches per ramp even if the native signal depth is higher because the intermediate values can be interpolated without loss of accuracy.

> [!NOTE]
> If the handheld has multiple screens (e.g., Nintendo DS family), **measure both top and bottom panels**.

#### Example (using HCFR software)

R, G, B, Y, C, M, Black, White chromaticity coordinates (expressed as CIE xyY coordinates in this example):
<img width="640" height="360" alt="Screenshot From 2025-09-03 16-44-40" src="https://github.com/user-attachments/assets/c5f60803-f372-4492-9f95-d2b5de59b2b2" />

Greyscale chromaticity coordinates (expressed as CIE xyY coordinates in this example):
<img width="640" height="360" alt="Screenshot From 2025-09-03 16-44-50" src="https://github.com/user-attachments/assets/1f97ca9c-6f21-4f67-966b-7b58643b0e8f" />

## Measurements guide for reflective displays (Work in Progress)

> [!WARNING]  
> This section is currently a work in progress and may undergo revisions as calibration methods and measurement techniques are further tested and validated.

### Introduction
Measuring reflective displays requires a fundamentally different approach compared to emissive screens. Instead of generating their own light, these displays rely exclusively on reflected light. Due to their physical composition (such as liquid crystal alignment and polarizers), the behavior of reflected color and gamma changes significantly based on how the display is illuminated and observed.

### Required Equipment
- **Spectrophotometer:** A device capable of reflective measurements (e.g., ColorMunki Photo).
- **Measurement Software:** **spotread** ([documentation](https://www.argyllcms.com/doc/spotread.html)) is recommended, though any software capable of accurately measuring and logging spectral reflectance will work.

### Setup and Environment
- **Warm-up:** Spectrophotometers require a warm-up period to ensure sensor stability before measuring. This can take up to 30 minutes depending on the model (e.g., ColorMunki Photo). Always refer to your instrument's specific manual.
- **Lighting:** **all external sources of ambient light must be eliminated**. Take these measurements in a completely dark room to prevent external light from altering the sensor readings.
- **Calibration (WIP):** This step is probably a critical one, however it is still under investigation. In `spotread`, arguments like `-Y W:fname.sp` (Save instrument white tile ref. spectrum) or `-Y S:fname.cmf` (Save instrument raw & XYZ spectral sensitivities) are available, but standardized best practices are not firmly established yet.

### Instrument Orientation
The physical orientation of the spectrophotometer against the display is critical. If you measure the screen with different spectrophotometer orientations, the measured reflectance will completely change due to the display's internal polarizers and reflective layers scattering light asymmetrically. NB: This step has great implications on the resulting gamma.

- **How to find the representative orientation:** Align the instrument with the direction from which the console is normally viewed, and document the display and instrument rotation so that the setup can be reproduced. As a validation step, export the measured luminance (Y) data from the XYZ coordinates and plot it in a spreadsheet tool such as LibreOffice Calc, Excel or Google Sheets.
  - For the consoles tested so far, the normal viewing orientation produces an exponential response. A logarithmic-looking or unusually flat response indicates that the instrument is probably rotated relative to the intended viewing direction.

| Orientation | Measurements | Output |
| :-------------: | :-------------: | :-------------: |
| <img height="300" alt="20260508_223035" src="https://github.com/user-attachments/assets/343f0442-c373-4f5c-b929-e2e6d66c5caf" /> | <img height="300" alt="low gamma" src="https://github.com/user-attachments/assets/6b5fc328-4e2a-4c31-8cbb-2ab6cddb23a2" /> <br>Very low gamma --> washed out image ❌ | <img width="300" alt="low_gamma" src="https://github.com/user-attachments/assets/fcbe2790-f8d4-4997-9c03-b96da9a604a4" /> |
| <img height="300" alt="20260508_223055" src="https://github.com/user-attachments/assets/d502b5f0-93a0-4b27-afec-a8d1027aa46a" /> | <img height="300" alt="high gamma" src="https://github.com/user-attachments/assets/cacd7768-bc39-4cbd-a7cb-426c178987d7" /> <br>Normal gamma ✔️  | <img width="300" alt="std_gamma" src="https://github.com/user-attachments/assets/47017d20-1527-4501-8895-a83489999ed4" /> |






### How to measure
If you are using `spotread`, use the following command to take a measure of the screen:

```bash
spotread -s -H -v -V -Y a log.txt
```

**Flag explanations:**
- `-s` : Print spectrum for each reading.
- `-H` : Use high resolution spectrum mode (if available).
- `-v` : Verbose mode.
- `-V` : Show the running average and standard deviation from the reference.
- `-Y a` : Use averaging measurement mode (if available).
- `log.txt` : The output text file where the measured values are saved.

> [!NOTE]
> If your spectrophotometer does not support `-Y a`, you can measure each patch at least 3 times. This way, the results can be manually averaged during post-processing to reduce the measurement's noise.

The output will look like the snippet below. XYZ and Lab coordinates are calculated using D50 illuminant by default, unless you set a different one in spotread. The reflectance data is the main information of interest.

```
Reading	X	Y	Z	L*	a*	b*	380.000	383.333	386.667	390.000	393.333	396.667	400.000	...
1	0.183685	0.182168	0.149141	1.645520	0.324562	0.021349 ...
2	0.185581	0.184557	0.151998	1.667099	0.308123	0.004620 ... 
3	0.185546	0.185224	0.148670	1.673125	0.280722	0.077836 ...
```

> [!WARNING]
> Some instruments have known wavelength-range limitations. See [Instrumental spectral limitations](#instrumental-spectral-limitations) before post-processing data from that instrument.



### What to measure
To reproduce the color space of a reflective display, use one of the following presets according to the desired compromise between fidelity and measurement time.

> [!WARNING]
> Saving the spectral reflectance data for every patch is essential (with `spotread`, the `-s` flag automatically includes all sampled wavelengths in each patch reading). Do not rely only on the XYZ values reported by the software. See [Spectral reflectance and XYZ calculation](#spectral-reflectance-and-xyz-calculation) for the reason.

| Level | Measurements | Patches | Result and limitations |
| ------------- | ------------- | :-------------: | ------------- |
| **Complete** / **Recommended** | Spectral reflectance for the full Red, Green, Blue, Yellow, Cyan, Magenta and Greyscale ramps. | $7N = 224$ | Directly measures every required response curve. The secondary ramps also enable validation tests that cannot be performed using only peak secondary measurements. |
| **Bare minimum** | Spectral reflectance for the full Red, Green and Blue ramps, followed by the pairs Black → White, Black → Yellow, Black → Cyan and Black → Magenta. Do not omit the intervening Black readings (*). | $3N + 8 = 104$ | Measures the primary gamma curves directly and captures the peak secondary colors, but does not provide secondary ramps for validation. |
| **Insufficient** | Spectral reflectance for the full Greyscale ramp, plus Red, Green, Blue, Yellow, Cyan and Magenta. | $N + 6 = 38$ | Accurate primary gamma curves are practically impossible to extract. See [XYZ additivity and gamma extraction](#xyz-additivity-and-gamma-extraction). |

> [!NOTE]
> The counts assume a 5-bit signal depth: $N = 2^5 = 32$ levels per full ramp. They count individual readings; the $+8$ in the Bare minimum preset is the four Black → color pairs. For a bit depth $b$, use $N = 2^b$.

(*) In the reflective workflow tested for this project, a measurement offset accumulates during the session. Measuring Black immediately before White and before each secondary color provides the corresponding offset reference for post-processing. Preserve this exact order in the raw data. This is an empirical correction for the tested instrument and setup, not a substitute for the instrument's calibration procedure.




## Measurements report (template)

You can find the report template in the [REPORT_TEMPLATE.md](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/REPORT_TEMPLATE.md) file

> [!IMPORTANT]
> Always share your full measurement data in a readable format, along with the raw files (e.g., `.chc` files if you use HCFR). This ensures that others can review and verify your work.
> If you only share the final results (such as shaders or LUTs) without the underlying data, your work cannot be reproduced or improved upon.

# **Measurements Validation**

To validate the results of a colorspace conversion:

1. **Calibrate your display**
   * Ensure your display supports the target gamut.
   * Use a hardware colorimeter or spectroradiometer to calibrate your display to the target colorspace (e.g., sRGB, DisplayP3 (sRGB EOTF), P3-D65 (PQ EOTF), Rec. 2020). Ensure you use a colorimeter or spectroradiometer capable of accurately measuring wide-gamut colorspaces, as not all devices support them correctly.
   * If hardware calibration is not possible, use a high-quality display with verified calibration, but note that results may have small deviations.
2. **Disable all display enhancements**
   * Turn off dynamic contrast, local dimming, HDR, blue-light filters, ABL (automatic brightness limiter) or any post-processing features that can alter color or gamma.
  
> [!WARNING]
> If you can't meet these requirements, please avoid performing this validation since you cannot reliably validate the results. If you still wish to provide opinions on the results, be sure to provide full context to avoid misleading conclusions.

# Technical notes for reflective displays

## Spectral reflectance and XYZ calculation

While an emissive display produces its own light, a reflective display works differently: it modifies the light falling onto it. Its visible color and brightness therefore change with the ambient illumination (illuminant).

For this reason, the primary result of a reflective-display measurement is its spectral reflectance: the fraction of light at each wavelength that the display reflects. Capturing this behavior is essential to reproduce how the screen responds under different illuminants.

By default, the XYZ values displayed by the software are calculated from the reflectance spectrum using a selected illuminant and standard observer (usually D50 with the 2° observer). They therefore describe the display only under those selected viewing conditions. Retaining the spectrum makes it possible to recalculate XYZ values for another illuminant and to inspect or handle unreliable wavelength regions during post-processing.

## Instrumental spectral limitations

`spotread` XYZ and Lab values depend on the integrity of the spectral data. Measurements made with the ColorMunki Photo show an evident instrumental limitation below 440 nm, where the response drops to a flat baseline and includes physically impossible negative values. Above 700 nm, the measured signal also becomes unstable near the instrument's operational limit. Inaccurate spectral readings in these regions propagate into the calculated XYZ values, with an impact that depends on the selected illuminant spectrum and standard-observer functions. These regions must therefore be inspected and treated cautiously during post-processing and when recalculating XYZ coordinates.

Here is an example of spectral reflectance data for a GBC greyscale measured with a ColorMunki Photo:

<img height="400" alt="greyscale spectral reflectance" src="https://github.com/user-attachments/assets/827b1cf3-a9a2-46bc-a6e9-654a47c9f9ea" />

## XYZ additivity and gamma extraction

To accurately derive the gamma curves of a reflective display, measurements of RGBCMYK ramps are necessary. Using the Greyscale ramp plus primary measurements, as for emissive displays, is not possible for the following reasons:

1. **Lack of XYZ Additivity:** In typical emissive or transmissive panels (such as standard TN or TFT LCDs), mixed colors can be predicted from the black-corrected primary measurements. For example, $`(XYZ_W - XYZ_K) ≃ (XYZ_R - XYZ_K) + (XYZ_G - XYZ_K) + (XYZ_B - XYZ_K)`$ and $`(XYZ_Y - XYZ_K) ≃ (XYZ_R - XYZ_K) + (XYZ_G - XYZ_K)`$; the same relations can be tested using spectral power distributions. This additivity makes it mathematically possible to estimate the primary (R, G, B) gamma curves from the Greyscale ramp and the primary measurements. On all reflective consoles tested so far, however, this additive model breaks down. The final reflected color strongly depends on how the physical liquid crystal layers interact with the illumination, meaning mixed colors (Yellow, Cyan, Magenta) and the individual gamma curves cannot be accurately predicted from the Greyscale ramp and peak primary measurements alone.
2. **Low Luminance Noise:** Spectrophotometers can struggle to measure dark patches accurately, leading to sensor noise at low signal levels. Because gamma extraction is highly sensitive to these errors, even minor measurement deviations can produce large distortions in the calculated curves.

Here is an example of gamma extracted from greyscale measurements. The blue and red scales are very distorted without interpolation.

| Gamma graph  | Blue scale | Red scale |
| ------------- | :-------------: | :-------------: |
| <img width="1000" alt="linear fit" src="https://github.com/user-attachments/assets/89cc9ab2-1a6b-4192-be2c-f597a5e4c749" /> | <img width="328" height="256" alt="cyan" src="https://github.com/user-attachments/assets/b739748b-0892-4122-896b-79d51e62b4f5" /> | <img width="328" height="256" alt="magenta" src="https://github.com/user-attachments/assets/167fc69c-1e77-4b9b-9d74-12904180a934" /> |
