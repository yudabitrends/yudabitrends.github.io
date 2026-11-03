# Whitening and the Geometry of ICA
# Generated from book/src/whitening.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(1)
A = np.array([[1.0, 0.6],
              [0.4, 1.0]])
T, runs = 1000, 10000
err = np.zeros(runs)
for r in range(runs):
    S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T),  # unit variance
                   rng.laplace(0.0, 1 / np.sqrt(2), T)])
    X = A @ S
    X = X - X.mean(axis=1, keepdims=True)
    d, E = np.linalg.eigh(X @ X.T / T)
    V = np.diag(d ** -0.5) @ E.T      # PCA whitening, sample covariance
    M = V @ A                         # whitened mixing, nearly orthogonal
    Um, _, Vmt = np.linalg.svd(M)
    U = (Um @ Vmt).T                  # oracle: U @ M closest to I
    P = U @ M                         # best orthogonal global matrix
    err[r] = P[0, 1]**2 + P[1, 0]**2
mean, se = T * err.mean(), T * err.std() / np.sqrt(runs)
print(f"T * E[eps12^2 + eps21^2] = {mean:.3f} +/- {se:.3f}")

# Next example (shares the chapter namespace).

import numpy as np

def whiten_svd(X, rank=None):
    X = np.asarray(X, dtype=float)           # sensors by observations
    if X.ndim != 2 or X.shape[0] < 1 or X.shape[1] < 2 or not np.isfinite(X).all():
        raise ValueError("Expected finite 2-D data with at least two observations")
    mean = X.mean(axis=1, keepdims=True)
    Xc = X - mean
    E, d, _ = np.linalg.svd(Xc, full_matrices=False)
    tol = np.finfo(float).eps * max(Xc.shape) * d[0]
    available = int(np.count_nonzero(d > tol))
    r = available if rank is None else rank
    if not isinstance(r, (int, np.integer)) or not 1 <= r <= available:
        raise ValueError("Requested rank exceeds the numerical signal rank")
    V = (np.sqrt(X.shape[1]) / d[:r, None]) * E[:, :r].T
    Z = V @ Xc
    return mean, V, Z

rng = np.random.default_rng(23)
S = rng.standard_normal((2, 2000))
A = np.array([[1., .4], [.2, 1.], [1.2, 1.4]])
X = A @ S
mean, V, Z = whiten_svd(X)
assert Z.shape == (2, X.shape[1])
assert np.allclose(Z @ Z.T / X.shape[1], np.eye(2))
assert np.allclose(np.linalg.pinv(V) @ Z + mean, X)
print("rank-aware whitening and reconstruction checks passed")

