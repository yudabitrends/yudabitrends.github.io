# Mathematical Background
# Generated from book/src/math-background.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)

# vec(AXB) = (B^T kron A) vec(X), with vec stacking columns
A, X, B = (rng.standard_normal(s) for s in [(3, 4), (4, 5), (5, 2)])
vec = lambda M: M.reshape(-1, order="F")
print(np.allclose(vec(A @ X @ B), np.kron(B.T, A) @ vec(X)))

# gradient of log|det W| by central differences
W, h = rng.standard_normal((4, 4)), 1e-6
logdet = lambda M: np.linalg.slogdet(M)[1]
G = np.zeros((4, 4))
for i in range(4):
    for j in range(4):
        D = np.zeros((4, 4)); D[i, j] = h
        G[i, j] = (logdet(W + D) - logdet(W - D)) / (2 * h)
print(f"{np.abs(G - np.linalg.inv(W).T).max():.1e}")

# closest orthogonal matrix: L R^T = (W W^T)^(-1/2) W
L, sv, Rt = np.linalg.svd(W)
d, E = np.linalg.eigh(W @ W.T)
print(np.allclose(L @ Rt, E @ np.diag(d ** -0.5) @ E.T @ W))
def random_orthogonal(n):                 # uniformly distributed on O(n)
    Q, R = np.linalg.qr(rng.standard_normal((n, n)))
    return Q * np.sign(np.diag(R))
dist = min(np.linalg.norm(W - random_orthogonal(4)) for _ in range(20000))
print(f"{np.linalg.norm(W - L @ Rt):.3f} {dist:.3f}")

# Next example (shares the chapter namespace).

import numpy as np
rng = np.random.default_rng(2026)
X = rng.normal(size=(4, 800))
X[-1] = X[0] + 2 * X[1]  # redundant sensor
Xc = X - X.mean(axis=1, keepdims=True)
L, singular, Rt = np.linalg.svd(Xc, full_matrices=False)
tol = np.finfo(Xc.dtype).eps * max(Xc.shape) * singular[0]
keep = singular > tol
V = (np.sqrt(Xc.shape[1]) / singular[keep])[:, None] * L[:, keep].T
Z = V @ Xc
assert keep.sum() == 3
assert np.allclose(Z @ Z.T / Z.shape[1], np.eye(3), atol=1e-12)
print("retained rank:", int(keep.sum()))
