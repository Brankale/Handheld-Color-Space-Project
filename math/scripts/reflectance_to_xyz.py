#!/usr/bin/env python3
"""
reflectance_to_xyz.py

Convert a single-column spectral reflectance file to CIE XYZ tristimulus
values using the colour-science library.

The input file must contain one reflectance value per line (0–1 range).
Lines starting with '#' are treated as comments and skipped.
--range-start, --range-end and --step define the wavelength axis.

If --illuminant is omitted, XYZ is computed for every illuminant available
in colour.SDS_ILLUMINANTS.

Examples
--------
# Single illuminant, print to stdout:
    python reflectance_to_xyz.py data.csv --range-start 380 --range-end 780 --step 5 --illuminant D65

# All illuminants, save to CSV:
    python reflectance_to_xyz.py data.csv --range-start 380 --range-end 780 --step 5 --output results.csv

# With ignored range reconstructed by spline:
    python reflectance_to_xyz.py data.csv --range-start 380 --range-end 780 --step 5 \\
        --illuminant D50 --ignore 380:400 750:780 --reconstruction-method spline
"""

import argparse
import csv
import sys
from typing import Optional

import numpy as np
import colour

# Fixed colour matching function name (always used)
CMF_NAME = "CIE 1931 2 Degree Standard Observer"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert spectral reflectance data to CIE XYZ tristimulus values.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "input_file",
        help="Path to a text/CSV file with a single column of reflectance values (0–1).",
    )
    parser.add_argument(
        "--range-start",
        type=float,
        required=True,
        metavar="NM",
        dest="range_start",
        help="Starting wavelength in nm.",
    )
    parser.add_argument(
        "--range-end",
        type=float,
        required=True,
        metavar="NM",
        dest="range_end",
        help="Ending wavelength in nm.",
    )
    parser.add_argument(
        "--step",
        type=float,
        required=True,
        metavar="NM",
        help="Wavelength step in nm.",
    )
    parser.add_argument(
        "--illuminant",
        type=str,
        default=None,
        metavar="NAME",
        help=(
            "Illuminant name (e.g. D65, D50, A, F2). "
            "If omitted, XYZ is computed for every illuminant in colour.SDS_ILLUMINANTS."
        ),
    )
    # Note: removed --cmf/--cmfs argument. CMF is fixed to CMF_NAME.
    parser.add_argument(
        "--ignore",
        nargs="+",
        metavar="START:END",
        default=None,
        help=(
            "Wavelength ranges to ignore, e.g. --ignore 380:400 750:780. "
            "Values in these ranges are filled/reconstructed according to "
            "--reconstruction-method."
        ),
    )
    parser.add_argument(
        "--reconstruction-method",
        choices=["none", "poly"],
        default="none",
        dest="reconstruction_method",
        help=(
            "How to fill ignored wavelength ranges. "
            "'none': linear interpolation between the nearest valid values. "
            "'poly': polynomial regression fitted on valid points. "
            "(default: none)"
        ),
    )
    parser.add_argument(
        "--regression-degree",
        type=int,
        default=3,
        dest="regression_degree",
        metavar="DEG",
        help="Polynomial / spline degree for reconstruction (default: 3).",
    )
    parser.add_argument(
        "--delimiter",
        type=str,
        default=None,
        metavar="CHAR",
        help="Column delimiter of the input file. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help="Output CSV file path. If omitted, results are printed to stdout.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

def _detect_delimiter(line: str) -> str:
    for delim in (",", "\t", ";"):
        if delim in line:
            return delim
    return " "


def read_reflectance(path: str, delimiter: Optional[str]) -> list:
    """
    Read a reflectance file and return a list of 1-D numpy arrays.

    Each non-comment line is parsed separately into a numpy array of floats
    (so a file with multiple data rows will produce multiple datasets). The
    delimiter is auto-detected from the first non-comment line if not
    provided.
    """
    samples = []
    with open(path, "r", encoding="utf-8") as fh:
        raw_lines = fh.readlines()

    non_comment = [ln.strip() for ln in raw_lines if ln.strip() and not ln.strip().startswith("#")]

    if not non_comment:
        raise ValueError("Input file contains no data rows.")

    delim = delimiter if delimiter is not None else _detect_delimiter(non_comment[0])

    for line in non_comment:
        if delim == " ":
            tokens = line.split()
        else:
            tokens = line.split(delim)
        floats = []
        for token in tokens:
            tok = token.strip()
            if tok:
                floats.append(float(tok))
        samples.append(np.array(floats, dtype=float))

    return samples


# ---------------------------------------------------------------------------
# Ignore-range helpers
# ---------------------------------------------------------------------------

def parse_ignore_ranges(tokens: list) -> list:
    """
    Parse ['380:400', '750:780'] → [(380.0, 400.0), (750.0, 780.0)].
    """
    ranges = []
    for token in tokens:
        parts = token.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid --ignore value '{token}'. Expected format: START:END (e.g. 380:400)."
            )
        start, end = float(parts[0]), float(parts[1])
        if start >= end:
            raise ValueError(
                f"Ignore range start ({start}) must be less than end ({end})."
            )
        ranges.append((start, end))
    return ranges


def build_valid_mask(wavelengths: np.ndarray, ignore_ranges: list) -> np.ndarray:
    """Return a boolean mask: True = wavelength is NOT in any ignored range."""
    mask = np.ones(len(wavelengths), dtype=bool)
    for start, end in ignore_ranges:
        mask &= ~((wavelengths >= start) & (wavelengths <= end))
    return mask


# ---------------------------------------------------------------------------
# Reconstruction
# ---------------------------------------------------------------------------

def reconstruct_none(
    wavelengths: np.ndarray,
    values: np.ndarray,
    valid_mask: np.ndarray,
) -> np.ndarray:
    """Linear interpolation from valid neighbours into ignored positions."""
    filled = values.copy()
    ignored_idx = np.where(~valid_mask)[0]
    filled[ignored_idx] = np.interp(
        wavelengths[ignored_idx],
        wavelengths[valid_mask],
        values[valid_mask],
    )
    return filled


def reconstruct_poly(
    wavelengths: np.ndarray,
    values: np.ndarray,
    valid_mask: np.ndarray,
    degree: int,
) -> np.ndarray:
    """Polynomial regression on valid points; predict ignored positions."""
    valid_wl = wavelengths[valid_mask]
    valid_val = values[valid_mask]

    if len(valid_wl) <= degree:
        raise ValueError(
            f"Not enough valid data points ({len(valid_wl)}) "
            f"for polynomial degree {degree}. "
            "Reduce --regression-degree or shrink the ignored range."
        )

    coeffs = np.polyfit(valid_wl, valid_val, degree)
    filled = values.copy()
    ignored_idx = np.where(~valid_mask)[0]
    filled[ignored_idx] = np.clip(np.polyval(coeffs, wavelengths[ignored_idx]), 0.0, 1.0)
    return filled


def apply_reconstruction(
    wavelengths: np.ndarray,
    values: np.ndarray,
    valid_mask: np.ndarray,
    method: str,
    degree: int,
) -> np.ndarray:
    if method == "none":
        return reconstruct_none(wavelengths, values, valid_mask)
    if method == "poly":
        return reconstruct_poly(wavelengths, values, valid_mask, degree)
    raise ValueError(f"Unknown reconstruction method: '{method}'")


# ---------------------------------------------------------------------------
# Illuminant resolution
# ---------------------------------------------------------------------------

def resolve_illuminants(name: Optional[str]) -> list:
    """
    Return a list of (name, SpectralDistribution) pairs.
    If name is None, returns all illuminants sorted by name.
    """
    if name is not None:
        if name not in colour.SDS_ILLUMINANTS:
            available = sorted(colour.SDS_ILLUMINANTS.keys())
            raise ValueError(
                f"Unknown illuminant '{name}'.\n"
                f"Available illuminants:\n  " + "\n  ".join(available)
            )
        return [(name, colour.SDS_ILLUMINANTS[name])]
    return [(k, colour.SDS_ILLUMINANTS[k]) for k in sorted(colour.SDS_ILLUMINANTS.keys())]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _header_lines(args: argparse.Namespace, ignore_ranges: list) -> list:
    lines = [
        f"Range     : {args.range_start} – {args.range_end} nm, step {args.step} nm",
        f"CMF       : {CMF_NAME}",
    ]
    if ignore_ranges:
        ranges_str = ", ".join(f"{s}–{e} nm" for s, e in ignore_ranges)
        lines.append(f"Ignored   : {ranges_str}  (reconstruction: {args.reconstruction_method})")
    return lines


def write_stdout(
    results: list,
    args: argparse.Namespace,
    ignore_ranges: list,
) -> None:
    for line in _header_lines(args, ignore_ranges):
        print(line)
    print()
    print(f"  {'Illuminant':<32s}  {'X':>12}  {'Y':>12}  {'Z':>12}")
    print("  " + "-" * 74)
    for name, xyz in results:
        print(f"  {name:<32s}  {xyz[0]:12.6f}  {xyz[1]:12.6f}  {xyz[2]:12.6f}")


def write_csv(
    results: list,
    args: argparse.Namespace,
) -> None:
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["illuminant", "X", "Y", "Z"])
        for name, xyz in results:
            writer.writerow([name, f"{xyz[0]:.6f}", f"{xyz[1]:.6f}", f"{xyz[2]:.6f}"])
    print(f"Results written to: {args.output}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    # Use fixed CMF
    cmfs = colour.MSDS_CMFS[CMF_NAME]

    # Build spectral shape and wavelength axis
    shape = colour.SpectralShape(args.range_start, args.range_end, args.step)
    wavelengths = shape.wavelengths
    expected_count = len(wavelengths)

    # Read reflectance file (may contain multiple datasets, one per line)
    try:
        samples = read_reflectance(args.input_file, args.delimiter)
    except (OSError, ValueError) as exc:
        print(f"ERROR reading input file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not samples:
        print("ERROR: No data rows found in input file.", file=sys.stderr)
        sys.exit(1)

    # Handle ignored ranges (parsed once, applied per-sample)
    ignore_ranges = []
    valid_mask = np.ones(len(wavelengths), dtype=bool)
    if args.ignore:
        try:
            ignore_ranges = parse_ignore_ranges(args.ignore)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        valid_mask = build_valid_mask(wavelengths, ignore_ranges)

        if np.all(valid_mask):
            print(
                "WARNING: --ignore ranges do not overlap with any wavelength in the data. "
                "No reconstruction will be applied.",
                file=sys.stderr,
            )
    elif args.reconstruction_method != "none":
        print(
            "WARNING: --reconstruction-method has no effect without --ignore.",
            file=sys.stderr,
        )

    # Resolve illuminants once
    try:
        illuminants = resolve_illuminants(args.illuminant)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # Process each sample line independently
    samples_results = []  # list of (sample_index, [(illuminant, xyz), ...])
    reconstructed_map = {}  # sample_index -> reconstructed reflectance array
    for i, sample_vals in enumerate(samples, start=1):
        if len(sample_vals) != expected_count:
            print(
                f"ERROR: Line {i} contains {len(sample_vals)} values, but the spectral range "
                f"{args.range_start}–{args.range_end} nm at step {args.step} nm "
                f"expects {expected_count} values. Skipping.",
                file=sys.stderr,
            )
            continue

        # Apply reconstruction if applicable
        if args.ignore and not np.all(valid_mask):
            try:
                filled = apply_reconstruction(
                    wavelengths, sample_vals, valid_mask,
                    args.reconstruction_method, args.regression_degree,
                )
                # store reconstructed full-spectrum reflectance for later printing
                reconstructed_map[i] = np.array(filled, dtype=float)
            except (ValueError, ImportError) as exc:
                print(f"ERROR during reconstruction for line {i}: {exc}", file=sys.stderr)
                continue
        else:
            filled = sample_vals.copy()

        # Build SpectralDistribution for this sample
        sd = colour.SpectralDistribution(dict(zip(wavelengths.tolist(), filled.tolist())), name=f"reflectance_{i}")

        # Compute XYZ for all requested illuminants
        results_i = []
        for ill_name, ill_sd in illuminants:
            try:
                xyz = colour.sd_to_XYZ(sd, cmfs=cmfs, illuminant=ill_sd)
                results_i.append((ill_name, xyz))
            except Exception as exc:
                print(
                    f"WARNING: Line {i}: could not compute XYZ for illuminant '{ill_name}': {exc}",
                    file=sys.stderr,
                )

        if results_i:
            samples_results.append((i, results_i))

    if not samples_results:
        print("ERROR: No XYZ values could be computed for any input line.", file=sys.stderr)
        sys.exit(1)

    # Reorder output grouped by illuminant
    # Build mapping: illuminant -> list of (sample_idx, xyz)
    illum_map = {}
    for sample_idx, results in samples_results:
        for name, xyz in results:
            illum_map.setdefault(name, []).append((sample_idx, xyz))

    illum_names = [name for (name, _) in illuminants]

    # If reconstruction was applied, print reconstructed reflectances first
    if reconstructed_map:
        print("Reconstructed reflectances (full spectrum) for samples:")
        for sample_idx in sorted(reconstructed_map.keys()):
            filled = reconstructed_map[sample_idx]
            print(f"Sample {sample_idx} (wavelength_nm, reflectance):")
            for wl, val in zip(wavelengths, filled):
                print(f"{int(wl):d}\t{val:.6f}")
            print()

    # Output to stdout grouped by illuminant
    if args.output is None:
        for line in _header_lines(args, ignore_ranges):
            print(line)
        print()
        for ill_name in illum_names:
            entries = illum_map.get(ill_name, [])
            if not entries:
                continue
            print(f"Illuminant: {ill_name}")
            print(f"  {'Sample':<8s} {'X':>12} {'Y':>12} {'Z':>12}")
            print("  " + "-" * 46)
            for sample_idx, xyz in sorted(entries, key=lambda x: x[0]):
                print(f"  {sample_idx:<8d} {xyz[0]:12.6f} {xyz[1]:12.6f} {xyz[2]:12.6f}")
            print()
    else:
        # Write CSV grouped by illuminant (rows: sample, illuminant, X, Y, Z)
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["sample", "illuminant", "X", "Y", "Z"])
            for ill_name in illum_names:
                entries = illum_map.get(ill_name, [])
                for sample_idx, xyz in sorted(entries, key=lambda x: x[0]):
                    writer.writerow([sample_idx, ill_name, f"{xyz[0]:.6f}", f"{xyz[1]:.6f}", f"{xyz[2]:.6f}"])
        print(f"Results written to: {args.output}")


if __name__ == "__main__":
    main()
