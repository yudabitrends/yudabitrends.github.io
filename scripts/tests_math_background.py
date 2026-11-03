"""Numerical checks for the corrected mathematical appendix."""
import numpy as np
from scipy.integrate import quad

L = np.array([[1., 0.], [1., 1.]])
C = L @ L.T
assert not np.allclose(L @ L, C)
d, E = np.linalg.eigh(C)
root = (E * np.sqrt(d)) @ E.T
assert np.allclose(root @ root, C)

A = np.array([[1., 2.], [0., 1.], [1., 0.]])
assert np.isclose(np.linalg.cond(A.T @ A), np.linalg.cond(A)**2)
assert np.allclose(np.linalg.svd(A, compute_uv=False)**2, np.linalg.eigvalsh(A.T @ A)[::-1])
assert np.isclose(np.linalg.eigvalsh(A @ A.T)[0], 0.)

# The location-M example uses unit-variance Laplace, not Laplace(scale=1).
b=1/np.sqrt(2)
e2=quad(lambda x: np.tanh(x)**2 * np.exp(-x/b)/b, 0, np.inf)[0]
assert abs(e2 - .3235) < .0001
assert abs(e2/(1-e2)**2 - .707) < .001

# Raw fourth-cumulant influence-function variances, not standardized kurtosis.
def variance(m2,m4,m6,m8):
    return m8-m4**2-12*m2*(m6-m2*m4)+36*m2*m2*(m4-m2*m2)
assert np.isclose(variance(1,3,15,105),24)
assert np.isclose(variance(1,9/5,27/7,9),1728/175)
assert np.isclose(variance(1,6,90,2520),1656)

# Finite-sample AR(1) mean variance approaches the stated long-run variance.
rho=.8; T=10000; k=np.arange(1,T)
exact_scaled=1+2*np.sum((1-k/T)*rho**k)
assert abs(exact_scaled - (1+rho)/(1-rho)) < .005
print('PASS appendix: covariance factors, rectangular SVD, conditioning, Laplace M-estimator, cumulant variances, AR(1) long-run variance')
