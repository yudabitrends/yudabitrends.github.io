"""Numerical checks for advanced ICA chapters (NumPy and SciPy required).

Run from any directory: python scripts/tests_advanced.py
These checks validate specific identities and counterexamples, not entire theorems.
"""
from pathlib import Path
from itertools import permutations
import ast
import html
import math
import re
import unittest

import numpy as np
from numpy.testing import assert_allclose
from scipy.optimize import linear_sum_assignment, linprog, root

BOOK = Path(__file__).resolve().parents[1] / "book" / "src"


def chapter_function(slug, name, **globals_):
    """Exercise the published function itself without running its full example."""
    text = (BOOK / (slug + ".html")).read_text(encoding="utf-8")
    for code in re.findall(r'<pre class="code" data-code="python"><code>(.*?)</code></pre>', text, re.S):
        tree = ast.parse(html.unescape(code))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                module = ast.Module(body=[node], type_ignores=[])
                ns = {"np": np, "permutations": permutations, **globals_}
                exec(compile(module, str(BOOK / (slug + ".html")), "exec"), ns)
                return ns[name]
    raise AssertionError(f"Function {name} not found in {slug}")


def model_order_figure_functions():
    """Load the actual numerical helpers without importing plotting dependencies."""
    path = BOOK.parent / "figures" / "model-order.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ("_sym_fastica", "_pca_ica")]
    ns = {"np": np}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), ns)
    return ns


class AdvancedICAChecks(unittest.TestCase):
    def test_split_figure_population_whitening_and_numerical_rank(self):
        pca_ica = model_order_figure_functions()["_pca_ica"]
        rng = np.random.default_rng(24)
        X = rng.normal(size=(4, 250))
        X[-1] = X[0] + 2 * X[1]
        Y, diagnostics = pca_ica(X, 3, seed=7, iters=1)
        self.assertEqual(diagnostics["rank"], 3)
        self.assertLess(diagnostics["whitening_error"], 1e-12)
        # The T-1/T mismatch would fail this normalization invariant.
        assert_allclose(Y @ Y.T / Y.shape[1], np.eye(3), atol=1e-12, rtol=0)
        with self.assertRaises(ValueError):
            pca_ica(X, 4, seed=7)

    def test_split_figure_reports_convergence_and_exhaustion(self):
        pca_ica = model_order_figure_functions()["_pca_ica"]
        X = np.random.default_rng(25).laplace(size=(3, 300))
        _, limited = pca_ica(X, 3, seed=7, iters=1, tol=1e-12)
        self.assertFalse(limited["converged"])
        self.assertEqual(limited["reason"], "iteration_limit")
        self.assertEqual(limited["n_iter"], 1)
        self.assertGreater(limited["delta"], limited["tolerance"])
        _, converged = pca_ica(X[:1], 1, seed=7)
        self.assertTrue(converged["converged"])
        self.assertEqual(converged["reason"], "converged")
        self.assertLess(converged["delta"], converged["tolerance"])

    def test_split_figure_detects_rank_deficient_update(self):
        fastica = model_order_figure_functions()["_sym_fastica"]
        class IdentityStart:
            def normal(self, size):
                return np.eye(size[0])
        # Saturated, duplicated rows give a rank-one update exactly in float64.
        Z = np.tile([100., 100., -100., -100.], (2, 1))
        W, diagnostics = fastica(Z, IdentityStart())
        self.assertFalse(diagnostics["converged"])
        self.assertEqual(diagnostics["reason"], "rank_deficient_update")
        assert_allclose(W @ W.T, np.eye(2), atol=1e-12)

    def test_noise_corrected_whitening_requires_full_cumulant(self):
        A = np.array([[1., .3], [.2, 1.4]])
        sigma2 = .4
        d, E = np.linalg.eigh(A @ A.T)
        V = np.diag(d ** -.5) @ E.T
        B = V @ A
        assert_allclose(B @ B.T, np.eye(2), atol=1e-12)
        C_total = V @ (A @ A.T + sigma2 * np.eye(2)) @ V.T
        self.assertGreater(np.linalg.norm(C_total - np.eye(2)), .1)
        w = np.array([.6, .8])
        q = B.T @ w
        cumulant = np.sum(np.array([3., -1.2]) * q ** 4)
        variance = w @ C_total @ w
        fourth_moment = cumulant + 3 * variance ** 2
        self.assertAlmostEqual(fourth_moment - 3 * variance ** 2, cumulant)
        self.assertGreater(abs((fourth_moment - 3) - cumulant), 1.)

    def test_order_criteria_rejects_singular_or_nonfinite_data(self):
        order = chapter_function("model-order", "order_criteria")
        rng = np.random.default_rng(42)
        for X in [np.eye(3), np.ones((3, 10)), np.full((3, 10), np.nan)]:
            with self.assertRaises(ValueError):
                order(X)
        aic, mdl = order(rng.normal(size=(3, 100)))
        self.assertTrue(0 <= aic < 3 and 0 <= mdl < 3)

    def test_l1_can_have_dense_minimizers(self):
        # The dual certificate lambda=(1,1) proves the optimum is 2.
        A = np.array([[1., 0., .5], [0., 1., .5]])
        x = np.ones(2)
        assert_allclose(A.T @ np.ones(2), np.ones(3))
        for t in [0., .5, 1., 2.]:
            s = np.array([1 - t / 2, 1 - t / 2, t])
            assert_allclose(A @ s, x)
            self.assertAlmostEqual(np.abs(s).sum(), 2.)
        self.assertEqual(np.count_nonzero([.5, .5, 1.]), 3)

    def test_exact_sparse_recovery_is_possible(self):
        angles = np.deg2rad([0., 60., 120.])
        A = np.vstack([np.cos(angles), np.sin(angles)])
        truth = np.array([1., 0., 0.])
        fit = linprog(np.ones(6), A_eq=np.hstack([A, -A]),
                      b_eq=A @ truth, bounds=(0, None), method="highs")
        self.assertTrue(fit.success)
        assert_allclose(fit.x[:3] - fit.x[3:], truth, atol=1e-10)

    def test_two_distinct_quartic_decompositions(self):
        def coefficients(angles):
            c, s = np.cos(angles), np.sin(angles)
            return np.array([math.comb(4, k) * c ** (4-k) * s ** k for k in range(5)])
        target = coefficients(np.deg2rad([0., 60., 120.])) @ np.array([3., 1., 2.])
        first = np.deg2rad(20.)
        def residual(z):
            return coefficients(np.r_[first, z[:2]]) @ z[2:] - target
        fit = root(residual, np.r_[np.deg2rad([99.6, 156.3]), [2.07, 1.69, 2.23]])
        self.assertTrue(fit.success)
        assert_allclose(residual(fit.x), np.zeros(5), atol=1e-8)
        angles = np.r_[first, fit.x[:2]]
        assert_allclose(np.round(np.rad2deg(angles), 1), [20., 99.6, 156.3])
        assert_allclose(np.round(fit.x[2:], 2), [2.07, 1.69, 2.23])
        c, s = np.cos(angles), np.sin(angles)
        variances = np.linalg.solve(np.array([c*c, c*s, s*s]), [1.5, 0., 1.5])
        self.assertTrue(np.all(variances > 0))
        assert_allclose(np.round(variances, 2), [1.21, 1.32, .47])
        A = np.vstack([c, s])
        assert_allclose(A @ np.diag(variances) @ A.T, 1.5 * np.eye(2), atol=1e-10)

    def test_pnl_diagonal_slopes_enter_separation(self):
        A = np.array([[1., .3], [.2, 1.]])
        D = np.diag([2., .5])
        W = np.linalg.inv(D @ A)
        assert_allclose(W @ D @ A, np.eye(2), atol=1e-12)
        self.assertGreater(np.linalg.norm(W @ A - np.eye(2)), .5)

    def test_one_to_one_component_matching(self):
        t = np.arange(64) * 2 * np.pi / 64
        S = np.array([np.cos(k * t) for k in [1, 2, 3]])
        estimate = np.array([(S[0] + S[1]) / np.sqrt(2), S[2], np.cos(4 * t)])
        C = np.abs(np.corrcoef(estimate, S)[:3, 3:])
        rows, cols = linear_sum_assignment(-C)
        expected = C[rows, cols].mean()
        match = chapter_function("group-ica", "match", n=3)
        self.assertAlmostEqual(match(estimate, S), expected)
        self.assertGreater(C.max(0).mean() - expected, .2)

    def test_fastica_exhaustion_is_reported(self):
        fastica = chapter_function("group-ica", "fastica")
        with self.assertRaises(RuntimeError):
            fastica(np.eye(3), np.random.default_rng(0), iters=0)

    def test_dual_regression_identity_and_variance_scaling(self):
        rng = np.random.default_rng(4)
        X = rng.normal(size=(12, 40))
        S = rng.normal(size=(3, 40))
        A = X @ np.linalg.pinv(S)
        maps = np.linalg.pinv(A) @ X
        correction = np.linalg.pinv(A) @ (X - A @ S)
        assert_allclose(maps, S + correction, atol=1e-11)
        D = np.diag(A.std(axis=0))
        normalized = A @ np.linalg.inv(D)
        assert_allclose(np.linalg.pinv(normalized) @ X, D @ maps, atol=1e-11)

    def test_gica1_full_unwhitened_reduction_equals_dual_regression(self):
        rng = np.random.default_rng(7)
        subjects = [rng.normal(size=(8, 40)) for _ in range(3)]
        Fs = [np.linalg.eigh(X @ X.T)[1].T for X in subjects]
        Y = np.vstack([F @ X for F, X in zip(Fs, subjects)])
        d, E = np.linalg.eigh(Y @ Y.T / Y.shape[1])
        G = E[:, -3:].T
        B = np.diag(np.sqrt(d[-3:]))
        S = np.linalg.solve(B, G @ Y)
        for X, F, Gi in zip(subjects, Fs, np.split(G, 3, axis=1)):
            reconstructed = F.T @ Gi.T @ B
            dual = X @ np.linalg.pinv(S)
            assert_allclose(reconstructed, dual, atol=1e-11)
            assert_allclose(np.linalg.pinv(Gi.T @ B) @ F @ X,
                            np.linalg.pinv(dual) @ X, atol=1e-10)

    def test_spatial_centering_is_not_global_signal_regression(self):
        rng = np.random.default_rng(9)
        X = rng.normal(size=(20, 8))
        X -= X.mean(axis=0, keepdims=True)
        g = X.mean(axis=1, keepdims=True)
        centered = X - g
        residual = X - g @ ((g.T @ X) / (g.T @ g))
        assert_allclose(g.T @ residual, np.zeros((1, 8)), atol=1e-12)
        self.assertGreater(np.linalg.norm(g.T @ centered), .1)
        self.assertLessEqual(np.linalg.matrix_rank(centered), 7)

    def test_fnc_sign_convention_and_effective_sample_size(self):
        rng = np.random.default_rng(10)
        A = rng.normal(size=(60, 3))
        A[:, 1] += .8 * A[:, 0]
        H = np.diag([-1., 1., -1.])
        R = np.corrcoef(A, rowvar=False)
        assert_allclose(np.corrcoef(A @ H, rowvar=False), H @ R @ H, atol=1e-12)
        self.assertEqual(53 * 52 // 2, 1378)
        effective = 300 * (1 - .8 ** 2) / (1 + .8 ** 2)
        self.assertEqual(round(effective), 66)


if __name__ == "__main__":
    unittest.main(verbosity=2)
