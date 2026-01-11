# Measurements report

- `template version`: 1
- `author`: the name of the author of the measurements.
- `date`: the date of the measurement. This is important because screen colors degrade over time and with use. Recording the measurement date helps track screen aging and maintain accuracy.
- `handheld`: the handheld device being measured.

## Screen
- `type`: emissive / reflective / transflective
  <br>Display technology used by the screen.

- `screen location`: top / bottom / n.a.
  <br>Physical location of the screen on the device. n.a. if only one screen is present.

- `bit depth`: integer
  <br>Bit depth per color channel (e.g., the NDS Lite uses 6 bits per channel, resulting in 262,144 colors).

- `manufacturer`: manufacturer name
  <br>Manufacturer of the measured screen panel.

## Meters
- `name`: name of the meter used
- `type`: colorimeter / spectroradiometer / spectrophotometer

## Software (list all software used)
- `software name`: the name of the software used to perform the measurements (e.g., HCFR)
    - `software version`: the version of the software used
    - `software config`: relevant configuration used to set up the software (e.g., command-line arguments)

## Measurement environment
- `ambient lighting`: yes / no / n.d.
  <br>Indicates whether ambient light was present during the measurements. This includes room lighting, indirect daylight, or any other external light sources that could affect the readings.

## Screen state
- `screen warm-up`: yes / no / n.d.
  <br>Indicates whether the screen was powered on for a sufficient amount of time before the measurements, allowing brightness and color output to stabilize.

- `brightness level`: max / custom
  <br>Specifies the brightness setting used during the measurements.
  Use `max` if the screen was set to its maximum brightness, or `custom` if a specific user-defined level was selected.

- `charger connected`: yes / no / n.d.
  <br>Indicates whether the console was connected to a charger during the measurements, as power state may affect screen brightness or stability.

- `screen protector / touchscreen overlay`: yes / no / n.d.
  <br>Indicates whether a screen protector, touchscreen overlay, or any additional layer was present on top of the display during the measurements.

- `console purchase year`: year / n.d.
  <br>Purchase year of the console. This information is used to estimate the screen panel age.

- `second-hand`: yes / no
  <br>yes if it is a second-hand console, no if it was purchased new

- `panel artifacts`: qualitative observations
  <br>Qualitative observations of visible screen artifacts such as spots, discoloration, uneven brightness, vignetting, glow, or other irregularities.

- `estimated console hours of usage`: numeric value / unknown
  <br>Approximate total usage time of the console in hours. This value does not need to be precise and can be a rough estimate.

# Notes

any relevant additional information about the screen or the measurements.
