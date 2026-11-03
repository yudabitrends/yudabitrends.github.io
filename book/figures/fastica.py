"""Figures for Chapter 8, FastICA."""
import numpy as np
import matplotlib.pyplot as plt

from figstyle import figure, save, clean_axes, whiten, ACCENT, RED, GREEN, GRAY


def _rule(name, N=150):
    """Quadrature nodes and weights for a unit-variance, zero-mean source."""
    if name == "uniform":
        x, w = np.polynomial.legendre.leggauss(N)
        return np.sqrt(3) * x, w / 2
    if name == "laplace":
        b = 1 / np.sqrt(2)
        x, w = np.polynomial.laguerre.laggauss(N)
        return np.concatenate([b * x, -b * x]), np.concatenate([w, w]) / 2
    if name == "exp":  # centered exponential, skewness 2
        x, w = np.polynomial.laguerre.laggauss(N)
        return x - 1, w
    raise ValueError(name)


def _population_ratios(srcs, q0, g, dg, iters):
    """One-unit FastICA with exact (quadrature) expectations; returns |q_other / q_target| per step."""
    (x1, w1), (x2, w2) = _rule(srcs[0]), _rule(srcs[1])
    S1, S2 = np.meshgrid(x1, x2, indexing="ij")
    Wt = np.outer(w1, w2)
    q = np.array(q0, float)
    q /= np.linalg.norm(q)
    hist = [q.copy()]
    for _ in range(iters):
        y = q[0] * S1 + q[1] * S2
        u = np.array([(Wt * S1 * g(y)).sum(), (Wt * S2 * g(y)).sum()]) - (Wt * dg(y)).sum() * q
        q = u / np.linalg.norm(u)
        hist.append(q.copy())
    hist = np.array(hist)
    i = int(np.argmax(np.abs(hist[-1])))
    return np.abs(hist[:, 1 - i] / hist[:, i])


def _whiten(X):
    return whiten(X)[0]


def _sym_orth(W):
    U, s, Vt = np.linalg.svd(W, full_matrices=False)
    if s[-1] <= np.finfo(float).eps * max(W.shape) * s[0]:
        raise ValueError("FastICA update lost numerical rank.")
    return U @ Vt


@figure
def ch08_convergence():
    """(a) One-unit FastICA with exact expectations: cubic (kurtosis; tanh with symmetric sources)
    and quadratic (tanh with skewed sources) convergence. (b) Symmetric FastICA on data."""
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))

    ax = axes[0]
    # (i) kurtosis, worked example: kappa = (-1.2, 3), q0 = (0.8, 0.6); rho_{k+1} = 0.4 rho_k^3
    r = [0.8 / 0.6]
    for _ in range(5):
        r.append(0.4 * r[-1] ** 3)
    th, dth = np.tanh, lambda u: 1 - np.tanh(u) ** 2
    seqs = [
        (np.array(r), ACCENT, "o", "-", "(i)"),
        (_population_ratios(("uniform", "laplace"), (0.8, 0.6), th, dth, 6), GREEN, "s", "-", "(ii)"),
        (_population_ratios(("exp", "exp"), (0.8, 0.6), th, dth, 6), RED, "^", "--", "(iii)"),
    ]
    for rr, col, mk, ls, lab in seqs:
        keep = [0]
        for k in range(1, len(rr)):          # stop at the accuracy floor of the quadrature
            if rr[k] < 1e-11 and lab != "(i)":
                keep.append(k)
                break
            keep.append(k)
        ax.semilogy(keep, rr[keep], color=col, marker=mk, ls=ls, lw=1.2, ms=4, mfc="white", label=lab)
    ax.set_xlabel("$k$")
    ax.set_ylabel("$|q_j^{(k)}/q_i^{(k)}|$")
    ax.set_ylim(1e-19, 10)
    ax.set_yticks([1e-18, 1e-12, 1e-6, 1])
    ax.set_xticks(range(0, 7))
    ax.set_title("(a)", pad=4)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    clean_axes(ax)

    # (b) symmetric FastICA on the four-source example of the chapter
    ax = axes[1]
    rng = np.random.default_rng(1)
    T = 10000
    S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T),
                   rng.laplace(0, 1 / np.sqrt(2), T),
                   np.sign(rng.standard_normal(T)),
                   rng.standard_t(5, T) / np.sqrt(5 / 3)])
    A = rng.standard_normal((4, 4))
    Z = _whiten(A @ S)
    nonlins = [
        (np.tanh, lambda y: 1 - np.tanh(y) ** 2, ACCENT, "o", "-", "$g=\\tanh u$"),
        (lambda y: y * np.exp(-y ** 2 / 2), lambda y: (1 - y ** 2) * np.exp(-y ** 2 / 2), GREEN, "s", "-",
         "$g=u\\,e^{-u^2/2}$"),
        (lambda y: y ** 3, lambda y: 3 * y ** 2, RED, "^", "--", "$g=u^3$"),
    ]
    for g, dg, col, mk, ls, lab in nonlins:
        W = _sym_orth(np.random.default_rng(0).standard_normal((4, 4)))
        ch = []
        for _ in range(30):
            Y = W @ Z
            Wn = _sym_orth(g(Y) @ Z.T / T - dg(Y).mean(axis=1)[:, None] * W)
            c = 1 - np.min(np.abs(np.sum(Wn * W, axis=1)))
            W = Wn
            ch.append(max(c, 1e-16))
            if c < 1e-14:
                break
        ax.semilogy(range(1, len(ch) + 1), ch, color=col, marker=mk, ls=ls, lw=1.2, ms=4, mfc="white", label=lab)
    ax.set_xlabel("$k$")
    ax.set_ylabel("$1-\\min_i |\\mathbf{w}_i^{(k)\\top}\\mathbf{w}_i^{(k-1)}|$")
    ax.set_ylim(1e-16, 3)
    ax.set_yticks([1e-15, 1e-10, 1e-5, 1])
    ax.set_title("(b)", pad=4)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    clean_axes(ax)
    fig.subplots_adjust(wspace=0.42)
    save(fig, "ch08-convergence")
