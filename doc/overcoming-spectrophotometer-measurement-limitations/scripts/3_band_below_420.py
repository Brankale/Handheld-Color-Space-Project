import matplotlib.pyplot as plt

from common import BASELINE_END, CLEAN_END, FULL, ORIENTATIONS, RAMP_COLOURS, RAMPS, band, load, md_table, save

fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
for ax, (o, label) in zip(axes, ORIENTATIONS.items()):
    wl, R = load(o)
    for k, ramp in enumerate(RAMPS):
        ax.plot(wl, R[k, FULL], color=RAMP_COLOURS[ramp], label=f"{ramp} #{FULL}")
        ax.plot(wl, R[k, 0], color=RAMP_COLOURS[ramp], ls=":", lw=0.9)
    ax.axvspan(380, CLEAN_END, color="tab:red", alpha=0.08, lw=0)
    ax.axhline(0, color="k", lw=0.5)
    ax.set(xlim=(380, 470), title=label, xlabel="Wavelength (nm)")
axes[0].set_ylabel("Reflectance factor (%)")
axes[0].legend(fontsize=7, loc="upper left")
fig.suptitle("Solid: reading 31, dotted: reading 0", fontsize=9)
save(fig, "3_zoom_380_470.png")

rows_neg = []
for o, label in ORIENTATIONS.items():
    wl, R = load(o)
    regions = {
        f"≤ {BASELINE_END:g}": wl <= BASELINE_END,
        "423.3": wl == wl[band(wl, CLEAN_END)],
        "426.7–730": wl > wl[band(wl, CLEAN_END)],
    }
    rows_neg.append([label] + [f"{(R[..., m] < 0).sum()} / {R[..., m].size}" for m in regions.values()])

print("\nNegative reflectance values per region (all ramps and readings)\n")
print(md_table(["Orientation", *(f"{k} nm" for k in regions)], rows_neg))
