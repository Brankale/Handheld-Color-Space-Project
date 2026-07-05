> [!NOTE]
> Some parts of this guide were developed with AI assistance.

> [!WARNING]
> I'm not a color scientist or expert. This guide may contain inaccuracies or misleading information. Please take it with a grain of salt. If you notice any issues, feel free to open an issue.

# Handheld Color Space Project

This project aims to **accurately reproduce the original color output of handheld console screens** on modern displays.

All data is **based on instrumented colorimetric measurements of real hardware**. Subjective, visual, or “by eye” adjustments are explicitly excluded.

Each display measurement is translated into a dedicated **RetroArch shader**, designed using color science principles, high-precision mathematical modeling, and validated against the original hardware to ensure faithful color reproduction as it appeared on the real device.


# Showcase

## Reflective displays

> [!NOTE]
> Physically accurate simulation of ambient illuminant effects through measured screen reflectance data, enabling the modeling of the display's reflective behavior instead of relying on chromatic adaptation.

> [!WARNING]
> The GBC shaders are based on "-45°" screen reflectance measurements (45°/0° geometry + 180° orientation), which produce a washed-out image due to the reflective properties of the original display. The screenshots shown here were generated using the "45° Simulation" parameter (45°/0° geometry + 0° orientation), a rough approximation that better represents the display's intended appearance.


| GBC no shader | GBC Illuminant A (WIP) | GBC Illuminant D50 (WIP) | GBC Illuminant D65 (WIP) |
| :-------------: | :-------------: | :-------------: |  :-------------: |
| <img width="200" height="180" alt="gbc_raw" src="https://github.com/user-attachments/assets/778f5ae6-6d22-4c2b-b449-9bd27065621c" /> | <img width="200" height="180" alt="gbc_a" src="https://github.com/user-attachments/assets/8b752141-7f34-42dd-a2f0-6a61b34b5db3" /> | <img width="200" height="180" alt="gbc_d50" src="https://github.com/user-attachments/assets/1a407db6-5b6f-4a1a-9e33-b8a9d0d9353f" /> | <img width="200" height="180" alt="gbc_d65" src="https://github.com/user-attachments/assets/a34409f7-a662-48c0-854f-71bf35c11b6e" /> |


## Emissive displays

| GBA no shader | GBA SP AGS-101 | GB Micro |
| :-------------: | :-------------: | :-------------: |
| <img width="240" height="160" alt="GB no shader" src="https://github.com/user-attachments/assets/f246821b-1583-4bee-b0b7-b801614d2a17" /> | <img width="240" height="160" alt="GBA SP AGS101" src="https://github.com/user-attachments/assets/d3c30f3b-ff4a-4d60-a827-9f01b62fb661" /> | <img width="240" height="160" alt="GBA micro" src="https://github.com/user-attachments/assets/a4d058b6-c347-4cf8-8f4f-65eb3a85dc5f" /> |  |

| DS no shader | DS Phat | DS Lite |
| :-------------: | :-------------: | :-------------: |
| <img width="256" height="192" alt="raw" src="https://github.com/user-attachments/assets/8e7f0c11-3dab-4217-95f5-f24c085129bc" /> | <img width="256" height="192" alt="ds_phat" src="https://github.com/user-attachments/assets/503444a4-13e0-4f75-a839-59cd8150d3b6" /> | <img width="256" height="192" alt="ds_lite" src="https://github.com/user-attachments/assets/98afdda1-5ec9-4b34-9347-cd5a59aa9cd7" /> | 

| 3DS no shader | 3DS | New 3DS XL (IPS) |
| :-------------: | :-------------: | :-------------: |
| <img width="800" alt="3ds_no_shader" src="https://github.com/user-attachments/assets/ad6fbbd6-4a31-4554-8387-1bb5facfc15a" /> | <img width="800" alt="3ds" src="https://github.com/user-attachments/assets/8b71e3e3-a9a7-41e7-ad1c-c8da47cfca3d" /> | <img width="800" alt="3ds_xl_ips" src="https://github.com/user-attachments/assets/e49c8c67-f320-4a7c-9b38-672e0a8515c5" /> |
| `no shader - already D65` | `D65 chromatic adaptation` | `D65 chromatic adaptation` |
| <img width="800" alt="3ds_no_shader" src="https://github.com/user-attachments/assets/ad6fbbd6-4a31-4554-8387-1bb5facfc15a" /> | <img width="800" alt="3ds_d65" src="https://github.com/user-attachments/assets/d0b764d3-b378-4e1a-a714-add092b10224" /> | <img width="800" alt="3ds_xl_ips_d65" src="https://github.com/user-attachments/assets/460b54cc-5f74-40af-b41f-6552b2645932" /> |






# Handhelds status report

| Nintendo Handheld  | Display Type | Display Data Collected? | Known Manufacturers | Measurements Notes |
| ------------- | :-------------: | :-------------: |  :-------------: | :------------- |
| `Game Boy` |  Reflective | 🔴 | ? | |
| `Game Boy Pocket` |  Reflective | 🔴 | ? | |
| `Game Boy Light` |  Emissive | 🔴 | ? | |
| `Game Boy Color` |  Reflective | 🕐 | ? | Currently provided data have issues |
| `Game Boy Advance AGB-001` |  Reflective | 🔴 | ? | Currently provided data have issues | 
| `Game Boy Advance SP AGS-001` |  Transflective<br>(frontlit on),<br>Reflective<br>(frontlit off) | 🔴 | ? | Currently provided data have issues |
| `Game Boy Advance SP AGS-101` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer |
| `Game Boy Micro` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer |
| `NDS Phat` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer |
| `NDS Lite` |  Emissive | 🔵⚠️ | Hitachi, Sharp ([link](https://www.wired.com/2008/02/sharp-hitachi-s)) | - unknown manufacturer<br>- greyscale gamma differs between reports (different manufacturers?) |
| `NDSi` |  Emissive | 🔴 | ? | |
| `NDSi XL` |  Emissive | 🔴 | ? |  |
| `3DS` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer<br>- equal primaries across measurements (except blue) and similar gamma |
| `3DS XL` |  Emissive | 🔴 | ? |  |
| `New 3DS` |  Emissive | 🔴 | ? | |
| `New 3DS XL` |  Emissive | 🔵⚠️ | ? | - only IPS top screen analyzed<br>- screen lottery<br>- unknown manufacturer<br>- [other info here - Erica Griffin](https://www.youtube.com/watch?v=QvDdaVZ7MCU) |
| `2DS` |  Emissive | 🔴 | ? |  |
| `New 2DS` |  Emissive | 🔴 | ? |  |
| `New 2DS XL` |  Emissive | 🔴 | ? | |
| `Wii U` |  Emissive | 🔴 | ? | |
| `Switch` |  Emissive | 🕐 | Innolux | - [other info here - Erica Griffin](https://www.youtube.com/watch?v=QvDdaVZ7MCU)  |
| `Switch Mini` |  Emissive | 🔴 | ? | |
| `Switch OLED` |  Emissive | 🔴 | ? | - [other info here - GamingTech](https://www.youtube.com/watch?v=mYnUdYoh_xc) |
| `Switch 2` |  Emissive | 🔴 | ? | |

| Sony Handheld  | Display Type | Display Data Collected? | Known Manufacturers | Measurements Notes |
| ------------- | :-------------: | :-------------: |  :-------------: | :------------- |
| `PSP-1000 (Phat)` |  Emissive | 🔵⚠️ | ? | - missing manufacturer<br>- missing exact model number |
| `PSP-2000 (Slim)` | ? | 🔴 | ? | |
| `PSP-3000 (Brite)` | ? | 🔴 | ? | |
| `PSP-N1000 (Go)` | ? | 🔴 | ? | |
| `PSP-E1000 (Street)` | ? | 🔴 | ? | |

**Legend**:
- 🔴: No data available / Invalid data
- 🔵: Data available
- 🟢: Data available and verified by two or more screen reports from different consoles
- ⚠️: Some information is missing (e.g., manufacturer, measurement tools, etc.)
- 🕐: Measurement data validation in progress




# Index

- [Retroarch Shaders](https://github.com/Brankale/Handheld-Color-Space-Project/edit/main/README.md#retroarch-shaders)
   -  [Shader parameters](https://github.com/Brankale/Handheld-Color-Space-Project/edit/main/README.md#shader-parameters)
      - [Chromatic Adaptation](https://github.com/Brankale/Handheld-Color-Space-Project/edit/main/README.md#chromatic-adaptation)
   -  [Debug Shader parameters](https://github.com/Brankale/Handheld-Color-Space-Project/edit/main/README.md#debug-shader-parameters)
      - [Show out of Gamut colors](https://github.com/Brankale/Handheld-Color-Space-Project/edit/main/README.md#show-out-of-gamut-colours) 


# Retroarch Shaders

In the `handheld` folder, you’ll find the measured consoles and their corresponding RetroArch shaders.

> [!NOTE]
> Currently, only the sRGB color space is supported. I haven’t found a way to instruct RetroArch or the operating system (at least on macOS) to interpret the shader’s output framebuffer as a non‑sRGB color space (such as Display P3, Rec. 2020, etc.). Given this limitation, there’s little benefit in supporting other color spaces, since you wouldn’t get the expected colors. If you know of any way (even a partial workaround) to overcome this limitation, I’d appreciate your support.

## Shader parameters
 
### Chromatic Adaptation

---

#### **OFF — Original Color Reproduction (Default)**

No chromatic adaptation is applied

- **Pros**
   - Most accurate representation of the original display behavior.
   - Preserves differences between screens of the same console model (often referred to as *“screen lottery”*).

- **Use case**
   - **Currently recommended for general use**.
   - This option must be used if you want to make side by side comparisons with the original console.
   - Recommended for consoles with unusual or very warm/cool white points to preserve the original look & feel.
 
> [!WARNING]
> Currently, it does not fully model the human visual adaptation system, which can result in **reduced perceptual accuracy** in some specific viewing conditions. A full CIECAM02 / CIECAM16 pipeline must be implemented to address this problem.

---

#### **ON — White Point Normalization**

Applies D65 white point (full chromatic adaptation)

- **Pros**
   - Can mitigate *screen lottery* by enforcing a shared white reference across displays.
   - Can slightly reduce out-of-gamut colors as a side effect.

- **Cons**
   - Can noticeably alter color balance on consoles with unusual or very warm/cool white points.
 
- **Use case**
   - You can use this option as a trade-off between the display’s original color reproduction and a neutral white balance tipically found on modern displays.

> [!WARNING]
> Currently, it does not fully model the human visual adaptation system, which can result in **reduced perceptual accuracy** in some specific viewing conditions. A full CIECAM02 / CIECAM16 pipeline must be implemented to address this problem.

---

#### Example

Chromatic adaptation on the GameBoy Micro shader:
- **OFF** (bottom left) = "blue tinted / cool temperature greyscale"
- **ON** (top right) = "neutral greyscale"

<img width="896" height="504" alt="chromatic adaptation example" src="https://github.com/user-attachments/assets/35d7e0e9-a668-494e-89d8-3141af177f23" />


## Debug Shader parameters

These parameters are used to analyze the shader's output image.

### Show out of Gamut colours

Enable this option to highlight in red the colors that cannot be represented in the sRGB color space. These colors are only approximations.


# Special Thanks

- **Pokéfan531** for almost all the consoles’ screen measurements and feedback
   - GitHub: https://github.com/Pokefan531/Handheld-Colorspace-Shaders
   - Tumblr: https://pokefan531.tumblr.com/post/766008194709454848/handheld-lcd-shader-projects
- **Pica200** for the 3DS and New 3DS consoles’ measurements
- **Anikom15** for helping me fix some issues with the shader code and and OS/program-specific color space management.
- **Libretro Forum**
   - forum thread: https://forums.libretro.com/t/real-gba-and-ds-phat-colors/1540
