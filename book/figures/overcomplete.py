"""Figures for Chapter 12, Overcomplete ICA and Sparse Component Analysis."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, clean_axes, style_scatter, ACCENT, RED, GREEN, GRAY, LIGHT


@figure
def ch12_sca():
    """Two mixtures of three sparse sources: scatter along the columns and the histogram of directions."""
    rng = np.random.default_rng(0)                     # same data as the script in Section 12.5
    n, T = 3, 4000
    S = rng.laplace(size=(n, T)) * (rng.random((n, T)) < 0.2)
    theta = np.deg2rad([15.0, 70.0, 125.0])
    A = np.vstack([np.cos(theta), np.sin(theta)])
    X = A @ S + 0.01 * rng.normal(size=(2, T))
    keep = np.linalg.norm(X, axis=0) > 0.2
    ang = np.arctan2(X[1, keep], X[0, keep]) % np.pi
    h, edges = np.histogram(ang, bins=180, range=(0, np.pi))
    hs = np.convolve(np.r_[h[-2:], h, h[:2]], np.ones(5) / 5, "valid")
    peaks = [i for i in range(180) if hs[i] >= hs[i - 1] and hs[i] > hs[(i + 1) % 180]]
    top = sorted(peaks, key=lambda i: -hs[i])[:n]
    th_hat = np.sort(edges[top] + np.pi / 360)
    print("  estimated angles:", np.round(np.rad2deg(th_hat), 1))

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1, 1.35]})
    ax = axes[0]
    ax.scatter(X[0], X[1], s=1.5, color=RED, alpha=0.5, linewidths=0, rasterized=True)
    for th in theta:
        ax.plot([-6 * np.cos(th), 6 * np.cos(th)], [-6 * np.sin(th), 6 * np.sin(th)],
                color=ACCENT, lw=0.8, ls="--", zorder=0)
    style_scatter(ax, "(a)", lim=4.0)
    ax.set_xticks([-4, -2, 0, 2, 4])
    ax.set_yticks([-4, -2, 0, 2, 4])
    ax.set_xlabel("$x_1$", labelpad=1)
    ax.set_ylabel("$x_2$", labelpad=0)

    ax = axes[1]
    centers = np.rad2deg(edges[:-1] + np.pi / 360)
    ax.bar(centers, h, width=1.0, color=LIGHT, edgecolor="none")
    ax.plot(centers, hs, color=RED, lw=1.1)
    for th in np.rad2deg(theta):
        ax.axvline(th, color=ACCENT, lw=0.8, ls="--")
    ax.plot(np.rad2deg(th_hat), hs[top][np.argsort(edges[top])], "o", color=GREEN, ms=4)
    ax.set_xlim(0, 180)
    ax.set_xticks([0, 45, 90, 135, 180])
    ax.set_xticklabels(["0°", "45°", "90°", "135°", "180°"])
    ax.set_xlabel(r"$\theta$")
    ax.set_title("(b)", pad=4)
    clean_axes(ax)
    fig.subplots_adjust(wspace=0.28)
    with plt.rc_context({"svg.hashsalt": "ch12-sca"}):   # stable element ids
        save(fig, "ch12-sca")
