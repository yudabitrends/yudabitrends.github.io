"""Figures for Chapter 1, The ICA Problem."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, whiten, kurt, style_scatter, ACCENT, RED, GREEN, GRAY, LIGHT


@figure
def ch01_signals():
    """Two sources and two microphone mixtures as time series."""
    t = np.linspace(0, 1, 600)
    s1 = np.sin(2 * np.pi * 5 * t)
    s2 = 2 * ((7 * t) % 1) - 1          # sawtooth
    A = np.array([[0.8, 0.45], [0.35, 0.9]])
    x = A @ np.vstack([s1, s2])
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 2.7), sharex=True)
    rows = [(s1, "$s_1(t)$", ACCENT), (s2, "$s_2(t)$", ACCENT)]
    for i, (sig, lab, col) in enumerate(rows):
        ax = axes[i, 0]
        ax.plot(t, sig, color=col, lw=1.1)
        ax.set_ylabel(lab, rotation=0, ha="right", va="center")
    for i in range(2):
        ax = axes[i, 1]
        ax.plot(t, x[i], color=RED, lw=1.1)
        ax.set_ylabel(f"$x_{i + 1}(t)$", rotation=0, ha="right", va="center")
    axes[0, 0].set_title("$\\mathbf{s}(t)$", pad=4)
    axes[0, 1].set_title("$\\mathbf{x}(t)=\\mathbf{A}\\,\\mathbf{s}(t)$", pad=4)
    for ax in axes.ravel():
        ax.set_yticks([])
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
    for ax in axes[1]:
        ax.set_xlabel("$t$")
        ax.set_xticks([0, 0.5, 1])
    fig.subplots_adjust(wspace=0.35, hspace=0.25)
    save(fig, "ch01-signals")


@figure
def ch01_scatter():
    """Sources, mixtures, PCA (whitened) and ICA solutions as scatter plots."""
    rng = np.random.default_rng(7)
    T = 1500
    S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T), rng.uniform(-np.sqrt(3), np.sqrt(3), T)])
    A = np.array([[1.0, 0.7], [0.25, 1.0]])
    X = A @ S
    Z, V = whiten(X)
    # ICA: rotation maximizing |kurtosis| of the first output (search over [0, pi))
    angles = np.linspace(0, np.pi, 721, endpoint=False)
    k = [abs(kurt(np.cos(a) * Z[0] + np.sin(a) * Z[1])) for a in angles]
    a = angles[int(np.argmax(k))]
    U = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])
    Y = U @ Z
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.05))
    data = [
        (S, "(a)  $\\mathbf{s}$", ACCENT, ("$s_1$", "$s_2$")),
        (X, "(b)  $\\mathbf{x}=\\mathbf{A}\\mathbf{s}$", RED, ("$x_1$", "$x_2$")),
        (Z, "(c)  $\\mathbf{z}=\\mathbf{V}\\mathbf{x}$", GRAY, ("$z_1$", "$z_2$")),
        (Y, "(d)  $\\mathbf{y}=\\mathbf{U}\\mathbf{z}$", GREEN, ("$y_1$", "$y_2$")),
    ]
    for ax, (D, title, col, (lx, ly)) in zip(axes, data):
        ax.scatter(D[0], D[1], s=1.2, color=col, alpha=0.55, linewidths=0, rasterized=True)
        style_scatter(ax, title, lim=3.0)
        ax.set_xticks([-2, 0, 2])
        ax.set_yticks([-2, 0, 2])
        ax.set_xlabel(lx, labelpad=1)
        ax.set_ylabel(ly, labelpad=0)
    # columns of the whitened mixing matrix in panel (c)
    At = V @ A
    for j in range(2):
        v = At[:, j] / np.linalg.norm(At[:, j]) * 2.6
        axes[2].annotate("", xy=(v[0], v[1]), xytext=(0, 0),
                         arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.1, mutation_scale=7))
    fig.subplots_adjust(wspace=0.55)
    save(fig, "ch01-scatter")


