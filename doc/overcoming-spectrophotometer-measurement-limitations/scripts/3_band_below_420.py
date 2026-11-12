import matplotlib.pyplot as plt
import numpy as np

from common import BASELINE_END, CUTOFF, FULL, ORIENTATIONS, RAMP_COLOURS, RAMPS, UNSTABLE_START, band, load, md_table, save, xyz

fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
for ax, (o, label) in zip(axes, ORIENTATIONS.items()):
    wl, R = load(o)
    for k, ramp in enumerate(RAMPS):
        ax.plot(wl, R[k, FULL], color=RAMP_COLOURS[ramp], label=f"{ramp} #{FULL}")
        ax.plot(wl, R[k, 0], color=RAMP_COLOURS[ramp], ls=":", lw=0.9)
    ax.axvspan(380, BASELINE_END, color="tab:red", alpha=0.08, lw=0)
    ax.axvspan(BASELINE_END, CUTOFF, color="tab:orange", alpha=0.08, lw=0)
    ax.axhline(0, color="k", lw=0.5)
    ax.set(xlim=(380, 470), title=label, xlabel="Wavelength (nm)")
axes[0].set_ylabel("Reflectance factor")
axes[0].legend(fontsize=7, loc="upper left")
fig.suptitle("Solid: reading 31, dotted: reading 0", fontsize=9)
save(fig, "3_zoom_380_470.png")

rows_neg, rows_plat = [], []
for o, label in ORIENTATIONS.items():
    wl, R = load(o)
    regions = {
        f"≤ {BASELINE_END:g}": wl <= BASELINE_END,
        f"{wl[band(wl, BASELINE_END) + 1]:.1f}–{wl[band(wl, CUTOFF) - 1]:.1f}": (wl > BASELINE_END) & (wl < CUTOFF - 1e-3),
        f"{CUTOFF:g}–{UNSTABLE_START:g}": (wl >= CUTOFF - 1e-3) & (wl <= UNSTABLE_START),
        f"> {UNSTABLE_START:g}": wl > UNSTABLE_START,
    }
    rows_neg.append([label] + [f"{(R[..., m] < 0).sum()} / {R[..., m].size}" for m in regions.values()])
    P = R[..., wl <= BASELINE_END]
    plateau = P.mean(-1).ravel()
    spread = (P.max(-1) - P.min(-1)).max()
    r450 = R[..., band(wl, 450)].ravel()
    Y = xyz(wl, R)[..., 1].ravel()
    rows_plat.append([
        label, f"{plateau.min():+.3f} … {plateau.max():+.3f}", f"{(plateau < 0).sum()} / {plateau.size}", f"{spread:.4f}",
        f"{np.corrcoef(plateau, r450)[0, 1]:.2f}", f"{np.corrcoef(plateau, Y)[0, 1]:.2f}",
    ])

print("\nNegative reflectance values per region (all ramps and readings)\n")
print(md_table(["Orientation", *(f"{k} nm" for k in regions)], rows_neg))
print(f"\nBaseline (mean of bands ≤ {BASELINE_END:g} nm) per spectrum\n")
print(md_table(["Orientation", "Range", "Negative spectra", "Max spread within baseline",
                "corr(baseline, R450)", "corr(baseline, Y)"], rows_plat))
