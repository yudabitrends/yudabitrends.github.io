# Non-Gaussianity and Kurtosis
# Generated from book/src/kurtosis.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
T, n = 10000, 3
S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T),  # kurtosis -1.2
               rng.laplace(0.0, 1 / np.sqrt(2), T),       # kurtosis +3
               rng.choice([-1.0, 1.0], T)])               # kurtosis -2
A = rng.standard_normal((n, n))
X = A @ S

X = X - X.mean(axis=1, keepdims=True)                     # whiten: z = V x
d, E = np.linalg.eigh(X @ X.T / T)
V = E @ np.diag(d ** -0.5) @ E.T
Z = V @ X

U = np.zeros((n, n))                          # rows: directions found so far
for p in range(n):
    w = rng.standard_normal(n)
    w /= np.linalg.norm(w)
    for it in range(1, 101):
        y = w @ Z
        w_new = (Z * y**3).mean(axis=1) - 3 * w           # fixed point
        w_new -= U[:p].T @ (U[:p] @ w_new)                # Gram-Schmidt
        norm = np.linalg.norm(w_new)
        if not np.isfinite(norm) or norm < 1e-12:
            raise RuntimeError("Degenerate update; restart or change contrast")
        w_new /= norm
        done = abs(w_new @ w) > 1 - 1e-12                 # converged
        w = w_new
        if done:
            break
    if not done:
        raise RuntimeError("Iteration limit reached before convergence")
    U[p] = w
    y = w @ Z
    kurt = np.mean(y**4) - 3 * np.mean(y**2)**2
    print(f"unit {p + 1}: {it} iterations, kurtosis {kurt:+.2f}")
print(np.round(U @ V @ A, 2) + 0.0)           # close to a signed permutation
