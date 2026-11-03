# Spatial ICA of fMRI
# Generated from book/src/fmri-ica.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
side, T, n = 40, 150, 3
yy, xx = np.mgrid[0:side, 0:side]
def blob(cy, cx, r):                                  # Gaussian blob on the grid
    return np.exp(-((yy - cy)**2 + (xx - cx)**2) / (2 * r**2)).ravel()
S = np.vstack([blob(12, 10, 3) + blob(12, 30, 3),     # three spatial maps, n x V
               blob(28, 20, 5),
               blob(22, 6, 2) + blob(32, 33, 3)])
t = np.arange(T)
block = ((t // 15) % 2).astype(float)                 # 15 scans on, 15 off
A = np.column_stack([block, np.sin(2 * np.pi * t / 40), np.roll(block, 3)])
X = A @ S + 0.3 * rng.standard_normal((T, side * side))   # T x V data

# Spatial ICA: voxels are the samples. Center each row, PCA-whiten to n dims.
Xc = X - X.mean(axis=1, keepdims=True)
d, E = np.linalg.eigh(Xc @ Xc.T / Xc.shape[1])
d, E = d[-n:], E[:, -n:]
Z = np.diag(d ** -0.5) @ E.T @ Xc                     # n x V, identity covariance

U = np.linalg.qr(rng.standard_normal((n, n)))[0]      # symmetric FastICA, g = tanh
for _ in range(1000):
    U_old = U.copy()
    Y = U @ Z
    U = np.tanh(Y) @ Z.T / Z.shape[1] - np.diag((1 - np.tanh(Y)**2).mean(1)) @ U
    u, _, vt = np.linalg.svd(U)
    U = u @ vt                                        # U <- (U U^T)^(-1/2) U
    if np.max(np.abs(np.abs(np.diag(U @ U_old.T)) - 1)) < 1e-9:
        break
else:
    raise RuntimeError("FastICA did not converge; inspect or restart.")
S_hat = U @ Z                                         # estimated maps
A_hat = E @ np.diag(d ** 0.5) @ U.T                   # estimated time courses

print(np.round(np.corrcoef(A.T)[0, 2], 2))            # true time courses 1 and 3
print(np.round(np.abs(np.corrcoef(S_hat, S)[:n, n:]), 2))
print(np.round(np.abs(np.corrcoef(A_hat.T, A.T)[:n, n:]), 2))
