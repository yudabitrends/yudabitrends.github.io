# Independence, Cumulants and Entropy
# Generated from book/src/probability.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
T = 1_000_000

def kurt(y):                           # fourth cumulant of a sample
    y = y - y.mean()
    return np.mean(y**4) - 3 * np.mean(y**2)**2

def cum22(y1, y2):                     # cum(y1, y1, y2, y2) of a sample
    y1, y2 = y1 - y1.mean(), y2 - y2.mean()
    return (np.mean(y1**2 * y2**2) - np.mean(y1**2) * np.mean(y2**2)
            - 2 * np.mean(y1 * y2)**2)

samples = {                            # unit-variance draws, as in the table
    "uniform":     rng.uniform(-np.sqrt(3), np.sqrt(3), T),
    "laplace":     rng.laplace(0.0, 1 / np.sqrt(2), T),
    "gaussian":    rng.standard_normal(T),
    "binary":      rng.choice([-1.0, 1.0], T),
    "exponential": rng.exponential(1.0, T),
    "student-t10": rng.standard_t(10, T) / np.sqrt(10 / 8),
}
for name, y in samples.items():
    print(f"{name:12s} kurt = {kurt(y):+.3f}")

# two uniform sources rotated by 45 degrees: white but dependent
s1, s2 = rng.uniform(-np.sqrt(3), np.sqrt(3), (2, T))
z1, z2 = (s1 - s2) / np.sqrt(2), (s1 + s2) / np.sqrt(2)
print(f"E[z1 z2]            = {np.mean(z1 * z2):+.3f}")
print(f"cum(z1, z1, z2, z2) = {cum22(z1, z2):+.3f}")
print(f"cum(s1, s1, s2, s2) = {cum22(s1, s2):+.3f}")
