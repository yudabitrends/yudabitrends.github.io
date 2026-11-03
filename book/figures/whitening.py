"""Figures for Chapter 3, Whitening and the Geometry of ICA."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, style_scatter, ACCENT, RED, GREEN, GRAY


def _arrow(ax, v, color, lw=1.2):
    ax.annotate("", xy=(v[0], v[1]), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=8))


@figure
def ch03_whitening():
    """A mixture of two uniform sources and three whitened versions of it (PCA, ZCA, Cholesky)."""
    rng = np.random.default_rng(3)
    T = 1500
    S = rng.uniform(-np.sqrt(3), np.sqrt(3), (2, T))       # unit-variance sources
    A = np.array([[1.0, 0.6], [0.4, 1.0]])
    X = A @ S
    X = X - X.mean(axis=1, keepdims=True)
    C = X @ X.T / T                                       # sample covariance
    d, E = np.linalg.eigh(C)
    d, E = d[::-1], E[:, ::-1].copy()                     # decreasing eigenvalues
    if E[:, 0].sum() < 0:                                 # first axis points up and right
        E[:, 0] = -E[:, 0]
    if np.linalg.det(E) < 0:                              # make E a rotation
        E[:, 1] = -E[:, 1]
    V_pca = np.diag(d ** -0.5) @ E.T
    V_zca = E @ np.diag(d ** -0.5) @ E.T
    V_chol = np.linalg.inv(np.linalg.cholesky(C))
    panels = [
        (X, None, "(a)  $\\mathbf{x}$", RED),
        (V_pca @ X, V_pca, "(b)  $\\mathbf{\\Lambda}^{-1/2}\\mathbf{E}^{\\top}\\mathbf{x}$", GRAY),
        (V_zca @ X, V_zca, "(c)  $\\mathbf{C}^{-1/2}\\mathbf{x}$", GRAY),
        (V_chol @ X, V_chol, "(d)  $\\mathbf{L}^{-1}\\mathbf{x}$", GRAY),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.1))
    for ax, (D, V, title, col) in zip(axes, panels):
        alpha = 0.35 if V is None else 0.5
        ax.scatter(D[0], D[1], s=1.2, color=col, alpha=alpha, linewidths=0, rasterized=True)
        style_scatter(ax, title, lim=3.0)
        ax.set_xticks([-2, 0, 2])
        ax.set_yticks([-2, 0, 2])
        if V is None:
            # principal axes of the covariance: eigenvectors scaled by 1.6 standard deviations
            for k in range(2):
                _arrow(ax, 1.6 * np.sqrt(d[k]) * E[:, k], ACCENT, lw=1.5)
        else:
            At = V @ A  # approximately orthogonal: finite-sample whitening
            for k in range(2):
                _arrow(ax, 2.2 * At[:, k] / np.linalg.norm(At[:, k]), GREEN)
    axes[0].set_xlabel("$x_1$", labelpad=1)
    axes[0].set_ylabel("$x_2$", labelpad=0)
    for ax in axes[1:]:
        ax.set_xlabel("$z_1$", labelpad=1)
        ax.set_ylabel("$z_2$", labelpad=0)
    fig.subplots_adjust(wspace=0.55)
    save(fig, "ch03-whitening")
