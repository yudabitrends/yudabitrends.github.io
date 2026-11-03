# Tensor and Second-Order Methods: JADE and SOBI
# Generated from book/src/jade-sobi.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

def whiten(X):
    """Center the rows of X; return Z = V X (identity sample covariance) and V."""
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or not np.isfinite(X).all() or X.shape[0] < 1 or X.shape[1] <= X.shape[0]:
        raise ValueError("Need finite channels-by-samples data with more samples than channels")
    X = X - X.mean(axis=1, keepdims=True)
    d, E = np.linalg.eigh(X @ X.T / X.shape[1])
    if d[-1] <= 0 or d[0] <= 1e-12 * d[-1]:
        raise ValueError("Rank-deficient data: reduce to a signal subspace first")
    V = E @ np.diag(d ** -0.5) @ E.T
    return V @ X, V

def joint_diagonalize(Qs, tol=1e-12, max_sweeps=100):
    """Jacobi joint diagonalization of symmetric matrices Qs (shape K x n x n).
    Returns an orthogonal U that makes every U Q U^T as diagonal as possible."""
    Qs = np.array(Qs, dtype=float, copy=True)
    if Qs.ndim != 3 or Qs.shape[0] == 0 or Qs.shape[1] == 0 or Qs.shape[1] != Qs.shape[2]:
        raise ValueError("Qs must be a nonempty stack of square matrices")
    if not np.isfinite(Qs).all() or not np.allclose(Qs, Qs.transpose(0, 2, 1)):
        raise ValueError("Joint diagonalization requires finite symmetric matrices")
    n = Qs.shape[1]
    U = np.eye(n)
    for sweep in range(max_sweeps):
        rotated = False
        for p in range(n - 1):
            for q in range(p + 1, n):
                h1 = Qs[:, p, p] - Qs[:, q, q]
                h2 = 2 * Qs[:, p, q]
                # closed-form Jacobi angle for the pair (p, q)
                theta = 0.25 * np.arctan2(2 * h1 @ h2, h1 @ h1 - h2 @ h2)
                if abs(theta) > tol:
                    rotated = True
                    c, s = np.cos(theta), np.sin(theta)
                    R = np.eye(n)
                    R[p, p] = R[q, q] = c
                    R[p, q], R[q, p] = -s, s
                    Qs = R.T @ Qs @ R      # rotate all matrices in the (p, q) plane
                    U = R.T @ U
        if not rotated:
            return U
    raise RuntimeError("Joint diagonalization did not converge within max_sweeps")

def jade(X):
    Z, V = whiten(X)
    n, T = Z.shape
    I = np.eye(n)
    M4 = np.einsum('it,jt,kt,lt->ijkl', Z, Z, Z, Z, optimize=True) / T
    C = (M4 - np.einsum('ij,kl->ijkl', I, I) - np.einsum('ik,jl->ijkl', I, I)
            - np.einsum('il,jk->ijkl', I, I))    # cumulant tensor of z
    Qs = C.reshape(n, n, n * n).transpose(2, 0, 1)    # the n^2 matrices Q(e_k e_l^T)
    return joint_diagonalize(Qs) @ V

rng = np.random.default_rng(1)
T = 10000
S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T),    # kappa = -1.2
               rng.laplace(0, 1 / np.sqrt(2), T),           # kappa = 3
               np.sign(rng.standard_normal(T))])            # kappa = -2
A = rng.standard_normal((3, 3))
P = jade(A @ S) @ A
print(np.round(P / np.abs(P).max(axis=1, keepdims=True), 2) + 0.0)

# Next example (shares the chapter namespace).

def sobi(X, lags):
    Z, V = whiten(X)
    T = Z.shape[1]
    lags = tuple(lags)
    if not lags or any(not isinstance(tau, (int, np.integer)) or not 0 < tau < T for tau in lags):
        raise ValueError("Each lag must be an integer between 1 and T-1")
    # lagged covariances of z, symmetrized before joint diagonalization
    Cs = [Z[:, :-tau] @ Z[:, tau:].T / (T - tau) for tau in lags]
    return joint_diagonalize(np.array([(C + C.T) / 2 for C in Cs])) @ V

rng = np.random.default_rng(2)
T = 20000
e = rng.standard_normal((3, T + 1))
s1, s3 = np.zeros(T), np.zeros(T)
for t in range(1, T):
    s1[t] = 0.5 * s1[t - 1] + e[0, t]       # AR(1): rho(1) = 0.5, rho(2) = 0.25
    s3[t] = -0.8 * s3[t - 1] + e[2, t]      # AR(1): rho(1) = -0.8
s2 = e[1, 1:] + e[1, :-1]                   # MA(1): rho(1) = 0.5, rho(2) = 0
S = np.vstack([s1, s2, s3])
S = S / S.std(axis=1, keepdims=True)        # three Gaussian sources
A = rng.standard_normal((3, 3))
for name, W in [("AMUSE, lag 1", sobi(A @ S, [1])),
                ("SOBI, lags 1-5", sobi(A @ S, range(1, 6))),
                ("JADE", jade(A @ S))]:
    P = W @ A
    print(name)
    print(np.round(P / np.abs(P).max(axis=1, keepdims=True), 2) + 0.0)
