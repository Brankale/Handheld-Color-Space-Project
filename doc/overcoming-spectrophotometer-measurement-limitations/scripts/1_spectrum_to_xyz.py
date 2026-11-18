import colour
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

from common import (CMFS, CUTOFF, D50, FULL, RAMPS, UNSTABLE_START, band, cmfs, integrands, load, md_table, save,
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


def gradient_under_curve(ax, values, color, wavelengths=None, label=None,
                         linestyle="-", alpha=0.95, linewidth=0.8):
    wavelengths = wl if wavelengths is None else wavelengths
    lower, upper = min(0, values.min()), max(0, values.max())
    colors = np.asarray(color)
    if colors.ndim < 2:
        colors = np.array([to_rgba(color)[:3]])
    rgba = np.ones((256, len(colors), 4))
    rgba[:, :, :3] = colors[None, :, :3]
    rgba[:, :, 3] = (alpha * np.abs(np.linspace(lower, upper, 256))
                     / max(abs(lower), upper, np.finfo(float).eps))[:, None]
    xlim = ax.get_xlim()
    area = ax.fill_between(wavelengths, values, facecolor="none", edgecolor="none")
    image = ax.imshow(rgba, extent=(wavelengths[0], wavelengths[-1], lower, upper),
                      origin="lower", aspect="auto", zorder=1)
    image.set_clip_path(area.get_paths()[0], ax.transData)
    ax.plot(wavelengths, values, color="0.2", lw=linewidth, zorder=2,
            label=label, ls=linestyle)
    ax.set_xlim(xlim)
    ax.autoscale(axis="y")
    bottom, top = ax.dataLim.intervaly
    ax.set_ylim(min(0, bottom) * 1.05, top + 0.05 * (top - min(0, bottom)))


r = R[0, FULL]
reflected = np.interp(wl, D50.wavelengths, D50.values) * r / 100

fig, (a, b, c) = chain(("Light: D50", f"Screen: White #{FULL}, 0°", "Reflected light"))
gradient_under_curve(a, D50.values, "#ffe6d0", wavelengths=D50.wavelengths)
a.set(ylabel="Relative power", ylim=(0, None))
gradient_under_curve(b, r, "0.65")
b.set(ylabel="Reflectance factor (%)")
gradient_under_curve(c, reflected, "#ffe6d0")
c.set(ylabel="Relative power")
for ax in (b, c):
    ax.axhline(0, color="k", lw=0.5)
save(fig, "1a_reflected_light.png")

fig, (a, b, c) = chain(("Reflected light", "Eye: CIE 1931 2° observer", "Light seen by the eye"))
gradient_under_curve(a, reflected, "#ffe6d0")
a.axhline(0, color="k", lw=0.5)
a.set(ylabel="Relative power")
for index, (name, color) in enumerate(zip(CMF_NAMES, XYZ_COLOURS)):
    sensitivity = CMFS.values[:, index]
    b.plot(CMFS.wavelengths, sensitivity, color=color, label=name, lw=0.8)
    b.fill_between(CMFS.wavelengths, sensitivity, color=color, alpha=0.25, lw=0)
b.set(ylabel="Sensitivity")
b.legend(fontsize=8)
for product, name, color in zip(integrands(wl, r), XYZ_NAMES, XYZ_COLOURS):
    c.plot(wl, product, color=color, lw=0.8)
    c.fill_between(wl, product, color=color, alpha=0.25, lw=0,
                   label=f"area = {name} = {product.sum():.3f}")
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

illuminants = (
    ("D75", "North sky daylight", 7504, "#ebecff"),
    ("A", "Incandescent", 2856, "#ffb264"),
    ("FL2", "Cool white fluorescent", 4230, "#ffd8b0"),
    ("LED-B5", "Cool white LED", 6598, "#fdf8ff"),
)
observer = cmfs(wl)
reflected_spectra = []
incident_spectra = []
for name, title, temperature, color in illuminants:
    illuminant = colour.SDS_ILLUMINANTS[name].copy().interpolate(colour.SpectralShape(300, 780, 1))
    power = np.interp(wl, illuminant.wavelengths, illuminant.values)
    power *= 100 / np.sum(power * observer[1])
    incident_spectra.append(power)
    reflected_spectra.append(power * R[0, FULL] / 100)
incident_spectra = np.array(incident_spectra)
reflected_spectra = np.array(reflected_spectra)
weighted_spectra = reflected_spectra[:, None, :] * observer

fig, axes = plt.subplots(2, 2, figsize=(12, 7.5), sharex=True,
                         layout="constrained")
for ax, incident, reflected, weighted, (name, title, temperature, color) in zip(
      axes.flat, incident_spectra, reflected_spectra, weighted_spectra, illuminants):
    limits = (min(0, reflected.min(), weighted.min()) * 1.1,
          max(reflected.max(), weighted.max(), incident.max() / 100) * 1.1)
    ax.set_facecolor("#f0f0f0")
    ax.plot(wl, incident / 100, color="0.4", ls="--", lw=1,
            label="Illuminant (right axis)")
    gradient_under_curve(ax, reflected, color, label="Reflected (left axis)", linewidth=1.2)
    for product, cmf_name, channel_color in zip(weighted, CMF_NAMES, XYZ_COLOURS):
        ax.plot(wl, product, color=channel_color, lw=1, zorder=3,
                label=f"Reflected × {cmf_name}")
    ax.axvspan(wl[0], CUTOFF, color="0.5", alpha=0.08, lw=0)
    ax.axvline(CUTOFF, color="0.4", ls=":", lw=0.8)
    ax.axhline(0, color="k", lw=0.5)
    ax.set(xlim=(wl[0], wl[-1]), ylim=limits,
           title=f"{title} · {name} · {temperature} K")
    incident_axis = ax.secondary_yaxis("right", functions=(lambda value: value * 100,
                                                           lambda value: value / 100))
    if ax.get_subplotspec().is_last_col():
        incident_axis.set_ylabel("Incident power (100× left scale)")
    if ax.get_subplotspec().is_first_col():
        ax.set_ylabel("Reflected power (relative units)")
    ax.text(0.02, 0.76, f"< {CUTOFF:g} nm", transform=ax.transAxes,
            ha="left", va="top", fontsize=8, color="0.35")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="lower center",
           bbox_to_anchor=(0.5, 1.0), ncol=5, fontsize=8, frameon=False)
fig.supxlabel("Wavelength (nm)")
save(fig, "1_illuminants_reflected.png")
