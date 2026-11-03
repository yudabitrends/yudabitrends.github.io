# Asymptotic Performance and the Cramér–Rao Bound
# Generated from book/src/performance.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
nonlin = {"tanh": (np.tanh, lambda u: 1 - np.tanh(u) ** 2),
          "pow3": (lambda u: u ** 3, lambda u: 3 * u ** 2)}
s = rng.laplace(0, 1 / np.sqrt(2), 10**7)     # unit-variance Laplace source

n, T, runs = 3, 5000, 2000
A = rng.normal(size=(n, n))
for name, (g, dg) in nonlin.items():
    # predicted asymptotic variance V_g, expectations by Monte Carlo
    Esg, Edg = np.mean(s * g(s)), np.mean(dg(s))
    V_g = (np.mean(g(s) ** 2) - Esg ** 2) / (Esg - Edg) ** 2
    eps2 = []
    for r in range(runs):
        S = np.vstack([rng.laplace(0, 1 / np.sqrt(2), T),  # target
                       rng.uniform(-np.sqrt(3), np.sqrt(3), (2, T))])
        X = A @ S
        X -= X.mean(axis=1, keepdims=True)
        d, E = np.linalg.eigh(X @ X.T / T)
        V = E @ np.diag(d ** -0.5) @ E.T            # sample whitening
        Z = V @ X
        w = np.linalg.solve((V @ A).T, np.eye(n)[0])  # start at target
        w /= np.linalg.norm(w)
        for it in range(200):                       # one-unit FastICA
            y = w @ Z
            w_new = Z @ g(y) / T - np.mean(dg(y)) * w
            w_new /= np.linalg.norm(w_new)
            done = 1 - abs(w_new @ w) < 1e-12
            w = w_new
            if done:
                break
        q = w @ V @ A                               # row of gain matrix
        eps2.append(np.mean((q[1:] / q[0]) ** 2))  # one independent value per run
    est = T * np.mean(eps2)
    se = T * np.std(eps2, ddof=1) / np.sqrt(runs)  # errors within one run can correlate
    print(f"{name}: predicted V_g = {V_g:.2f}, "
          f"observed T*ISR = {est:.2f} +/- {2 * se:.2f}")
