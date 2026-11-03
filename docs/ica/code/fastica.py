# FastICA
# Generated from book/src/fastica.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

def whiten(X):
    """Rows are channels; use covariance / T, matching all sample expectations."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError("X must be a finite channels-by-samples matrix")
    n, T = X.shape
    if n < 1 or T <= n:
        raise ValueError("Need more samples than channels; reduce rank first")
    mean = X.mean(axis=1, keepdims=True)
    Xc = X - mean
    E, d, _ = np.linalg.svd(Xc / np.sqrt(T), full_matrices=False)
    if d[-1] <= 1e-12 * d[0]:
        raise ValueError("Rank-deficient data: select a signal subspace first")
    V = (E / d) @ E.T
    return V @ Xc, V, mean

def sym_orth(W):
    """Polar factor by SVD, avoiding squaring the condition number."""
    if not np.isfinite(W).all():
        raise ValueError("Nonfinite FastICA update")
    L, d, Rt = np.linalg.svd(W, full_matrices=False)
    if d[-1] <= 1e-12 * d[0]:
        raise ValueError("Degenerate update: change contrast or handle Gaussian residual")
    return L @ Rt

def fastica_symmetric(X, g, dg, max_iter=100, tol=1e-12, seed=0):
    Z, V, mean = whiten(X)
    n, T = Z.shape
    W = sym_orth(np.random.default_rng(seed).standard_normal((n, n)))
    for it in range(1, max_iter + 1):
        Y = W @ Z
        W_new = sym_orth(g(Y) @ Z.T / T - dg(Y).mean(axis=1)[:, None] * W)
        change = np.clip(1 - np.min(np.abs(np.sum(W_new * W, axis=1))), 0, 1)
        W = W_new
        print(f"iteration {it}: 1 - min|<w_new, w_old>| = {change:.1e}")
        if change < tol:
            return W @ V, mean
    raise RuntimeError("FastICA did not converge; inspect rank, contrast and starts")

rng = np.random.default_rng(1)
T = 10000
S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T),
               rng.laplace(0, 1 / np.sqrt(2), T),
               np.sign(rng.standard_normal(T)),
               rng.standard_t(5, T) / np.sqrt(5 / 3)])
A = rng.standard_normal((4, 4))
X = A @ S
W, mean = fastica_symmetric(X, np.tanh, lambda y: 1 - np.tanh(y) ** 2)
Y = W @ (X - mean)                          # apply the fitted centering as well
P = W @ A
print(np.round(P / np.abs(P).max(axis=1, keepdims=True), 2) + 0.0)
