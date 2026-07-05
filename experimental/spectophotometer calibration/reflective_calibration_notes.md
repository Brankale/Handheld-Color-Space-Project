# Reflective Display Measurement — Calibration Notes

> These notes are intended to fill the **Calibration (WIP)** subsection of the
> *Measurements guide for reflective displays* section in `CONTRIBUTING.md`.
>
> Each claim is tagged:
> - ✅ **verified** — sourced directly from ArgyllCMS documentation
> - ⚠️ **assumption** — inferred from physical principles or general instrument practice; must be confirmed before publishing
> - 🔬 **empirical** — observed during actual measurement sessions

---

## Calibration

### Why calibrate

A spectrophotometer performing reflective measurements relies on two internal
references to convert raw sensor counts into physically meaningful reflectance
values:

**White reference calibration**
The instrument illuminates a known, factory-characterized white tile and records
the resulting per-wavelength sensor response. This stored response becomes the
100 % reflectance baseline. Every subsequent sample measurement is divided
wavelength-by-wavelength against this baseline, which corrects for:

- The spectral shape of the instrument's light source (the white LED in the
  ColorMunki Photo)
- Non-uniform sensitivity of the detector array across wavelengths
- Slow aging of the light source

**Dark reference calibration**
The sensor generates a small electronic signal even when no light reaches it
(dark current). Subtracting this offset from each measurement prevents it from
inflating the reported reflectance, an effect that is proportionally largest on
dark patches where the true signal is small.

> ⚠️ **assumption** — Whether the ColorMunki Photo performs a dark scan as part
> of its standard calibration sequence (as opposed to requiring a separate step)
> is **not described in the ArgyllCMS documentation**. The ArgyllCMS instruments
> page only references the white tile for this class of instrument. Confirm from
> the X-Rite ColorMunki Photo user manual before relying on this point.
> See [Hardware Owner Checklist](./calibration_checklist.md) — Test 1.

Sources: [ArgyllCMS spotread — `-Y W` flag](https://www.argyllcms.com/doc/spotread.html),
[ArgyllCMS — Operation of particular instruments (ColorMunki)](https://www.argyllcms.com/doc/instruments.html)

---

### How `spotread` handles calibration

#### Automatic prompt at startup

✅ From the `-N` flag documentation:

> *"Any instrument that requires regular calibration will ask for calibration on
> initial start-up."*

When `spotread` connects to an instrument that requires periodic calibration, it
automatically prompts the user to perform it before the first measurement.

#### Calibration validity and timeout

✅ From the same source:

> *"The `-N` flag suppresses this initial calibration if a valid and not timed out
> previous calibration is recorded in the instrument or on the host computer."*

This means the calibration state is tracked either inside the instrument's
firmware or by the ArgyllCMS driver on the host. Once that record expires,
`spotread` prompts again automatically.

> ⚠️ **assumption** — The specific timeout duration is **not documented publicly**
> in the ArgyllCMS documentation. It is instrument-specific and hardcoded in the
> ArgyllCMS driver. The exact value can only be determined empirically.
> See [Hardware Owner Checklist](./calibration_checklist.md) — Test 2.

#### Flags and keys for calibration control

| Flag / Key | Behaviour | Source |
|---|---|---|
| *(none — default)* | Prompts for calibration at startup if needed | ✅ `-N` flag doc |
| `-N` | Skips initial calibration **if a valid, non-expired one exists**. Use only on the 2nd+ invocation within a single session. | ✅ `-N` flag doc |
| `k` (interactive key) | Triggers a recalibration at any point during an active `spotread` session | ✅ spotread key commands |
| `-O` | Performs one calibration or measurement and exits; combine with `-N` for scripted workflows | ✅ `-O` flag doc |

> ✅ From the `-N` docs: *"It is advisable to only use this option on the second
> and subsequent measurements in a single session."*

#### Recalibration during long sessions

For a 224-patch reflective session (7 channels × 32 patches), measuring all
patches in a single pass takes considerable time. **Recalibration with `k` is
recommended between color channels**, not only at the start of the session.

The rationale is discussed in [Empirical Observations](#empirical-observations).

---

### Calibration procedure with `spotread` (ColorMunki Photo)

> ⚠️ **assumption** — The step-by-step physical procedure below is based on
> general X-Rite spectrophotometer practice. The ArgyllCMS documentation does
> not describe the ColorMunki Photo's calibration sequence in detail. Verify
> against the X-Rite ColorMunki Photo user manual, and record the exact prompt
> text that `spotread` displays (see Checklist — Test 1).

1. Allow the instrument to warm up for **at least 30 minutes** with the USB
   cable connected before starting `spotread`. This brings the sensor and LED to
   a stable operating temperature.
2. Launch `spotread` (without `-N`). It will connect to the instrument and
   automatically prompt for calibration.
3. When prompted, rotate the ColorMunki's aperture wheel to the **calibration
   position** (the position that exposes the instrument's internal white
   reference tile).
4. Trigger the measurement when `spotread` instructs (button press or key press).
5. The instrument reads the white tile and stores the per-wavelength response as
   its calibration reference.
6. After calibration, `spotread` enters its normal measurement loop.

For **subsequent invocations within the same session** (e.g., restarting
`spotread` to start a new log file), use `-N` to skip the repeated calibration
prompt — provided the timeout has not yet expired.

To **recalibrate mid-session** without quitting `spotread`, press `k`.

---

### What calibration affects — and what it does not

| | Corrected by calibration | Notes |
|---|---|---|
| Spectral shape of instrument response | ✅ yes | Per-wavelength normalization against white tile |
| Absolute reflectance scale | ✅ yes | All values normalized to white tile = 100 % |
| Dark floor / sensor offset | ✅ yes (if dark cal is performed) | See note on dark cal above |
| **Gamma curve shape (exponent)** | ❌ **no** | See below |
| Washed-out appearance due to wrong instrument orientation | ❌ **no** | See below |

#### Calibration does not alter the gamma curve shape

> ⚠️ **assumption** — Inferred from the linear, per-wavelength nature of the
> normalization. Not stated explicitly in ArgyllCMS documentation.

White reference calibration applies a **multiplicative scalar per wavelength**:

$$R(\lambda) = \frac{S_{\text{sample}}(\lambda)}{S_{\text{white tile}}(\lambda)}$$

This scales all patches uniformly. The *ratio* between a mid-grey patch and the
white patch — which defines the gamma curve — is unaffected. Calibration
therefore changes the **absolute scale** but not the **shape** of the gamma
curve.

If the measured gamma appears too low (washed-out greyscale), the cause is
almost certainly the **physical orientation of the instrument** relative to the
display's polarizers, not calibration. See *Instrument Orientation* in the
main guide.

> ⚠️ **clarification** — A missing or incorrect dark calibration *can* affect the
> apparent gamma at low luminance levels, because an uncorrected dark offset
> artificially raises the black level and compresses the bottom of the tone
> curve. This is distinct from the intrinsic gamma exponent; it is a floor
> artefact, not a curve shape change.

---

### Diagnostic flags — not calibration

The following `spotread` flags are often discussed alongside calibration but do
**not** perform or alter it. They are diagnostic or informational tools.

#### `-Y W:fname.sp` — Save white tile reference spectrum

✅ Source: [ArgyllCMS spotread — `-Y W` flag](https://www.argyllcms.com/doc/spotread.html)

> *"Reflective instruments use a white reference tile to calibrate against, and
> typically the spectral reflectance of the white tile is recorded inside the
> instrument to calibrate to. The saved spectrum can be used to compare against
> the measurements of a reference grade measurement of the white tile to check
> for tile deterioration, or can be used as a reference for checking on
> instrument calibration accuracy or consistency."*

Use cases:
- Document the white tile spectrum at the start of a measurement campaign
- Detect tile deterioration over time by comparing saved spectra across sessions
- Use with `-R fname.sp` to compute delta E against a known reference

Supported instruments: Spectrolino, i1Pro, i1Pro2, ColorMunki spectrometer.

#### `-Y S:fname.cmf` — Save sensor spectral sensitivities

✅ Source: [ArgyllCMS spotread — `-Y S` flag](https://www.argyllcms.com/doc/spotread.html)

> *"Some colorimeters (such as the i1d3) are calibrated by measuring the spectral
> sensitivity of their three sensors [...] This option saves these curves."*

This flag is designed for **colorimeters** that use CCSS-based calibration. For
the ColorMunki Photo (a spectrophotometer), the output is informational only —
it does **not** constitute a calibration procedure.

#### `-R fname.sp` — Preset reference spectrum

✅ Source: [ArgyllCMS spotread — `-R` flag](https://www.argyllcms.com/doc/spotread.html)

Presets a reference spectrum for computing delta E against all subsequent
readings. Useful for quantifying repeatability between measurements or
verifying consistency against a previously saved white tile reference.

---

### XRGA calibration standard

✅ Source: [ArgyllCMS — Operation of particular instruments (ColorMunki)](https://www.argyllcms.com/doc/instruments.html)

> *"Native Calibration Standard: Reflection measurements are natively X-Rite XRGA."*

The ColorMunki Photo natively outputs reflectance data under the XRGA standard.
The `-A` flag in `spotread` controls the active standard:

| Flag | Standard |
|---|---|
| `-A N` | Native (default) |
| `-A A` | XRGA |
| `-A X` | XRDI |
| `-A G` | GMDI |

When comparing measurements across different instruments (e.g., ColorMunki vs.
Spectrolino), ensure all sessions use a consistent standard, or explicitly
convert. See [ArgyllCMS XRGA documentation](https://www.argyllcms.com/doc/XRGA.html).

---

## Empirical Observations

> 🔬 This section records observations from actual reflective display measurement
> sessions. Claims here are labelled empirical and should be distinguished from
> claims derived from documentation.

### Intra-session luminance drift

**Instrument**: ColorMunki Photo + `spotread`  
**Display**: Reflective LCD (Game Boy Color)  
**Session setup**: ≥30 minutes warm-up before calibration; `spotread` command
as documented in *How to measure*

#### Observation

🔬 When measuring the same greyscale scale from black to white on successive
passes within the same session, later passes yield systematically higher
luminance values. Near-black patches show the largest absolute increase; near-
white patches show a comparatively smaller increase.

#### Ruling out warm-up as the cause

🔬 All sessions included a warm-up of at least 30 minutes before calibration.
The drift therefore occurs **during the measurement session itself**, not because
of a cold instrument at startup.

#### Inferred mechanism

> ⚠️ **assumption** — The following explanation is inferred from physical
> principles and is consistent with the observation, but has not been verified
> instrumentally.

A 30-minute warm-up brings the instrument to thermal equilibrium under **idle**
conditions (LED mostly off). During active measurement, the LED fires for every
patch. Over a session of hundreds of measurements, this creates a cumulative
thermal load beyond the idle equilibrium, causing the sensor's dark current to
rise progressively.

The effect is additive: every measurement has a small positive offset added.
Because near-black patches have a very low true signal, even a small additive
offset produces a large relative change. Near-white patches, having a large true
signal, show the same absolute offset but a much smaller relative change.

This is consistent with the observed direction of drift (values increasing) and
with the distribution of the effect across the greyscale.

Note: the same logic predicts that gamma extracted from these measurements will
appear compressed at the low end if drift is not corrected — the black level
rises while the white level stays relatively stable.

#### Practical consequence

A 30-minute warm-up is **necessary but not sufficient** for long sessions.
Recalibrate using the `k` key **between color channels** (e.g., after completing
all 32 patches of the red channel, before starting the green channel).

The optimal recalibration interval has not yet been quantified. See
[Hardware Owner Checklist](./calibration_checklist.md) — Test 3.

---

## Recommended `spotread` command

Consistent with the *How to measure* section of the guide, and adding no
unnecessary changes to the established command:

```
spotread -s -H -v -V -Y a log.txt
```

For **the first invocation** of a session: run as above; `spotread` will
automatically prompt for calibration.

For **subsequent invocations** within the same session (new log file, same
session): add `-N` to skip re-prompting if the timeout has not expired.

```
spotread -s -H -v -V -Y a -N log2.txt
```

To **recalibrate mid-session** without restarting: press `k` while `spotread`
is running.

---

## References

1. ArgyllCMS `spotread` documentation — flags `-N`, `-O`, `-Y W`, `-Y S`, `-R`, `-A`;
   interactive keys `k`, `r`, `s`
   https://www.argyllcms.com/doc/spotread.html

2. ArgyllCMS — Operation of particular instruments (ColorMunki Photo section;
   XRGA native calibration standard)
   https://www.argyllcms.com/doc/instruments.html

3. ArgyllCMS — XRGA calibration standard
   https://www.argyllcms.com/doc/XRGA.html

4. X-Rite ColorMunki Photo user manual — **required** to verify the physical
   calibration sequence (dark scan presence/absence) before publishing this guide
