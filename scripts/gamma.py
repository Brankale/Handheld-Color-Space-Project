import argparse
import numpy as np
import colour

from measurement_csv import read_named_xyz, read_xyz_ramp
    

def compute_local_gamma_xyz(
    gray_xyz: np.ndarray,
    primaries_xyz: np.ndarray,
    primaries_black_xyz: np.ndarray,
):
    """
    Calculate the local gamma for each gray level and for each RGB channel.

    Parameters
    ----------
    gray_xyz : ndarray, shape (N, 3)
        XYZ coordinates of the grayscale, ordered from black to white.
    primaries_xyz : ndarray, shape (3, 3)
        XYZ coordinates of the RGB primaries (R, G, B).
    primaries_black_xyz : ndarray, shape (3,)
        XYZ coordinates of black measured with the RGB primaries.

    Returns
    -------
    gamma : ndarray, shape (N, 3)
        Local gamma for each level and each channel (R, G, B).
        The first value (black) is NaN.
    """

    gray_xyz = np.array(gray_xyz, dtype=float, copy=True)
    primaries_xyz = np.array(primaries_xyz, dtype=float, copy=True)
    primaries_black_xyz = np.asarray(primaries_black_xyz, dtype=float)

    # ---------------------------------------------------------
    # 1. Black subtraction
    # ---------------------------------------------------------
    gray_black_xyz = gray_xyz[0].copy()
    
    primaries_xyz -= primaries_black_xyz
    gray_xyz -= gray_black_xyz

    # ---------------------------------------------------------
    # 2. Normalization with respect to white's Y
    # ---------------------------------------------------------
    Y_white = gray_xyz[-1, 1]
    if Y_white <= 0:
        raise ValueError("Invalid white Y")

    primaries_xyz /= Y_white
    gray_xyz /= Y_white
    
    # ---------------------------------------------------------
    # 3. XYZ → RGB matrix from primaries
    # ---------------------------------------------------------
    
    M_RGB_to_XYZ = colour.normalised_primary_matrix(
        colour.XYZ_to_xy(primaries_xyz),
        colour.XYZ_to_xy(gray_xyz[-1])
    )
    M_XYZ_to_RGB = np.linalg.inv(M_RGB_to_XYZ)

    scaling_factors = (M_XYZ_to_RGB @ gray_xyz.T).T

    # ---------------------------------------------------------
    # 4. Local gamma calculation for each channel
    # ---------------------------------------------------------
    gamma = np.full_like(scaling_factors, np.nan)

    for i in range(1, len(gray_xyz) - 1): # skip black & white
        x = i / (len(gray_xyz) - 1)
        for j in range(3):
            gamma[i, j] = np.log(scaling_factors[i, j]) / np.log(x)

    return gamma


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate local RGB gamma from XYZ measurement CSV files."
    )
    parser.add_argument(
        "--greyscale", required=True, help="Semicolon-delimited grayscale XYZ CSV"
    )
    parser.add_argument(
        "--colors", required=True, help="Semicolon-delimited WKRGBYCM XYZ CSV"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        gray_xyz = read_xyz_ramp(args.greyscale)
        if len(gray_xyz) < 3:
            raise ValueError("grayscale CSV must contain at least three measurements")
        colors = read_named_xyz(args.colors, ("K", "R", "G", "B"))
    except (OSError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error

    primaries_xyz = np.stack([colors[reading] for reading in ("R", "G", "B")])
    gamma = compute_local_gamma_xyz(gray_xyz, primaries_xyz, colors["K"])
    print(gamma)


if __name__ == "__main__":
    main()