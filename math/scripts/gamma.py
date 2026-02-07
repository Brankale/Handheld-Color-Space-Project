import numpy as np
import colour

# XYZ tristimulus values of the display primaries at maximum intensity.
# Measured with a colorimeter at RGB = (255, 0, 0), (0, 255, 0), (0, 0, 255).
# Format: [X, Y, Z] in cd/m² (for Y) and corresponding units for X and Z.
R_XYZ = np.array([80.087959, 44.390423, 7.957929])
G_XYZ = np.array([72.80497, 129.96553, 14.341978])
B_XYZ = np.array([46.255764, 26.354113, 232.461929])

# XYZ tristimulus values for a grayscale ramp measured at equally-spaced RGB input levels.
# For N measurements: RGB = (0,0,0), (255/(N-1), 255/(N-1), 255/(N-1)), ..., (255,255,255)
# In this case: 32 measurements from RGB(0,0,0) to RGB(255,255,255) in steps of ~8.23.
# Each array represents the X, Y, or Z component for all gray levels, ordered from black to white.
GREYSCALE_X = np.array([0.332459, 0.525326, 1.008979,   1.845502,   3.073584,   4.727659,   6.905479,   9.405849,   12.336161,  15.638198,  19.357267,  23.638029,  28.204622,  33.267914,  38.959389,  44.302197,  50.796482,  57.571964,  65.053772,  72.649704,  80.116005,  89.051048,  98.057373,  106.409271, 117.024399, 127.233376, 137.666611, 148.437973, 159.034164, 171.053101, 183.953506, 197.222885])
GREYSCALE_Y = np.array([0.318527, 0.50752,  0.976888,   1.785201,   2.969783,   4.563434,   6.655342,   9.066425,   11.905767,  15.092443,  18.703249,  22.823696,  27.267467,  32.182541,  37.738117,  43.007633,  49.354424,  56.015709,  63.41972,   70.93705,   78.360176,  87.277763,  96.348503,  104.83593,  115.553864, 125.992752, 136.803848, 147.886322, 159.040695, 171.619461, 185.223755, 199.22644])
GREYSCALE_Z = np.array([0.545375, 0.889808, 1.750687,   3.25484,    5.468789,   8.45261,    12.407026,  16.908323,  22.096497,  28.032585,  34.566441,  42.247925,  50.143837,  59.017887,  68.769035,  77.548027,  88.6213,    99.647224,  111.725456, 123.83342,  135.299301, 148.874557, 161.711365, 172.312881, 187.653778, 200.614365, 211.736008, 223.64064,  232.504211, 243.095688, 252.148026, 256.539063])

PRIMARIES_XYZ = np.stack([R_XYZ, G_XYZ, B_XYZ], axis=0)
GREYSCALE_XYZ = np.stack([GREYSCALE_X, GREYSCALE_Y, GREYSCALE_Z], axis=1)
    

def compute_local_gamma_xyz(
    gray_xyz: np.ndarray,
    primaries_xyz: np.ndarray
):
    """
    Calculate the local gamma for each gray level and for each RGB channel.

    Parameters
    ----------
    gray_xyz : ndarray, shape (N, 3)
        XYZ coordinates of the grayscale, ordered from black to white.
    primaries_xyz : ndarray, shape (3, 3)
        XYZ coordinates of the RGB primaries (R, G, B).

    Returns
    -------
    gamma : ndarray, shape (N, 3)
        Local gamma for each level and each channel (R, G, B).
        The first value (black) is NaN.
    """

    gray_xyz = np.asarray(gray_xyz, dtype=float)
    primaries_xyz = np.asarray(primaries_xyz, dtype=float)

    # ---------------------------------------------------------
    # 1. Black subtraction
    # ---------------------------------------------------------
    black_xyz = gray_xyz[0]
    
    primaries_xyz -= black_xyz
    gray_xyz -= black_xyz

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


def main():
    gamma = compute_local_gamma_xyz(GREYSCALE_XYZ, PRIMARIES_XYZ)
    print(gamma)


if __name__ == "__main__":
    main()