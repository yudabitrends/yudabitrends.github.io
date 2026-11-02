"""Figures for Chapter 6, Negentropy, Mutual Information and Likelihood."""
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import fftconvolve

from figstyle import figure, save, clean_axes, ACCENT, RED, GREEN, LIGHT

R3 = np.sqrt(3.0)
B0 = 1 / np.sqrt(2.0)                    # Laplace scale for unit variance
H = 0.002                                # grid step for densities
U = np.arange(-24.0, 24.0 + H / 2, H)
H_GAUSS = 0.5 * np.log(2 * np.pi * np.e)  # entropy of N(0, 1)
EG_NU = 0.37456720749143807              # E log cosh(nu), nu ~ N(0, 1)
K_G = 79.01556728333674                  # 1 / (2 c_G^2) for G = log cosh


def F_unif(x):
    return np.clip((x + R3) / (2 * R3), 0.0, 1.0)


def F_lap(x):
    return np.where(x < 0, 0.5 * np.exp(np.minimum(x, 0) / B0), 1 - 0.5 * np.exp(-np.maximum(x, 0) / B0))


def F_mix(x):
    """5/7 uniform + 2/7 Laplace (both unit variance): unit variance, kurtosis 0."""
    return 5 / 7 * F_unif(x) + 2 / 7 * F_lap(x)


def cell_density(F, a):
    """Density of a*s on the grid U, averaged over each grid cell (from the CDF F of s)."""
    return (F((U + H / 2) / a) - F((U - H / 2) / a)) / H


def logcosh(x):
    return np.abs(x) + np.log1p(np.exp(-2 * np.abs(x))) - np.log(2)


def density_of_sum(F1, a, F2, b):
    """Density of a*s1 + b*s2 on the grid U, by numerical convolution."""
    a, b = abs(a), abs(b)
    if a < 1e-12:
        return cell_density(F2, b)
    if b < 1e-12:
        return cell_density(F1, a)
    p = fftconvolve(cell_density(F1, a), cell_density(F2, b), mode="same") * H
    p = np.maximum(p, 0.0)
    return p / (p.sum() * H)


def contrasts(p):
    """Exact negentropy and its log cosh approximation for a density on the grid U."""
    plogp = np.where(p > 0, p * np.log(np.where(p > 0, p, 1.0)), 0.0)
    J = H_GAUSS + plogp.sum() * H
    jg = K_G * (np.sum(logcosh(U) * p) * H - EG_NU) ** 2
    return np.array([J, jg])


@figure
def ch06_negentropy():
    """Sum of marginal negentropies along the circle: exact value and two approximations."""
    theta = np.linspace(0, np.pi / 2, 91)
    cases = [("(a)  $\\kappa_1=-1.2,\\ \\kappa_2=3$", F_unif, F_lap, -1.2, 3.0),
             ("(b)  $\\kappa_1=\\kappa_2=0$", F_mix, F_mix, 0.0, 0.0)]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.45))
    for ax, (title, F1, F2, k1, k2) in zip(axes, cases):
        c, s = np.cos(theta), np.sin(theta)
        exact = np.array([contrasts(density_of_sum(F1, ci, F2, si)) + contrasts(density_of_sum(F1, si, F2, ci))
                          for ci, si in zip(c, s)])
        cum = ((k1 * c ** 4 + k2 * s ** 4) ** 2 + (k1 * s ** 4 + k2 * c ** 4) ** 2) / 48   # kurt(y_i) exactly
        cum = cum / cum[0] if cum[0] > 0 else cum
        ax.plot(theta, exact[:, 0] / exact[0, 0], color=ACCENT, lw=1.6, label="$\\sum_i J(y_i)$")
        ax.plot(theta, cum, color=RED, lw=1.3, ls=(0, (5, 2.5)),
                label="$\\sum_i \\frac{1}{48}\\operatorname{kurt}(y_i)^2$")
        ax.plot(theta, exact[:, 1] / exact[0, 1], color=GREEN, lw=1.3, ls=(0, (1.2, 1.8)),
                label="$\\sum_i k_G\\,[\\mathrm{E}\\,G(y_i)-\\mathrm{E}\\,G(\\nu)]^2$")
        ax.set_title(title, pad=4)
        ax.set_xlim(0, np.pi / 2)
        ax.set_ylim(-0.04, 1.08)
        ax.set_xticks([0, np.pi / 8, np.pi / 4, 3 * np.pi / 8, np.pi / 2])
        ax.set_xticklabels(["$0$", "$\\pi/8$", "$\\pi/4$", "$3\\pi/8$", "$\\pi/2$"])
        ax.set_yticks([0, 0.5, 1])
        ax.set_xlabel("$\\theta$", labelpad=1)
        ax.axhline(0, color=LIGHT, lw=0.6, zorder=0)
        clean_axes(ax)
    axes[1].legend(loc="upper center", frameon=False, fontsize=9, handlelength=2.4,
                   bbox_to_anchor=(0.5, 0.93))
    fig.subplots_adjust(wspace=0.22)
    save(fig, "ch06-negentropy")
