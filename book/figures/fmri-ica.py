"""Figures for Chapter 14, Spatial ICA of fMRI."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, ACCENT, GREEN, GRAY


def synthetic_spatial_ica():
    """The synthetic example of the chapter's code listing (same seed and steps)."""
    rng = np.random.default_rng(0)
    side, T, n = 40, 150, 3
    yy, xx = np.mgrid[0:side, 0:side]

    def blob(cy, cx, r):
        return np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * r ** 2)).ravel()

    S = np.vstack([blob(12, 10, 3) + blob(12, 30, 3),
                   blob(28, 20, 5),
                   blob(22, 6, 2) + blob(32, 33, 3)])
    t = np.arange(T)
    block = ((t // 15) % 2).astype(float)
    A = np.column_stack([block, np.sin(2 * np.pi * t / 40), np.roll(block, 3)])
    X = A @ S + 0.3 * rng.standard_normal((T, side * side))
    Xc = X - X.mean(axis=1, keepdims=True)
    d, E = np.linalg.eigh(Xc @ Xc.T / Xc.shape[1])
    d, E = d[-n:], E[:, -n:]
    Z = np.diag(d ** -0.5) @ E.T @ Xc
    U = np.linalg.qr(rng.standard_normal((n, n)))[0]
    for _ in range(100):
        Y = U @ Z
        U = np.tanh(Y) @ Z.T / Z.shape[1] - np.diag((1 - np.tanh(Y) ** 2).mean(1)) @ U
        u, _, vt = np.linalg.svd(U)
        U = u @ vt
    S_hat = U @ Z
    A_hat = E @ np.diag(d ** 0.5) @ U.T
    return side, t, A, S, A_hat, S_hat


@figure
def ch14_synthetic():
    """True and estimated maps and time courses of the synthetic spatial ICA example."""
    side, t, A, S, A_hat, S_hat = synthetic_spatial_ica()
    n = S.shape[0]
    C = np.corrcoef(S_hat, S)[:n, n:]
    fig, axes = plt.subplots(3, n, figsize=(6.6, 4.9),
                             gridspec_kw={"height_ratios": [1, 1, 0.62]})
    for i in range(n):
        j = int(np.argmax(np.abs(C[:, i])))           # estimate matched to source i
        sgn = np.sign(C[j, i])
        est = sgn * S_hat[j]
        est = (est - est.mean()) / est.std()           # z-scored map
        tc = sgn * A_hat[:, j]
        for row, (img, lim) in enumerate(((S[i] / S[i].max(), 1.0), (est, np.abs(est).max()))):
            ax = axes[row, i]
            ax.imshow(img.reshape(side, side), cmap="RdBu_r", vmin=-lim, vmax=lim,
                      interpolation="nearest")
            ax.set_xticks([])
            ax.set_yticks([])
        axes[0, i].set_title(f"$i = {i + 1}$", pad=4)
        ax = axes[2, i]
        a = (A[:, i] - A[:, i].mean()) / A[:, i].std()
        b = (tc - tc.mean()) / tc.std()
        ax.plot(t, a, color=GRAY, lw=1.6, alpha=0.6)
        ax.plot(t, b, color=GREEN, lw=0.9)
        ax.set_yticks([])
        ax.set_xticks([0, 50, 100, 150])
        ax.set_xlabel("$t$", labelpad=1)
        for side_ in ("top", "right", "left"):
            ax.spines[side_].set_visible(False)
    axes[0, 0].set_ylabel("$\\mathbf{S}$", rotation=0, ha="right", va="center", labelpad=8)
    axes[1, 0].set_ylabel("$\\hat{\\mathbf{S}}$", rotation=0, ha="right", va="center", labelpad=8)
    axes[2, 0].set_ylabel("$\\mathbf{A},\\ \\hat{\\mathbf{A}}$", rotation=0, ha="right", va="center", labelpad=8)
    fig.subplots_adjust(wspace=0.12, hspace=0.18)
    save(fig, "ch14-synthetic")
