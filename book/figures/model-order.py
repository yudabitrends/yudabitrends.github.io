"""Figures for Chapter 11, Noise, Model Order and Reliability."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, FuncFormatter

from figstyle import figure, save, clean_axes, ACCENT, RED, GREEN, GRAY, LIGHT


def _ar1(E, phi):
    Y = np.empty_like(E)
    Y[:, 0] = E[:, 0]
    for t in range(1, E.shape[1]):
        Y[:, t] = phi * Y[:, t - 1] + np.sqrt(1 - phi ** 2) * E[:, t]
    return Y


def _mdl_curve(X):
    m, T = X.shape
    ell = np.sort(np.linalg.eigvalsh(np.cov(X)))[::-1]
    out = []
    for k in range(m):
        tail = ell[k:]
        loglr = (m - k) * (np.mean(np.log(tail)) - np.log(np.mean(tail)))
        p = m * k - k * (k - 1) / 2 + 1
        out.append(-T / 2 * loglr + p / 2 * np.log(T))
    return ell, np.array(out)


@figure
def ch11_order():
    """Sample eigenvalues and MDL curves for independent and AR(1)-dependent samples."""
    rng = np.random.default_rng(1)
    m, n, T = 30, 8, 5000
    A = rng.normal(size=(m, n))
    S = rng.laplace(0, 1 / np.sqrt(2), (n, T))
    N = rng.normal(size=(m, T))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
    ks = np.arange(1, m + 1)
    for phi, col, mk in [(0.0, ACCENT, "o"), (0.9, RED, "s")]:
        X = A @ _ar1(S, phi) + _ar1(N, phi)
        ell, mdl = _mdl_curve(X)
        axes[0].plot(ks, ell, mk, color=col, ms=3.5, label=f"$\\phi={phi:g}$")
        k = np.arange(m)
        sel = k >= 6
        axes[1].plot(k[sel], mdl[sel] - mdl.min(), "-", marker=mk, color=col, ms=3, lw=1.0)
        kmin = int(np.argmin(mdl))
        axes[1].plot([kmin], [0], mk, color=col, ms=8, mfc="none", mew=1.4)
        print(f"  phi={phi}: MDL order {kmin}, noise eigenvalues {ell[n:].min():.2f}-{ell[n:].max():.2f}")
    axes[0].set_yscale("log")
    axes[0].yaxis.set_major_locator(FixedLocator([0.5, 1, 2, 5, 10, 20, 50]))
    axes[0].yaxis.set_minor_locator(NullLocator())
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    axes[0].axhline(1.0, color=GRAY, lw=0.8, ls=":")
    axes[0].axvline(n + 0.5, color=LIGHT, lw=0.8)
    axes[0].set_xlabel("$k$")
    axes[0].set_ylabel(r"$\ell_k$")
    axes[0].set_title("(a)", pad=4)
    axes[0].legend(frameon=False, fontsize=9)
    axes[1].set_xlabel("$k$")
    axes[1].set_ylabel(r"$\Delta\mathrm{MDL}(k)$")
    axes[1].set_ylim(-30, 600)
    axes[1].axvline(n, color=LIGHT, lw=0.8)
    axes[1].set_title("(b)", pad=4)
    for ax in axes:
        clean_axes(ax)
    fig.subplots_adjust(wspace=0.32)
    with plt.rc_context({"svg.hashsalt": "ch11-order"}):   # stable element ids
        save(fig, "ch11-order")


def _sym_fastica(Z, rng, iters=500):
    k, T = Z.shape
    W = np.linalg.qr(rng.normal(size=(k, k)))[0]
    for _ in range(iters):
        Y = W @ Z
        Wn = np.tanh(Y) @ Z.T / T - np.diag((1 - np.tanh(Y) ** 2).mean(1)) @ W
        d, E = np.linalg.eigh(Wn @ Wn.T)
        Wn = E @ np.diag(d ** -0.5) @ E.T @ Wn
        done = np.max(1 - np.abs(np.sum(Wn * W, 1))) < 1e-10
        W = Wn
        if done:
            break
    return W


def _pca_ica(X, k, seed):
    Xc = X - X.mean(1, keepdims=True)
    d, E = np.linalg.eigh(np.cov(Xc))
    idx = np.argsort(d)[::-1][:k]
    Z = np.diag(d[idx] ** -0.5) @ E[:, idx].T @ Xc
    return _sym_fastica(Z, np.random.default_rng(seed)) @ Z


@figure
def ch11_split():
    """|corr(source, component)| for too few, the right number, and too many components."""
    rng = np.random.default_rng(2)
    m, n, T = 20, 6, 3000
    S = rng.laplace(0, 1 / np.sqrt(2), (n, T))
    A = rng.normal(size=(m, n))
    a1 = A[:, 0]
    u = rng.normal(size=m)
    u -= (u @ a1) / (a1 @ a1) * a1
    u *= np.linalg.norm(a1) / np.linalg.norm(u)
    A[:, 1] = np.cos(np.deg2rad(30)) * a1 + np.sin(np.deg2rad(30)) * u   # 30 degrees from a1
    X = A @ S + 0.7 * rng.normal(size=(m, T))
    ell, mdl = _mdl_curve(X)
    print(f"  eigenvalues {np.round(ell[:8], 2)}; MDL order {int(np.argmin(mdl))}")
    orders = [5, 6, 9]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.35), gridspec_kw={"width_ratios": orders})
    for ax, k in zip(axes, orders):
        Y = _pca_ica(X, k, seed=7)
        C = np.abs(np.corrcoef(np.vstack([S, Y]))[:n, n:])
        order = sorted(range(k), key=lambda j: (C[:, j].argmax() if C[:, j].max() > 0.5 else n, -C[:, j].max()))
        C = C[:, order]
        ax.imshow(C, cmap="Blues", vmin=0, vmax=1, aspect="equal")
        for i in range(n):
            for j in range(k):
                if C[i, j] >= 0.15:
                    ax.text(j, i, f"{C[i, j]:.2f}".lstrip("0"), ha="center", va="center", fontsize=6.5,
                            color="white" if C[i, j] > 0.6 else "#1a1a1a")
        ax.set_xticks(range(k))
        ax.set_xticklabels([f"$y_{{{j + 1}}}$" for j in range(k)], fontsize=8)
        ax.set_yticks(range(n))
        ax.set_yticklabels([f"$s_{{{i + 1}}}$" for i in range(n)], fontsize=8)
        ax.tick_params(length=0)
        ax.set_title(f"$k={k}$", pad=4)
        for side in ax.spines.values():
            side.set_visible(False)
        print(f"  k={k}: best |corr| per source {np.round(C.max(1), 2)}")
    fig.subplots_adjust(wspace=0.25)
    with plt.rc_context({"svg.hashsalt": "ch11-split"}):   # stable element ids
        save(fig, "ch11-split")
