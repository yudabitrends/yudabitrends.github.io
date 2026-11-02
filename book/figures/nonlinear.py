"""Figures for Chapter 13, Nonlinear ICA."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, style_scatter, ACCENT, RED, GREEN, GRAY


def _darmois(x1, x2):
    """Darmois map for x = (s1, s1 + s2), s1, s2 ~ U(0, 1): x2 first, then x1 given x2."""
    y1 = np.where(x2 <= 1, x2 ** 2 / 2, 1 - (2 - x2) ** 2 / 2)
    lo, hi = np.maximum(0, x2 - 1), np.minimum(1, x2)
    y2 = (x1 - lo) / (hi - lo)
    return y1, y2


@figure
def ch13_darmois():
    """A linear mixture and its Darmois transform, with the source coordinate lines."""
    rng = np.random.default_rng(3)
    T = 1500
    s1, s2 = rng.uniform(0, 1, T), rng.uniform(0, 1, T)
    x1, x2 = s1, s1 + s2
    y1, y2 = _darmois(x1, x2)
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.9))
    axes[0].scatter(x1, x2, s=1.4, color=GRAY, alpha=0.5, linewidths=0, rasterized=True)
    axes[1].scatter(y1, y2, s=1.4, color=GRAY, alpha=0.5, linewidths=0, rasterized=True)
    t = np.linspace(1e-4, 1 - 1e-4, 400)
    for c in (0.2, 0.4, 0.6, 0.8):
        # level line s1 = c (s2 varies) and s2 = c (s1 varies)
        for (a1, a2, col, ls) in ((np.full_like(t, c), t, ACCENT, "-"), (t, np.full_like(t, c), RED, "--")):
            xx1, xx2 = a1, a1 + a2
            axes[0].plot(xx1, xx2, color=col, lw=1.1, ls=ls)
            yy1, yy2 = _darmois(xx1, xx2)
            axes[1].plot(yy1, yy2, color=col, lw=1.1, ls=ls)
    style_scatter(axes[0], "(a)  $\\mathbf{x}$")
    style_scatter(axes[1], "(b)  $\\mathbf{y}=\\mathbf{g}(\\mathbf{x})$")
    axes[0].set_xlim(-0.05, 1.05)
    axes[0].set_ylim(-0.05, 2.05)
    axes[1].set_xlim(-0.03, 1.03)
    axes[1].set_ylim(-0.03, 1.03)
    axes[0].set_xticks([0, 1])
    axes[0].set_yticks([0, 1, 2])
    axes[1].set_xticks([0, 1])
    axes[1].set_yticks([0, 1])
    axes[0].set_xlabel("$x_1$", labelpad=1)
    axes[0].set_ylabel("$x_2$", labelpad=0)
    axes[1].set_xlabel("$y_1$", labelpad=1)
    axes[1].set_ylabel("$y_2$", labelpad=0)
    fig.subplots_adjust(wspace=0.35)
    save(fig, "ch13-darmois")


@figure
def ch13_swirl():
    """m(z) = R(beta |z|^2) z maps N(0, I) onto itself while mixing the coordinates."""
    rng = np.random.default_rng(4)
    T = 2000
    z = rng.standard_normal((2, T))

    def swirl(v1, v2, beta=0.4):
        a = beta * (v1 ** 2 + v2 ** 2)
        return np.cos(a) * v1 - np.sin(a) * v2, np.sin(a) * v1 + np.cos(a) * v2

    m1, m2 = swirl(z[0], z[1])
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.9))
    axes[0].scatter(z[0], z[1], s=1.4, color=GRAY, alpha=0.45, linewidths=0, rasterized=True)
    axes[1].scatter(m1, m2, s=1.4, color=GRAY, alpha=0.45, linewidths=0, rasterized=True)
    t = np.linspace(-3, 3, 600)
    for c in (-2, -1, 0, 1, 2):
        for (a1, a2, col, ls) in ((np.full_like(t, c), t, ACCENT, "-"), (t, np.full_like(t, c), RED, "--")):
            axes[0].plot(a1, a2, color=col, lw=0.9, ls=ls)
            b1, b2 = swirl(a1, a2)
            axes[1].plot(b1, b2, color=col, lw=0.9, ls=ls)
    style_scatter(axes[0], "(a)  $\\mathbf{z}$", lim=3.0)
    style_scatter(axes[1], "(b)  $\\mathbf{m}(\\mathbf{z})$", lim=3.0)
    for ax, (lx, ly) in zip(axes, (("$z_1$", "$z_2$"), ("$m_1$", "$m_2$"))):
        ax.set_xticks([-2, 0, 2])
        ax.set_yticks([-2, 0, 2])
        ax.set_xlabel(lx, labelpad=1)
        ax.set_ylabel(ly, labelpad=0)
    fig.subplots_adjust(wspace=0.35)
    save(fig, "ch13-swirl")
