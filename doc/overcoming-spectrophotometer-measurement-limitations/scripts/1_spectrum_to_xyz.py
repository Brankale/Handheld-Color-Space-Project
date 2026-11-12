import matplotlib.pyplot as plt
import numpy as np

from common import CMFS, CUTOFF, D50, FULL, RAMPS, UNSTABLE_START, band, integrands, load, md_table, save, shade_regions

wl, R = load("top")

fig, ax = plt.subplots(figsize=(8, 4))
for i, (name, col) in enumerate(zip((r"$\bar{x}$", r"$\bar{y}$", r"$\bar{z}$"), ("tab:red", "tab:green", "tab:blue"))):
    ax.plot(CMFS.wavelengths, CMFS.values[:, i], color=col, label=name)
ax2 = ax.twinx()
ax2.plot(D50.wavelengths, D50.values, color="0.3", ls="--", label="D50")
ax.set(xlim=(380, 730), xlabel="Wavelength (nm)", ylabel="CIE 1931 2° CMF")
ax2.set(ylabel="D50 relative power", ylim=(0, None))
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8)
save(fig, "1_cmfs_d50.png")

fig, ax = plt.subplots(figsize=(8, 4))
cmap = plt.get_cmap("viridis")
for r in range(R.shape[1]):
    ax.plot(wl, R[0, r], color=cmap(r / (R.shape[1] - 1)), lw=0.8)
shade_regions(ax)
ax.axhline(0, color="k", lw=0.5)
ax.set(xlim=(380, 730), xlabel="Wavelength (nm)", ylabel="Reflectance factor", title="White ramp, readings 0–31 (0°)")
ax.legend(loc="lower right", fontsize=8)
fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 31)), ax=ax, label="Reading")
save(fig, "1_white_ramp.png")

i_cut, i_ir = band(wl, CUTOFF), band(wl, UNSTABLE_START)
rows = []
for k, name in enumerate(RAMPS):
    I = integrands(wl, R[k, FULL])
    total = I.sum(-1)
    lo, hi = I[:, :i_cut].sum(-1) / total, I[:, i_ir + 1 :].sum(-1) / total
    rows.append([name] + [f"{100 * v:.1f} %" for v in lo] + [f"{100 * v:.2f} %" for v in hi])
I = integrands(wl, np.ones_like(wl))
total = I.sum(-1)
rows.append(["Perfect reflector"] + [f"{100 * v:.1f} %" for v in I[:, :i_cut].sum(-1) / total]
            + [f"{100 * v:.2f} %" for v in I[:, i_ir + 1 :].sum(-1) / total])
c, u = f"{CUTOFF:g}", f"{UNSTABLE_START:g}"
print(f"\nShare of X, Y, Z from bands below {c} nm and above {u} nm (reading {FULL}, 0°, raw data)\n")
print(md_table(["Ramp", f"X < {c}", f"Y < {c}", f"Z < {c}", f"X > {u}", f"Y > {u}", f"Z > {u}"], rows))
