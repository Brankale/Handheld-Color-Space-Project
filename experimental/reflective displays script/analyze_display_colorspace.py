"""

analyze_display_colorspace.py

=============================================================================

Reflective handheld display colorspace analysis tool.

Reads spectral reflectance measurements for the R, G, B, Y, C, M and Gray
ramps of a display, then computes:

  1. The EOTF (gamma) polynomial for each primary channel (R, G, B).
  2. The linear RGB -> XYZ conversion matrix derived from the primary
     chromaticities at maximum drive level.
  3. A luminance-scaling coefficient k for each secondary colour (Yellow,
     Cyan, Magenta, Gray) that minimises the mean CAM16-UCS delta-E across
     the full ramp.

All computation is performed with the colour-science library.

Results are printed to stdout and written to a CSV file.

Usage example:

    python analyze_display_colorspace.py \
        --red    red.csv   --green  green.csv  --blue   blue.csv \
        --yellow yellow.csv --cyan  cyan.csv   --magenta magenta.csv \
        --gray   gray.csv  \
        --illuminant D50   --max-degree 3 \
        --output-dir ./results

CSV format expected:

    Row 0  : wavelength values [nm], separated by the file's delimiter
    Rows 1-32 : spectral reflectance of each patch (patch 0 = black at row 1,
                patch 31 = maximum drive at row 32)

"""

import argparse
import csv
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import colour

# ---------------------------------------------------------------------------

# Constants

# ---------------------------------------------------------------------------

OBSERVER = "CIE 1931 2 Degree Standard Observer"

SECONDARIES = ["cyan", "magenta", "yellow", "gray"]

# Pairs of primary channel indices (0=R,1=G,2=B) that are active for each

# secondary colour.  Gray uses all three.

SECONDARY_ACTIVE_CHANNELS = {
    "yellow":  (0, 1),
    "cyan":    (1, 2),
    "magenta": (0, 2),
    "gray":    (0, 1, 2),
}

# ---------------------------------------------------------------------------

# Step 1 - CSV Parsing

# ---------------------------------------------------------------------------

def clamp_reflectance(refl: np.ndarray) -> np.ndarray:
    """Clamp reflectance values to the physically valid range [0, 1]."""
    return np.clip(refl, 0.0, 1.0)


def load_csv(filepath: str) -> tuple[np.ndarray, np.ndarray]:

    """Load a reflectance CSV file.
    Returns
    -------
    wavelengths : ndarray, shape (N,)
        Wavelength values in nm.
    reflectances : ndarray, shape (32, N)
        Spectral reflectance for each of the 32 patches.
        Row 0 corresponds to the darkest (black) patch.
    """
    import csv as _csv
    from io import StringIO

    text = open(filepath, "r", encoding="utf-8", errors="replace").read()

    def _parse_cell(s: str) -> float:
        # csv.reader already strips surrounding quotes; just swap decimal comma.
        return float(s.strip().replace(",", "."))

    def _parse_csv(sep: str):
        reader = _csv.reader(StringIO(text), delimiter=sep)
        rows = [row for row in reader if any(c.strip() for c in row)]
        if len(rows) < 33:
            return None
        try:
            wavelength = np.array([_parse_cell(c) for c in rows[0]])
            reflectance = np.array([[_parse_cell(c) for c in row] for row in rows[1:33]])
            if reflectance.shape[0] == 32 and reflectance.shape[1] > 1:
                return wavelength, reflectance
        except (ValueError, IndexError):
            return None
        return None

    for sep in [",", ";", "\t"]:
        result = _parse_csv(sep)
        if result is not None:
            return result

    raise ValueError(
        f"{filepath}: could not parse CSV. Tried column separators ',', ';', '\\t'. "
        "Check that the file has exactly 33 rows (1 wavelength header + 32 patches)."
    )


def apply_wavelength_clip(
    wavelengths: np.ndarray,
    reflectances: np.ndarray,
    wl_min: float | None,
    wl_max: float | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Restrict wavelengths and reflectances to the reliable spectral window.

    If both wl_min and wl_max are None the data is returned unchanged.

    Parameters
    ----------
    wl_min : float or None
        Lower bound (nm), inclusive.  None means no lower clipping.
    wl_max : float or None
        Upper bound (nm), inclusive.  None means no upper clipping.
    """
    if wl_min is None and wl_max is None:
        return wavelengths, reflectances

    mask = np.ones(len(wavelengths), dtype=bool)
    if wl_min is not None:
        mask &= wavelengths >= wl_min
    if wl_max is not None:
        mask &= wavelengths <= wl_max

    if not np.any(mask):
        raise ValueError(
            f"Wavelength clip [{wl_min}, {wl_max}] nm excludes all "
            f"{len(wavelengths)} samples "
            f"({wavelengths[0]:.0f}-{wavelengths[-1]:.0f} nm)."
        )

    return wavelengths[mask], reflectances[:, mask]


# ---------------------------------------------------------------------------

# Step 2 - Reflectance -> XYZ

# ---------------------------------------------------------------------------

def reflectances_to_XYZ(
    wavelengths: np.ndarray,
    reflectances: np.ndarray,
    illuminant_sd: colour.SpectralDistribution,
    cmfs: colour.MultiSpectralDistributions,
) -> np.ndarray:
    
    xyz = np.zeros((reflectances.shape[0], 3))
    for i, row in enumerate(reflectances):
        sd = colour.SpectralDistribution(row, wavelengths, interpolator=colour.SpragueInterpolator)
        xyz[i] = colour.sd_to_XYZ(sd, cmfs=cmfs, illuminant=illuminant_sd)
    return xyz

# ---------------------------------------------------------------------------

# Step 4 - Polynomial Gamma Fitting

# ---------------------------------------------------------------------------

def fit_gamma(
    xyz_corrected: np.ndarray,
    max_degree: int,
    channel_name: str,
) -> tuple[np.ndarray, int, float]:

    """Fit a polynomial gamma-exponent EOTF for one primary channel.

    The polynomial approximates γ(x) such that x^γ(x) ≈ linear_light(x),
    where x is the normalised drive level [0..1]. Coefficients are suitable
    for shader use as pow(drive, gamma_poly(drive)).

    Parameters
    ----------
    xyz_corrected : ndarray, shape (32, 3)
        Black-corrected XYZ values for the primary ramp.
    max_degree : int
        Maximum polynomial degree to try.
    Returns
    -------
    coeffs : ndarray
        Polynomial coefficients (lowest degree first) for γ(x).
    best_degree : int
        Degree selected (lowest RMSE <= max_degree).
    rmse : float
        Root-mean-square error of the gamma-exponent fit.
    """
    x = np.linspace(0.0, 1.0, 32)          # normalised drive level [0..1]
    y_raw = xyz_corrected[:, 1]             # Y (luminance) channel
    y_max = y_raw[-1]
    if y_max <= 0.0:
        raise ValueError(
            f"Primary '{channel_name}': maximum Y value is zero or negative "
            "after black subtraction - check the input CSV."
        )
    y_norm = y_raw / y_max                  # normalised luminance [0..1]

    # γ(x) = log(y_norm) / log(x)  so that x^γ ≈ y_norm
    # Exclude endpoints (log(0) undefined, x=1 → 0/0) and y_norm<=0
    mask = (x > 1e-6) & (x < 1.0 - 1e-6) & (y_norm > 1e-6)
    gamma_vals = np.log(y_norm[mask]) / np.log(x[mask])

    best_degree = 1
    best_coeffs = None
    best_rmse = np.inf
    for deg in range(1, max_degree + 1):
        coeffs = np.polynomial.polynomial.polyfit(x[mask], gamma_vals, deg)
        gamma_pred = np.polynomial.polynomial.polyval(x[mask], coeffs)
        rmse = float(np.sqrt(np.mean((gamma_vals - gamma_pred) ** 2)))
        if rmse < best_rmse:
            best_rmse = rmse
            best_degree = deg
            best_coeffs = coeffs

    return best_coeffs, best_degree, best_rmse

def polyval_gamma(coeffs: np.ndarray, t: float) -> float:
    """Evaluate t^gamma_poly(t), clamped to [0, 1].

    Returns 0 for t<=0, 1 for t>=1, otherwise pow(t, gamma(t)).
    """
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    gamma = float(np.polynomial.polynomial.polyval(t, coeffs))
    gamma = max(0.01, gamma)   # guard against zero/negative exponent
    return float(t ** gamma)

# ---------------------------------------------------------------------------
# Step 6 - Secondary Luminance Scaling (binary search)
# ---------------------------------------------------------------------------
# CAM16-UCS delta-E via colour-science
# ---------------------------------------------------------------------------

def _cam16ucs_per_patch(
    xyz_pred_abs: np.ndarray,  # (N, 3) absolute XYZ for predicted colour
    xyz_meas_abs: np.ndarray,  # (N, 3) absolute XYZ for measured colour
    XYZ_w: np.ndarray,
    L_A: float,
    Y_b: float,
) -> np.ndarray:
    """Compute CAM16-UCS delta-E for each row of two absolute-XYZ arrays.

    Pipeline: XYZ -> CAM16 -> JMh -> CAM16UCS -> delta_E_CAM16UCS.
    Returns ndarray of shape (N,).
    """
    surround  = colour.VIEWING_CONDITIONS_CAM16["Average"]
    spec_pred = colour.XYZ_to_CAM16(xyz_pred_abs, XYZ_w, L_A, Y_b,
                                     surround=surround, compute_H=False)
    spec_meas = colour.XYZ_to_CAM16(xyz_meas_abs, XYZ_w, L_A, Y_b,
                                     surround=surround, compute_H=False)
    Jab_pred = colour.JMh_CAM16_to_CAM16UCS(
        np.stack([spec_pred.J, spec_pred.M, spec_pred.h], axis=-1)
    )
    Jab_meas = colour.JMh_CAM16_to_CAM16UCS(
        np.stack([spec_meas.J, spec_meas.M, spec_meas.h], axis=-1)
    )
    return colour.difference.delta_E_CAM16UCS(Jab_pred, Jab_meas)


def _mean_delta_e_cam16(
    k: float,
    xyz_estimated_corrected: np.ndarray,  # (N, 3), black-corrected estimated XYZ
    xyz_measured_corrected: np.ndarray,   # (N, 3), black-corrected measured XYZ
    xyz_black: np.ndarray,                # (3,)
    XYZ_w: np.ndarray,                    # (3,) illuminant white, Y=100 scale
    L_A: float,
    Y_b: float,
) -> tuple[float, float]:
    """Return (mean, std) CAM16-UCS delta-E across all patches."""
    xyz_pred = np.clip(k * xyz_estimated_corrected + xyz_black, 1e-6, None)
    xyz_meas = np.clip(xyz_measured_corrected + xyz_black, 1e-6, None)
    de = _cam16ucs_per_patch(xyz_pred, xyz_meas, XYZ_w, L_A, Y_b)
    return float(np.mean(de)), float(np.std(de, ddof=0))


def find_k_coefficient(
    secondary_name: str,
    active_channels: tuple,
    poly_coeffs: list,           # [poly_R, poly_G, poly_B]
    matrix_M: np.ndarray,        # 3x3 RGB lin -> XYZ
    xyz_corrected_secondary: np.ndarray,  # (32, 3) black-corrected measured XYZ
    xyz_black: np.ndarray,
    XYZ_w: np.ndarray,
    L_A: float,
    Y_b: float,
    tol: float = 1e-4,
) -> tuple[float, float, float]:
    """Find the luminance scaling coefficient k for one secondary colour using
    a golden-section search that minimises the mean CAM16-UCS delta-E.

    The comparison is made against the raw measured XYZ values (no smoothing).

    Parameters
    ----------
    active_channels : tuple of int
        Indices of the R/G/B channels that are active for this secondary.
    Returns
    -------
    k_optimal : float
    mean_delta_e : float
    std_delta_e : float
    """
    n_patches = 31  # patches 1..31 (exclude patch 0 = black)
    x_values = np.arange(1, 32) / 31.0  # normalised drive levels
    # Build RGB linear ramps for patches 1..31
    rgb_lin = np.zeros((n_patches, 3))
    for idx in active_channels:
        for j, t in enumerate(x_values):
            rgb_lin[j, idx] = polyval_gamma(poly_coeffs[idx], t)
    # Estimated XYZ (black-corrected) from the matrix
    xyz_estimated = (matrix_M @ rgb_lin.T).T  # (31, 3)
    # Raw measured XYZ (black-corrected), patches 1..31
    xyz_measured = xyz_corrected_secondary[1:]  # (31, 3)
    # Compute k range from luminance ratios (Y channel = index 1)
    y_est = xyz_estimated[:, 1]
    y_meas = xyz_measured[:, 1]
    valid = y_est > 1e-6
    k_ratios = y_meas[valid] / y_est[valid]
    k_min = float(np.min(k_ratios))
    k_max = float(np.max(k_ratios))
    print(f"    [{secondary_name}] k search range: [{k_min:.4f}, {k_max:.4f}]")
    # Binary search: we minimise a unimodal objective by bisecting the interval.
    # The delta-E as a function of k is approximately convex (bowl-shaped), so
    # we use a golden-section search within the range.
    def objective(k):
        mean, _ = _mean_delta_e_cam16(
            k, xyz_estimated, xyz_measured, xyz_black, XYZ_w, L_A, Y_b
        )
        return mean
    # Golden-section search
    gr = (np.sqrt(5.0) + 1.0) / 2.0
    a, b = k_min, k_max
    c = b - (b - a) / gr
    d = a + (b - a) / gr
    while abs(b - a) > tol:
        if objective(c) < objective(d):
            b = d
        else:
            a = c
        c = b - (b - a) / gr
        d = a + (b - a) / gr

    k_optimal = (a + b) / 2.0
    mean_de, std_de = _mean_delta_e_cam16(
        k_optimal, xyz_estimated, xyz_measured, xyz_black, XYZ_w, L_A, Y_b
    )
    return k_optimal, mean_de, std_de


def compute_secondary_plot_data(
    active_channels: tuple,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_corrected_secondary: np.ndarray,  # (32, 3) black-corrected
    xyz_black: np.ndarray,
    XYZ_w: np.ndarray,
    L_A: float,
    Y_b: float,
    k: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-patch luminance and CAM16-UCS delta-E for one secondary colour.

    Returns
    -------
    patches      : ndarray (31,)  patch indices 1..31
    y_measured   : ndarray (31,)  absolute measured Y
    y_estimated  : ndarray (31,)  k-scaled estimated Y
    de_per_patch : ndarray (31,)  CAM16-UCS delta-E per patch
    """
    n_patches = 31
    x_values  = np.arange(1, 32) / 31.0

    rgb_lin = np.zeros((n_patches, 3))
    for idx in active_channels:
        for j, t in enumerate(x_values):
            rgb_lin[j, idx] = polyval_gamma(poly_coeffs[idx], t)

    xyz_estimated_corr = (matrix_M @ rgb_lin.T).T    # (31, 3)
    xyz_measured_corr  = xyz_corrected_secondary[1:]  # (31, 3)

    xyz_pred = np.clip(k * xyz_estimated_corr + xyz_black, 1e-6, None)
    xyz_meas = np.clip(xyz_measured_corr     + xyz_black, 1e-6, None)

    de_per_patch = _cam16ucs_per_patch(xyz_pred, xyz_meas, XYZ_w, L_A, Y_b)
    return np.arange(1, 32), xyz_meas[:, 1], xyz_pred[:, 1], de_per_patch

# ---------------------------------------------------------------------------

# Output helpers

# ---------------------------------------------------------------------------

def print_matrix(matrix: np.ndarray, label: str):
    """Pretty-print a 3×3 matrix in row-major order (each row = one primary)."""
    print(f"\n  {label} [row-major; shader use: XYZ = rgb · M]:")
    row_labels = ["R", "G", "B"]
    for i, row in enumerate(matrix.T):
        print(f"    {row_labels[i]}:  [{row[0]:>12.9f},  {row[1]:>12.9f},  {row[2]:>12.9f}]")

def save_results_csv(
    output_path: str,
    illuminant: str,
    xyz_black_global: np.ndarray,
    xyz_blacks_per_file: dict,
    gamma_results: dict,          # {channel: (coeffs, degree, rmse)}
    matrix_M: np.ndarray,
    secondary_results: dict,      # {name: (k, mean_de)}
    Y_white: float,
):

    """Write all computed results to a CSV file."""
    rows = []
    # Metadata
    rows.append(["# Reflective Display Colorspace Analysis"])
    rows.append(["illuminant", illuminant])
    rows.append(["observer", OBSERVER])
    rows.append([])
    # Black points
    rows.append(["# Black point XYZ (per file)"])
    rows.append(["file", "X", "Y", "Z"])
    for name, xyz in xyz_blacks_per_file.items():
        rows.append([name, f"{xyz[0]:.6f}", f"{xyz[1]:.6f}", f"{xyz[2]:.6f}"])
    rows.append(["global_minimum",
                 f"{xyz_black_global[0]:.6f}",
                 f"{xyz_black_global[1]:.6f}",
                 f"{xyz_black_global[2]:.6f}"])
    rows.append([])
    # White point luminance
    rows.append(["# White point luminance"])
    rows.append(["# Y_white = Y_gray_max (black-corrected) + Y_global_black"])
    rows.append(["Y_white", f"{Y_white:.6f}"])
    rows.append([])
    # Gamma
    rows.append(["# Gamma polynomials (EOTF: gamma-exponent poly, shader use: pow(drive, gamma_poly(drive)))"])
    rows.append(["channel", "degree", "rmse", "coefficients (c0, c1, ...)"])
    for ch in ["R", "G", "B"]:
        coeffs, deg, rmse = gamma_results[ch]
        rows.append([ch, str(deg), f"{rmse:.8f}"] + [f"{c:.10f}" for c in coeffs])
    rows.append([])
    # RGB -> XYZ matrix
    rows.append(["# RGB linear -> XYZ matrix, normalised"])
    rows.append(["# row-major: each row is one primary; shader use: XYZ = rgb · M"])
    rows.append(["", "X", "Y", "Z"])
    for i, ch in enumerate(["R", "G", "B"]):
        col = matrix_M[:, i]
        rows.append([ch, f"{col[0]:.9f}", f"{col[1]:.9f}", f"{col[2]:.9f}"])
    rows.append([])
    # Secondary coefficients
    rows.append(["# Secondary luminance scaling coefficients"])
    rows.append(["secondary", "k", "mean_delta_e_cam16", "std_delta_e_cam16"])
    for name, (k, de, std) in secondary_results.items():
        rows.append([name, f"{k:.6f}", f"{de:.4f}", f"{std:.4f}"])

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# ---------------------------------------------------------------------------

# Pipeline steps (called from main)

# ---------------------------------------------------------------------------

def load_all_csv(
    csv_paths: dict,
    wl_min: float | None = None,
    wl_max: float | None = None,
) -> dict:
    """Load every colour channel CSV, clamp reflectances to [0, 1] and
    verify that all files share the same wavelength axis.

    Parameters
    ----------
    wl_min, wl_max : float or None
        Optional wavelength clipping bounds (nm, inclusive).
        If both are None the full measured range is used.

    Returns
    -------
    data : dict  name -> (wavelengths, reflectances)
    """
    data = {}
    for name, path in csv_paths.items():
        wavelengths, reflectances = load_csv(path)
        reflectances = clamp_reflectance(reflectances)
        wavelengths, reflectances = apply_wavelength_clip(
            wavelengths, reflectances, wl_min, wl_max
        )
        data[name] = (wavelengths, reflectances)
        print(f"  Loaded '{name}': {reflectances.shape[0]} patches, "
              f"{len(wavelengths)} wavelength samples "
              f"({wavelengths[0]:.0f}-{wavelengths[-1]:.0f} nm)")

    wl_ref = data["red"][0]
    for name, (wl, _) in data.items():
        if not np.allclose(wl, wl_ref):
            raise ValueError(
                f"Wavelength axis of '{name}' differs from 'red'. "
                "All CSV files must share the same wavelength sampling."
            )
    return data


def compute_all_xyz(data: dict, illuminant_name: str) -> dict:
    """Convert every reflectance ramp to XYZ tristimulus values.

    Returns
    -------
    xyz_raw : dict  name -> ndarray shape (32, 3)
    """
    try:
        illuminant_sd = colour.SDS_ILLUMINANTS[illuminant_name]
    except KeyError:
        print(f"ERROR: Unknown illuminant '{illuminant_name}'.")
        print(f"       Available: {list(colour.SDS_ILLUMINANTS.keys())}")
        sys.exit(1)

    xyz_raw = {}
    for name, (wl, refl) in data.items():
        xyz_raw[name] = reflectances_to_XYZ(wl, refl, illuminant_sd, colour.MSDS_CMFS[OBSERVER])
    return xyz_raw


def subtract_black(
    xyz_raw: dict,
    csv_paths: dict,
) -> tuple[dict, dict, np.ndarray]:
    """Subtract each channel's own black (patch 0) from its ramp.

    The global minimum black is the patch-0 XYZ whose Y luminance is lowest
    across all files; it is returned as the absolute-XYZ reference for
    downstream calculations (e.g. CAM16 viewing conditions).

    Returns
    -------
    xyz_corrected    : dict  name -> ndarray (32, 3)  ramp minus its own black
    xyz_blacks       : dict  name -> ndarray (3,)
    xyz_black_global : ndarray (3,)  patch-0 with the lowest Y luminance
    """
    xyz_blacks = {name: xyz_raw[name][0] for name in csv_paths}

    # Global minimum: the black patch with the lowest Y luminance
    min_Y_name = min(xyz_blacks, key=lambda n: xyz_blacks[n][1])
    xyz_black_global = xyz_blacks[min_Y_name]

    print("\n  Black point XYZ per file (patch 0):")
    print(f"  {'File':<12} {'X':>10} {'Y':>10} {'Z':>10}")
    print(f"  {'-'*44}")
    for name, xyz in xyz_blacks.items():
        marker = "  <- global min (lowest Y)" if name == min_Y_name else ""
        print(f"  {name:<12} {xyz[0]:>10.4f} {xyz[1]:>10.4f} {xyz[2]:>10.4f}{marker}")

    # Each ramp is corrected by subtracting its own black
    xyz_corrected = {name: xyz_raw[name] - xyz_blacks[name] for name in csv_paths}
    return xyz_corrected, xyz_blacks, xyz_black_global


def fit_all_primaries(
    xyz_corrected: dict,
    max_degree: int,
) -> tuple[dict, list]:
    """Fit gamma polynomials for the R, G, B primary channels.

    Returns
    -------
    gamma_results : dict  channel -> (coeffs, degree, rmse)
    poly_coeffs   : list  [poly_R, poly_G, poly_B]
    """
    primary_map = {"R": "red", "G": "green", "B": "blue"}
    gamma_results = {}
    poly_coeffs = [None, None, None]

    for ch, color_name in primary_map.items():
        coeffs, degree, rmse = fit_gamma(xyz_corrected[color_name], max_degree, ch)
        gamma_results[ch] = (coeffs, degree, rmse)
        poly_coeffs[["R", "G", "B"].index(ch)] = coeffs
        print(f"  {ch}: degree={degree},  RMSE={rmse:.8f}")
        coeff_str = ", ".join(f"{c:.6f}" for c in coeffs)
        print(f"     coefficients (c0..c{degree}): [{coeff_str}]")

    return gamma_results, poly_coeffs


def compute_primary_matrix(xyz_corrected: dict) -> np.ndarray:
    """Build the 3x3 RGB-linear -> XYZ matrix from primary XYZ at full drive.

    Returns
    -------
    matrix_M : ndarray (3, 3)  columns are XYZ of R, G, B at maximum drive.
    """
    xyz_R_max = xyz_corrected["red"][31]
    xyz_G_max = xyz_corrected["green"][31]
    xyz_B_max = xyz_corrected["blue"][31]
    return np.column_stack([xyz_R_max, xyz_G_max, xyz_B_max])


def optimise_all_secondaries(
    xyz_corrected: dict,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_blacks: dict,
    illuminant_name: str,
) -> dict:
    """Optimise the luminance scaling coefficient k for every secondary colour.

    Each secondary's own black (patch 0) is used to reconstruct absolute XYZ
    before the CAM16 comparison, which is the physically correct reference.

    Returns
    -------
    secondary_results : dict  name -> (k, mean_de, std_de)
    """
    xy_illuminant = colour.CCS_ILLUMINANTS[OBSERVER][illuminant_name]
    XYZ_w = colour.xy_to_XYZ(xy_illuminant) * 100.0
    Y_display_max = float(xyz_corrected["gray"][31, 1]) + float(xyz_blacks["gray"][1])
    L_A = Y_display_max / 5.0
    Y_b = 20.0

    print(f"  Viewing conditions: L_A={L_A:.2f}, Y_b={Y_b:.1f}")
    print(f"  Illuminant XYZ_w (Y=100 scale): "
          f"X={XYZ_w[0]:.4f}  Y={XYZ_w[1]:.4f}  Z={XYZ_w[2]:.4f}")

    secondary_results = {}
    for sec_name in SECONDARIES:
        active = SECONDARY_ACTIVE_CHANNELS[sec_name]
        active_labels = [["R", "G", "B"][i] for i in active]
        print(f"\n  Optimising k for '{sec_name}' (active channels: {active_labels})...")
        k_opt, mean_de, std_de = find_k_coefficient(
            sec_name, active, poly_coeffs, matrix_M,
            xyz_corrected[sec_name], xyz_blacks[sec_name], XYZ_w, L_A, Y_b,
        )
        secondary_results[sec_name] = (k_opt, mean_de, std_de)
        print(f"    -> k = {k_opt:.6f},  mean DeltaE CAM16-UCS = {mean_de:.4f}  (std = {std_de:.4f})")

    return secondary_results


def print_summary(
    illuminant: str,
    xyz_black: np.ndarray,
    gamma_results: dict,
    matrix_M: np.ndarray,
    secondary_results: dict,
    Y_white: float,
) -> None:
    """Print the results summary to stdout."""
    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Illuminant : {illuminant}   Observer: {OBSERVER}")
    print(f"\n  Global minimum black point (lowest Y, used as absolute reference):")
    print(f"    X={xyz_black[0]:.6f}  Y={xyz_black[1]:.6f}  Z={xyz_black[2]:.6f}")
    print(f"\n  White point luminance Y (gray corrected + global black):")
    print(f"    Y_white = {Y_white:.6f}")
    print(f"\n  Gamma polynomials (EOTF: drive level [0,1] -> normalised luminance):")
    for ch in ["R", "G", "B"]:
        coeffs, deg, rmse = gamma_results[ch]
        coeff_str = ", ".join(f"{c:.8f}" for c in coeffs)
        print(f"    {ch}: degree {deg}, RMSE={rmse:.8f},  coeffs=[{coeff_str}]")
    print_matrix(matrix_M, "RGB linear -> XYZ matrix (normalised)")
    print(f"\n  Secondary luminance scaling coefficients k:")
    print(f"  {'Secondary':<12} {'k':>10} {'mean DeltaE':>13} {'std DeltaE':>12}")
    print(f"  {'-'*50}")
    for name, (k, de, std) in secondary_results.items():
        flag = "  [!] outside expected range (0.85-1.0)" if not (0.75 <= k <= 1.05) else ""
        print(f"  {name:<12} {k:>10.6f} {de:>13.4f} {std:>12.4f}{flag}")


def compute_primary_plot_data(
    channel_idx: int,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_corrected_primary: np.ndarray,  # (32, 3) black-corrected
    xyz_black_primary: np.ndarray,
    XYZ_w: np.ndarray,
    L_A: float,
    Y_b: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-patch luminance and CAM16-UCS delta-E for one primary channel.

    Returns
    -------
    patches      : ndarray (31,)  patch indices 1..31
    y_measured   : ndarray (31,)  absolute measured Y
    y_estimated  : ndarray (31,)  estimated Y from gamma polynomial + matrix
    de_per_patch : ndarray (31,)  CAM16-UCS delta-E per patch
    """
    n_patches = 31
    x_values  = np.arange(1, 32) / 31.0

    rgb_lin = np.zeros((n_patches, 3))
    for j, t in enumerate(x_values):
        rgb_lin[j, channel_idx] = polyval_gamma(poly_coeffs[channel_idx], t)

    xyz_estimated_corr = (matrix_M @ rgb_lin.T).T    # (31, 3)
    xyz_measured_corr  = xyz_corrected_primary[1:]    # (31, 3)

    xyz_pred = np.clip(xyz_estimated_corr + xyz_black_primary, 1e-6, None)
    xyz_meas = np.clip(xyz_measured_corr  + xyz_black_primary, 1e-6, None)

    de_per_patch = _cam16ucs_per_patch(xyz_pred, xyz_meas, XYZ_w, L_A, Y_b)
    return np.arange(1, 32), xyz_meas[:, 1], xyz_pred[:, 1], de_per_patch


def compute_primary_gamma_data(
    channel_idx: int,
    poly_coeffs: list,
    xyz_corrected_primary: np.ndarray,  # (32, 3) black-corrected
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-patch measured and polynomial-estimated gamma for one primary.

    Returns
    -------
    patch_indices : ndarray  indices into the 32-patch ramp (approx 1..30)
    gamma_meas    : ndarray  measured instantaneous gamma at each patch
    gamma_est     : ndarray  polynomial-estimated gamma at each patch
    """
    x_all = np.linspace(0.0, 1.0, 32)
    y_raw = xyz_corrected_primary[:, 1]
    y_max = y_raw[-1]
    if y_max <= 0.0:
        return np.array([]), np.array([]), np.array([])
    y_norm = y_raw / y_max

    mask = (x_all > 1e-6) & (x_all < 1.0 - 1e-6) & (y_norm > 1e-6)
    x_m = x_all[mask]
    gamma_meas = np.log(y_norm[mask]) / np.log(x_m)
    gamma_est  = np.polynomial.polynomial.polyval(x_m, poly_coeffs[channel_idx])

    return np.where(mask)[0], gamma_meas, gamma_est


def plot_primaries(
    gamma_results: dict,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_corrected: dict,
    xyz_blacks: dict,
    illuminant_name: str,
    output_dir: str,
) -> plt.Figure:
    """Return a 2×2 figure: luminance + ΔE for R, G, B primaries (4th cell empty)."""
    xy_illuminant = colour.CCS_ILLUMINANTS[OBSERVER][illuminant_name]
    XYZ_w         = colour.xy_to_XYZ(xy_illuminant) * 100.0
    Y_display_max = float(xyz_corrected["gray"][31, 1]) + float(xyz_blacks["gray"][1])
    L_A           = Y_display_max / 5.0
    Y_b           = 20.0

    primary_map = [
        ("R", "red",   0, "#880000", "#ff6666"),
        ("G", "green", 1, "#006600", "#66cc66"),
        ("B", "blue",  2, "#000088", "#6666ff"),
    ]
    de_color = "#cc3300"

    fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
    fig.suptitle(
        "Primary channels — measured vs estimated luminance and ΔE (CAM16-UCS)",
        fontsize=13,
    )

    for ax, (ch, color_name, ch_idx, dark, light) in zip(axes.flat, primary_map):
        _, deg, rmse = gamma_results[ch]

        patches, y_meas, y_est, de = compute_primary_plot_data(
            ch_idx, poly_coeffs, matrix_M,
            xyz_corrected[color_name], xyz_blacks[color_name],
            XYZ_w, L_A, Y_b,
        )
        mean_de = float(np.mean(de))
        std_de  = float(np.std(de, ddof=0))

        ln1 = ax.plot(patches, y_meas, color=dark,  marker="o", ms=4, lw=1.5,
                      label="Y measured")
        ln2 = ax.plot(patches, y_est,  color=light, marker="s", ms=4, lw=1.5,
                      linestyle="--", label="Y estimated")
        ax.set_xlabel("Patch index")
        ax.set_ylabel("Luminance Y (absolute)")
        ax.set_title(
            f"{ch} (degree {deg}, RMSE={rmse:.6f})   "
            f"mean ΔE={mean_de:.3f}   std={std_de:.3f}"
        )

        ax2 = ax.twinx()
        ln3  = ax2.plot(patches, de, color=de_color, marker="^", ms=4, lw=1.2,
                        linestyle=":", label="ΔE CAM16-UCS")
        ax2.set_ylabel("ΔE CAM16-UCS", color=de_color)
        ax2.tick_params(axis="y", labelcolor=de_color)

        lines  = ln1 + ln2 + ln3
        labels = [line.get_label() for line in lines]
        ax.legend(lines, labels, fontsize=8, loc="upper left")

    axes.flat[3].set_visible(False)
    fig.tight_layout()
    return fig


def plot_primary_gamma(
    gamma_results: dict,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_corrected: dict,
    xyz_blacks: dict,
    illuminant_name: str,
    output_dir: str,
) -> plt.Figure:
    """Return a 2×2 figure: gamma + ΔE for R, G, B primaries (4th cell empty)."""
    xy_illuminant = colour.CCS_ILLUMINANTS[OBSERVER][illuminant_name]
    XYZ_w         = colour.xy_to_XYZ(xy_illuminant) * 100.0
    Y_display_max = float(xyz_corrected["gray"][31, 1]) + float(xyz_blacks["gray"][1])
    L_A           = Y_display_max / 5.0
    Y_b           = 20.0

    primary_map = [
        ("R", "red",   0, "#880000", "#ff6666"),
        ("G", "green", 1, "#006600", "#66cc66"),
        ("B", "blue",  2, "#000088", "#6666ff"),
    ]
    de_color = "#cc3300"

    fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
    fig.suptitle(
        "Primary channels — measured vs estimated gamma and ΔE (CAM16-UCS)",
        fontsize=13,
    )

    for ax, (ch, color_name, ch_idx, dark, light) in zip(axes.flat, primary_map):
        _, deg, rmse = gamma_results[ch]

        patch_idx, gamma_meas, gamma_est = compute_primary_gamma_data(
            ch_idx, poly_coeffs, xyz_corrected[color_name],
        )
        _, _, _, de = compute_primary_plot_data(
            ch_idx, poly_coeffs, matrix_M,
            xyz_corrected[color_name], xyz_blacks[color_name],
            XYZ_w, L_A, Y_b,
        )
        mean_de = float(np.mean(de))
        std_de  = float(np.std(de, ddof=0))

        ln1 = ax.plot(patch_idx, gamma_meas, color=dark,  marker="o", ms=4, lw=1.5,
                      label="γ measured")
        ln2 = ax.plot(patch_idx, gamma_est,  color=light, marker="s", ms=4, lw=1.5,
                      linestyle="--", label="γ estimated (poly)")
        ax.set_xlabel("Patch index")
        ax.set_ylabel("Gamma γ")
        ax.set_title(
            f"{ch} — gamma (degree {deg})   "
            f"mean ΔE={mean_de:.3f}   std={std_de:.3f}"
        )

        ax2 = ax.twinx()
        patches = np.arange(1, 32)
        ln3  = ax2.plot(patches, de, color=de_color, marker="^", ms=4, lw=1.2,
                        linestyle=":", label="ΔE CAM16-UCS")
        ax2.set_ylabel("ΔE CAM16-UCS", color=de_color)
        ax2.tick_params(axis="y", labelcolor=de_color)

        lines  = ln1 + ln2 + ln3
        labels = [line.get_label() for line in lines]
        ax.legend(lines, labels, fontsize=8, loc="upper right")

    axes.flat[3].set_visible(False)
    fig.tight_layout()
    return fig


def plot_secondaries(
    secondary_results: dict,
    xyz_corrected: dict,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_blacks: dict,
    illuminant_name: str,
    output_dir: str,
) -> plt.Figure:
    """Return a 2×2 figure: measured/estimated luminance and ΔE (CAM16-UCS)
    for yellow, cyan, magenta and gray.
    """
    xy_illuminant = colour.CCS_ILLUMINANTS[OBSERVER][illuminant_name]
    XYZ_w         = colour.xy_to_XYZ(xy_illuminant) * 100.0
    Y_display_max = float(xyz_corrected["gray"][31, 1]) + float(xyz_blacks["gray"][1])
    L_A           = Y_display_max / 5.0
    Y_b           = 20.0

    plot_colors = {
        "yellow":  ("#aa8800", "#ffcc00"),
        "cyan":    ("#006688", "#00bbdd"),
        "magenta": ("#880066", "#dd00bb"),
        "gray":    ("#333333", "#888888"),
    }
    de_color = "#cc3300"

    fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
    fig.suptitle(
        "Secondary colours — measured vs estimated luminance and ΔE (CAM16-UCS)",
        fontsize=13,
    )

    for ax, sec_name in zip(axes.flat, SECONDARIES):
        k, mean_de, std_de = secondary_results[sec_name]
        active      = SECONDARY_ACTIVE_CHANNELS[sec_name]
        dark, light = plot_colors[sec_name]

        patches, y_meas, y_est, de = compute_secondary_plot_data(
            active, poly_coeffs, matrix_M,
            xyz_corrected[sec_name], xyz_blacks[sec_name],
            XYZ_w, L_A, Y_b, k,
        )

        ln1 = ax.plot(patches, y_meas, color=dark,  marker="o", ms=4, lw=1.5,
                      label="Y measured")
        ln2 = ax.plot(patches, y_est,  color=light, marker="s", ms=4, lw=1.5,
                      linestyle="--", label="Y estimated (k-scaled)")
        ax.set_xlabel("Patch index")
        ax.set_ylabel("Luminance Y (absolute)")
        ax.set_title(
            f"{sec_name.capitalize()}   k={k:.4f}   "
            f"mean ΔE={mean_de:.3f}   std={std_de:.3f}"
        )

        ax2 = ax.twinx()
        ln3  = ax2.plot(patches, de, color=de_color, marker="^", ms=4, lw=1.2,
                        linestyle=":", label="ΔE CAM16-UCS")
        ax2.set_ylabel("ΔE CAM16-UCS", color=de_color)
        ax2.tick_params(axis="y", labelcolor=de_color)

        lines  = ln1 + ln2 + ln3
        labels = [line.get_label() for line in lines]
        ax.legend(lines, labels, fontsize=8, loc="upper left")

    fig.tight_layout()
    return fig


def compute_secondary_gamma_data(
    active_channels: tuple,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_corrected_secondary: np.ndarray,  # (32, 3) black-corrected
    xyz_black_secondary: np.ndarray,      # (3,)
    XYZ_w: np.ndarray,
    L_A: float,
    Y_b: float,
    k: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-patch measured and estimated gamma + ΔE for one secondary colour.

    Returns
    -------
    patch_indices : ndarray  1-based patch indices (approx 1..30)
    gamma_meas    : ndarray  measured instantaneous gamma
    gamma_est     : ndarray  k-scaled estimated gamma
    de_per_patch  : ndarray  CAM16-UCS delta-E for patches 1..31
    """
    n_patches = 31
    x_values  = np.arange(1, 32) / 31.0

    rgb_lin = np.zeros((n_patches, 3))
    for idx in active_channels:
        for j, t in enumerate(x_values):
            rgb_lin[j, idx] = polyval_gamma(poly_coeffs[idx], t)

    xyz_estimated_corr = (matrix_M @ rgb_lin.T).T    # (31, 3)
    xyz_measured_corr  = xyz_corrected_secondary[1:]  # (31, 3)

    xyz_pred = np.clip(k * xyz_estimated_corr + xyz_black_secondary, 1e-6, None)
    xyz_meas = np.clip(xyz_measured_corr       + xyz_black_secondary, 1e-6, None)

    de_per_patch = _cam16ucs_per_patch(xyz_pred, xyz_meas, XYZ_w, L_A, Y_b)

    y_meas = xyz_meas[:, 1]
    y_est  = xyz_pred[:, 1]
    y_meas_norm = y_meas / max(float(y_meas[-1]), 1e-9)
    y_est_norm  = y_est  / max(float(y_est[-1]),  1e-9)

    mask = (
        (x_values > 1e-6) & (x_values < 1.0 - 1e-6)
        & (y_meas_norm > 1e-6) & (y_est_norm > 1e-6)
    )
    x_m        = x_values[mask]
    gamma_meas = np.log(y_meas_norm[mask]) / np.log(x_m)
    gamma_est  = np.log(y_est_norm[mask])  / np.log(x_m)

    return np.arange(1, 32)[mask], gamma_meas, gamma_est, de_per_patch


def plot_secondary_gamma(
    secondary_results: dict,
    xyz_corrected: dict,
    poly_coeffs: list,
    matrix_M: np.ndarray,
    xyz_blacks: dict,
    illuminant_name: str,
    output_dir: str,
) -> plt.Figure:
    """Return a 2×2 figure: gamma + ΔE (CAM16-UCS) for yellow, cyan, magenta, gray."""
    xy_illuminant = colour.CCS_ILLUMINANTS[OBSERVER][illuminant_name]
    XYZ_w         = colour.xy_to_XYZ(xy_illuminant) * 100.0
    Y_display_max = float(xyz_corrected["gray"][31, 1]) + float(xyz_blacks["gray"][1])
    L_A           = Y_display_max / 5.0
    Y_b           = 20.0

    plot_colors = {
        "yellow":  ("#aa8800", "#ffcc00"),
        "cyan":    ("#006688", "#00bbdd"),
        "magenta": ("#880066", "#dd00bb"),
        "gray":    ("#333333", "#888888"),
    }
    de_color = "#cc3300"

    fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
    fig.suptitle(
        "Secondary colours — measured vs estimated gamma and ΔE (CAM16-UCS)",
        fontsize=13,
    )

    for ax, sec_name in zip(axes.flat, SECONDARIES):
        k, mean_de, std_de = secondary_results[sec_name]
        active      = SECONDARY_ACTIVE_CHANNELS[sec_name]
        dark, light = plot_colors[sec_name]

        patch_idx, gamma_meas, gamma_est, de = compute_secondary_gamma_data(
            active, poly_coeffs, matrix_M,
            xyz_corrected[sec_name], xyz_blacks[sec_name],
            XYZ_w, L_A, Y_b, k,
        )
        patches_de = np.arange(1, 32)

        ln1 = ax.plot(patch_idx, gamma_meas, color=dark,  marker="o", ms=4, lw=1.5,
                      label="γ measured")
        ln2 = ax.plot(patch_idx, gamma_est,  color=light, marker="s", ms=4, lw=1.5,
                      linestyle="--", label="γ estimated (k-scaled)")
        ax.set_xlabel("Patch index")
        ax.set_ylabel("Gamma γ")
        ax.set_title(
            f"{sec_name.capitalize()} — gamma   k={k:.4f}   "
            f"mean ΔE={mean_de:.3f}   std={std_de:.3f}"
        )

        ax2 = ax.twinx()
        ln3  = ax2.plot(patches_de, de, color=de_color, marker="^", ms=4, lw=1.2,
                        linestyle=":", label="ΔE CAM16-UCS")
        ax2.set_ylabel("ΔE CAM16-UCS", color=de_color)
        ax2.tick_params(axis="y", labelcolor=de_color)

        lines  = ln1 + ln2 + ln3
        labels = [line.get_label() for line in lines]
        ax.legend(lines, labels, fontsize=8, loc="upper right")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------

# Main

# ---------------------------------------------------------------------------

def run_for_illuminant(
    illuminant: str,
    console: str,
    csv_paths: dict,
    data: dict,
    output_dir: str,
    max_degree: int,
) -> None:
    """Run steps 2-6 of the pipeline for a single illuminant and save outputs."""
    output_prefix = f"{console}_illuminant_{illuminant}"

    print("=" * 70)
    print(f"  Illuminant : {illuminant}   Console: {console}")
    print("=" * 70)

    print("\n[Step 2/6] Converting reflectances to XYZ "
          f"(illuminant={illuminant}, {OBSERVER})...")
    xyz_raw = compute_all_xyz(data, illuminant)

    print("\n[Step 3/6] Subtracting black point and reporting black levels...")
    xyz_corrected, xyz_blacks, xyz_black = subtract_black(xyz_raw, csv_paths)

    print(f"\n[Step 4/6] Fitting gamma polynomials (max degree {max_degree})...")
    gamma_results, poly_coeffs = fit_all_primaries(xyz_corrected, max_degree)

    print("\n[Step 5/6] Computing RGB linear -> XYZ matrix from primaries...")
    matrix_M = compute_primary_matrix(xyz_corrected)

    print("\n[Step 6/6] Optimising secondary luminance scaling coefficients "
          "(binary/golden-section search, metric: CAM16-UCS delta-E)...")
    secondary_results = optimise_all_secondaries(
        xyz_corrected, poly_coeffs, matrix_M, xyz_blacks, illuminant
    )

    k_gray = secondary_results["gray"][0]
    Y_R = xyz_corrected["red"][31, 1]
    Y_G = xyz_corrected["green"][31, 1]
    Y_B = xyz_corrected["blue"][31, 1]
    Y_norm = (Y_R + Y_G + Y_B) * k_gray
    matrix_M_norm = matrix_M / Y_norm
    print(f"\n  Matrix normalised by Y_max = "
          f"(Y_R={Y_R:.4f} + Y_G={Y_G:.4f} + Y_B={Y_B:.4f}) × k_gray={k_gray:.6f} "
          f"= {Y_norm:.6f}")

    Y_white = float(xyz_corrected["gray"][31, 1]) + float(xyz_black[1])
    print(f"\n  White point luminance: Y_white = {Y_white:.6f} "
          f"(Y_gray_corrected={float(xyz_corrected['gray'][31,1]):.6f} "
          f"+ Y_black_global={float(xyz_black[1]):.6f})")

    print_summary(illuminant, xyz_black, gamma_results, matrix_M_norm, secondary_results, Y_white)

    fig_prim_lum = plot_primaries(
        gamma_results, poly_coeffs, matrix_M,
        xyz_corrected, xyz_blacks, illuminant, output_dir,
    )
    fig_prim_gamma = plot_primary_gamma(
        gamma_results, poly_coeffs, matrix_M,
        xyz_corrected, xyz_blacks, illuminant, output_dir,
    )
    fig_sec_lum = plot_secondaries(
        secondary_results, xyz_corrected, poly_coeffs,
        matrix_M, xyz_blacks, illuminant, output_dir,
    )
    fig_sec_gamma = plot_secondary_gamma(
        secondary_results, xyz_corrected, poly_coeffs,
        matrix_M, xyz_blacks, illuminant, output_dir,
    )

    pdf_path = os.path.join(output_dir, f"{output_prefix}_deltaE.pdf")
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(fig_prim_lum)
        pdf.savefig(fig_prim_gamma)
        pdf.savefig(fig_sec_lum)
        pdf.savefig(fig_sec_gamma)
    for fig in [fig_prim_lum, fig_prim_gamma, fig_sec_lum, fig_sec_gamma]:
        plt.close(fig)
    print(f"  PDF saved to: {pdf_path}")

    output_csv_path = os.path.join(output_dir, f"{output_prefix}_params.csv")
    print(f"\n  Saving results to: {output_csv_path}")
    save_results_csv(
        output_csv_path,
        illuminant,
        xyz_black,
        xyz_blacks,
        gamma_results,
        matrix_M_norm,
        secondary_results,
        Y_white,
    )
    print("  Done.")
    print("=" * 70)


def main():

    parser = argparse.ArgumentParser(
        description="Reflective handheld display colorspace analysis tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--console-name", required=True, help="Name of the device/display under test. Used as prefix for output files.")
    parser.add_argument("--red",      required=True, help="CSV file for Red ramp")
    parser.add_argument("--green",    required=True, help="CSV file for Green ramp")
    parser.add_argument("--blue",     required=True, help="CSV file for Blue ramp")
    parser.add_argument("--yellow",   required=True, help="CSV file for Yellow ramp")
    parser.add_argument("--cyan",     required=True, help="CSV file for Cyan ramp")
    parser.add_argument("--magenta",  required=True, help="CSV file for Magenta ramp")
    parser.add_argument("--gray",     required=True, help="CSV file for Gray ramp")
    parser.add_argument(
        "--illuminant", default=None,
        help="CIE illuminant name as recognised by colour-science (e.g. D50, D65, A). "
             "If omitted, all available illuminants are processed.",
    )
    parser.add_argument(
        "--max-degree", type=int, default=3,
        help="Maximum polynomial degree for gamma fitting (best degree <= this is chosen).",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory for output files.  Defaults to the directory of --red.",
    )
    parser.add_argument(
        "--wl-min", type=float, default=None,
        help="Lower wavelength bound for clipping (nm, inclusive). "
             "Omit to use the full measured range.",
    )
    parser.add_argument(
        "--wl-max", type=float, default=None,
        help="Upper wavelength bound for clipping (nm, inclusive). "
             "Omit to use the full measured range.",
    )
    args = parser.parse_args()

    if args.output_dir is None:
        output_dir = str(Path(args.red).parent)
    else:
        output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    csv_paths = {
        "red":     args.red,
        "green":   args.green,
        "blue":    args.blue,
        "yellow":  args.yellow,
        "cyan":    args.cyan,
        "magenta": args.magenta,
        "gray":    args.gray,
    }

    illuminants = (
        [args.illuminant]
        if args.illuminant is not None
        else list(colour.SDS_ILLUMINANTS.keys())
    )

    print("=" * 70)
    print("  Reflective Display Colorspace Analysis")
    print("=" * 70)
    print(f"  Console    : {args.console_name}")
    print(f"  Observer   : {OBSERVER}")
    print(f"  Max poly degree: {args.max_degree}")
    if args.wl_min is not None or args.wl_max is not None:
        lo = f"{args.wl_min:.0f} nm" if args.wl_min is not None else "(full)"
        hi = f"{args.wl_max:.0f} nm" if args.wl_max is not None else "(full)"
        print(f"  Wavelength clip: [{lo}, {hi}]")
    print(f"  Illuminants to process ({len(illuminants)}): {', '.join(illuminants)}")
    print()

    print("[Step 1/6] Loading CSV files...")
    data = load_all_csv(csv_paths, wl_min=args.wl_min, wl_max=args.wl_max)

    for illuminant in illuminants:
        try:
            run_for_illuminant(
                illuminant, args.console_name, csv_paths, data, output_dir, args.max_degree,
            )
        except Exception as exc:
            print(f"\n  [WARNING] Skipping illuminant '{illuminant}': {exc}")
            print("=" * 70)


if __name__ == "__main__":

    main()
