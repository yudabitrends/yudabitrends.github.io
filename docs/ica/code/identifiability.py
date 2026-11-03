# Identifiability
# Generated from book/src/identifiability.html; edit the chapter source.
# Requires Python 3, NumPy and SciPy. Run the blocks in this order.

import numpy as np

rng = np.random.default_rng(0)
T, runs = 5000, 500
th = np.linspace(0, np.pi, 1800, endpoint=False)    # all directions (w ~ -w)
c, s = np.cos(th), np.sin(th)

def source(k):
    """Normalized sum of k unit-variance uniforms: kurtosis -1.2 / k."""
    u = rng.uniform(-np.sqrt(3), np.sqrt(3), (k, T))
    return u.sum(axis=0) / np.sqrt(k)

for k in [1, 2, 4, 8]:
    err = []
    for _ in range(runs):
        a = rng.uniform(0, np.pi / 2)                   # true rotation angle
        Q = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        z = Q @ np.vstack([source(k), source(k)])       # whitened mixture
        m = [np.mean(z[0]**(4 - j) * z[1]**j) for j in range(5)]
        m4 = (c**4 * m[0] + 4 * c**3 * s * m[1] + 6 * c**2 * s**2 * m[2]
              + 4 * c * s**3 * m[3] + s**4 * m[4])     # E[(w^T z)^4]
        m2 = (c**2 * np.mean(z[0]**2) + 2 * c * s * np.mean(z[0] * z[1])
              + s**2 * np.mean(z[1]**2))                # E[(w^T z)^2]
        d = (th[np.argmax(np.abs(m4 - 3 * m2**2))] - a) % (np.pi / 2)
        err.append(min(d, np.pi / 2 - d))               # error modulo pi/2
    rms = np.degrees(np.sqrt(np.mean(np.square(err))))
    print(f"k = {k}: kurtosis {-1.2 / k:+.2f}, rms error {rms:5.2f} deg")
