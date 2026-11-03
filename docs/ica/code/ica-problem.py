# The ICA Problem
# Generated from book/src/ica-problem.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
T = 5000
S = np.vstack([rng.uniform(-np.sqrt(3), np.sqrt(3), T),   # uniform: sub-Gaussian, unit variance
               rng.laplace(0.0, 1 / np.sqrt(2), T)])      # Laplace: super-Gaussian, unit variance
A = np.array([[1.0, 0.6],
              [0.4, 1.0]])
X = A @ S                                    # observed mixtures, shape (2, T)

# Step 1: whiten, z = V x with sample covariance I
X = X - X.mean(axis=1, keepdims=True)
d, E = np.linalg.eigh(X @ X.T / T)
V = E @ np.diag(d ** -0.5) @ E.T
Z = V @ X

# Step 2: rotate, choosing the direction whose projection has the largest |kurtosis|
def kurt(y):
    return np.mean(y ** 4) - 3 * np.mean(y ** 2) ** 2

angles = np.linspace(0, np.pi, 360, endpoint=False)
scores = [abs(kurt(np.cos(a) * Z[0] + np.sin(a) * Z[1])) for a in angles]
a = angles[np.argmax(scores)]
U = np.array([[np.cos(a), np.sin(a)],
              [-np.sin(a), np.cos(a)]])
Y = U @ Z                                    # estimated sources
W = U @ V                                    # estimated unmixing matrix
print(np.round(W @ A, 2))                    # close to a signed permutation
