import numpy as np
import colour # https://www.colour-science.org/

# insert here measured display absolute XYZ values
HANDHELD_R_XYZ = np.array([80.087959, 44.390423, 7.957929])
HANDHELD_G_XYZ = np.array([72.80497, 129.96553, 14.341978])
HANDHELD_B_XYZ = np.array([46.255764, 26.354113, 232.46139])
HANDHELD_BLACK_XYZ = np.array([0.332459, 0.318527, 0.545375])
HANDHELD_WHITE_XYZ = np.array([197.222885, 199.22644, 256.539063])

# remove black offset
HANDHELD_R_XYZ -= HANDHELD_BLACK_XYZ
HANDHELD_G_XYZ -= HANDHELD_BLACK_XYZ
HANDHELD_B_XYZ -= HANDHELD_BLACK_XYZ
HANDHELD_WHITE_XYZ -= HANDHELD_BLACK_XYZ

# normalize to white luminance Y
HANDHELD_R_XYZ_NORMALIZED = HANDHELD_R_XYZ / HANDHELD_WHITE_XYZ[1]
HANDHELD_G_XYZ_NORMALIZED = HANDHELD_G_XYZ / HANDHELD_WHITE_XYZ[1]
HANDHELD_B_XYZ_NORMALIZED = HANDHELD_B_XYZ / HANDHELD_WHITE_XYZ[1]
HANDHELD_W_XYZ_NORMALIZED = HANDHELD_WHITE_XYZ / HANDHELD_WHITE_XYZ[1]

# CIE xyY coordinates of the destination colorspace white point
TARGET_W_CHROMATICITY = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']

if __name__ == "__main__":
    target_colourspace = colour.RGB_Colourspace(
        name = 'Reference Display',
        primaries = np.array([
            colour.XYZ_to_xy(HANDHELD_R_XYZ_NORMALIZED),
            colour.XYZ_to_xy(HANDHELD_G_XYZ_NORMALIZED),
            colour.XYZ_to_xy(HANDHELD_B_XYZ_NORMALIZED)
        ]),
        whitepoint = colour.XYZ_to_xy(HANDHELD_W_XYZ_NORMALIZED),
        cctf_encoding=None,   # useless to find the RGB->XYZ and CAT matrices
        cctf_decoding=None    # useless to find the RGB->XYZ and CAT matrices
    )

    print("RGB -> XYZ matrix:")
    print(target_colourspace.matrix_RGB_to_XYZ)

    print("---------")

    cat_mtx = colour.adaptation.matrix_chromatic_adaptation_VonKries(
        XYZ_w = HANDHELD_W_XYZ_NORMALIZED,
        XYZ_wr = colour.xy_to_XYZ(TARGET_W_CHROMATICITY),
        transform = "Bradford"
    )
    print("Chromatic Adaptation Transform Matrix (Bradford):")
    print(cat_mtx)