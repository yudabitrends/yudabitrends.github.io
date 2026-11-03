"""Regression checks for convergence accounting in the Chapter 10 figure."""
from pathlib import Path
import importlib.util
import sys
import unittest

import numpy as np

FIGURES = Path(__file__).resolve().parents[1] / 'book' / 'figures'
sys.path.insert(0, str(FIGURES))
spec = importlib.util.spec_from_file_location('ica_performance_figure', FIGURES / 'performance.py')
performance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(performance)


class FigureAccountingChecks(unittest.TestCase):
    def batch(self, R=24, T=1000, **kwargs):
        return performance._one_unit_isr(np.random.default_rng(123), 'laplace', 'uniform',
                                         *performance.NONLIN['tanh'], T, R, **kwargs)

    def test_successful_runs_have_exhaustive_counts(self):
        values, counts = self.batch()
        self.assertEqual(counts['attempted'], 24)
        self.assertEqual(counts['effective'], values.size)
        self.assertEqual(counts['converged'], counts['effective'] + counts['wrong_target'])
        self.assertEqual(counts['attempted'], sum(counts[k] for k in
                         ['effective', 'wrong_target', 'nonconverged', 'numerical_failure']))
        self.assertEqual(counts['effective'], 24)
        self.assertTrue(np.isfinite(values).all())
        self.assertTrue((values >= 0).all())

    def test_iteration_exhaustion_does_not_pass_target_filter(self):
        # Even an exact target initialization must not be labelled converged
        # without applying and checking the fixed-point update.
        values, counts = self.batch(max_iter=0)
        self.assertEqual(values.size, 0)
        self.assertEqual(counts['nonconverged'], 24)
        self.assertEqual(counts['converged'], 0)
        self.assertEqual(counts['max_iterations'], 0)
        with self.assertRaises(RuntimeError):
            performance._summarize_isr([(values, counts)])

    def test_zero_update_is_a_numerical_failure(self):
        zero = lambda y: np.zeros_like(y)
        values, counts = performance._one_unit_isr(np.random.default_rng(124),
            'laplace', 'uniform', zero, zero, 200, 12)
        self.assertEqual(values.size, 0)
        self.assertEqual(counts['numerical_failure'], 12)
        self.assertEqual(counts['nonconverged'], 0)
        self.assertEqual(counts['converged'], 0)
        self.assertEqual(counts['max_iterations'], 1)

    def test_wrong_target_and_nonconvergence_are_distinct(self):
        # Deliberately tiny samples expose both failure modes. Do not pin
        # platform-sensitive exact counts; the exhaustive partition is key.
        values, counts = performance._one_unit_isr(np.random.default_rng(123),
            'laplace', 'uniform', *performance.NONLIN['pow3'], 6, 128, max_iter=80)
        self.assertGreater(counts['wrong_target'], 0)
        self.assertGreater(counts['nonconverged'], 0)
        self.assertEqual(values.size, counts['effective'])
        self.assertEqual(counts['attempted'], sum(counts[k] for k in
                         ['effective', 'wrong_target', 'nonconverged', 'numerical_failure']))
        self.assertEqual(counts['converged'], counts['effective'] + counts['wrong_target'])

    def test_monte_carlo_se_uses_sample_standard_deviation(self):
        def counts(n):
            return dict(attempted=n, converged=n, effective=n, nonconverged=0,
                        wrong_target=0, numerical_failure=0, max_iterations=3)
        mean, se, combined = performance._summarize_isr([
            (np.array([1., 3.]), counts(2)), (np.array([5.]), counts(1))])
        self.assertAlmostEqual(mean, 3.)
        self.assertAlmostEqual(se, 2/np.sqrt(3))  # sample variance = 4, not 8/3
        self.assertEqual(combined['attempted'], 3)
        self.assertEqual(combined['effective'], 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
