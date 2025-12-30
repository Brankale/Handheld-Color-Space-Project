# Index

- [Displays types](#displays-types)
   - [Measurements tools](https://github.com/Brankale/Handheld-Color-Space-Project/edit/main/README.md#measurements-tools) 
- [Do the measurements](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#do-the-measurements)
   - [Introduction](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#introduction)
   - [Measurements guide for emissive displays](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#measurements-guide-for-emissive-displays)
   - [Measurements report (template)](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#measurements-report-template)
- [Measurements Validation](https://github.com/Brankale/Handheld-Color-Space-Project/blob/main/README.md#measurements-validation)


# Displays types

- `Emissive`: the display **emits its own light** (no external illumination needed).
- `Reflective`: the display **does not emit light**; it reflects ambient light. Pixels modulate reflection, rather than emitting light.
- `Transflective`: **hybrid** of emissive and reflective. A backlight is present, but the display can also use ambient light (via a partially reflective layer).

## Measurements tools

Depending on the display type, you must use the appropriate meter to ensure accurate measurements. Here is a summary table:

| Meter  | Emissive | Reflective | Transflective |
| ------------- | :-------------: | :-------------: | :-------------: | 
| Colorimeter        | ✅ good accuracy | ⚠️ not recommended (2) | ❓ |
| Spectroradiometer  | ✅ highest accuracy | ⚠️ not recommended (2) | ❓ |
| Spectrophotometer  | ⚠️ not recommended (1) | ✅ | ❓ |

(1) [AI provided info] A spectrophotometer primarily measures reflected light from surfaces. Some models have an “emissive mode,” but they’re generally slower, less sensitive at low light, and not ideal for bright HDR peaks or very dark near-black, common in emissive displays.

(2) [AI provided info]

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
