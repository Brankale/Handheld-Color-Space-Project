import numpy as np

from common import FULL, ORIENTATIONS, RAMPS, load, md_table, noise_floor, orientation_metrics, ramp_noise, xyz

pairs = orientation_metrics()
name = lambda p: f"{ORIENTATIONS[p[0]]} vs {ORIENTATIONS[p[1]]}"

rows = []
for p, m in pairs.items():
    k, r = np.unravel_index(np.nanargmax(m["dE"]), m["dE"].shape)
    rows.append([
        name(p), *(f"{np.nanmean(abs(m[c])):.4f}" for c in ("dX", "dY", "dZ")), f"{np.nanmean(m['dxy']):.4f}",
        f"{np.nanmean(m['dE']):.2f}", f"{np.nanpercentile(m['dE'], 95):.2f}", f"{m['dE'][k, r]:.2f} ({RAMPS[k]} #{r})",
    ])
print("\nDifferences between orientations, raw data, all ramps and readings\n")
print(md_table(["Pair", "mean \\|ΔX\\|", "mean \\|ΔY\\|", "mean \\|ΔZ\\|", "mean Δxy", "mean ΔE", "p95 ΔE", "max ΔE"], rows))

rows = [[ramp] + [f"{np.nanmean(m['dE'][k]):.2f} / {np.nanmax(m['dE'][k]):.2f} / {m['dE'][k, FULL]:.2f}"
                  for m in pairs.values()] for k, ramp in enumerate(RAMPS)]
print(f"\nΔE between orientations per ramp: mean / max / reading {FULL}\n")
print(md_table(["Ramp"] + [name(p) for p in pairs], rows))

Y = {o: xyz(*load(o))[:, FULL, 1] for o in ORIENTATIONS}
rows = [[ramp] + [f"{Y[o][k]:.3f}" for o in ORIENTATIONS] for k, ramp in enumerate(RAMPS)]
print(f"\nY of reading {FULL} per orientation, raw data\n")
print(md_table(["Ramp"] + list(ORIENTATIONS.values()), rows))

mean, p95 = noise_floor()
rows = []
for o, label in ORIENTATIONS.items():
    dE = ramp_noise(o)
    k, r = np.unravel_index(np.nanargmax(dE), dE.shape)
    rows.append([label, f"{np.nanmean(dE):.2f}", f"{np.nanpercentile(dE, 95):.2f}", f"{dE[k, r]:.2f} ({RAMPS[k]} #{r + 1})"])
rows.append(["All", f"{mean:.2f}", f"{p95:.2f}", ""])
print("\nReading-to-reading noise: ΔE of each reading from the mean of its neighbours × √(2/3), raw data\n")
print(md_table(["Orientation", "mean ΔE", "p95 ΔE", "max ΔE"], rows))
print(f"\nNoise floor: mean ΔE = {mean:.2f}, p95 ΔE = {p95:.2f}")
