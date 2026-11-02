"""Figures for Chapter 9, Tensor and Second-Order Methods: JADE and SOBI."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, clean_axes, ACCENT, RED, GREEN, GRAY, LIGHT


def _whiten(X):
    X = X - X.mean(axis=1, keepdims=True)
    d, E = np.linalg.eigh(np.cov(X))
    V = E @ np.diag(d ** -0.5) @ E.T
    return V @ X


def _sources(rng, T):
    """The three Gaussian sources of the chapter: AR(1) a=0.5, MA(1) theta=1, AR(1) a=-0.8."""
    e = rng.standard_normal((3, T + 1))
    s1 = np.zeros(T)
    s3 = np.zeros(T)
    for t in range(1, T):
        s1[t] = 0.5 * s1[t - 1] + e[0, t]
        s3[t] = -0.8 * s3[t - 1] + e[2, t]
    s2 = e[1, 1:] + e[1, :-1]
    S = np.vstack([s1, s2, s3])
    return S / S.std(axis=1, keepdims=True)


@figure
def ch09_sobi():
    """(a) Autocorrelations of the three sources. (b) Joint-diagonalization criterion of one Jacobi
    pair as a function of the angle, with the closed-form minimizer."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))

    ax = axes[0]
    tau = np.arange(0, 9)
    rho = [0.5 ** tau, np.where(tau == 0, 1.0, np.where(tau == 1, 0.5, 0.0)), (-0.8) ** tau]
    styles = [(ACCENT, "o", "-", "$s_1$"), (GREEN, "s", "--", "$s_2$"), (RED, "^", ":", "$s_3$")]
    ax.axhline(0, color=LIGHT, lw=0.8, zorder=0)
    ax.axvline(1, color=GRAY, lw=0.7, ls=":", zorder=0)
    for r, (col, mk, ls, lab) in zip(rho, styles):
        ax.plot(tau, r, color=col, marker=mk, ls=ls, lw=1.1, ms=4.2, mfc="white", label=lab)
    ax.set_xlabel("$\\tau$")
    ax.set_ylabel("$\\rho_i(\\tau)$")
    ax.set_xticks(range(0, 9, 2))
    ax.set_ylim(-1.05, 1.1)
    ax.set_title("(a)", pad=4)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    clean_axes(ax)

    ax = axes[1]
    rng = np.random.default_rng(2)
    T = 20000
    S = _sources(rng, T)
    A = rng.standard_normal((3, 3))
    Z = _whiten(A @ S)
    Cs = []
    for t in range(1, 6):
        C = Z[:, :-t] @ Z[:, t:].T / (T - t)
        Cs.append((C + C.T) / 2)
    p, q = 0, 1

    def crit(theta):
        c, s = np.cos(theta), np.sin(theta)
        R = np.eye(3)
        R[p, p] = R[q, q] = c
        R[p, q], R[q, p] = -s, s
        tot = 0.0
        for C in Cs:
            M = R.T @ C @ R
            tot += (M ** 2).sum() - (np.diag(M) ** 2).sum()
        return tot

    th = np.linspace(-np.pi / 4, np.pi / 4, 721)
    vals = np.array([crit(t) for t in th])
    h1 = np.array([C[p, p] - C[q, q] for C in Cs])
    h2 = np.array([2 * C[p, q] for C in Cs])
    th_star = 0.25 * np.arctan2(2 * h1 @ h2, h1 @ h1 - h2 @ h2)
    ax.plot(th, vals, color=ACCENT, lw=1.4)
    ax.plot([th_star], [crit(th_star)], marker="o", color=RED, ms=5.5, zorder=3)
    ax.annotate("$\\theta^\\star$", xy=(th_star, crit(th_star)), xytext=(th_star - 0.3, crit(th_star) + 0.08 * (vals.max() - vals.min())),
                color=RED, fontsize=10, arrowprops=dict(arrowstyle="-", color=RED, lw=0.7))
    ax.set_xticks([-np.pi / 4, 0, np.pi / 4])
    ax.set_xticklabels(["$-\\pi/4$", "$0$", "$\\pi/4$"])
    ax.set_xlabel("$\\theta$")
    ax.set_ylabel("$\\mathcal{C}(\\theta)$")
    ax.set_title("(b)", pad=4)
    clean_axes(ax)
    fig.subplots_adjust(wspace=0.32)
    save(fig, "ch09-sobi")
