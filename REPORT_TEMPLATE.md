## Measurements report

- `template version`: 1
- `author`: the name of the author of the measurements.
- `date`: the date of the measurement. This is important because screen colors degrade over time and with use. Recording the measurement date helps track screen aging and maintain accuracy.
- `handheld`: the handheld device being measured.

- **screen**
  - `type`: emissive / reflective / transflective
    Display technology used by the screen.

  - `screen location`: top / bottom
    Physical location of the screen on the device. Only applicable if multiple screens are present.

  - `bit depth`: integer
    Bit depth per color channel (e.g., the NDS Lite uses 6 bits per channel, resulting in 262,144 colors).

  - `manufacturer`: manufacturer name
    Manufacturer of the measured screen panel.

- **meters**
    - `name`: name of the meter used
    - `type`: colorimeter / spectroradiometer / spectrophotometer

- **software (list all software used)**
    - `software name`: the name of the software used to perform the measurements (e.g., HCFR)
        - `software version`: the version of the software used
        - `software config`: relevant configuration used to set up the software (e.g., command-line arguments)

- **measurement environment**
    - `ambient lighting`: yes / no / n.d.
    Indicates whether ambient light was present during the measurements. This includes room lighting, indirect daylight, or any other external light sources that could affect the readings.

- **screen state**
  - `screen warm-up`: yes / no / n.d.
    Indicates whether the screen was powered on for a sufficient amount of time before the measurements, allowing brightness and color output to stabilize.

  - `brightness level`: max / custom
    Specifies the brightness setting used during the measurements.
    Use `max` if the screen was set to its maximum brightness, or `custom` if a specific user-defined level was selected.

  - `charger connected`: yes / no / n.d.
    Indicates whether the console was connected to a charger during the measurements, as power state may affect screen brightness or stability.

  - `screen protector / touchscreen overlay`: yes / no / n.d.
    Indicates whether a screen protector, touchscreen overlay, or any additional layer was present on top of the display during the measurements.

  - `console purchase year (new only)`: year / unknown
    Purchase year of the console, provided only if the console was bought new and before it went out of production. This information is used as a proxy to estimate the screen panel age. If these conditions are not met, use `unknown`.

  - `panel artifacts`: qualitative observations
    Qualitative observations of visible screen artifacts such as spots, discoloration, uneven brightness, vignetting, glow, or other irregularities.

  - `estimated console hours of usage`: numeric value / unknown
    Approximate total usage time of the console in hours. This value does not need to be precise and can be a rough estimate.


- **measurement method**
    - `test pattern size`: full screen / windowed (specify size or percentage if applicable)
    - `sensor positioning`: contact / non-contact (specify distance if non-contact)
    - `measurement angle`: perpendicular / angled (specify angle if known)
    - `methodology`: detailed description of how the measurements were performed, including the sequence of steps, measurement strategy, and any precautions taken to reduce errors

- **notes**: any relevant additional information about the screen or the measurements.
