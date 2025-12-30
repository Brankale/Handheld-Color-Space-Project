import numpy as np
import colour

# CIE xyY coordinates of the target display for which you want to reproduce colors.
REFERENCE_R_CHROMATICITY = np.array([0.4710, 0.3098])    # R primary (x, y)
REFERENCE_G_CHROMATICITY = np.array([0.3313, 0.4792])    # G primary (x, y)
REFERENCE_B_CHROMATICITY = np.array([0.1533, 0.1491])    # B primary (x, y)
REFERENCE_W_CHROMATICITY = np.array([0.2922, 0.3053])    # W primary (x, y)

# CIE xyY coordinates of the destination colorspace white point
TARGET_W_CHROMATICITY = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']

if __name__ == "__main__":
    target_colourspace = colour.RGB_Colourspace(
        name = 'Reference Display',
        primaries = np.array([
            REFERENCE_R_CHROMATICITY,
            REFERENCE_G_CHROMATICITY,
            REFERENCE_B_CHROMATICITY
        ]),
        whitepoint = REFERENCE_W_CHROMATICITY
    )

    print("RGB -> XYZ matrix:")
    print(target_colourspace.matrix_RGB_to_XYZ)

    cat_mtx = colour.adaptation.matrix_chromatic_adaptation_VonKries(
        XYZ_w = colour.xy_to_XYZ(REFERENCE_W_CHROMATICITY),
        XYZ_wr = colour.xy_to_XYZ(TARGET_W_CHROMATICITY),
        transform = "Bradford"
    )
    print("\nChromatic Adaptation Transform Matrix (Bradford):")
    print(cat_mtx)
