from functools import cache
from itertools import combinations
from pathlib import Path

import colour
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "handhelds" / "Nintendo GBC" / "[2026-11-09][Pokefan531]" / "measurements"
REPEAT_DATA = DATA.parents[1] / "[2026-05-13][Pokefan531]" / "measurements"
REPEAT_FILES = ("gbc-gamma1 2026-05-09.txt", "gbc-gamma2 2026-05-09.txt")
IMG = HERE.parent / "img"

ORIENTATIONS = {"top": "0°", "middle": "90°", "bottom": "180°"}
RAMPS = ("White", "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta")
RAMP_COLOURS = {
    "White": "0.45", "Red": "tab:red", "Green": "tab:green", "Blue": "tab:blue",
    "Yellow": "goldenrod", "Cyan": "tab:cyan", "Magenta": "tab:pink",
}
FULL = 31
BASELINE_END = 420.0
CLEAN_END = 423.333
UNSTABLE_START = 700.0
CUTOFF = 440.0

CMFS = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
D50 = colour.SDS_ILLUMINANTS["D50"].copy().interpolate(colour.SpectralShape(300, 780, 1))
CAM16_KWARGS = {"L_A": 318.31, "Y_b": 20, "surround": colour.VIEWING_CONDITIONS_CAM16["Average"]}


@cache
def load(orientation):
    """Wavelengths (n,) and reflectance (ramp, reading, n) for one orientation."""
    sheets = pd.read_excel(DATA / f"gbc-all-{orientation}.ods", engine="odf", sheet_name=list(RAMPS))
    wl = np.array(sheets["White"].columns[7:], float)
    R = np.stack([sheets[r].sort_values("Reading").iloc[:, 7:].to_numpy(float) for r in RAMPS])
    return wl, R


def band(wl, nm):
    return int(np.argmin(abs(wl - nm)))


def cmfs(wl):
    return np.stack([np.interp(wl, CMFS.wavelengths, CMFS.values[:, i]) for i in range(3)])


def weights(wl):
    """k·S(λ)·cmf(λ), shape (3, n): the band sum of R·weights is XYZ with Y(white) = 1."""
    S = np.interp(wl, D50.wavelengths, D50.values)
    W = S * cmfs(wl)
    return W / W[1].sum()


def integrands(wl, R):
    return R[..., None, :] * weights(wl)


def xyz(wl, R):
    return integrands(wl, R).sum(-1)


def white(wl):
    return weights(wl).sum(-1)


def cam16ucs(XYZ, wl):
    spec = colour.XYZ_to_CAM16(XYZ * 100, white(wl) * 100, **CAM16_KWARGS)
    return colour.JMh_CAM16_to_CAM16UCS(np.stack([spec.J, spec.M, spec.h], -1))


def metrics(ref, test, wl):
    """Differences of test vs ref, both XYZ arrays (..., 3)."""
    d = test - ref
    with np.errstate(invalid="ignore", divide="ignore"):
        dxy = np.linalg.norm(colour.XYZ_to_xy(test) - colour.XYZ_to_xy(ref), axis=-1)
        dE = colour.delta_E(cam16ucs(ref, wl), cam16ucs(test, wl), method="CAM16-UCS")
    return {"dX": d[..., 0], "dY": d[..., 1], "dZ": d[..., 2], "dxy": dxy, "dE": dE}


def orientation_metrics():
    """Metrics between raw XYZ of each pair of orientations, arrays (ramp, reading)."""
    data = {o: load(o) for o in ORIENTATIONS}
    wl = data["top"][0]
    XYZ = {o: xyz(wl, R) for o, (_, R) in data.items()}
    return {(a, b): metrics(XYZ[a], XYZ[b], wl) for a, b in combinations(ORIENTATIONS, 2)}


def clean(wl, R):
    """Bands through 423.333 nm inclusive and all negative values set to 0."""
    return np.clip(np.where(wl <= wl[band(wl, CLEAN_END)], 0.0, R), 0.0, None)


@cache
def load_repetitions(filename):
    """Read 32 documented five-reading blocks, returning wavelengths and raw spectra."""
    path = REPEAT_DATA / filename
    blocks = path.read_text().strip().split("\n\n")
    sizes = [len(block.splitlines()) - (index == 0) for index, block in enumerate(blocks)]
    frame = pd.read_csv(path, sep="\t")
    wl = np.array(frame.columns[7:], float)
    values = frame.to_numpy(float)
    if sizes != [5] * 32 or frame.shape != (160, 113):
        raise ValueError(f"{path}: expected 32 blocks of five readings and 106 spectral bands")
    if tuple(frame.columns[:7]) != ("Reading", "X", "Y", "Z", "L*", "a*", "b*"):
        raise ValueError(f"{path}: unexpected measurement columns")
    if not np.array_equal(values[:, 0], np.arange(1, 161)) or not np.isfinite(values).all():
        raise ValueError(f"{path}: invalid reading sequence or non-finite measurements")
    if not np.allclose(wl, np.linspace(380, 730, 106), rtol=0, atol=0.00051):
        raise ValueError(f"{path}: unexpected wavelength grid")
    return wl, values[:, 7:].reshape(32, 5, 106)


def repetition_differences(XYZ, wl):
    """Ten pairwise CAM16-UCS distances within each five-reading patch block."""
    XYZ = np.asarray(XYZ)
    if XYZ.shape[-2:] != (5, 3) or not np.isfinite(XYZ).all():
        raise ValueError("Expected finite XYZ values with shape (..., 5, 3)")
    appearance = cam16ucs(XYZ, wl)
    if not np.isfinite(appearance).all():
        raise ValueError("Non-finite CAM16-UCS coordinates in repeated measurements")
    return np.stack([np.linalg.norm(appearance[..., first, :] - appearance[..., second, :], axis=-1)
                     for first, second in combinations(range(5), 2)], axis=-1)


@cache
def repeatability():
    """Historical within-patch differences after section 3 cleaning, one (32, 10) array per file."""
    return {filename: repetition_differences(xyz(wl, clean(wl, spectra)), wl)
            for filename in REPEAT_FILES for wl, spectra in [load_repetitions(filename)]}


def noise_floor():
    """Mean and empirical p95 of historical within-patch repeatability differences."""
    dE = np.concatenate([values.ravel() for values in repeatability().values()])
    return float(np.mean(dE)), float(np.percentile(dE, 95))


def md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---:" if i else "---" for i in range(len(header))) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def signed(v, digits=4):
    s = f"{v:+.{digits}f}"
    return s[1:] if float(s) == 0 else s


def ramp_summary_row(label, m):
    """One row of a ramp table from metrics over the 32 readings."""
    rng = lambda a: f"{signed(np.nanmin(a))} … {signed(np.nanmax(a))}"
    i = int(np.nanargmax(m["dE"]))
    return [
        label, rng(m["dX"]), rng(m["dY"]), rng(m["dZ"]),
        f"{np.nanmean(m['dxy']):.4f} ± {np.nanstd(m['dxy']):.4f}",
        f"{np.nanmean(m['dE']):.2f} ± {np.nanstd(m['dE']):.2f}",
        f"{m['dE'][i]:.2f} (#{i})",
    ]


RAMP_HEADER = ["Orientation", "ΔX range", "ΔY range", "ΔZ range", "Δxy mean ± sd", "ΔE mean ± sd", "ΔE max (reading)"]


def to_srgb(XYZ, wl):
    """XYZ encoded as sRGB without chromatic adaptation; returns (rgb clipped, clipped flag)."""
    rgb = colour.XYZ_to_sRGB(XYZ, chromatic_adaptation_transform=None)
    clipped = (rgb < 0).any(-1) | (rgb > 1).any(-1)
    return np.clip(rgb, 0, 1), clipped


def plot_swatches(cases, wl, path, labels=("raw", "method")):
    """cases: list of (title, XYZ_a, XYZ_b, dE)."""
    fig, axes = plt.subplots(1, len(cases), figsize=(2.2 * len(cases), 1.9), squeeze=False)
    any_clipped = False
    for ax, (title, a, b, dE) in zip(axes[0], cases):
        (ra, ca), (rb, cb) = to_srgb(a, wl), to_srgb(b, wl)
        any_clipped |= bool(ca or cb)
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, color=ra))
        ax.add_patch(plt.Rectangle((1, 0), 1, 1, color=rb))
        ax.set_xlim(0, 2), ax.set_ylim(0, 1), ax.set_aspect("equal"), ax.axis("off")
        ax.set_title(f"{title}\nΔE = {dE:.2f}", fontsize=9)
        ax.text(0.5, -0.12, labels[0] + ("*" if ca else ""), ha="center", va="top", fontsize=8)
        ax.text(1.5, -0.12, labels[1] + ("*" if cb else ""), ha="center", va="top", fontsize=8)
    if any_clipped:
        fig.text(0.5, 0.0, "* sRGB values clipped", ha="center", fontsize=7)
    save(fig, path)


def shade_regions(ax, cutoff=CUTOFF):
    ax.axvspan(380, cutoff, color="tab:red", alpha=0.08, lw=0, label=f"< {cutoff:g} nm")
    ax.axvspan(UNSTABLE_START, 730, color="tab:orange", alpha=0.08, lw=0, label=f"> {UNSTABLE_START:g} nm")


def save(fig, path):
    IMG.mkdir(exist_ok=True)
    fig.savefig(IMG / path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved img/{path}")
