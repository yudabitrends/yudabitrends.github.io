"""Figures for Chapter 5, Non-Gaussianity and Kurtosis."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, clean_axes, ACCENT, RED, GRAY, LIGHT


@figure
def ch05_landscape():
    """|kurt(w^T z)| along the unit circle for two whitened sources: theory and sample estimate."""
    rng = np.random.default_rng(5)
    T = 5000
    th0 = np.pi / 6                                   # source directions: th0 and th0 + pi/2
    R = np.array([[np.cos(th0), -np.sin(th0)], [np.sin(th0), np.cos(th0)]])
    theta = np.linspace(0, np.pi, 721)
    Wt = np.vstack([np.cos(theta), np.sin(theta)])    # columns: w_theta
    unif = lambda: rng.uniform(-np.sqrt(3), np.sqrt(3), T)
    cases = [
        ("(a)", -1.2, -2.0, unif, lambda: rng.choice([-1.0, 1.0], T)),
        ("(b)", -1.2, 3.0, unif, lambda: rng.laplace(0.0, 1 / np.sqrt(2), T)),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.35))
    for ax, (lab, k1, k2, d1, d2) in zip(axes, cases):
        S = np.vstack([d1(), d2()])
        S = (S - S.mean(axis=1, keepdims=True)) / S.std(axis=1, keepdims=True)
        Y = Wt.T @ (R @ S)                            # projections w_theta^T z
        emp = np.mean(Y ** 4, axis=1) - 3 * np.mean(Y ** 2, axis=1) ** 2
        c, s = np.cos(theta - th0), np.sin(theta - th0)
        F = k1 * c ** 4 + k2 * s ** 4                 # kurt = sum_i q_i^4 kappa_i
        for t in (th0, th0 + np.pi / 2):
            ax.axvline(t, color=GRAY, lw=0.8, ls=(0, (4, 3)), zorder=1)
        ax.plot(theta, np.abs(F), color=ACCENT, lw=1.5, zorder=3)
        ax.plot(theta[::10], np.abs(emp[::10]), "o", ms=2.3, color=RED, mec="none", zorder=4)
        if k1 * k2 > 0:                               # interior critical points: minima of |kurt|
            for sgn in (1, -1):
                tc = (th0 + sgn * np.arctan(np.sqrt(k1 / k2))) % np.pi
                ax.plot([tc], [abs(1 / (1 / k1 + 1 / k2))], "o", ms=5.5, mfc="white", mec=ACCENT,
                        mew=1.2, zorder=5, clip_on=False)
        ax.set_title(f"{lab}  $\\kappa_1={k1:g},\\ \\kappa_2={k2:g}$", pad=4)
        ax.set_xlim(0, np.pi)
        ax.set_ylim(0, 4.0)
        ax.set_xticks([0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi])
        ax.set_xticklabels(["$0$", "$\\pi/4$", "$\\pi/2$", "$3\\pi/4$", "$\\pi$"])
        ax.set_xlabel("$\\theta$", labelpad=1)
        ax.axhline(0, color=LIGHT, lw=0.6, zorder=0)
        clean_axes(ax)
    axes[0].set_ylabel("$|\\operatorname{kurt}(\\mathbf{w}_\\theta^\\top\\mathbf{z})|$")
    fig.subplots_adjust(wspace=0.28)
    save(fig, "ch05-landscape")
