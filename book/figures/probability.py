"""Figures for Chapter 2, Independence, Cumulants and Entropy."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, clean_axes, ACCENT, RED, GRAY, LIGHT


@figure
def ch02_densities():
    """Unit-variance uniform, Gaussian and Laplace densities, on linear and log scales."""
    u = np.linspace(-4.0, 4.0, 1601)
    a = np.sqrt(3.0)                     # uniform on [-a, a] has variance 1
    b = 1.0 / np.sqrt(2.0)               # Laplace with scale b has variance 1
    unif = np.where(np.abs(u) <= a, 1.0 / (2 * a), np.nan)
    gauss = np.exp(-u ** 2 / 2) / np.sqrt(2 * np.pi)
    lap = np.exp(-np.abs(u) / b) / (2 * b)
    curves = [
        (unif, RED, "-", "$\\kappa=-1.2$"),
        (gauss, GRAY, "--", "$\\kappa=0$"),
        (lap, ACCENT, "-", "$\\kappa=3$"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.35))
    for p, col, ls, lab in curves:
        axes[0].plot(u, p, color=col, ls=ls, lw=1.3, label=lab)
        axes[1].plot(u, np.log(p), color=col, ls=ls, lw=1.3)
    # vertical edges of the uniform density
    for s in (-a, a):
        axes[0].plot([s, s], [0, 1 / (2 * a)], color=RED, lw=1.3)
    axes[0].set_ylim(0, 0.75)
    axes[0].set_ylabel("$p(s)$")
    axes[0].legend(frameon=False, fontsize=9.5, loc="upper right", handlelength=1.8)
    axes[1].set_ylim(-7.5, 0.2)
    axes[1].set_ylabel("$\\log p(s)$")
    for ax, title in zip(axes, ("(a)", "(b)")):
        ax.set_xlim(-4, 4)
        ax.set_xticks([-4, -2, 0, 2, 4])
        ax.set_xlabel("$s$", labelpad=1)
        ax.set_title(title, pad=4)
        ax.axvline(0, color=LIGHT, lw=0.6, zorder=0)
        clean_axes(ax)
    fig.subplots_adjust(wspace=0.32)
    save(fig, "ch02-densities")
