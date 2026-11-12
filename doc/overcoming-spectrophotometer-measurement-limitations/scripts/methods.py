import numpy as np
from scipy.optimize import curve_fit

from common import BASELINE_END, CUTOFF, band, cmfs, integrands, weights

GAUSS_WINDOW = 40.0


def clean(wl, R):
    """Bands at or below the flat baseline and negative values set to 0."""
    return np.clip(np.where(wl <= BASELINE_END, 0.0, R), 0.0, None)


def cleaning(wl, R, cutoff=CUTOFF):
    return integrands(wl, clean(wl, R))


def truncation(wl, R, cutoff=CUTOFF):
    R = clean(wl, R)
    R[..., : band(wl, cutoff)] = 0.0
    return integrands(wl, R)


def hold(wl, R, cutoff=CUTOFF):
    R = clean(wl, R)
    i = band(wl, cutoff)
    R[..., :i] = R[..., i : i + 1]
    return integrands(wl, R)


def gauss(x, a, mu, sigma):
    return a * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def fit_gauss(x, y, cutoff):
    p0 = (max(y.max(), 1e-6), x[np.argmax(y)], 20.0)
    bounds = ([0.0, cutoff - 60, 5.0], [np.inf, cutoff + 60, 100.0])
    return curve_fit(gauss, x, y, p0=p0, bounds=bounds)[0]


def gaussian(wl, R, cutoff=CUTOFF):
    """Truncation, then R·x̄ and R·z̄ below the cutoff replaced by Gaussians fitted on [cutoff, cutoff + 40 nm]."""
    I = truncation(wl, R, cutoff)
    R = clean(wl, R)
    i = band(wl, cutoff)
    c = cmfs(wl)
    kS = weights(wl)[1] / c[1]
    win = (wl >= wl[i] - 1e-6) & (wl <= wl[i] + GAUSS_WINDOW + 1e-6)
    for idx in np.ndindex(R.shape[:-1]):
        for ch in (0, 2):
            p = fit_gauss(wl[win], R[idx][win] * c[ch, win], wl[i])
            I[idx][ch, :i] = gauss(wl[:i], *p) * kS[:i]
    return I


METHODS = {"cleaning": cleaning, "truncation": truncation, "gaussian": gaussian, "hold": hold}
