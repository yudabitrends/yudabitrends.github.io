"""Regression checks for the ICA book's foundational results and examples.

Run with: python scripts/tests_foundations.py
The SVD tests execute the function published in whitening.html, so source-code
changes cannot silently diverge from the tested implementation.
"""
from __future__ import annotations

import contextlib
from fractions import Fraction as F
import html
import io
from math import factorial
from pathlib import Path
import re
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def published_whitener():
    source = (ROOT / 'book/src/whitening.html').read_text(encoding='utf-8')
    blocks = re.findall(r'<pre\b[^>]*data-code="python"[^>]*><code>([\s\S]*?)</code></pre>', source)
    block = next(html.unescape(b) for b in blocks if 'def whiten_svd(' in b)
    namespace = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(block, 'whitening.html', 'exec'), namespace)
    return namespace['whiten_svd']


class FoundationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.whitener = staticmethod(published_whitener())

    def test_full_row_rank_does_not_ensure_non_degenerate_outputs(self):
        A = np.array([[1., 0.], [0., 1.], [0., 0.]])
        W = np.array([[0., 1., 0.], [0., 0., 1.]])
        self.assertEqual(np.linalg.matrix_rank(W), 2)
        self.assertEqual(np.linalg.matrix_rank(W @ A), 1)
        self.assertEqual(np.linalg.det(W @ A @ A.T @ W.T), 0.)

    def test_exact_reconstruction_does_not_imply_separation(self):
        A = np.array([[1., .6], [.4, 1.]])
        B = np.array([[1., -1.], [1., 1.]]) / np.sqrt(2.)
        W, Ahat = B @ np.linalg.inv(A), A @ B.T
        np.testing.assert_allclose(Ahat @ W, np.eye(2), atol=1e-14)
        # Unit-variance uniform sources: mixed cum(y1,y1,y2,y2) is -3/5.
        cross_cumulant = np.sum((-6. / 5) * B[0]**2 * B[1]**2)
        self.assertAlmostEqual(cross_cumulant, -3. / 5)

    def test_svd_rank_and_covariance_and_reconstruction(self):
        rng = np.random.default_rng(71)
        S = rng.normal(size=(2, 501))
        A = np.array([[1., .2], [.4, 1.], [1.4, 1.2]])
        X = A @ S + np.array([[10.], [-2.], [.7]])
        mean, V, Z = self.whitener(X)
        self.assertEqual(Z.shape, (2, 501))
        np.testing.assert_allclose(Z @ Z.T / X.shape[1], np.eye(2), atol=1e-13)
        np.testing.assert_allclose(np.linalg.pinv(V) @ Z + mean, X, atol=1e-13)
        # Transform fresh data using the fitted mean and matrix, preserving dimensions.
        new_X = A @ rng.normal(size=(2, 27)) + mean
        self.assertEqual((V @ (new_X - mean)).shape, (2, 27))

    def test_svd_rejects_rank_deficiency_and_invalid_input(self):
        rng = np.random.default_rng(72)
        X = np.vstack([rng.normal(size=20), np.ones(20)])
        for data, rank in [(X, 2), (X, 0), (X, 1.5), (np.ones((2, 10)), None),
                           (np.zeros((0, 5)), None), (np.ones(10), None),
                           (np.array([[np.nan, 1.]]), None), (np.ones((2, 1)), None)]:
            with self.subTest(shape=np.shape(data), rank=rank):
                with self.assertRaises(ValueError):
                    self.whitener(data, rank)

    def test_regularized_inverse_square_root_is_not_exact_whitening(self):
        d = np.array([.01, 2., 10.])
        alpha = .1
        V = np.diag(1. / np.sqrt(d + alpha))
        covariance = V @ np.diag(d) @ V.T
        np.testing.assert_allclose(np.diag(covariance), d / (d + alpha))
        self.assertFalse(np.allclose(covariance, np.eye(3)))

    def test_rectangular_left_inverse_family(self):
        rng = np.random.default_rng(73)
        A = rng.normal(size=(5, 3))
        Ap = np.linalg.pinv(A)
        projector = np.eye(5) - A @ Ap
        W = Ap + rng.normal(size=(3, 5)) @ projector
        np.testing.assert_allclose(W @ A, np.eye(3), atol=1e-13)
        np.testing.assert_allclose(W, Ap + W @ projector, atol=1e-13)
        self.assertGreater(np.linalg.norm(W - Ap), .1)

    def test_contemporaneous_independence_does_not_diagonalize_lags(self):
        rng = np.random.default_rng(74)
        noise = rng.normal(size=100002)
        S = np.vstack([noise[1:], noise[:-1]])
        covariance = S @ S.T / S.shape[1]
        lagged = S[:, 1:] @ S[:, :-1].T / (S.shape[1] - 1)
        self.assertLess(abs(covariance[0, 1]), .02)
        self.assertGreater(lagged[1, 0], .98)
        self.assertLess(abs(lagged[0, 1]), .02)

    def test_centered_standardized_kurtosis_influence_variance(self):
        gaussian = {k: F(0) if k % 2 else F(factorial(k), 2**(k//2)*factorial(k//2))
                    for k in range(9)}
        uniform = {k: F(0) if k % 2 else F(3**(k//2), k+1) for k in range(9)}
        laplace = {k: F(0) if k % 2 else F(factorial(k), 2**(k//2)) for k in range(9)}
        exponential = {k: F(sum((-1)**(k-j) * factorial(k) // factorial(k-j)
                              for j in range(k+1))) for k in range(9)}
        for label, moments, expected in [('Gaussian', gaussian, F(24)),
                                         ('uniform', uniform, F(1152, 875)),
                                         ('Laplace', laplace, F(1188)),
                                         ('centered exponential', exponential, F(8064))]:
            with self.subTest(distribution=label):
                m3, m4, m5, m6, m8 = [moments[k] for k in [3, 4, 5, 6, 8]]
                coefficients = {0: m4, 1: -4*m3, 2: -2*m4, 4: F(1)}
                mean = sum(c * moments[k] for k, c in coefficients.items())
                direct = sum(a*b*moments[i+j] for i, a in coefficients.items()
                             for j, b in coefficients.items()) - mean**2
                Vs = m8 - m4**2 + 4*m4**3 - 4*m4*m6
                stated = Vs + 16*m3**2*(1+m4) - 8*m3*m5
                self.assertEqual(mean, 0)
                self.assertEqual(direct, stated)
                self.assertEqual(direct, expected)

    def test_kurtosis_bound_and_zero_kurtosis_plane(self):
        rng = np.random.default_rng(75)
        kappa = np.array([-1.2, 3., 0.])
        q = rng.normal(size=(2000, 3))
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        self.assertTrue(np.all(np.abs(q**4 @ kappa) <= np.max(np.abs(kappa)) + 1e-12))
        # Two zero-kurtosis directions remain indistinguishable to Comon's contrast.
        a = .37
        Q = np.array([[1., 0., 0.], [0., np.cos(a), -np.sin(a)],
                      [0., np.sin(a), np.cos(a)]])
        kappa_zero_plane = np.array([3., 0., 0.])
        self.assertAlmostEqual(np.sum((Q**4 @ kappa_zero_plane)**2), 9.)
        self.assertGreater(np.sum(np.abs(Q)) - 3., .1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
