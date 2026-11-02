"""Figures for Chapter 7, Natural Gradient, Infomax and Stability."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, clean_axes, ACCENT, RED, GRAY


def _err(P):
    """Largest relative interference max_{i != j} |p_ij / p_ii| of a global matrix close to the identity."""
    D = np.abs(P / np.diag(P)[:, None])
    np.fill_diagonal(D, 0.0)
    return D.max()


def _rot(a):
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


@figure
def ch07_dynamics():
    """(a) Equivariance: natural vs ordinary gradient for three mixing matrices with the same P(0).
    (b) Stability: matched vs mismatched nonlinearities started next to the separating point."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))

    # (a) Laplace sources, phi = tanh, same initial global matrix P0 for every A
    rng = np.random.default_rng(3)
    T = 20000
    S = rng.laplace(0, 1 / np.sqrt(2), (2, T))
    P0 = np.array([[1.0, 0.5], [-0.4, 1.0]])
    iters, mu = 150, 0.2
    ax = axes[0]
    shades = {1: "#e08a87", 10: RED, 100: "#6e2422"}
    for c in (1, 10, 100):
        A = _rot(0.3) @ np.diag([1.0, 1.0 / c]) @ _rot(1.1)
        X = A @ S
        for kind in ("natural", "ordinary"):
            W = P0 @ np.linalg.inv(A)
            e = [_err(P0)]
            for _ in range(iters):
                Y = W @ X
                if kind == "natural":
                    W = W + mu * (np.eye(2) - np.tanh(Y) @ Y.T / T) @ W
                else:
                    W = W + mu * (np.linalg.inv(W).T - np.tanh(Y) @ X.T / T)
                e.append(_err(W @ A))
            if kind == "natural":
                ax.semilogy(e, color=ACCENT, lw=1.6 if c == 1 else 0.0,
                            marker=None if c == 1 else ("o" if c == 10 else "s"),
                            markevery=(10 if c == 10 else 15, 25), ms=3.2, mfc="none", mec=ACCENT)
            else:
                ax.semilogy(e, color=shades[c], lw=1.2, ls="--")
    ax.text(iters + 3, 0.0105, "$\\nabla,\\ c=1$", color=shades[1], fontsize=8.5, va="center")
    ax.text(70, 0.62, "$\\nabla,\\ c=10,\\,100$", color=RED, fontsize=8.5, va="center")
    ax.text(88, 0.0058, "$\\tilde\\nabla,\\ c=1,\\,10,\\,100$", color=ACCENT, fontsize=8.5, va="center")
    ax.set_xlim(0, iters + 35)
    ax.set_ylim(2e-3, 1.5)
    ax.set_xlabel("$k$")
    ax.set_ylabel("$\\max_{i\\neq j}\\,|p_{ij}/p_{ii}|$")
    ax.set_title("(a)", pad=4)
    clean_axes(ax)

    # (b) start next to the separating point; matched vs mismatched nonlinearity
    ax = axes[1]
    rng = np.random.default_rng(5)
    T = 20000
    srcs = {"sub": rng.uniform(-np.sqrt(3), np.sqrt(3), (2, T)),
            "super": rng.laplace(0, 1 / np.sqrt(2), (2, T))}
    phis = {"tanh": np.tanh, "cube": lambda y: y ** 3}
    A = np.array([[1.0, 0.6], [0.4, 1.0]])
    iters = 300
    curves = [("sub", "cube", ACCENT, "-", "$y^3,\\ \\kappa<0$"),
              ("super", "tanh", ACCENT, "--", "$\\tanh,\\ \\kappa>0$"),
              ("sub", "tanh", RED, "-", "$\\tanh,\\ \\kappa<0$"),
              ("super", "cube", RED, "--", "$y^3,\\ \\kappa>0$")]
    for src, ph, col, ls, lab in curves:
        S = srcs[src]
        phi = phis[ph]
        # separating point: W = D A^{-1}, with D found by the diagonal part of the update
        W = np.linalg.inv(A)
        for _ in range(500):
            Y = W @ A @ S
            W = W + 0.1 * np.diag(1 - np.mean(phi(Y) * Y, axis=1)) @ W
        W = (np.eye(2) + 0.01 * np.array([[0.0, 1.0], [-1.0, 0.0]])) @ W   # small perturbation
        X = A @ S
        e = [_err(W @ A)]
        for _ in range(iters):
            Y = W @ X
            W = W + 0.1 * (np.eye(2) - phi(Y) @ Y.T / T) @ W
            e.append(_err(W @ A))
        ax.semilogy(e, color=col, ls=ls, lw=1.3, label=lab)
    ax.set_ylim(1e-3, 30.0)
    ax.set_yticks([1e-3, 1e-2, 1e-1, 1])
    ax.set_xlabel("$k$")
    ax.set_title("(b)", pad=4)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=2, columnspacing=1.2, handlelength=2.2)
    clean_axes(ax)
    fig.subplots_adjust(wspace=0.32)
    save(fig, "ch07-dynamics")
