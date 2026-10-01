import argparse
from pathlib import Path
import shutil
import subprocess

import numpy as np
import colour
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from measurement_csv import read_named_xyz, read_xyz_ramp


def prepare_xyz_measurements(
    gray_xyz: np.ndarray,
    primaries_xyz: np.ndarray,
    primaries_black_xyz: np.ndarray,
):
    gray_xyz = np.array(gray_xyz, dtype=float, copy=True)
    primaries_xyz = np.array(primaries_xyz, dtype=float, copy=True)
    primaries_black_xyz = np.asarray(primaries_black_xyz, dtype=float)

    gray_black_xyz = gray_xyz[0].copy()
    gray_xyz -= gray_black_xyz
    primaries_xyz -= primaries_black_xyz

    white_y = gray_xyz[-1, 1]
    if white_y <= 0:
        raise ValueError("Invalid white Y")

    gray_xyz /= white_y
    primaries_xyz /= white_y
    return gray_xyz, primaries_xyz


def compute_rgb_scaling_factors(
    gray_xyz: np.ndarray,
    primaries_xyz: np.ndarray,
):
    rgb_to_xyz_matrix = colour.normalised_primary_matrix(
        colour.XYZ_to_xy(primaries_xyz),
        colour.XYZ_to_xy(gray_xyz[-1]),
    )
    xyz_to_rgb_matrix = np.linalg.inv(rgb_to_xyz_matrix)
    scaling_factors = (xyz_to_rgb_matrix @ gray_xyz.T).T
    return scaling_factors, rgb_to_xyz_matrix


def create_normalized_levels(number_of_measurements: int):
    return np.linspace(0.0, 1.0, number_of_measurements)


def compute_local_gamma(
    normalized_response: np.ndarray,
    normalized_levels: np.ndarray,
):
    gamma = np.full(len(normalized_response), np.nan)

    for index in range(1, len(normalized_response) - 1):
        response = normalized_response[index]
        level = normalized_levels[index]

        if not np.isfinite(response) or response <= 0:
            continue

        gamma[index] = np.log(response) / np.log(level)

    return gamma


def get_valid_gamma_points(
    normalized_levels: np.ndarray,
    gamma_values: np.ndarray,
):
    valid_levels = []
    valid_gamma_values = []

    for index in range(len(gamma_values)):
        level = normalized_levels[index]
        gamma = gamma_values[index]

        if np.isfinite(level) and np.isfinite(gamma):
            valid_levels.append(level)
            valid_gamma_values.append(gamma)

    return np.array(valid_levels), np.array(valid_gamma_values)


def fit_gamma_polynomial(
    normalized_levels: np.ndarray,
    gamma_values: np.ndarray,
    degree: int,
):
    valid_levels, valid_gamma_values = get_valid_gamma_points(
        normalized_levels,
        gamma_values,
    )

    required_points = degree + 1
    if len(valid_levels) < required_points:
        raise ValueError(
            f"polynomial degree {degree} requires at least {required_points} "
            f"valid gamma points, but only {len(valid_levels)} are available"
        )

    coefficients = np.polyfit(valid_levels, valid_gamma_values, degree)
    fitted_gamma_values = np.polyval(coefficients, valid_levels)

    residuals = valid_gamma_values - fitted_gamma_values
    squared_residuals = residuals ** 2
    rms = float(np.sqrt(np.mean(squared_residuals)))

    return coefficients, rms


def compute_grayscale_gamma_from_rgb_polynomials(
    normalized_levels: np.ndarray,
    red_coefficients: np.ndarray,
    green_coefficients: np.ndarray,
    blue_coefficients: np.ndarray,
    luminance_weights: np.ndarray,
):
    grayscale_gamma = np.full(len(normalized_levels), np.nan)

    for index in range(1, len(normalized_levels) - 1):
        level = normalized_levels[index]

        red_gamma = np.polyval(red_coefficients, level)
        green_gamma = np.polyval(green_coefficients, level)
        blue_gamma = np.polyval(blue_coefficients, level)

        red_response = level ** red_gamma
        green_response = level ** green_gamma
        blue_response = level ** blue_gamma

        grayscale_response = (
            luminance_weights[0] * red_response
            + luminance_weights[1] * green_response
            + luminance_weights[2] * blue_response
        )

        if not np.isfinite(grayscale_response) or grayscale_response <= 0:
            continue

        grayscale_gamma[index] = np.log(grayscale_response) / np.log(level)

    return grayscale_gamma


def compute_fitted_grayscale_xyz(
    normalized_levels: np.ndarray,
    red_coefficients: np.ndarray,
    green_coefficients: np.ndarray,
    blue_coefficients: np.ndarray,
    rgb_to_xyz_matrix: np.ndarray,
):
    fitted_rgb = np.zeros((len(normalized_levels), 3))

    for index in range(len(normalized_levels)):
        level = normalized_levels[index]

        if level == 0:
            continue

        if level == 1:
            fitted_rgb[index] = np.ones(3)
            continue

        red_gamma = np.polyval(red_coefficients, level)
        green_gamma = np.polyval(green_coefficients, level)
        blue_gamma = np.polyval(blue_coefficients, level)

        fitted_rgb[index, 0] = level ** red_gamma
        fitted_rgb[index, 1] = level ** green_gamma
        fitted_rgb[index, 2] = level ** blue_gamma

    fitted_xyz = (rgb_to_xyz_matrix @ fitted_rgb.T).T
    return fitted_xyz


def compute_cam16ucs_delta_e(
    measured_xyz: np.ndarray,
    fitted_xyz: np.ndarray,
    white_xyz: np.ndarray,
):
    measured_cam16ucs = colour.XYZ_to_CAM16UCS(
        measured_xyz,
        XYZ_w=white_xyz,
    )
    fitted_cam16ucs = colour.XYZ_to_CAM16UCS(
        fitted_xyz,
        XYZ_w=white_xyz,
    )
    delta_e = colour.delta_E(
        measured_cam16ucs,
        fitted_cam16ucs,
        method="CAM16-UCS",
    )
    delta_e = np.asarray(delta_e, dtype=float)

    if not np.all(np.isfinite(delta_e)):
        raise ValueError("CAM16-UCS Delta E contains non-finite values")

    return delta_e


def compute_rms(reference_values: np.ndarray, calculated_values: np.ndarray):
    squared_residuals = []

    for index in range(len(reference_values)):
        reference_value = reference_values[index]
        calculated_value = calculated_values[index]

        if not np.isfinite(reference_value):
            continue
        if not np.isfinite(calculated_value):
            continue

        residual = reference_value - calculated_value
        squared_residuals.append(residual ** 2)

    if len(squared_residuals) == 0:
        raise ValueError("no valid points are available for RMS calculation")

    return float(np.sqrt(np.mean(squared_residuals)))


def print_fit_result(
    curve_name: str,
    coefficients: np.ndarray,
    rms: float,
):
    coefficients_text = np.array2string(
        coefficients,
        precision=8,
        separator=", ",
    )
    print(f"{curve_name} polynomial coefficients: {coefficients_text}")
    print(f"{curve_name} RMS: {rms:.8f}")


def print_delta_e_results(
    normalized_levels: np.ndarray,
    delta_e: np.ndarray,
):
    print("CAM16-UCS Delta E, measured grayscale vs fitted grayscale:")

    for index in range(len(delta_e)):
        level = normalized_levels[index]
        print(f"  level {level:.6f}: {delta_e[index]:.6f}")

    mean_delta_e = float(np.mean(delta_e))
    rms_delta_e = float(np.sqrt(np.mean(delta_e ** 2)))
    maximum_index = int(np.argmax(delta_e))
    maximum_delta_e = delta_e[maximum_index]
    maximum_level = normalized_levels[maximum_index]

    print(f"CAM16-UCS Delta E mean: {mean_delta_e:.6f}")
    print(f"CAM16-UCS Delta E RMS: {rms_delta_e:.6f}")
    print(
        f"CAM16-UCS Delta E maximum: {maximum_delta_e:.6f} "
        f"at level {maximum_level:.6f}"
    )


def plot_calculated_grayscale(
    axis,
    normalized_levels: np.ndarray,
    measured_gamma: np.ndarray,
    calculated_gamma: np.ndarray,
    rms: float,
):
    measured_levels, measured_values = get_valid_gamma_points(
        normalized_levels,
        measured_gamma,
    )
    calculated_levels, calculated_values = get_valid_gamma_points(
        normalized_levels,
        calculated_gamma,
    )

    axis.scatter(
        measured_levels,
        measured_values,
        color="dimgray",
        s=24,
        label="Gray measured",
    )
    axis.plot(
        calculated_levels,
        calculated_values,
        color="black",
        linewidth=2,
        label=f"Gray calculated from RGB fits (RMS={rms:.5f})",
    )


def plot_single_gamma_curve(
    axis,
    normalized_levels: np.ndarray,
    gamma_values: np.ndarray,
    coefficients: np.ndarray,
    rms: float,
    curve_name: str,
    color: str,
):
    valid_levels, valid_gamma_values = get_valid_gamma_points(
        normalized_levels,
        gamma_values,
    )

    first_level = valid_levels[0]
    last_level = valid_levels[-1]
    smooth_levels = np.linspace(first_level, last_level, 300)
    smooth_gamma_values = np.polyval(coefficients, smooth_levels)

    axis.scatter(
        valid_levels,
        valid_gamma_values,
        color=color,
        s=24,
        label=f"{curve_name} measured",
    )
    axis.plot(
        smooth_levels,
        smooth_gamma_values,
        color=color,
        linewidth=2,
        label=f"{curve_name} fit (RMS={rms:.5f})",
    )


def save_gamma_graph(figure: Figure, output_path: str):
    absolute_output_path = Path(output_path).expanduser().resolve()
    output_directory = absolute_output_path.parent

    if not output_directory.is_dir():
        raise ValueError(
            f"graph output directory does not exist: {output_directory}"
        )

    canvas = FigureCanvasAgg(figure)
    canvas.print_png(str(absolute_output_path))

    if not absolute_output_path.is_file():
        raise OSError(f"graph file was not created: {absolute_output_path}")

    file_size = absolute_output_path.stat().st_size
    if file_size == 0:
        raise OSError(f"graph file is empty: {absolute_output_path}")

    print(f"Graph saved to: {absolute_output_path} ({file_size} bytes)")
    return absolute_output_path


def open_saved_graph(image_path: Path):
    image_opener = shutil.which("xdg-open")

    if image_opener is None:
        print("Open the saved PNG to view the graph.")
        return

    subprocess.Popen(
        [image_opener, str(image_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def plot_gamma_results(
    normalized_levels: np.ndarray,
    measured_gray_gamma: np.ndarray,
    calculated_gray_gamma: np.ndarray,
    rgb_gamma: np.ndarray,
    red_coefficients: np.ndarray,
    green_coefficients: np.ndarray,
    blue_coefficients: np.ndarray,
    gray_rms: float,
    red_rms: float,
    green_rms: float,
    blue_rms: float,
    delta_e: np.ndarray,
    degree: int,
    output_path: str,
):
    figure = Figure(figsize=(11, 9))
    gamma_axis = figure.add_subplot(2, 1, 1)
    delta_e_axis = figure.add_subplot(2, 1, 2)

    plot_calculated_grayscale(
        gamma_axis,
        normalized_levels,
        measured_gray_gamma,
        calculated_gray_gamma,
        gray_rms,
    )
    plot_single_gamma_curve(
        gamma_axis,
        normalized_levels,
        rgb_gamma[:, 0],
        red_coefficients,
        red_rms,
        "Red",
        "red",
    )
    plot_single_gamma_curve(
        gamma_axis,
        normalized_levels,
        rgb_gamma[:, 1],
        green_coefficients,
        green_rms,
        "Green",
        "green",
    )
    plot_single_gamma_curve(
        gamma_axis,
        normalized_levels,
        rgb_gamma[:, 2],
        blue_coefficients,
        blue_rms,
        "Blue",
        "blue",
    )

    gamma_axis.set_title(
        f"RGB polynomial fits and calculated grayscale gamma (degree {degree})"
    )
    gamma_axis.set_xlabel("Normalized input level")
    gamma_axis.set_ylabel("Local gamma")
    gamma_axis.grid(True, alpha=0.3)
    gamma_axis.legend()

    delta_e_axis.plot(
        normalized_levels,
        delta_e,
        color="black",
        marker="o",
        linewidth=1.5,
    )
    delta_e_axis.set_title("Measured vs fitted grayscale - CAM16-UCS Delta E")
    delta_e_axis.set_xlabel("Normalized input level")
    delta_e_axis.set_ylabel("Delta E")
    delta_e_axis.grid(True, alpha=0.3)
    figure.tight_layout()

    saved_image_path = save_gamma_graph(figure, output_path)
    open_saved_graph(saved_image_path)

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
    primaries_xyz: np.ndarray,
    primaries_black_xyz: np.ndarray,
):
    """
    Calculate the local gamma for each gray level and for each RGB channel.
    Calculate the local gamma for grayscale and each RGB channel.

    Parameters
    ----------
@ -33,63 +461,188 @@ def compute_local_gamma_xyz(
        XYZ coordinates of the grayscale, ordered from black to white.
    primaries_xyz : ndarray, shape (3, 3)
        XYZ coordinates of the RGB primaries (R, G, B).
    primaries_black_xyz : ndarray, shape (3,)
        XYZ coordinates of black measured with the RGB primaries.

    Returns
    -------
    gamma : ndarray, shape (N, 3)
    normalized_levels : ndarray, shape (N,)
        Input levels normalized between zero and one.
    gray_gamma : ndarray, shape (N,)
        Local gamma calculated from normalized Y luminance.
    rgb_gamma : ndarray, shape (N, 3)
        Local gamma for each level and each channel (R, G, B).
        The first value (black) is NaN.
        Black and white values are NaN because gamma is undefined there.
    luminance_weights : ndarray, shape (3,)
        Relative Y contributions of the R, G and B primaries.
    normalized_gray_xyz : ndarray, shape (N, 3)
        Black-subtracted grayscale XYZ values normalized to white Y.
    rgb_to_xyz_matrix : ndarray, shape (3, 3)
        Matrix used to reconstruct fitted grayscale XYZ values.
    """
    normalized_gray_xyz, normalized_primaries_xyz = prepare_xyz_measurements(
        gray_xyz,
        primaries_xyz,
        primaries_black_xyz,
    )
    scaling_factors, rgb_to_xyz_matrix = compute_rgb_scaling_factors(
        normalized_gray_xyz,
        normalized_primaries_xyz,
    )
    luminance_weights = rgb_to_xyz_matrix[1].copy()
    luminance_weight_sum = np.sum(luminance_weights)

    if not np.isfinite(luminance_weight_sum) or luminance_weight_sum <= 0:
        raise ValueError("invalid RGB luminance weights")
    luminance_weights /= luminance_weight_sum
    normalized_levels = create_normalized_levels(len(normalized_gray_xyz))

    gray_gamma = compute_local_gamma(
        normalized_gray_xyz[:, 1],
        normalized_levels,
    )
    rgb_gamma = np.column_stack(
        [
            compute_local_gamma(scaling_factors[:, channel_index], normalized_levels)
            for channel_index in range(3)
        ]
    )
    return (
        normalized_levels,
        gray_gamma,
        rgb_gamma,
        luminance_weights,
        normalized_gray_xyz,
        rgb_to_xyz_matrix,
    )


def non_negative_integer(value: str):
    try:
        integer_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error

    if integer_value < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")

    return integer_value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate local grayscale and RGB gamma from XYZ measurement CSV files."
    )
    parser.add_argument(
        "--greyscale", required=True, help="Semicolon-delimited grayscale XYZ CSV"
    )
    parser.add_argument(
        "--colors", required=True, help="Semicolon-delimited WKRGBYCM XYZ CSV"
    )
    parser.add_argument(
        "--degree",
        type=non_negative_integer,
        default=3,
        help="Degree of the polynomial approximation (default: 3)",
    )
    parser.add_argument(
        "--output",
        default="gamma_plot.png",
        help="Path of the graph PNG file (default: gamma_plot.png)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        gray_xyz = read_xyz_ramp(args.greyscale)
        if len(gray_xyz) < 3:
            raise ValueError("grayscale CSV must contain at least three measurements")
        colors = read_named_xyz(args.colors, ("K", "R", "G", "B"))

        primaries_xyz = np.stack(
            [colors["R"], colors["G"], colors["B"]]
        )
        (
            normalized_levels,
            gray_gamma,
            rgb_gamma,
            luminance_weights,
            normalized_gray_xyz,
            rgb_to_xyz_matrix,
        ) = compute_local_gamma_xyz(
            gray_xyz,
            primaries_xyz,
            colors["K"],
        )

        red_coefficients, red_rms = fit_gamma_polynomial(
            normalized_levels,
            rgb_gamma[:, 0],
            args.degree,
        )
        green_coefficients, green_rms = fit_gamma_polynomial(
            normalized_levels,
            rgb_gamma[:, 1],
            args.degree,
        )
        blue_coefficients, blue_rms = fit_gamma_polynomial(
            normalized_levels,
            rgb_gamma[:, 2],
            args.degree,
        )
        calculated_gray_gamma = compute_grayscale_gamma_from_rgb_polynomials(
            normalized_levels,
            red_coefficients,
            green_coefficients,
            blue_coefficients,
            luminance_weights,
        )
        gray_rms = compute_rms(gray_gamma, calculated_gray_gamma)
        fitted_gray_xyz = compute_fitted_grayscale_xyz(
            normalized_levels,
            red_coefficients,
            green_coefficients,
            blue_coefficients,
            rgb_to_xyz_matrix,
        )
        delta_e = compute_cam16ucs_delta_e(
            normalized_gray_xyz,
            fitted_gray_xyz,
            normalized_gray_xyz[-1],
        )
    except (OSError, ValueError, np.linalg.LinAlgError) as error:
        raise SystemExit(f"error: {error}") from error

    print(f"Gray RMS calculated from RGB polynomials: {gray_rms:.8f}")
    print_fit_result("Red", red_coefficients, red_rms)
    print_fit_result("Green", green_coefficients, green_rms)
    print_fit_result("Blue", blue_coefficients, blue_rms)
    print_delta_e_results(normalized_levels, delta_e)

    try:
        plot_gamma_results(
            normalized_levels,
            gray_gamma,
            calculated_gray_gamma,
            rgb_gamma,
            red_coefficients,
            green_coefficients,
            blue_coefficients,
            gray_rms,
            red_rms,
            green_rms,
            blue_rms,
            delta_e,
            args.degree,
            args.output,
        )
    except (OSError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()