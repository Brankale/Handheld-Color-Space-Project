import colour
import matplotlib.pyplot as plt
import numpy as np

from common import (CMFS, CUTOFF, D50, FULL, RAMPS, UNSTABLE_START, band, integrands, load, md_table, save,
                    shade_regions)

wl, R = load("top")
XYZ_NAMES = ("X", "Y", "Z")
XYZ_COLOURS = ("tab:red", "tab:green", "tab:blue")
CMF_NAMES = (r"$\bar{x}$", r"$\bar{y}$", r"$\bar{z}$")


def chain(titles):
    """Three side-by-side panels joined by × and = signs."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), sharex=True)
    fig.subplots_adjust(wspace=0.6)
    for ax, title in zip(axes, titles):
        ax.set(xlim=(380, 730), xlabel="Wavelength (nm)", title=title)
    for sign, a, b in (("×", axes[0], axes[1]), ("=", axes[1], axes[2])):
        # Left part of the gap: the right part holds the next panel's y labels.
        x = a.get_position().x1 + 0.25 * (b.get_position().x0 - a.get_position().x1)
        fig.text(x, 0.5, sign, ha="center", va="center", fontsize=22)
    return fig, axes


r = R[0, FULL]
reflected = np.interp(wl, D50.wavelengths, D50.values) * r / 100

fig, (a, b, c) = chain(("Light: D50", f"Screen: White #{FULL}, 0°", "Reflected light"))
a.plot(D50.wavelengths, D50.values, color="0.3")
a.set(ylabel="Relative power", ylim=(0, None))
b.plot(wl, r, color="0.3")
b.set(ylabel="Reflectance factor (%)")
c.plot(wl, reflected, color="0.3")
c.set(ylabel="Relative power")
for ax in (b, c):
    ax.axhline(0, color="k", lw=0.5)
save(fig, "1a_reflected_light.png")

fig, (a, b, c) = chain(("Reflected light", "Eye: CIE 1931 2° observer", "Light seen by the eye"))
a.plot(wl, reflected, color="0.3")
a.axhline(0, color="k", lw=0.5)
a.set(ylabel="Relative power")
for i, (name, col) in enumerate(zip(CMF_NAMES, XYZ_COLOURS)):
    b.plot(CMFS.wavelengths, CMFS.values[:, i], color=col, label=name)
b.set(ylabel="Sensitivity")
b.legend(fontsize=8)
for p, name, col in zip(integrands(wl, r), XYZ_NAMES, XYZ_COLOURS):
    c.plot(wl, p, color=col, lw=0.8)
    c.fill_between(wl, p, color=col, alpha=0.25, lw=0, label=f"area = {name} = {p.sum():.3f}")
c.axhline(0, color="k", lw=0.5)
c.legend(fontsize=8)
save(fig, "1b_light_to_xyz.png")

fig, ax = plt.subplots(figsize=(8, 4))
cmap = plt.get_cmap("viridis")
for r in range(R.shape[1]):
    ax.plot(wl, R[0, r], color=cmap(r / (R.shape[1] - 1)), lw=0.8)
shade_regions(ax)
ax.axhline(0, color="k", lw=0.5)
ax.set(xlim=(380, 730), xlabel="Wavelength (nm)", ylabel="Reflectance factor (%)", title="White ramp, readings 0–31 (0°)")
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
I = integrands(wl, np.full_like(wl, 100.0))
total = I.sum(-1)
rows.append(["Perfect reflector"] + [f"{100 * v:.1f} %" for v in I[:, :i_cut].sum(-1) / total]
            + [f"{100 * v:.2f} %" for v in I[:, i_ir + 1 :].sum(-1) / total])
c, u = f"{CUTOFF:g}", f"{UNSTABLE_START:g}"
print(f"\nShare of X, Y, Z from bands below {c} nm and above {u} nm (reading {FULL}, 0°, raw data)\n")
print(md_table(["Ramp", f"X < {c}", f"Y < {c}", f"Z < {c}", f"X > {u}", f"Y > {u}", f"Z > {u}"], rows))

rows = []
observer = CMFS.values
reflectances = np.vstack((R[:, FULL], np.full_like(wl, 100.0)))
shares_by_illuminant = []
for name in ("D50", "D55", "D65", "D75"):
    illuminant = colour.SDS_ILLUMINANTS[name].copy().interpolate(colour.SpectralShape(300, 780, 1))
    power = np.interp(wl, illuminant.wavelengths, illuminant.values)
    shares = []
    for channel in (0, 2):
        product = reflectances * power * np.interp(wl, CMFS.wavelengths, observer[:, channel])
        shares.append(100 * product[:, :i_cut].sum(-1) / product.sum(-1))
    shares_by_illuminant.append(np.stack(shares, axis=-1))
for name, shares in zip((*RAMPS, "Perfect reflector"), np.concatenate(shares_by_illuminant, axis=-1)):
    rows.append([name] + [f"{value:.1f} %" for value in shares])
print(f"\nShare of X and Z below {c} nm by illuminant (reading {FULL}, 0°, raw data)\n")
print(md_table(["Ramp"] + [f"{name} {channel} < {c}" for name in ("D50", "D55", "D65", "D75")
                          for channel in ("X", "Z")], rows))
