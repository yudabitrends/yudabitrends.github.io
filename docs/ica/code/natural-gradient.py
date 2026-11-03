# Natural Gradient, Infomax and Stability
# Generated from book/src/natural-gradient.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

def natural_gradient_ica(X, phi, mu=0.1, iters=500):
    """Batch natural-gradient ICA: W <- W + mu (I - E[phi(y) y^T]) W."""
    n, T = X.shape
    W = np.eye(n)
    for _ in range(iters):
        Y = W @ X
        W += mu * (np.eye(n) - phi(Y) @ Y.T / T) @ W
    return W

def extended_infomax(X, mu=0.1, iters=500):
    """phi_i(y) = y + k_i tanh(y), k_i = +1 or -1 set by the switching rule."""
    n, T = X.shape
    W = np.eye(n)
    k = np.ones(n)  # retain the previous sign when the statistic is near zero
    for _ in range(iters):
        Y = W @ X
        stat = (np.mean(1 - np.tanh(Y) ** 2, axis=1) * np.mean(Y ** 2, axis=1)
                - np.mean(np.tanh(Y) * Y, axis=1))
        k = np.where(stat > 1e-6, 1, np.where(stat < -1e-6, -1, k))
        W += mu * (np.eye(n) - (Y + k[:, None] * np.tanh(Y)) @ Y.T / T) @ W
    return W

def interference(P):
    """Max over rows of P of second-largest / largest |entry|; 0 = separated."""
    R = np.sort(np.abs(P), axis=1)
    return np.max(R[:, -2] / R[:, -1])

rng = np.random.default_rng(0)
T = 20000
A = np.array([[1.0, 0.6],
              [0.4, 1.0]])
sources = {"uniform": rng.uniform(-np.sqrt(3), np.sqrt(3), (2, T)),   # kappa = -1.2
           "Laplace": rng.laplace(0, 1 / np.sqrt(2), (2, T))}        # kappa = +3
methods = {"tanh": lambda X: natural_gradient_ica(X, np.tanh),
           "cube": lambda X: natural_gradient_ica(X, lambda y: y ** 3),
           "extended": extended_infomax}
for sname, S in sources.items():
    for mname, method in methods.items():
        W = method(A @ S)
        print(f"{sname:8s} {mname:9s} interference = {interference(W @ A):.3f}")
