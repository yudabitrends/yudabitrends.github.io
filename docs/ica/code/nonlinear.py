# Nonlinear ICA
# Generated from book/src/nonlinear.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np
from scipy import stats

rng = np.random.default_rng(1)
T = 100_000
s1 = rng.uniform(0, 1, T)                 # two independent sources
s2 = rng.uniform(0, 1, T)
x1, x2 = s1, s1 + s2                      # a linear mixture

# Darmois construction, taking x2 first and x1 second
y1 = np.where(x2 <= 1, x2**2 / 2, 1 - (2 - x2)**2 / 2)   # CDF of x2 (triangular)
lo, hi = np.maximum(0, x2 - 1), np.minimum(1, x2)         # given x2, x1 ~ U(lo, hi)
y2 = (x1 - lo) / (hi - lo)                                # conditional CDF of x1

# Test that (y1, y2) is uniform on the unit square: chi-square on a 10 x 10 grid
H, _, _ = np.histogram2d(y1, y2, bins=10, range=[[0, 1], [0, 1]])
chi2 = ((H - T / 100) ** 2 / (T / 100)).sum()
print(f"chi2 = {chi2:.1f} on 99 df, p = {stats.chi2.sf(chi2, 99):.2f}")
# ... yet each output depends on both sources
print(np.round(np.corrcoef([y1, y2, s1, s2])[:2, 2:], 2))
