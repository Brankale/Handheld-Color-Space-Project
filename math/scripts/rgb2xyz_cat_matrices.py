import numpy as np
import colour # https://www.colour-science.org/

# insert here measured display absolute XYZ values
HANDHELD_R_XYZ_RAW = np.array([80.087959, 44.390423, 7.957929])
HANDHELD_G_XYZ_RAW = np.array([72.80497, 129.96553, 14.341978])
HANDHELD_B_XYZ_RAW = np.array([46.255764, 26.354113, 232.46139])
HANDHELD_BLACK_XYZ_RAW = np.array([0.332459, 0.318527, 0.545375])
HANDHELD_WHITE_XYZ_RAW = np.array([197.222885, 199.22644, 256.539063])

# remove black artifact + normalize to white luminance Y
Y = HANDHELD_WHITE_XYZ_RAW[1] - HANDHELD_BLACK_XYZ_RAW[1]
HANDHELD_R_XYZ_NORMALIZED = (HANDHELD_R_XYZ_RAW - HANDHELD_BLACK_XYZ_RAW) / Y
HANDHELD_G_XYZ_NORMALIZED = (HANDHELD_G_XYZ_RAW - HANDHELD_BLACK_XYZ_RAW) / Y
HANDHELD_B_XYZ_NORMALIZED = (HANDHELD_B_XYZ_RAW - HANDHELD_BLACK_XYZ_RAW) / Y
HANDHELD_W_XYZ_NORMALIZED = (HANDHELD_WHITE_XYZ_RAW - HANDHELD_BLACK_XYZ_RAW) / Y

# CIE xyY coordinates of the destination colorspace white point
TARGET_W_CHROMATICITY = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']

def get_cat_bradford(handheld_white_normalized_xyz):
    return colour.adaptation.matrix_chromatic_adaptation_VonKries(
        XYZ_w = handheld_white_normalized_xyz,
        XYZ_wr = colour.xy_to_XYZ(TARGET_W_CHROMATICITY),
        transform = "Bradford"
    )

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

    print("Chromatic Adaptation Transform Matrix (Bradford):")
    print(get_cat_bradford(HANDHELD_W_XYZ_NORMALIZED))

    print("---------")

    print("Chromatic Adaptation Transform Matrix (Bradford) + black artifacts:")
    print(get_cat_bradford(HANDHELD_WHITE_XYZ_RAW / HANDHELD_WHITE_XYZ_RAW[1]))