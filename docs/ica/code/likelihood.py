# Negentropy, Mutual Information and Likelihood
# Generated from book/src/likelihood.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
T, runs = 10000, 300
EG_nu = 0.374567                          # E log cosh(nu), nu ~ N(0, 1)

def logcosh(u):
    return np.abs(u) + np.log1p(np.exp(-2 * np.abs(u))) - np.log(2)

def zero_kurtosis_source(size):
    """Uniform with probability 5/7, Laplacian with probability 2/7."""
    pick = rng.random(size) < 5 / 7
    return np.where(pick, rng.uniform(-np.sqrt(3), np.sqrt(3), size),
                    rng.laplace(0.0, 1 / np.sqrt(2), size))

sources = [("Gaussian", rng.standard_normal),
           ("zero-kurtosis", zero_kurtosis_source)]
for name, draw in sources:
    k, g = [], []
    for _ in range(runs):
        y = draw(T)
        y = (y - y.mean()) / y.std()              # standardize
        k.append(np.mean(y**4) - 3)               # sample kurtosis
        g.append(np.mean(logcosh(y)) - EG_nu)     # E G(y) - E G(nu)
    print(f"{name:14s} kurtosis {np.mean(k):+.3f} +/- {np.std(k):.3f}   "
          f"G-statistic {np.mean(g):+.4f} +/- {np.std(g):.4f}")
