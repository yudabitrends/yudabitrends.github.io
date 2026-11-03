"""Regression checks for figure whitening and orthogonal updates."""
import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np

FIGURES = Path(__file__).resolve().parents[1] / "book" / "figures"
sys.path.insert(0, str(FIGURES))
from figstyle import whiten

def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), FIGURES / f"{name}.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

class FigureNumerics(unittest.TestCase):
    def test_population_normalization_and_centering(self):
        X = np.random.default_rng(71).normal(size=(3, 17)) + np.array([[2], [-3], [5]])
        Z, V = whiten(X)
        np.testing.assert_allclose(Z.mean(axis=1), 0, atol=1e-14)
        np.testing.assert_allclose(Z @ Z.T / X.shape[1], np.eye(3), atol=1e-13)
        np.testing.assert_allclose(V, V.T, atol=1e-14)

    def test_figure_helpers_use_same_convention(self):
        X = np.random.default_rng(19).normal(size=(3, 23))
        for name in ("fastica", "jade-sobi"):
            Z = module(name)._whiten(X)
            np.testing.assert_allclose(Z @ Z.T / X.shape[1], np.eye(3), atol=1e-13)

    def test_invalid_or_deficient_data_rejected(self):
        for X in (np.ones((2, 12)), np.eye(3), np.ones((3, 2)), np.array([1., 2.]),
                  np.array([[1., np.nan, 3.]]), np.empty((0, 2))):
            with self.subTest(shape=X.shape), self.assertRaises(ValueError):
                whiten(X)

    def test_svd_polar_update(self):
        orth = module("fastica")._sym_orth
        M = np.array([[1., 2.], [3., 5.]])
        W = orth(M)
        np.testing.assert_allclose(W @ W.T, np.eye(2), atol=1e-13)
        with self.assertRaises(ValueError):
            orth(np.zeros((2, 2)))

if __name__ == "__main__":
    unittest.main(verbosity=2)
