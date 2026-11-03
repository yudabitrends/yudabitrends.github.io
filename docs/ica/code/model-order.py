# Noise, Model Order and Reliability
# Generated from book/src/model-order.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

def order_criteria(X):
    """Orders chosen by AIC and MDL from the sample covariance eigenvalues."""
    m, T = X.shape
    if m < 2 or T <= m or not np.isfinite(X).all():
        raise ValueError("Need finite data with T > m >= 2.")
    ell = np.sort(np.linalg.eigvalsh(np.cov(X)))[::-1]
    if ell[-1] <= np.finfo(float).eps * m * ell[0]:
        raise ValueError("Covariance is numerically rank deficient.")
    aic, mdl = [], []
    for k in range(m):
        tail = ell[k:]                      # the m - k smallest eigenvalues
        loglr = (m - k) * (np.mean(np.log(tail)) - np.log(np.mean(tail)))
        p = m * k - k * (k - 1) / 2 + 1     # free parameters of the model
        aic.append(-T * loglr + 2 * p)
        mdl.append(-T / 2 * loglr + p / 2 * np.log(T))
    return int(np.argmin(aic)), int(np.argmin(mdl))

def ar1(E, phi):
    """Turn each row of white noise E into a unit-variance AR(1) series."""
    Y = np.empty_like(E)
    Y[:, 0] = E[:, 0]
    for t in range(1, E.shape[1]):
        Y[:, t] = phi * Y[:, t - 1] + np.sqrt(1 - phi ** 2) * E[:, t]
    return Y

rng = np.random.default_rng(1)
m, n, T = 30, 8, 5000
A = rng.normal(size=(m, n))
S = rng.laplace(0, 1 / np.sqrt(2), (n, T))
N = rng.normal(size=(m, T))
for phi in [0.0, 0.9]:
    X = A @ ar1(S, phi) + ar1(N, phi)
    print(f"phi = {phi}: all samples (AIC, MDL) = {order_criteria(X)}, "
          f"every 10th sample = {order_criteria(X[:, ::10])}")
