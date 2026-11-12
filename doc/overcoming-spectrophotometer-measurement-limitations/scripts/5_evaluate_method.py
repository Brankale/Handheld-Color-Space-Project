import argparse

import matplotlib.pyplot as plt
import numpy as np

from common import (
    CUTOFF, FULL, ORIENTATIONS, RAMP_COLOURS, RAMP_HEADER, RAMPS, cmfs, integrands, load, md_table, metrics,
    IMG, noise_floor, plot_swatches, ramp_summary_row, save, signed, weights,
)
from methods import METHODS

SWATCH_THRESHOLD = 2.0

parser = argparse.ArgumentParser()
parser.add_argument("--method", choices=METHODS, required=True)
name = parser.parse_args().method
method = METHODS[name]

res = {}
for o in ORIENTATIONS:
    wl, R = load(o)
    raw, new = integrands(wl, R), method(wl, R)
    res[o] = (raw, new, metrics(raw.sum(-1), new.sum(-1), wl))
show = wl <= 500
x, W, c = wl[show], weights(wl)[:, show], cmfs(wl)[:, show]
raw, new = res["top"][0][:, FULL][..., show], res["top"][1][:, FULL][..., show]

# reflectance implied by each channel: identical for all methods except the Gaussian one
fig, axes = plt.subplots(2, 4, figsize=(14, 6), sharex=True)
for ax, (k, ramp) in zip(axes.flat, enumerate(RAMPS)):
    ax.plot(x, raw[k, 1] / W[1], color="0.6", marker=".", ms=3, label="raw")
    rx, rz = new[k, 0] / W[0], new[k, 2] / W[2]
    if np.allclose(rx, rz):
        ax.plot(x, rx, color=RAMP_COLOURS[ramp], label=name)
    else:
        ax.plot(x, rx, color=RAMP_COLOURS[ramp], label=rf"{name}, from R·$\bar{{x}}$")
        ax.plot(x, rz, color=RAMP_COLOURS[ramp], ls="--", label=rf"{name}, from R·$\bar{{z}}$")
    ax.axvline(CUTOFF, color="k", ls=":", lw=0.7)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_title(ramp, fontsize=9)
    ax.legend(fontsize=6)
axes.flat[-1].axis("off")
for ax in axes[1]:
    ax.set_xlabel("Wavelength (nm)")
for ax in axes[:, 0]:
    ax.set_ylabel("Reflectance factor")
fig.suptitle(f"{name}: reflectance, reading {FULL}, 0°", fontsize=10)
save(fig, f"method_{name}_spectrum.png")

fig, axes = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
for col, ramp in enumerate(("White", "Red", "Blue")):
    k = RAMPS.index(ramp)
    for row, (ch, label) in enumerate(((0, r"R·$\bar{x}$"), (2, r"R·$\bar{z}$"))):
        ax = axes[row, col]
        ax.plot(x, raw[k, ch] / W[ch] * c[ch], color="0.6", marker=".", ms=3, label="raw")
        ax.plot(x, new[k, ch] / W[ch] * c[ch], color=RAMP_COLOURS[ramp], label=name)
        ax.axvline(CUTOFF, color="k", ls=":", lw=0.7)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title(f"{ramp} #{FULL}: {label}", fontsize=9)
        ax.legend(fontsize=7)
for ax in axes[1]:
    ax.set_xlabel("Wavelength (nm)")
fig.suptitle(f"{name}: reflectance × CMF, 0°", fontsize=10)
save(fig, f"method_{name}_products.png")

if name == "cleaning":
    reference = noise_floor()[1]
    with plt.rc_context({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#b0b4b8", "axes.labelcolor": "#363b40",
        "xtick.color": "#555b61", "ytick.color": "#555b61",
        "savefig.facecolor": "white",
    }):
        for ramps, filename in (
            (("Red", "Green", "Blue"), "method_cleaning_delta_e_primaries.png"),
            (("Yellow", "Cyan", "Magenta", "White"), "method_cleaning_delta_e_secondaries_greyscale.png"),
        ):
            figure, axes = plt.subplots(1, 3, figsize=(12, 2.45), sharex=True, sharey=True)
            for axis, (orientation, label) in zip(axes, ORIENTATIONS.items()):
                for ramp in ramps:
                    ramp_index = RAMPS.index(ramp)
                    axis.plot(np.arange(FULL + 1), res[orientation][2]["dE"][ramp_index],
                              color=RAMP_COLOURS[ramp], marker="o", markersize=2.5,
                              linewidth=1.35, label="Grey" if ramp == "White" else ramp)
                axis.axhline(reference, color="#7b8288", linestyle=(0, (4, 3)), linewidth=0.8)
                axis.axhline(3, color="#c5c8cb", linestyle=":", linewidth=0.9)
                axis.set(xlim=(-0.4, 31.4), ylim=(0, 6.15), xticks=(0, 8, 16, 24, 31),
                         yticks=(0, 1, 2, 3, 4, 5, 6), xlabel="Patch index")
                axis.set_title(label, fontsize=10, pad=8)
                axis.grid(axis="y", color="#e9ebed", linewidth=0.6)
                axis.set_axisbelow(True)
            axes[0].set_ylabel(r"CAM16-UCS $\Delta E$")
            handles, labels = axes[0].get_legend_handles_labels()
            axes[-1].legend(handles, labels, loc="upper right", frameon=False, handlelength=1.8)
            figure.subplots_adjust(wspace=0.12, left=0.055, right=0.99, bottom=0.22, top=0.86)
            figure.savefig(IMG / filename, dpi=160, bbox_inches="tight")
            plt.close(figure)
            print(f"saved img/{filename}")

    for orientation, label in ORIENTATIONS.items():
        differences = res[orientation][2]
        rows = []
        for ramp in ("Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "White"):
            ramp_index = RAMPS.index(ramp)
            values = differences["dE"][ramp_index]
            rows.append([
                ramp, *(signed(differences[metric][ramp_index, FULL]) for metric in ("dX", "dY", "dZ")),
                f"{differences['dxy'][ramp_index, FULL]:.4f}",
                f"{values.mean():.2f}", f"{np.percentile(values, 95):.2f}", f"{values.max():.2f}",
            ])
        values = differences["dE"]
        rows.append(["All ramps", *(["N/A"] * 4), f"{values.mean():.2f}",
                     f"{np.percentile(values, 95):.2f}", f"{values.max():.2f}"])
        print(f"\n{name}, {label}\n")
        print(md_table(["Colour", "ΔX", "ΔY", "ΔZ", "Δxy", "Mean ΔE", "p95 ΔE", "Max ΔE"], rows))
else:
    for o, label in ORIENTATIONS.items():
        raw, new, m = res[o]
        rows = []
        for k, ramp in enumerate(RAMPS):
            X, Y, Z = new[k, FULL].sum(-1)
            rows.append([ramp, f"{X:.4f}", f"{Y:.4f}", f"{Z:.4f}", *(signed(m[d][k, FULL]) for d in ("dX", "dY", "dZ")),
                         f"{m['dxy'][k, FULL]:.4f}", f"{m['dE'][k, FULL]:.2f}"])
        print(f"\n{name}, reading {FULL}, {label}\n")
        print(md_table(["Ramp", "X", "Y", "Z", "ΔX", "ΔY", "ΔZ", "Δxy", "ΔE"], rows))

    for k, ramp in enumerate(RAMPS):
        rows = [ramp_summary_row(label, {d: v[k] for d, v in res[o][2].items()}) for o, label in ORIENTATIONS.items()]
        print(f"\n{name}, {ramp} ramp, readings 0–{FULL}\n")
        print(md_table(RAMP_HEADER, rows))

dE = np.stack([res[o][2]["dE"] for o in ORIENTATIONS])
_, floor95 = noise_floor()
print(f"\n{name}, all spectra: mean ΔE = {np.nanmean(dE):.2f}, max ΔE = {np.nanmax(dE):.2f}, "
    f"share above the historical repeatability p95 ({floor95:.2f}) = {(dE > floor95).mean():.0%}")

below = wl < CUTOFF - 1e-3
rows = []
for ch, label in ((0, "R·x̄"), (2, "R·z̄")):
    implied = np.stack([res[o][1][..., ch, below] / weights(wl)[ch, below] for o in ORIENTATIONS]).max(-1)
    rows.append([label, f"{implied.max():.2f}", f"{(implied > 1).sum()} / {implied.size}"])
print(f"\n{name}, reflectance implied below {CUTOFF:g} nm\n")
print(md_table(["From", "Max", "Spectra above 1"], rows))

cases = []
for k, ramp in enumerate(RAMPS):
    oi, r = np.unravel_index(np.nanargmax(dE[:, k]), dE[:, k].shape)
    if dE[oi, k, r] > SWATCH_THRESHOLD:
        o = list(ORIENTATIONS)[oi]
        raw, new, _ = res[o]
        cases.append((f"{ramp} #{r}, {ORIENTATIONS[o]}", raw[k, r].sum(-1), new[k, r].sum(-1), dE[oi, k, r]))
cases.sort(key=lambda case: -case[3])
if cases:
    plot_swatches(cases, wl, f"method_{name}_swatches.png", labels=("raw", name))
else:
    print(f"No case with ΔE > {SWATCH_THRESHOLD:g}: no swatches")
