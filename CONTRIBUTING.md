# Index

- [Displays types](#displays-types)
   - [Measurements tools](#measurements-tools) 
- [Do the measurements](#do-the-measurements)
   - [Introduction](#introduction)
   - [Measurements guide for emissive displays](#measurements-guide-for-emissive-displays)
   - [Measurements guide for reflective displays (Work in Progress)](#measurements-guide-for-reflective-displays-work-in-progress)
   - [Measurements report (template)](#measurements-report-template)
- [Measurements Validation](#measurements-validation)


# Displays types

- `Emissive`: the display **emits its own light** (no external illumination needed).
- `Reflective`: the display **does not emit light**; it reflects ambient light. Pixels modulate reflection, rather than emitting light.
- `Transflective`: **hybrid** of emissive and reflective. A backlight is present, but the display can also use ambient light (via a partially reflective layer).

## Measurements tools

Depending on the display type, you must use the appropriate meter to ensure accurate measurements. Here is a summary table:

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
> Measurements of mods (e.g., IPS and OLED panel replacements) is allowed but only if clearly documented.

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
* **Use full-screen color patches**:
  * Requires homebrew software on modded handhelds, hardware modifications, or special cartridges.
* **Optionally remove screen protectors or digitizers**:
  * Extra layers (e.g., touchscreen or protective films) can alter measurements, so removing them improves accuracy.
* **Colorimeter usage**:
  * **With screen protector**: Place the sensor in contact with the protector to keep it perpendicular, reduce light leakage, and minimize external light influence.
  * **Without screen protector**: Place the sensor directly on the screen but avoid pressing too hard to prevent distortion or Newton rings. Alternatively, position the meter very close to the screen, ensuring perpendicular alignment—small viewing angle changes can significantly affect color and brightness on TN panels.

### What to Measure

To accurately characterize a handheld screen’s colorspace, you should record the following data:
* Chromaticity coordinates of:
   * Red, Green, Blue
   * Yellow, Cyan, Magenta
   * Black, White
* Chromaticity coordinates of the greyscale:
   * Measure the entire grayscale range from black to white.
   * The number of color patches to measure must be a power of two (e.g., 32 patches, 64 patches, 128 patches, etc.) to facilitate integration with shaders.
   * The maximum number of patches to measure depends on the screen’s bit depth (e.g., the GBC has a 5-bit depth, so the number of patches to measure is 2^5 = 32).
   * As a general recommendation, measure at least 32 grayscale patches to ensure sufficient accuracy.

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

- **How to find the correct orientation:** A recommended validation step is to export the measured luminance (Y) data (taken from XYZ coordinates) from your software and plot it in a spreadsheet tool like LibreOffice Calc / Excel / Google Sheets. 
  - If the resulting curve looks **logarithmic**, the instrument's orientation is completely wrong for that display. 
  - If the curve exhibits an **exponential** shape, it is likely correct. You are generally looking for the orientation that yields the most prominent/largest exponential response.

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
- `-s` : Print spectrum for each reading
- `-H` : Use high resolution spectrum mode (if available)
- `-v` : Verbose mode
- `-V` : Show running average and std. devation from ref.
- `-Y a` : Use averaging measurement mode (if available)
- `log.txt` : The output text file where the measured values are saved.

> [!NOTE]
> If your spectrophotometer does not support `-Y a`, measure each patch 3 to 5 times. This way, the results can be manually averaged during post-processing to reduce the measurement's noise.

The output will look like the snippet below. XYZ and Lab coordinates are calculated using D50 illuminant by default, unless you set a different one in spotread. The reflectance data is the main information of interest.

```
Reading	X	Y	Z	L*	a*	b*	380.000	383.333	386.667	390.000	393.333	396.667	400.000	...
1	0.183685	0.182168	0.149141	1.645520	0.324562	0.021349 ...
2	0.185581	0.184557	0.151998	1.667099	0.308123	0.004620 ... 
3	0.185546	0.185224	0.148670	1.673125	0.280722	0.077836 ...
```

> [!WARNING]
> spotread XYZ and Lab reported values depend on the integrity of the spectral data. For instance, the ColorMunki Photo exhibits significant limitations below 440nm, showing a drop-off and a flat baseline (including physically impossible negative values). This is likely a combined effect of the instrument's low LED emission in the violet/UV range, the screen's internal UV filters and polarizers and instrument limitations but currently we don't have any clear evidence of this. At wavelengths above 700nm, the signal becomes unstable probably due to a low signal-to-noise ratio as the sensor reaches its operational limit. This must be taken into consideration in the post-processing step when calculating XYZ coordinates.
>
> Here's an example image showing spectral reflectance data of the greyscale taken from a GBC using a Colormunki Photo:
> <img height="400" alt="greyscale spectral reflectance" src="https://github.com/user-attachments/assets/827b1cf3-a9a2-46bc-a6e9-654a47c9f9ea" />



### What to measure
To properly profile a reflective display, you must measure **224 individual color patches** in total: a full 32-patch scale (assuming a standard 5-bit depth) for Red, Green, Blue, Yellow, Cyan, Magenta, and the Greyscale (7 scales × 32 patches). Tests must be performed to ensure this is the lowest number of patches to measure to get a good trade-off between accuracy and time spent measuring.

It is not physically viable to simply measure the Greyscale and mathematically derive the gamma of the Red, Green, and Blue channels. This extensive manual sampling of all colors is absolutely mandatory for the following reasons:

1. **Lack of XYZ Additivity:** In typical emissive panels (like standard TN or TFT LCDs), you can sum the XYZ coordinates of the individual primary color channels (R, G, B) to accurately predict mixed colors (e.g., $`XYZ_{red} + XYZ_{green} ≃ XYZ_{yellow}`$ or in other words $`SPD_{red} + SPD_{green} ≃ SPD_{yellow}`$). On reflective displays, however, this additive property completely breaks down. The final reflected color strongly depends on how the physical liquid crystal layers interact with the ambient light, meaning mixed colors (Yellow, Cyan, Magenta) behave unpredictably compared to their individual R, G, B components. (e.g., $`XYZ_{red} + XYZ_{green} > XYZ_{yellow}`$ or in other words $`SPD_{red} + SPD_{green} > SPD_{yellow}`$)
2. **Gamma Extraction and Low Luminance Noise:** While it is not phisically accurate, it is mathematically possible to derive the primary (R, G, B) gamma curves from a grayscale measurement but there are some fundamental flaws to keep in mind. Spectrophotometers struggle to accurately measure dark patches, leading to inherent sensor noise at low luminance levels. In addition, because the math to extrapolate gamma is highly sensitive, even minor measurement errors can result in massive, cascading deviations in the calculated gamma curve.

Here's an example of gamma extracted from greyscale measurements. Blue and red scale are very distorted without performing interpolation.

| Gamma graph  | Blue scale | Red scale |
| ------------- | :-------------: | :-------------: |
| <img width="1000" alt="linear fit" src="https://github.com/user-attachments/assets/89cc9ab2-1a6b-4192-be2c-f597a5e4c749" /> | <img width="328" height="256" alt="cyan" src="https://github.com/user-attachments/assets/b739748b-0892-4122-896b-79d51e62b4f5" /> | <img width="328" height="256" alt="magenta" src="https://github.com/user-attachments/assets/167fc69c-1e77-4b9b-9d74-12904180a934" /> |




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
3. **Disable all display enhancements**
   * Turn off dynamic contrast, local dimming, HDR, blue-light filters, ABL (automatic brightness limiter) or any post-processing features that can alter color or gamma.
  
> [!WARNING]
> If you can't meet these requirements, please avoid performing this validation since you cannot reliably validate the results. If you still wish to provide opinions on the results, be sure to provide full context to avoid misleading conclusions.
