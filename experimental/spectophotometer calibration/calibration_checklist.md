# Hardware Owner Checklist
## Reflective Display Calibration — Tests to Run

These tests fill the remaining gaps in `reflective_calibration_notes.md` before
the calibration section can be published in `CONTRIBUTING.md`.

For each test, record: instrument model, firmware version (from `spotread -v`
output), date, and exact console output.

---

### Test 1 — Verify the ColorMunki Photo calibration sequence (CRITICAL)

**Goal**: Determine whether `spotread` prompts for a dark/black position
separately from the white tile, or only for the white tile.

**Steps**:
1. Connect the ColorMunki Photo
2. Run `spotread -v -s`
3. Do **not** press anything yet — copy the exact calibration prompt text
4. Follow the calibration through to completion, noting every prompt
5. Record:
   - Does the instrument ask for a dark/closed position before the white tile?
   - Does it ask only for the white tile?
   - Exact text of each prompt
6. Cross-check the sequence with the X-Rite ColorMunki Photo user manual

**Why it matters**: The calibration notes currently flag the dark scan as
unverified. This test resolves it.

---

### Test 2 — Determine the calibration timeout

**Goal**: Find the approximate window after which `spotread` requires
recalibration on restart.

**Steps**:
1. Perform a calibration (normal startup, no `-N`)
2. Close `spotread`
3. Wait a fixed interval, then restart `spotread` **without** `-N`
4. Record whether it prompts for calibration again

Suggested intervals to test: 15 min, 30 min, 45 min, 60 min, 90 min.

**Expected result**: At some interval the prompt reappears. The last interval
where it did not is the approximate timeout window.

**Why it matters**: Currently documented as "unspecified" in the notes. The
result will let contributors know whether `-N` is safe across a full session.

---

### Test 3 — Quantify intra-session drift

**Goal**: Determine how fast luminance values drift during a measurement session,
and therefore how frequently to recalibrate.

**Steps**:
1. Warm up ≥30 min, then calibrate
2. Identify three stable reference patches on the display:
   - Near-white (e.g., full white)
   - Mid-grey (e.g., 50 % grey)
   - Near-black (e.g., full black)
3. Measure all three patches immediately after calibration → record Y values
4. Measure ~10 non-reference patches normally, then remeasure the three reference
   patches → record Y values + measurement number
5. Repeat step 4 every ~10 measurements throughout the full session
6. At the end, plot Y (luminance) vs. measurement number for each reference patch

**What to look for**:
- The measurement number at which drift in Y exceeds a meaningful threshold
  (e.g., ΔY > 0.5 in absolute reflectance units)
- Whether near-black drifts significantly faster than near-white (confirms the
  dark current hypothesis)
- A practical recalibration interval (e.g., "every 30 patches" or "every channel")

**Why it matters**: Currently the calibration notes say "recalibrate between
channels" without a quantified basis. This test provides it.

---

### Test 4 — Save and document the white tile reference

**Goal**: Establish a baseline white tile spectrum for future deterioration checks.

**Steps**:
1. After calibration, run:
   ```
   spotread -Y W:white_tile_YYYYMMDD.sp
   ```
2. Save the `.sp` file alongside the measurement data
3. Repeat at the start of future sessions and compare files

**Why it matters**: Allows detection of tile degradation over time. Useful for
long-term data quality assurance.

---

### Test 5 — Record full verbose startup output

**Goal**: Document the exact instrument state at the start of every session.

**Steps**:
1. Always run `spotread` with `-v` and redirect the initial output to a text file
2. Record at minimum:
   - Instrument model and serial number (if shown)
   - Firmware version
   - Calibration confirmation message

**Why it matters**: Required for the measurement report template and for
reproducibility.
