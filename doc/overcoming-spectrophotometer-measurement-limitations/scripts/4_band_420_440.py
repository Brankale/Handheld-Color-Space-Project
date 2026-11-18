import matplotlib.pyplot as plt
import numpy as np

from common import CUTOFF, ORIENTATIONS, RAMP_COLOURS, RAMPS, band, integrands, load, md_table, save

CANDIDATES = (430, 433.333, 436.667, 440, 443.333)
DROP_READINGS = slice(16, 32)


def drop_shape(wl, R):
    """R/R450 per ramp, mean over the brighter readings."""
    return (R[:, DROP_READINGS] / R[:, DROP_READINGS, band(wl, 450)][..., None]).mean(1)


results = {o: load(o) for o in ORIENTATIONS}
wl = results["top"][0]
D = {o: drop_shape(*d) for o, d in results.items()}

fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
for ax, (o, label) in zip(axes, ORIENTATIONS.items()):
    for k, ramp in enumerate(RAMPS):
        ax.plot(wl, D[o][k], color=RAMP_COLOURS[ramp], marker=".", label=ramp)
    ax.set(xlim=(418, 482), ylim=(-0.6, 1.4), title=label, xlabel="Wavelength (nm)")
    ax.axhline(0, color="k", lw=0.5)
    ax.axvline(CUTOFF, color="k", ls="--", lw=0.7)
axes[0].set_ylabel("R / R(450 nm)")
axes[0].legend(fontsize=7)
fig.suptitle(f"Shape of the drop, mean of readings {DROP_READINGS.start}–{DROP_READINGS.stop - 1}", fontsize=9)
save(fig, "4_drop_shape.png")

Wc = integrands(wl, np.ones_like(wl))
rows = []
for c in CANDIDATES:
    i = band(wl, c)
    rows.append([
        f"{c:.1f}",
        f"{100 * Wc[0, :i].sum() / Wc[0].sum():.1f} %", f"{100 * Wc[2, :i].sum() / Wc[2].sum():.1f} %",
    ])
print("\nCutoff candidates: share of X and Z (perfect reflector, D50) left below the cutoff\n")
print(md_table(["Cutoff (nm)", "X below", "Z below"], rows))
