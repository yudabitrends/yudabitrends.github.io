# Group ICA, Dual Regression and IVA
# Generated from book/src/group-ica.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np
from itertools import permutations

def fastica(Z, rng, iters=1000):                       # symmetric FastICA, g = tanh
    U = np.linalg.qr(rng.standard_normal((len(Z), len(Z))))[0]
    for _ in range(iters):
        U_old = U.copy()
        Y = U @ Z
        U = np.tanh(Y) @ Z.T / Z.shape[1] - np.diag((1 - np.tanh(Y)**2).mean(1)) @ U
        u, _, vt = np.linalg.svd(U); U = u @ vt
        if np.max(np.abs(np.abs(np.diag(U @ U_old.T)) - 1)) < 1e-9:
            return U
    raise RuntimeError("FastICA did not converge; inspect or restart.")

def pca_rows(X, k):                                   # k leading eigenvectors, as rows
    d, E = np.linalg.eigh(X @ X.T / X.shape[1])
    return E[:, ::-1][:, :k].T, d[::-1][:k]

rng = np.random.default_rng(0)
side, T, M, q, n = 30, 100, 6, 5, 3                   # grid, scans, subjects, PCA dims
yy, xx = np.mgrid[0:side, 0:side]
blob = lambda cy, cx, r: np.exp(-((yy - cy)**2 + (xx - cx)**2) / (2 * r**2)).ravel()
Xs, Ss = [], []
for i in range(M):                                    # blobs shifted at random per subject
    S = np.vstack([blob(cy + rng.integers(-4, 5), cx + rng.integers(-4, 5), r)
                   for cy, cx, r in [(8, 8, 3), (20, 22, 4), (8, 22, 3)]])
    A = np.cumsum(rng.standard_normal((T, n)), 0)    # subject-specific time courses
    X = (A - A.mean(0)) / A.std(0) @ S + 0.3 * rng.standard_normal((T, side**2))
    Xs.append(X - X.mean(1, keepdims=True)); Ss.append(S)

Fs = [pca_rows(X, q)[0] for X in Xs]                  # subject PCA: q x T each
Y = np.vstack([F @ X for F, X in zip(Fs, Xs)])        # temporal concatenation: Mq x V
G, lam = pca_rows(Y, n)                               # group PCA: n x Mq
Z = np.diag(lam ** -0.5) @ G @ Y
U = fastica(Z, rng)
S_g, B = U @ Z, np.diag(lam ** 0.5) @ U.T             # group maps; G Y = B S_g

def match(S_est, S_true):                             # one-to-one assignment; n = 3 here
    C = np.abs(np.corrcoef(S_est, S_true)[:n, n:])
    return max(C[range(n), p].mean() for p in permutations(range(n)))
r0, r1, r2 = [], [], []
for X, F, Gi, S in zip(Xs, Fs, np.split(G, M, axis=1), Ss):
    S_1 = np.linalg.pinv(Gi.T @ B) @ F @ X            # GICA1 back-reconstruction
    A_dr = X @ np.linalg.pinv(S_g)                    # dual regression, stage 1
    S_dr = np.linalg.pinv(A_dr) @ X                   # dual regression, stage 2
    r0.append(match(S_g, S)); r1.append(match(S_1, S)); r2.append(match(S_dr, S))
print(Y.shape, S_g.shape)
print(np.round([np.mean(r0), np.mean(r1), np.mean(r2)], 3))
