# Overcomplete ICA and Sparse Component Analysis
# Generated from book/src/overcomplete.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
n, T = 3, 4000
S = rng.laplace(size=(n, T))
S *= rng.random((n, T)) < 0.2                 # each source active 20% of time
theta = np.deg2rad([15.0, 70.0, 125.0])       # true column directions
A = np.vstack([np.cos(theta), np.sin(theta)]) # 2 x 3, unit-norm columns
X = A @ S + 0.01 * rng.normal(size=(2, T))    # two sensors, weak noise

# 1) columns: peaks of the histogram of directions of the larger points
keep = np.linalg.norm(X, axis=0) > 0.2
ang = np.arctan2(X[1, keep], X[0, keep]) % np.pi   # sign removed
width = np.pi / 180
h, edges = np.histogram(ang, bins=180, range=(0, np.pi))
h = np.convolve(np.r_[h[-2:], h, h[:2]], np.ones(5) / 5, "valid")  # circular
peaks = [i for i in range(180)
         if h[i] >= h[i - 1] and h[i] > h[(i + 1) % 180]]
top = sorted(peaks, key=lambda i: -h[i])[:n]
th_hat = np.sort(edges[top] + width / 2)
A_hat = np.vstack([np.cos(th_hat), np.sin(th_hat)])
print("estimated angles (deg):", np.round(np.rad2deg(th_hat), 1))

# 2) sources: the l1 solution uses the two signed columns adjacent to x(t)
dirs = np.r_[th_hat, th_hat + np.pi]          # the 2n signed directions
S_l1 = np.zeros((n, T))
for t in range(T):
    rel = (dirs - np.arctan2(X[1, t], X[0, t])) % (2 * np.pi)
    i, j = np.argmin(rel) % n, np.argmax(rel) % n   # one on each side
    S_l1[[i, j], t] = np.linalg.solve(A_hat[:, [i, j]], X[:, t])
S_pinv = np.linalg.pinv(A_hat) @ X            # minimum l2-norm solution

def snr_db(S_est):
    err = np.sum((S - S_est) ** 2, axis=1)
    return np.round(10 * np.log10(np.sum(S ** 2, axis=1) / err), 1)
print("SNR (dB), l1:  ", snr_db(S_l1))
print("SNR (dB), pinv:", snr_db(S_pinv))
