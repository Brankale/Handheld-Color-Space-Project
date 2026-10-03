import argparse
import numpy as np
import colour # https://www.colour-science.org/

from measurement_csv import read_named_xyz

# CIE xyY coordinates of the destination colorspace white point
TARGET_W_CHROMATICITY = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']

def get_cat_bradford(handheld_white_normalized_xyz):
    return colour.adaptation.matrix_chromatic_adaptation_VonKries(
        XYZ_w = handheld_white_normalized_xyz,
        XYZ_wr = colour.xy_to_XYZ(TARGET_W_CHROMATICITY),
        transform = "Bradford"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate display conversion matrices from XYZ measurements."
    )
    parser.add_argument(
        "--colors", required=True, help="Semicolon-delimited WKRGBYCM XYZ CSV"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        colors = read_named_xyz(args.colors, ("W", "K", "R", "G", "B"))
    except (OSError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error

    black_xyz_raw = colors["K"]
    white_xyz_raw = colors["W"]
    white_luminance = white_xyz_raw[1] - black_xyz_raw[1]
    if white_luminance <= 0:
        raise SystemExit("error: white luminance must be greater than black luminance")

    normalized = {
        reading: (colors[reading] - black_xyz_raw) / white_luminance
        for reading in ("R", "G", "B", "W")
    }

    target_colourspace = colour.RGB_Colourspace(
        name = 'Reference Display',
        primaries = np.array([
            colour.XYZ_to_xy(normalized["R"]),
            colour.XYZ_to_xy(normalized["G"]),
            colour.XYZ_to_xy(normalized["B"])
        ]),
        whitepoint = colour.XYZ_to_xy(normalized["W"]),
        cctf_encoding=None,   # useless to find the RGB->XYZ and CAT matrices
        cctf_decoding=None    # useless to find the RGB->XYZ and CAT matrices
    )

    print("RGB -> XYZ matrix:")
    print(target_colourspace.matrix_RGB_to_XYZ)

    print("---------")

    print("Chromatic Adaptation Transform Matrix (Bradford):")
    print(get_cat_bradford(normalized["W"]))

    print("---------")

    print("Chromatic Adaptation Transform Matrix (Bradford) + black artifacts:")
    print(get_cat_bradford(white_xyz_raw / white_xyz_raw[1]))


if __name__ == "__main__":
    main()