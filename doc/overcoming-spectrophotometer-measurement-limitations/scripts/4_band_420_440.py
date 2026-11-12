import matplotlib.pyplot as plt
import numpy as np

from common import BASELINE_END, CUTOFF, FULL, ORIENTATIONS, RAMP_COLOURS, RAMPS, band, integrands, load, md_table, save

BANDS = (420, 423.333, 426.667, 430, 433.333, 436.667, 440, 443.333, 446.667, 450)
CANDIDATES = (430, 433.333, 436.667, 440, 443.333)
TRUSTED = (446.0, 461.0)
DROP_READINGS = slice(16, 32)
LEAK_GREY, LEAK_CONTAMINATED, LEAK_INVALID = 0.05, 0.10, 0.25


def leak(wl, R):
    """Per ramp: share of the baseline jitter that reappears in each band, after removing the trusted-band trend."""
    share, corr = np.zeros((len(RAMPS), len(BANDS))), np.zeros((len(RAMPS), len(BANDS)))
    for k in range(len(RAMPS)):
        P = R[k][:, wl <= BASELINE_END].mean(1)
        T = R[k][:, (wl >= TRUSTED[0]) & (wl <= TRUSTED[1])].mean(1)
        A = np.column_stack([T, np.ones_like(T)])
        resid = lambda y: y - A @ np.linalg.lstsq(A, y, rcond=None)[0]
        p = resid(P)
        for j, nm in enumerate(BANDS):
            y = resid(R[k][:, band(wl, nm)])
            share[k, j] = (y @ p) / (p @ p)
            corr[k, j] = np.corrcoef(y, p)[0, 1]
    return share.mean(0), corr.mean(0), corr.min(0)


def drop_shape(wl, R):
    """R/R450 per ramp, mean over the brighter readings."""
    return (R[:, DROP_READINGS] / R[:, DROP_READINGS, band(wl, 450)][..., None]).mean(1)


results = {o: load(o) for o in ORIENTATIONS}
wl = results["top"][0]
L = {o: leak(*d) for o, d in results.items()}
neg = {o: [int((R[..., band(wl, nm)] < 0).sum()) for nm in BANDS] for o, (_, R) in results.items()}
D = {o: drop_shape(*d) for o, d in results.items()}

rows = []
for j, nm in enumerate(BANDS):
    rows.append([f"{nm:.1f}"]
                + [f"{100 * L[o][0][j]:.1f} %" for o in ORIENTATIONS]
                + [f"{L[o][1][j]:.2f} ({L[o][2][j]:.2f})" for o in ORIENTATIONS]
                + [str(sum(neg[o][j] for o in ORIENTATIONS))])
labels = list(ORIENTATIONS.values())
print("\nBaseline leak per band: share of the baseline jitter found in the band, and correlation mean (min) over the 7 ramps\n")
print(md_table(["Band (nm)", *(f"Leak {l}" for l in labels), *(f"Corr {l}" for l in labels), "Negatives / 672"], rows))

# zones
leak_max = np.max([L[o][0] for o in ORIENTATIONS], 0)
neg_total = np.sum([neg[o] for o in ORIENTATIONS], 0)
zones = []
for j, nm in enumerate(BANDS):
    if nm <= BASELINE_END:
        zones.append("baseline")
    elif neg_total[j] > 0 or leak_max[j] >= LEAK_INVALID:
        zones.append("invalid")
    elif leak_max[j] >= LEAK_CONTAMINATED:
        zones.append("contaminated")
    elif leak_max[j] >= LEAK_GREY:
        zones.append("grey")
    else:
        zones.append("reliable")
rows = [[f"{nm:.1f}", f"{100 * leak_max[j]:.1f} %", str(neg_total[j]), zones[j]] for j, nm in enumerate(BANDS)]
print(f"\nZones: invalid = negatives or leak ≥ {LEAK_INVALID:.0%}, contaminated = leak ≥ {LEAK_CONTAMINATED:.0%}, "
      f"grey = leak ≥ {LEAK_GREY:.0%}, reliable otherwise (max leak over orientations)\n")
print(md_table(["Band (nm)", "Max leak", "Negatives", "Zone"], rows))

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

ZONE_COLOURS = {"baseline": "0.6", "invalid": "tab:red", "contaminated": "tab:orange", "grey": "gold", "reliable": "tab:green"}
fig, ax = plt.subplots(figsize=(8, 4))
step = wl[1] - wl[0]
for nm, z in zip(BANDS, zones):
    ax.axvspan(nm - step / 2, nm + step / 2, color=ZONE_COLOURS[z], alpha=0.25, lw=0)
for nm in wl[(wl < BANDS[0]) & (wl > 380)]:
    ax.axvspan(nm - step / 2, nm + step / 2, color=ZONE_COLOURS["baseline"], alpha=0.25, lw=0)
ax.axvspan(BANDS[-1] + step / 2, 480, color=ZONE_COLOURS["reliable"], alpha=0.25, lw=0)
_, R = results["top"]
for k, ramp in enumerate(RAMPS):
    ax.plot(wl, R[k, FULL], color=RAMP_COLOURS[ramp], marker=".", lw=1)
ax.axhline(0, color="k", lw=0.5)
handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.4) for c in ZONE_COLOURS.values()]
ax.legend(handles, ZONE_COLOURS.keys(), fontsize=8, loc="upper left")
ax.set(xlim=(400, 480), xlabel="Wavelength (nm)", ylabel="Reflectance factor", title=f"Reliability zones, reading {FULL} (0°)")
save(fig, "4_zones.png")

Wc = integrands(wl, np.ones_like(wl))
rows = []
for c in CANDIDATES:
    i, j = band(wl, c), BANDS.index(c)
    rows.append([
        f"{c:.1f}", zones[j], f"{100 * leak_max[j:].max():.1f} %", str(neg_total[j:].sum()),
        f"{100 * Wc[0, :i].sum() / Wc[0].sum():.1f} %", f"{100 * Wc[2, :i].sum() / Wc[2].sum():.1f} %",
    ])
print("\nCutoff candidates: worst leak and negatives at or above the cutoff (up to 450 nm), share of X and Z (perfect reflector, D50) left below it\n")
print(md_table(["Cutoff (nm)", "Zone", "Worst leak ≥ cutoff", "Negatives ≥ cutoff", "X below", "Z below"], rows))
