
import numpy as np
import colour

# https://www.colour-science.org/

# measured display absolute XYZ values
REFERENCE_BLACK_XYZ = np.array([0.332459, 0.318527, 0.545375])
REFERENCE_R_XYZ = np.array([80.087959, 44.390423, 7.957929]) - REFERENCE_BLACK_XYZ
REFERENCE_G_XYZ = np.array([72.80497, 129.96553, 14.341978]) - REFERENCE_BLACK_XYZ
REFERENCE_B_XYZ = np.array([46.255764, 26.354113, 232.46139]) - REFERENCE_BLACK_XYZ
REFERENCE_W_XYZ = np.array([46.255764, 26.354113, 232.46139]) - REFERENCE_BLACK_XYZ

REFERENCE_W_XYZ_NORMALIZED = REFERENCE_W_XYZ / REFERENCE_W_XYZ[1]
REFERENCE_R_XYZ_NORMALIZED = REFERENCE_R_XYZ / REFERENCE_W_XYZ[1]
REFERENCE_G_XYZ_NORMALIZED = REFERENCE_G_XYZ / REFERENCE_W_XYZ[1]
REFERENCE_B_XYZ_NORMALIZED = REFERENCE_B_XYZ / REFERENCE_W_XYZ[1]

# CIE xyY coordinates of the destination colorspace white point
TARGET_W_CHROMATICITY = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']

if __name__ == "__main__":
    target_colourspace = colour.RGB_Colourspace(
        name = 'Reference Display',
        primaries = np.array([
            colour.XYZ_to_xy(REFERENCE_R_XYZ_NORMALIZED),
            colour.XYZ_to_xy(REFERENCE_G_XYZ_NORMALIZED),
            colour.XYZ_to_xy(REFERENCE_B_XYZ_NORMALIZED)
        ]),
        whitepoint = colour.XYZ_to_xy(REFERENCE_W_XYZ_NORMALIZED),
        cctf_encoding=None,   # assume linear
        cctf_decoding=None
    )
    print("RGB -> XYZ matrix:")
    rgb_to_xyz = target_colourspace.matrix_RGB_to_XYZ
    print(rgb_to_xyz)

    cat_mtx = colour.adaptation.matrix_chromatic_adaptation_VonKries(
        XYZ_w = REFERENCE_W_XYZ_NORMALIZED,
        XYZ_wr = colour.xy_to_XYZ(TARGET_W_CHROMATICITY),
        transform = "Bradford"
    )
    print("\nChromatic Adaptation Transform Matrix (Bradford):")
    print(cat_mtx)

    custom_rgb_array = np.array([1.0, 0.0, 0.0])
    srgb_array = colour.RGB_to_RGB(
        RGB=custom_rgb_array,
        input_colourspace=target_colourspace,
        output_colourspace='sRGB',
        chromatic_adaptation_transform = 'Bradford',
        apply_cctf_decoding = True,
        apply_cctf_encoding = True
    )

    print("output color")
    print(srgb_array * 255.0)