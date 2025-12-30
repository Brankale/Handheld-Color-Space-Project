> [!NOTE]
> Some parts of this guide were developed with AI assistance.

> [!WARNING]
> I'm not a color scientist or expert. This guide may contain inaccuracies or misleading information. Please take it with a grain of salt. If you notice any issues, feel free to open an issue.

# Handheld Color Space Project

This project aims to **accurately reproduce the original color output of handheld console screens** on modern displays.

All data is **based on instrumented colorimetric measurements of real hardware**. Subjective, visual, or “by eye” adjustments are explicitly excluded.

Each display measurement is translated into a dedicated **RetroArch shader**, designed using color science principles, high-precision mathematical modeling, and validated against the original hardware to ensure faithful color reproduction as it appeared on the real device.


# Showcase

| Preview  | Preview | Preview |
| :-------------: | :-------------: | :-------------: |
|  <br>`GBA no shader`<br><img width="352" height="300" alt="raw" src="https://github.com/user-attachments/assets/66f2a88a-c17d-41d7-ac27-20a93116e2ab" /> |  <br>`GBA` (WIP - not definitive)<br><img width="352" height="300" alt="gba" src="https://github.com/user-attachments/assets/655e5971-c81c-485d-b573-ba82eb75af8e" /> |  <br>`GBA SP AGS-001` (WIP - not definitive)<br><img width="352" height="300" alt="gba_sp_ags001" src="https://github.com/user-attachments/assets/558aaee1-58d4-4cb4-882b-cc775cd24294" /> |  |
|  <br>`GBA SP AGS-101`<br><img width="352" height="300" alt="gba_sp_ags101" src="https://github.com/user-attachments/assets/00e9f902-a233-49b4-a86f-e9be5884bf22" /> |  <br>`GB Micro`<br><img width="352" height="300" alt="gb_micro" src="https://github.com/user-attachments/assets/eaa651cc-6994-4c78-ad3c-5c71d9a24e81" /> |  |

# Handhelds status report

| Nintendo Handheld  | Display Type | Display Data Collected? | Known Manufacturers | Measurements Notes |
| ------------- | :-------------: | :-------------: |  :-------------: | :------------- |
| `Game Boy` |  Reflective | 🔴 | ? | |
| `Game Boy Pocket` |  Reflective | 🔴 | ? | |
| `Game Boy Light` |  Emissive | 🔴 | ? | |
| `Game Boy Color` |  Reflective | 🕐 | ? | |
| `Game Boy Advance AGB-001` |  Reflective | 🕐 | ? | | 
| `Game Boy Advance SP AGS-001` |  Transflective<br>(frontlit on),<br>Reflective<br>(frontlit off) | 🕐 | ? | |
| `Game Boy Advance SP AGS-101` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer |
| `Game Boy Micro` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer |
| `NDS Phat` |  Emissive | 🔵⚠️ | ? | - unknown manufacturer |
| `NDS Lite` |  Emissive | 🔵⚠️ | Hitachi, Sharp ([link](https://www.wired.com/2008/02/sharp-hitachi-s)) | - unknown manufacturer<br>- greyscale gamma differs between reports (different manufacturers?) |
| `NDSi` |  Emissive | 🔴 | ? | |
| `NDSi XL` |  Emissive | 🔴 | ? |  |
| `3DS` |  Emissive | 🔵⚠️ / 🕐 | ? | - unknown manufacturer |
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
- 🔴: No data available or not yet analyzed
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

> [!NOTE]
> Some consoles have two shader variants: one with a **CLUT (Color Look-Up Table)** and one without. The CLUT variant was designed to provide better color accuracy, but this comes at the cost of fewer configuration options compared to the other variant. At the moment, this version is **NOT RECOMMENDED**, as the LUT does not actually improve color accuracy and out-of-gamut colors are simply clipped.


## Shader parameters

> [!NOTE]
> Only available in the non‑LUT shader version.

### Chromatic Adaptation

Every shader includes a `Chromatic Adaptation` option. Depending on how you set it, you will get different results:

- **OFF**: Enables “**absolute color accuracy**”, meaning colors match the console’s screen exactly (except for out-of-gamut colors). Use this setting for side-by-side comparisons between your display and the console’s screen.

- **ON**: Enables “**perceptual color accuracy**”, which models the eye’s chromatic adaptation (the brain’s way of interpreting the same colors under different illuminants). This is the default option because it:
   - Removes screen tinting by using the D65 illuminant, helping mitigate the “screen lottery” where different panels have slight color variations.
   - Reduces out-of-gamut colors, lowering Delta E.


#### Example

Chromatic adaptation on the GameBoy Micro shader (**OFF** = "blue tinted / cool temperature greyscale", **ON** = "neutral greyscale")

<img width="592" height="500" alt="chromatic adaptation" src="https://github.com/user-attachments/assets/4a452df8-e732-4c4f-9de6-2d2bd965f2a6" />

## Debug Shader parameters

> [!NOTE]
> Only available in the non‑LUT shader version.

These parameters are used to analyze the shader's output image.

### Show out of Gamut colours

Enable this option to highlight in red the colors that cannot be represented in the sRGB color space. These colors are only approximations.


# Special Thanks

- **Pokéfan531** for almost all the consoles’ screen measurements and feedback
   - GitHub: https://github.com/Pokefan531/Handheld-Colorspace-Shaders
   - Tumblr: https://pokefan531.tumblr.com/post/766008194709454848/handheld-lcd-shader-projects
- **Pica200** for the 3DS and New 3DS consoles’ measurements
- **Libretro Forum**
   - forum thread: https://forums.libretro.com/t/real-gba-and-ds-phat-colors/1540
