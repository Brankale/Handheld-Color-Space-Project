from itertools import combinations

import colour
import matplotlib.pyplot as plt
import numpy as np

from common import FULL, ORIENTATIONS, RAMP_COLOURS, RAMPS, integrands, load, md_table, metrics, noise_floor, save, signed
from methods import METHODS

MARKERS = {"raw": "o", "cleaning": "s", "truncation": "v", "gaussian": "D", "hold": "^"}

XYZ = {name: [] for name in ("raw", *METHODS)}
for o in ORIENTATIONS:
    wl, R = load(o)
    XYZ["raw"].append(integrands(wl, R).sum(-1))
    for name, method in METHODS.items():
        XYZ[name].append(method(wl, R).sum(-1))
XYZ = {k: np.stack(v) for k, v in XYZ.items()}  # (orientation, ramp, reading, 3)
M = {name: metrics(XYZ["raw"], XYZ[name], wl) for name in METHODS}
floor, floor95 = noise_floor()

rows = []
for name, m in M.items():
    rows.append([
        name, signed(np.nanmean(m["dX"])), signed(np.nanmean(m["dY"])), signed(np.nanmean(m["dZ"])),
        f"{np.nanmean(m['dxy']):.4f}", f"{np.nanmean(m['dE']):.2f}", f"{np.nanpercentile(m['dE'], 95):.2f}",
        f"{np.nanmax(m['dE']):.2f}", f"{np.nanmean(m['dE'][:, :, FULL]):.2f}",
    ])
print("\nAll methods vs raw data, 3 orientations × 7 ramps × 32 readings\n")
print(md_table(["Method", "mean ΔX", "mean ΔY", "mean ΔZ", "mean Δxy", "mean ΔE", "p95 ΔE", "max ΔE", f"mean ΔE #{FULL}"], rows))

rows = []
for a, b in combinations(METHODS, 2):
    m = metrics(XYZ[a], XYZ[b], wl)
    rows.append([f"{a} vs {b}", signed(np.nanmean(m["dZ"])), f"{np.nanmean(m['dE']):.2f}", f"{np.nanmax(m['dE']):.2f}"])
print("\nMethods against each other\n")
print(md_table(["Pair", "mean ΔZ", "mean ΔE", "max ΔE"], rows))
print(f"\nNoise floor: mean ΔE = {floor:.2f}, p95 ΔE = {floor95:.2f}")

fig, ax = plt.subplots(figsize=(10, 4))
width = 0.8 / len(METHODS)
x = np.arange(len(RAMPS))
for j, (name, m) in enumerate(M.items()):
    mean = np.nanmean(m["dE"], axis=(0, 2))
    top = np.nanmax(m["dE"], axis=(0, 2))
    pos = x + (j - (len(METHODS) - 1) / 2) * width
    ax.bar(pos, mean, width, label=name)
    ax.scatter(pos, top, marker="_", color="k", s=60, zorder=3)
ax.axhline(floor95, color="k", ls="--", lw=0.8, label=f"noise p95 ({floor95:.2f})")
ax.set_xticks(x, RAMPS)
ax.set(ylabel="ΔE CAM16-UCS vs raw", title="Mean ΔE per ramp (bars) and max ΔE (ticks), all orientations and readings")
ax.legend(fontsize=8, ncol=3)
save(fig, "6_delta_e.png")

xy = {k: colour.XYZ_to_xy(v[0, :, FULL]) for k, v in XYZ.items()}
fig, axes = plt.subplots(2, 4, figsize=(14, 7))
for ax, (k, ramp) in zip(axes.flat, enumerate(RAMPS)):
    for name, p in xy.items():
        ax.scatter(*p[k], marker=MARKERS[name], s=45, label=name,
                   facecolor="none" if name == "raw" else RAMP_COLOURS[ramp], edgecolor="k" if name == "raw" else "none")
    ax.set_title(f"{ramp} #{FULL}, 0°", fontsize=9)
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.3)
    ax.tick_params(labelsize=7)
    ax.set(xlabel="x", ylabel="y")
handles, labels = axes.flat[0].get_legend_handles_labels()
axes.flat[-1].axis("off")
axes.flat[-1].legend(handles, labels, loc="center")
fig.tight_layout()
save(fig, "6_xy.png")
