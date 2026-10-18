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
- [Sources](#sources)


# Displays types

- `Emissive`: the display **emits its own light** (no external illumination needed).
- `Transmissive`: the display uses a separate backlight and modulates the light passing through the panel. A backlit LCD is therefore transmissive, whereas an OLED is emissive. Although the physical principles differ, both are measured from the viewing side using an instrument's emissive mode.
- `Reflective`: the display **does not emit light**; it reflects ambient light. Pixels modulate reflection, rather than emitting light.
- `Transflective`: **hybrid** of transmissive and reflective. A backlight is present, but the display can also use ambient light (via a partially reflective layer).

## Measurements tools

> [!WARNING]
> **Marketing terms used for instruments can sometimes be misleading.** Product names often describe an instrument's main market or use, not every measurement it can perform. For example, some portable optical spectrometers, such as the i1Pro and ColorMunki Photo/Design, work as spectrophotometers in reflective mode and as spectroradiometers in emissive mode: the built-in lamp is used for reflective measurements and switched off for emissive measurements [2, 3]. The word *colorimeter* can also refer to different instrument types, including display colorimeters and reflective colorimeters with their own light source. Check the instrument's supported modes and outputs rather than relying on its product name alone [2, 3]. The same brand can also cover different instrument types: the ColorMunki Photo/Design is a spectrometer, whereas the ColorMunki Display is a display colorimeter [2].

### 1. Colorimeter

#### What it does and how it works

Human vision uses three kinds of cone cells in the eye to sense light. Each kind responds differently, and the brain combines their signals to perceive color. A colorimeter uses a simplified version of this idea: three sensors, each behind a colored filter designed to approximate the CIE 1931 standard observer curves (standardized curves derived from human color vision), measure three signals from the incoming light. It does not separate and record the full spectrum [1, 2].

#### The question it helps answer

**What three color signals does this light produce?**

#### What it measures

After applying a correction, the colorimeter reports three values called **X, Y and Z** (CIE 1931). Together they describe the measured color; **Y** is luminance, in cd/m². The colorimeter does not record the spectrum, so color cannot be recalculated for a different illuminant (light source). This matters for reflective displays, whose appearance depends on the light illuminating them [1–3].

#### Where it is useful

Colorimeters are useful for measuring emissive and transmissive displays. They are generally fast, and good models can perform well on dim patches [1].

#### Limitations and requirements

The filters only approximate human vision, and their error depends partly on the light spectrum. A display colorimeter therefore needs a suitable display correction; a correction made for one display technology may not be accurate for another [1, 2]. A correction can be created by measuring the same display with the colorimeter and a spectroradiometer (CCMX, *Colorimeter Correction Matrix*), or calculated from spectral samples for that display type (CCSS, *Colorimeter Calibration Spectral Sample*). The CCSS method only works with colorimeters whose spectral sensitivities are known, such as the i1Display Pro and Spyder 4/5 [1–3].

#### Modes and variants

Some colorimeters include their own light source and can measure light reflected by a surface. These are reflective colorimeters, a different type from display colorimeters. They can report color values for surfaces, but do not provide the spectral reflectance required by this project's reflective-display workflow [2].

### 2. Spectrophotometer

#### What it does and how it works

A spectrophotometer is an optical spectrometer with its own built-in light source. It illuminates the sample and compares the light that comes back with the light returned by a white reference tile, wavelength by wavelength. Because the result is a ratio to that white reference, every reflective spectrophotometer must be calibrated against it [3, 6].

#### The question it helps answer

**How much of the light at each wavelength does this surface reflect?**

#### What it measures

It reports **spectral reflectance**: the fraction of light reflected at each wavelength. Keeping the spectrum lets software calculate color values for different illuminants; the resulting XYZ values depend on the illuminant selected [3, 6].

#### Where it is useful

A spectrophotometer is useful when the measurement needs the surface's reflectance spectrum, rather than only a set of color values. This is the type of data used by this project's reflective-display workflow [3, 6].

#### Limitations and requirements

Before reflective measurements, calibrate the instrument against its white reference tile, following its prompts and manual. In `spotread`, press `k` to repeat the tile calibration when needed [3]. Low-light readings and usable wavelength ranges depend on the instrument, so inspect the measurements and retain the spectral data for post-processing [3].

#### Modes and variants

Some portable spectrophotometers, such as the i1Pro and ColorMunki Photo/Design, also have an emissive mode: the built-in lamp is switched off and the instrument measures light coming from the source. In that mode it works as a spectroradiometer. See [Product names, modes, and functional names](#product-names-modes-and-functional-names) [2, 3].

#### Measurement geometry

The measurement geometry describes the angle at which light reaches the sample and the angle at which the instrument reads it. It is written as *illumination/viewing*. Common geometries for spectrophotometers are [4, 6]:

| Geometry | How it works | Use in this project |
| --- | --- | --- |
| 45°/0° or 0°/45°, directional | Light at 45° from one direction, reading perpendicular to the sample (or the reverse). Excludes the mirror-like (specular) reflection. | ✅ **OK**: reproduces a single directional light source, including its effect on contrast. Results depend on how the instrument is rotated, so **record the orientation in the report; without it, measurements cannot be compared**. See [Instrument Orientation](#instrument-orientation). |
| 45°/0° or 0°/45°, annular | Light at 45° from a ring all around the sample, reading perpendicular (or the reverse). Excludes the specular reflection. | ✅ **OK**: an average over all light directions; reproducible, but does not reproduce the effect of a single light source. |
| d/8° SCE (sphere) | Diffuse light from all directions inside a white sphere; reading at 8°; specular reflection excluded. | ✅ **OK**: represents very diffuse light; not directly comparable with 45°/0° measurements. |
| d/8° SCI (sphere) | As above, but the specular reflection is included. | ⚠️ **OK with limitations**: includes the glare from the screen surface, which inflates dark patches and lowers the measured contrast. |
| Multi-angle | Light from one angle; readings from several angles. | ✅ **OK**, and the best option when available: measure as many angles as possible, always including a 45°/0° reading for comparison with other measurements. Multi-angle data also help shaders simulate the screen under different geometries and orientations. |

> [!WARNING]
> These recommendations are provisional and need review. The supporting data are limited and not conclusive, so treat them as a general indication only. Few user measurements are available, so measurements made with any geometry are welcome, as long as the geometry and orientation are recorded in the report.

**Why it matters for reflective displays.** A matte paper scatters light in a similar way in all directions, so the geometry has a limited effect. A reflective LCD can behave differently: its polarizers, color filters and rear reflector can send light preferentially in some directions. The measured reflectance therefore applies to the geometry used, and measurements made with different geometries are not directly comparable.

- Record the instrument model, its measurement geometry and, for directional geometries, its orientation in the report.
- If the results change when the instrument is rotated, see [Instrument Orientation](#instrument-orientation).
- A spectroradiometer with external illumination lets you choose the geometry, for example one closer to real use (lamp above, viewer in front). This method has not been tested by this project; see [Reflective displays](#reflective-displays).

### 3. Spectroradiometer

#### What it does and how it works

A spectroradiometer is an optical spectrometer without its own light source. It measures the light that reaches it, wavelength by wavelength, and reports it in absolute units thanks to a factory calibration. When measuring a display, the light comes from the display itself. A reflective sample must instead be lit by a separate lamp, and the instrument measures the light reflected by the sample [3, 7].

#### The question it helps answer

**How much light from this source reaches the instrument at each wavelength, in absolute terms?**

#### What it measures

It records the source's spectrum as an absolute measurement, rather than as a fraction of a white reference. Software can use the spectrum to calculate XYZ values [2, 3, 7].

#### Where it is useful

A spectroradiometer is useful for measuring the spectrum and absolute light output of emissive and transmissive displays. Spectral measurements can also be used to create a correction for a colorimeter [1–3].

#### Limitations and requirements

Absolute light measurements require a suitable absolute calibration; follow the instrument's model-specific instructions [3, 7]. Low-light performance depends on the instrument and conditions: a portable spectroradiometer (such as an i1Pro or ColorMunki Photo/Design in emissive mode) can be slower or less reliable on dim patches than a good, corrected colorimeter [1]. A reflective sample does not emit its own light, so measuring it with a spectroradiometer needs a separate, stable external lamp and a white reference measured under the same lighting. This method has not been tested by this project, and it requires extra equipment and careful control of the illumination.

#### Modes and variants

The name **spectroradiometer** is often associated with high-end, costly laboratory instruments (reference spectroradiometers) [2]. A portable spectrophotometer in emissive mode also works as a spectroradiometer (portable spectroradiometer), although its performance is not necessarily equivalent to a reference instrument [2, 3, 7]. See [Product names, modes, and functional names](#product-names-modes-and-functional-names).

### Product names, modes, and functional names

Use this table to map a product and its measurement mode to the functional name used in this guide. The rest of the guide uses only the functional names: **spectrophotometer** for reflectance measurements and **spectroradiometer** for absolute measurements of emitted light.

| Instrument type | Mode and illumination | Functional name | Output and units | Example instruments |
| --- | --- | --- | --- | --- |
| Optical spectrometer | Reflective; built-in light illuminates the sample and the instrument measures the returned light against a white reference | Spectrophotometer | Spectral reflectance at each sampled wavelength; `spotread` reports `%/nm` [3] | i1Pro or ColorMunki Photo/Design in reflective mode |
| Optical spectrometer | Emissive; measures light from the source. On a multi-mode instrument, its reflective lamp is off | Spectroradiometer | Absolute spectral radiance in `mW/(m²·sr·nm)` [3] | i1Pro or ColorMunki Photo/Design in emissive mode; reference-grade examples include JETI specbos, Photo Research, and Konica Minolta CS-2000 [2] |
| Display colorimeter | Emissive; the display provides the light being measured | Display colorimeter | Absolute XYZ values; luminance Y is in `cd/m²` [3] | i1Display Pro, ColorMunki Display or Spyder [1, 2] |
| Reflective colorimeter | Reflective; built-in light illuminates the sample | Reflective colorimeter | Color values, but no spectrum; the output scale depends on the instrument and software [2] | DTP51 or SwatchMate Cube [2] |

**Important:** display colorimeters and reflective colorimeters are distinct instrument types. Do not assume that a display colorimeter contains a lamp or can switch to reflective measurement [2].

### Choosing an instrument by display type

**Legend:** ✅ **OK**: suitable for the measurement. ⚠️ **OK with limitations**: usable, with the limitations listed in the cell. ❌ **KO**: cannot measure the quantity required. ❓ **Not tested by this project**: the method has not been tried yet. The symbols indicate suitability, not a ranking of instruments.

Emissive and transmissive displays are measured the same way: the instrument measures the light coming from or through the screen. The same guidance therefore applies to both.

| Instrument and mode | Emissive or transmissive display |
| --- | --- |
| Display colorimeter | ✅ **OK** with a suitable display-specific correction based on spectral data, ideally measured from the same display: fast and can perform well on dim patches.<br>⚠️ **OK with limitations** without that correction: readings may be inaccurate; do not rely on them as final results [1–3]. |
| Portable spectroradiometer | ✅ **OK**: a direct spectral measurement when the instrument has suitable absolute calibration. It can also provide spectral data for a colorimeter correction. It may be slower or less reliable at low light than a good corrected colorimeter [1–3]. |
| Reference spectroradiometer | ✅ **OK**: measures the emitted spectrum and absolute light output with suitable calibration. Accuracy and low-light performance still depend on the model and conditions [2, 3, 7]. |
| Spectrophotometer | ❌ **KO**: it illuminates the sample and measures reflected light, not the light emitted or transmitted by the screen. |

A spectroradiometer measures the spectrum directly, but that does not mean every model performs equally well at every light level. A suitable display correction can make a colorimeter the more practical choice for fast measurements and dim patches; the spectroradiometer provides the spectral reference needed to create or select that correction [1–3].

#### Reflective displays

| Instrument and mode | Reflective display |
| --- | --- |
| Display colorimeter | ❌ **KO**: it has no light source and reports XYZ values, not the spectral reflectance required by this project's workflow [1–3]. |
| Reflective colorimeter | ⚠️ **OK with limitations**: a fallback when no spectrophotometer is available. Its built-in light illuminates the surface and it reports color values, but:<br>• it does not record spectral reflectance, so its XYZ values apply only to its built-in light source and cannot be recalculated for another illuminant;<br>• noisy wavelength regions cannot be inspected or discarded;<br>• its calibration targets ordinary surfaces and has not been verified on reflective LCDs; without a spectrophotometer it cannot be corrected;<br>• the output scale depends on the instrument and software.<br>Document the instrument used [2, 4]. |
| Spectrophotometer | ✅ **OK**: measures spectral reflectance. Calibrate against the white tile and keep the full spectrum; check the instrument's low-light and wavelength limitations [3, 6]. |
| Spectroradiometer with external illumination | ❓ **Not tested by this project**. Possible setup: light the display with a stable external lamp, then measure the display and a white reference under the same lighting; reflectance = display ÷ white reference, wavelength by wavelength. It requires extra equipment and careful control of the illumination, which makes the setup more complex and costly. |

#### Transflective displays

Measure the transmissive and reflective components separately, using the relevant instrument for each. For the setup described here, measure the transmissive component with the backlight on and the reflective component with it off. For the transmissive component, apply the emissive/transmissive guidance above.

| Instrument and mode | Transflective display |
| --- | --- |
| Display colorimeter, transmissive component | ✅ **OK** with the backlight on and a suitable display-specific correction based on spectral data.<br>⚠️ **OK with limitations** without that correction: readings may be inaccurate; do not rely on them as final results [1–3]. |
| Portable spectroradiometer, transmissive component | ✅ **OK**: measure with the backlight on; requires suitable absolute calibration. Low-light performance depends on the model [2, 3]. |
| Reference spectroradiometer, transmissive component | ✅ **OK**: measure with the backlight on; absolute calibration and low-light performance depend on the instrument [2, 3, 7]. |
| Spectrophotometer, reflective component | ✅ **OK**: measure with the backlight off. Calibrate against the white tile and retain the spectral readings [3, 6]. |
| Spectroradiometer with external illumination, reflective component | ❓ **Not tested by this project**. Possible setup: with the backlight off, light the display with a stable external lamp, then measure the display and a white reference under the same lighting; reflectance = display ÷ white reference, wavelength by wavelength. It requires extra equipment and careful control of the illumination, which makes the setup more complex and costly. |

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
| **Complete** | CIE XYZ coordinates for the full Red, Green, Blue, Yellow, Cyan, Magenta and Greyscale ramps. | 7N = 224 | Provides direct measurements of all primary, secondary and greyscale response curves. |
| **Recommended** | CIE XYZ coordinates for the full Red, Green and Blue ramps, plus Black, White, Yellow, Cyan and Magenta. | 3N + 5 = 101 | Produces results that are practically equivalent to the Complete preset for emissive and transmissive displays, with substantially fewer measurements. |
| **Bare minimum** | CIE XYZ coordinates for the full Greyscale ramp, plus Red, Green, Blue, Yellow, Cyan and Magenta. | N + 6 = 38 | The primary gamma curves must be calculated rather than measured directly and may be slightly less accurate because measurement errors can be amplified by the mathematical extraction steps. |

> [!NOTE]
> The counts assume a 5-bit signal depth: $N = 2^5 = 32$ levels per full ramp. For a bit depth $b$, use $N = 2^b$. For emissive and transmissive displays, is not necessary to measure more than 32 patches per ramp even if the native signal depth is higher because the intermediate values can be interpolated without loss of accuracy. 

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
- **Lighting:** **all external sources of ambient light must be eliminated**. Take these measurements in a completely dark room to prevent external light from altering the sensor readings.
- **Instrument stabilization/warm-up:** Spectrophotometers require a warm-up period to ensure sensor stability before measuring. This can take up to 30 minutes depending on the model (e.g., ColorMunki Photo). Always refer to your instrument's specific manual.
- **Instrument calibration (WIP):** This step is probably a critical one, however it is still under investigation. In `spotread`, arguments like `-Y W:fname.sp` (Save instrument white tile ref. spectrum) or `-Y S:fname.cmf` (Save instrument raw & XYZ spectral sensitivities) are available, but standardized best practices are not firmly established yet.

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
| **Complete** / **Recommended** | Spectral reflectance for the full Red, Green, Blue, Yellow, Cyan, Magenta and Greyscale ramps. | 7N = 224 | Directly measures every required response curve. The secondary ramps also enable validation tests that cannot be performed using only peak secondary measurements. |
| **Bare minimum** | Spectral reflectance for the full Red, Green and Blue ramps, followed by the pairs Black → White, Black → Yellow, Black → Cyan and Black → Magenta. Do not omit the intervening Black readings (*). | 3N + 8 = 104 | Measures the primary gamma curves directly and captures the peak secondary colors, but does not provide secondary ramps for validation. |
| **Insufficient** | Spectral reflectance for the full Greyscale ramp, plus Red, Green, Blue, Yellow, Cyan and Magenta. | N + 6 = 38 | Accurate primary gamma curves are practically impossible to extract. See [XYZ additivity and gamma extraction](#xyz-additivity-and-gamma-extraction). |

> [!NOTE]
> The counts assume a 5-bit signal depth: $N = 2^5 = 32$ levels per full ramp. For a bit depth $b$, use $N = 2^b$.

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

`spotread` XYZ and Lab values depend on the integrity of the spectral data. Measurements made with the ColorMunki Photo show an instrumental limitation below 440 nm, where the response drops to a flat baseline and includes physically impossible negative values. Above 700 nm, the measured signal also becomes unstable near the instrument's operational limit. Inaccurate spectral readings in these regions propagate into the calculated XYZ values, with an impact that depends on the selected illuminant spectrum and standard-observer functions. These regions must therefore be inspected and treated cautiously during post-processing and when recalculating XYZ coordinates.

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

## Sources

The following sources are used in this guide.

1. ArgyllCMS, [Wide Gamut Displays and Colorimeters](https://www.argyllcms.com/doc/WideGamutColmters.html).
2. ArgyllCMS, [Operation of particular instruments](https://www.argyllcms.com/doc/instruments.html).
3. ArgyllCMS, [spotread documentation](https://www.argyllcms.com/doc/spotread.html).
4. X-Rite, [Colorimeter and spectrophotometer comparison](https://www.xrite.com/blog/colorimeter-vs-spectrophotometer).
5. Wikipedia, [Spectrometer](https://en.wikipedia.org/wiki/Spectrometer).
6. Wikipedia, [Spectrophotometry](https://en.wikipedia.org/wiki/Spectrophotometry).
7. Wikipedia, [Spectroradiometer](https://en.wikipedia.org/wiki/Spectroradiometer).
