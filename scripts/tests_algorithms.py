"""Numerical checks for the ICA textbook's algorithm chapters.

Run: python scripts/tests_algorithms.py
Requires NumPy and SciPy. Loads actual chapter function definitions without
running the longer demonstrations. All random checks use fixed seeds.
"""
from pathlib import Path
import ast
import contextlib
import html
import io
import itertools
import re
import unittest

import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import quad
from scipy.optimize import linear_sum_assignment
from scipy.signal import lfilter
from scipy.special import gamma
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]


def load_definitions(chapter):
    text = (ROOT / 'book' / 'src' / (chapter + '.html')).read_text(encoding='utf-8')
    snippets = re.findall(r'<pre class="code" data-code="python"><code>(.*?)</code></pre>',
                          text, flags=re.S)
    assert snippets, chapter
    namespace = {}
    for snippet in snippets:
        tree = ast.parse(html.unescape(snippet), filename=chapter)
        tree.body = [item for item in tree.body
                     if isinstance(item, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
        exec(compile(tree, chapter, 'exec'), namespace)
    return namespace


FAST = load_definitions('fastica')
JD = load_definitions('jade-sobi')
NG = load_definitions('natural-gradient')


def leakage(G):
    """One-to-one assignment, normalized by each matched diagonal gain."""
    R = np.abs(G) / np.linalg.norm(G, axis=1, keepdims=True)
    rows, cols = linear_sum_assignment(-R)
    matched = G[rows][:, cols]
    normalized = matched / np.diag(matched)[:, None]
    return np.max(np.abs(normalized - np.eye(len(G))))


def off_diagonal_energy(Qs):
    diagonal = np.diagonal(Qs, axis1=-2, axis2=-1)
    return np.sum(Qs * Qs) - np.sum(diagonal * diagonal)


class AlgorithmChecks(unittest.TestCase):
    def test_whitening_convention_and_training_mean(self):
        rng = np.random.default_rng(12)
        X = np.array([[2., .4, -.1], [.2, 1., .5], [-.1, .1, 1.]]) @ rng.normal(size=(3, 600))
        X += np.array([[15.], [-7.], [3.]])
        Z, V, mean = FAST['whiten'](X)
        assert_allclose(Z @ Z.T / X.shape[1], np.eye(3), atol=2e-12)
        assert_allclose(Z.mean(axis=1), 0, atol=2e-14)
        assert_allclose(Z, V @ (X - mean), atol=1e-14)
        Zj, Vj = JD['whiten'](X)
        assert_allclose(Zj @ Zj.T / X.shape[1], np.eye(3), atol=2e-12)
        assert_allclose(Zj, Vj @ (X - mean), atol=1e-14)

    def test_whitening_rejects_invalid_data(self):
        bad = [np.ones((2, 20)), np.ones((2, 2)), np.array([[1., np.nan, 2.]]),
               np.ones(5), np.empty((0, 5)), np.vstack([np.arange(10), np.arange(10)])]
        for name, namespace in [('FastICA', FAST), ('JADE', JD)]:
            for X in bad:
                with self.subTest(name=name, shape=X.shape):
                    with self.assertRaises(ValueError):
                        namespace['whiten'](X)

    def test_polar_factor_and_failure_paths(self):
        rng = np.random.default_rng(3)
        W = rng.normal(size=(4, 4))
        Q = FAST['sym_orth'](W)
        assert_allclose(Q @ Q.T, np.eye(4), atol=2e-14)
        for bad in [np.zeros((3, 3)), np.ones((3, 3)), np.full((2, 2), np.inf)]:
            with self.assertRaises(ValueError):
                FAST['sym_orth'](bad)
        X = rng.normal(size=(3, 100))
        with self.assertRaises(RuntimeError):
            FAST['fastica_symmetric'](X, np.tanh, lambda x: 1-np.tanh(x)**2, max_iter=0)

    def test_fastica_and_jade_separation(self):
        rng = np.random.default_rng(44)
        T = 24000
        S = np.vstack([rng.laplace(0, 1/np.sqrt(2), T),
                       rng.uniform(-np.sqrt(3), np.sqrt(3), T),
                       np.sign(rng.normal(size=T))])
        A = np.array([[1., .4, -.3], [.3, 1.2, .2], [-.2, .1, 1.1]])
        X = A @ S + np.array([[20.], [-8.], [3.]])
        with contextlib.redirect_stdout(io.StringIO()):
            W, mean = FAST['fastica_symmetric'](X, np.tanh, lambda x: 1-np.tanh(x)**2)
        self.assertLess(leakage(W @ A), .05)
        Y = W @ (X - mean)
        assert_allclose(Y, W @ A @ (S-S.mean(axis=1, keepdims=True)), atol=3e-14)
        assert_allclose(Y @ Y.T / T, np.eye(3), atol=1e-12)
        self.assertLess(leakage(JD['jade'](X) @ A), .05)

    def test_exact_cubic_population_update(self):
        # Independent symmetric finite laws with kurtoses -2, 0 and 2.
        supports = [np.array([-1., 1.]), np.array([-np.sqrt(3), 0, np.sqrt(3)]),
                    np.array([-np.sqrt(5), 0, np.sqrt(5)])]
        weights = [np.array([.5, .5]), np.array([1/6, 2/3, 1/6]), np.array([.1, .8, .1])]
        combinations = list(itertools.product(*[range(len(x)) for x in supports]))
        S = np.array([[supports[j][indices[j]] for indices in combinations] for j in range(3)])
        p = np.array([np.prod([weights[j][indices[j]] for j in range(3)]) for indices in combinations])
        q = np.array([.4, .5, .7]); q /= np.linalg.norm(q)
        y = q @ S
        updated = (S * (p*y**3)) .sum(axis=1) - 3*q
        assert_allclose(updated, np.array([-2., 0., 2.])*q**3, atol=2e-15)
        # Stein identity gives an exactly zero Gaussian tanh update.
        density = lambda x: np.exp(-x*x/2)/np.sqrt(2*np.pi)
        residual = quad(lambda x: (x*np.tanh(x)-(1-np.tanh(x)**2))*density(x),
                        -np.inf, np.inf, epsabs=1e-12)[0]
        self.assertAlmostEqual(residual, 0., places=12)

    def test_jacobi_angle_against_exhaustive_grid(self):
        rng = np.random.default_rng(6)
        M = rng.normal(size=(7, 2, 2)); M = (M+M.transpose(0, 2, 1))/2
        h1 = M[:, 0, 0]-M[:, 1, 1]; h2 = 2*M[:, 0, 1]
        theta = .25*np.arctan2(2*h1@h2, h1@h1-h2@h2)
        value = np.sum((-np.sin(2*theta)*h1+np.cos(2*theta)*h2)**2)/2
        grid = np.linspace(-np.pi/4, np.pi/4, 20001)
        exhaustive = np.sum((-np.sin(2*grid[:, None])*h1+np.cos(2*grid[:, None])*h2)**2, axis=1)/2
        self.assertLessEqual(value, exhaustive.min()+1e-12)
        U = JD['joint_diagonalize'](M)
        self.assertAlmostEqual(off_diagonal_energy(U @ M @ U.T), value, places=11)

    def test_joint_diagonalizer_and_signature_gap(self):
        rng = np.random.default_rng(7)
        Q, _ = np.linalg.qr(rng.normal(size=(4, 4)))
        signatures = rng.normal(size=(6, 4))
        D = np.array([np.diag(row) for row in signatures])
        M = Q @ D @ Q.T
        U = JD['joint_diagonalize'](M)
        assert_allclose(U @ U.T, np.eye(4), atol=1e-13)
        self.assertLess(abs(off_diagonal_energy(U @ M @ U.T)), 1e-11)
        theta = .17
        R = np.eye(4); c,s=np.cos(theta),np.sin(theta)
        R[:2,:2] = [[c,-s],[s,c]]
        expected = .5*np.sin(2*theta)**2 * np.sum((signatures[:,0]-signatures[:,1])**2)
        self.assertAlmostEqual(off_diagonal_energy(R.T @ D @ R), expected, places=12)
        with self.assertRaises(RuntimeError):
            JD['joint_diagonalize'](M, max_sweeps=0)
        for bad in [np.zeros((0, 2, 2)), np.zeros((2, 0, 0)), np.ones((2, 2, 3)),
                    np.array([[[1., 2.], [0., 1.]]]), np.full((2,2,2), np.nan)]:
            with self.assertRaises(ValueError): JD['joint_diagonalize'](bad)

    def test_sobi_temporal_separation_and_lag_guards(self):
        rng=np.random.default_rng(8); T=40000
        S=np.vstack([lfilter([np.sqrt(1-a*a)], [1,-a], rng.normal(size=T+600))[600:]
                     for a in [.2, .7, -.8]])
        A=np.array([[1., .4, .2], [-.3, 1.1, .2], [.1, -.2, 1.]])
        X=A@S
        self.assertLess(leakage(JD['sobi'](X, [1,2,3,5,7]) @ A), .06)
        for lags in [[], [0], [-1], [1.5], [T], [1, T+1]]:
            with self.assertRaises(ValueError): JD['sobi'](X, lags)

    def test_likelihood_gradient_and_equivariance(self):
        rng=np.random.default_rng(9); X=rng.laplace(size=(3, 500))
        W=np.eye(3)+.08*rng.normal(size=(3,3)); Y=W@X
        gradient=np.linalg.inv(W).T-np.tanh(Y)@X.T/X.shape[1]
        def objective(M):
            U=M@X
            logcosh=np.abs(U)+np.log1p(np.exp(-2*np.abs(U)))-np.log(2)
            return np.linalg.slogdet(M)[1]-np.mean(logcosh.sum(axis=0))
        numerical=np.zeros_like(W); h=1e-6
        for i,j in itertools.product(range(3), repeat=2):
            E=np.zeros_like(W); E[i,j]=h
            numerical[i,j]=(objective(W+E)-objective(W-E))/(2*h)
        assert_allclose(gradient, numerical, atol=1e-9, rtol=2e-8)
        relative=(np.eye(3)-np.tanh(Y)@Y.T/X.shape[1])@W
        assert_allclose(relative, gradient@W.T@W, atol=2e-15)
        self.assertGreater(np.sum(gradient*relative), 0)
        A=np.array([[1.,.4,.2],[-.2,1.,.1],[.1,.3,1.2]])
        B=W@np.linalg.inv(A); Z=A@X; V=B@Z
        updated=B+.03*(np.eye(3)-np.tanh(V)@V.T/X.shape[1])@B
        assert_allclose(updated@A,W+.03*relative,atol=1e-14)
        result=NG['natural_gradient_ica'](X,np.tanh,mu=.03,iters=1)
        assert_allclose(result,np.eye(3)+.03*(np.eye(3)-np.tanh(X)@X.T/X.shape[1]),atol=1e-15)

    def test_variance_table_by_independent_quadrature(self):
        sech=lambda x: 2*np.exp(-abs(x))/(1+np.exp(-2*abs(x)))
        laws=[('Laplace',lambda x: np.exp(-np.sqrt(2)*abs(x))/np.sqrt(2),np.inf,[2.01,1.82,6.00]),
              ('sech',lambda x: .5*sech(np.pi*x/2),np.inf,[4.43,4.37,9.00]),
              ('logistic',lambda x: np.pi/(4*np.sqrt(3))*sech(np.pi*x/(2*np.sqrt(3)))**2,np.inf,[10.37,10.96,15.43]),
              ('uniform',lambda x: 1/(2*np.sqrt(3)),np.sqrt(3),[.69,.71,.43])]
        nonlinearities=[(np.tanh,lambda x: 1-np.tanh(x)**2),
                        (lambda x:x*np.exp(-x*x/2),lambda x:(1-x*x)*np.exp(-x*x/2)),
                        (lambda x:x**3,lambda x:3*x*x)]
        for name,p,bound,expected in laws:
            E=lambda f: 2*quad(lambda x:f(x)*p(x),0,bound,epsabs=1e-10)[0]
            self.assertAlmostEqual(E(lambda x:x*x),1.,places=10)
            for index,(g,dg) in enumerate(nonlinearities):
                mu=E(lambda x:x*g(x))
                V=(E(lambda x:g(x)**2)-mu**2)/(mu-E(dg))**2
                with self.subTest(law=name,contrast=index):
                    self.assertLess(abs(V-expected[index]),.0051)

    def test_centering_fisher_and_dependent_sample_constants(self):
        E=lambda f: quad(lambda x:f(x)*np.exp(-(x+1)),-1,np.inf,epsabs=1e-10)[0]
        g=np.tanh; mu=E(lambda x:x*g(x)); den=(mu-E(lambda x:1-g(x)**2))**2
        uncentered=(E(lambda x:g(x)**2)-mu**2)/den
        centered=uncentered-E(g)**2/den
        self.assertLess(abs(uncentered-3.75),.005)
        self.assertLess(abs(centered-3.14),.005)
        nu=5; scale=np.sqrt((nu-2)/nu)
        fisher=quad(lambda x: ((nu+1)*x/(nu-2+x*x))**2*student_t.pdf(x/scale,nu)/scale,
                    -np.inf,np.inf,epsabs=1e-11)[0]
        self.assertAlmostEqual(fisher,nu*(nu+1)/((nu-2)*(nu+3)),places=10)
        alpha=4.; beta=np.sqrt(gamma(1/alpha)/gamma(3/alpha))
        genfisher=2*quad(lambda x:(alpha*x**(alpha-1)/beta**alpha)**2 *
                         alpha*np.exp(-(x/beta)**alpha)/(2*beta*gamma(1/alpha)),0,np.inf)[0]
        self.assertAlmostEqual(genfisher,alpha**2*gamma(2-1/alpha)*gamma(3/alpha)/gamma(1/alpha)**2,places=10)
        info=np.array([[2.,1.],[1.,1.25]])
        self.assertAlmostEqual(np.linalg.inv(info)[0,0],1.25/(2*1.25-1),places=14)
        series=1+2*np.sum(.8**(2*np.arange(1,1000)))
        self.assertAlmostEqual(series,(1+.8**2)/(1-.8**2),places=13)


if __name__ == '__main__':
    unittest.main(verbosity=2)
