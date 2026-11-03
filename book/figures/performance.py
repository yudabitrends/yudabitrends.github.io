"""Figures for Chapter 10, Asymptotic Performance and the Cramer-Rao Bound."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, FuncFormatter

from figstyle import figure, save, clean_axes, ACCENT, RED, GREEN, GRAY, LIGHT

B = 1 / np.sqrt(2)          # Laplace scale for unit variance
R3 = np.sqrt(3)             # uniform half-width for unit variance
NONLIN = {
    "tanh": (np.tanh, lambda u: 1 - np.tanh(u) ** 2),
    "gauss": (lambda u: u * np.exp(-u * u / 2), lambda u: (1 - u * u) * np.exp(-u * u / 2)),
    "pow3": (lambda u: u ** 3, lambda u: 3 * u ** 2),
}


def _draw(rng, law, shape):
    if law == "laplace":
        return rng.laplace(0, B, shape)
    return rng.uniform(-R3, R3, shape)


def _predicted(law, g, dg):
    """V_g by numerical quadrature on a fine grid."""
    if law == "laplace":
        s = np.linspace(-40, 40, 800001)
        p = np.exp(-np.abs(s) / B) / (2 * B)
    else:
        s = np.linspace(-R3, R3, 800001)
        p = np.full_like(s, 1 / (2 * R3))
    E = lambda f: np.trapezoid(f * p, s)
    Esg, Edg = E(s * g(s)), E(dg(s))
    return (E(g(s) ** 2) - Esg ** 2) / (Esg - Edg) ** 2


def _one_unit_isr(rng, target, other, g, dg, T, R, max_iter=200, tol=1e-12):
    """Per-run T*ISR and exhaustive diagnostics for a bounded-memory batch.

    Only converged runs whose target gain exceeds the other gain contribute.
    A finite-iteration estimate is never silently treated as converged. Runs
    freeze individually at the sign-invariant tolerance; zero/nonfinite
    updates are numerical failures. R is the batch size, not the plotted n.
    """
    if T < 3 or R < 1 or max_iter < 0 or tol <= 0:
        raise ValueError("Need T >= 3, R >= 1, max_iter >= 0 and tol > 0")
    S = np.stack([_draw(rng, target, (R, T)), _draw(rng, other, (R, T))], 1)
    A = np.array([[1.0, 0.6], [0.4, 1.0]])
    X = A @ S
    X -= X.mean(axis=2, keepdims=True)
    d, E = np.linalg.eigh(X @ X.transpose(0, 2, 1) / T)
    V = E @ (d[:, :, None] ** -0.5 * E.transpose(0, 2, 1))
    Z = V @ X
    VA = V @ A
    w = np.linalg.inv(VA).transpose(0, 2, 1)[:, :, 0]
    w /= np.linalg.norm(w, axis=1, keepdims=True)
    converged = np.zeros(R, dtype=bool)
    numerical_failure = np.zeros(R, dtype=bool)
    iterations = np.zeros(R, dtype=int)
    for iteration in range(1, max_iter + 1):
        active = np.flatnonzero(~converged & ~numerical_failure)
        if active.size == 0:
            break
        Za = Z[active]
        wa = w[active]
        y = np.einsum("ri,rit->rt", wa, Za)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            wn = np.einsum("rit,rt->ri", Za, g(y)) / T - dg(y).mean(1)[:, None] * wa
            norms = np.linalg.norm(wn, axis=1)
        good = np.isfinite(wn).all(axis=1) & np.isfinite(norms) & (norms > 0)
        numerical_failure[active[~good]] = True
        iterations[active] = iteration
        wn = wn[good] / norms[good, None]
        delta = np.clip(1 - np.abs(np.sum(wn * wa[good], axis=1)), 0, 1)
        w[active[good]] = wn
        converged[active[good][delta < tol]] = True
    q = np.einsum("ri,rij->rj", w, VA)
    numerical_failure |= ~np.isfinite(q).all(axis=1)
    converged &= ~numerical_failure
    target_dominant = np.abs(q[:, 0]) > np.abs(q[:, 1])
    accepted = converged & target_dominant
    nonconverged = ~converged & ~numerical_failure
    wrong_target = converged & ~target_dominant
    stats = {
        "attempted": R,
        "converged": int(converged.sum()),
        "effective": int(accepted.sum()),
        "nonconverged": int(nonconverged.sum()),
        "wrong_target": int(wrong_target.sum()),
        "numerical_failure": int(numerical_failure.sum()),
        "max_iterations": int(iterations.max()),
    }
    assert stats["attempted"] == sum(stats[key] for key in
                                    ("effective", "nonconverged", "wrong_target", "numerical_failure"))
    assert stats["converged"] == stats["effective"] + stats["wrong_target"]
    return T * (q[accepted, 1] / q[accepted, 0]) ** 2, stats


def _summarize_isr(batches):
    """Conditional mean/Monte Carlo SE plus all attempted-run outcomes."""
    vals = np.concatenate([values for values, _ in batches])
    keys = ("attempted", "converged", "effective", "nonconverged", "wrong_target", "numerical_failure")
    stats = {key: sum(batch[key] for _, batch in batches) for key in keys}
    stats["max_iterations"] = max(batch["max_iterations"] for _, batch in batches)
    assert vals.size == stats["effective"]
    assert stats["attempted"] == sum(stats[key] for key in
                                    ("effective", "nonconverged", "wrong_target", "numerical_failure"))
    if vals.size < 2:
        raise RuntimeError(f"Need at least two effective independent runs: {stats}")
    return vals.mean(), vals.std(ddof=1) / np.sqrt(vals.size), stats


@figure
def ch10_isr():
    """Empirical T*ISR of one-unit FastICA against the asymptotic variance V_g."""
    rng = np.random.default_rng(10)
    Ts = [500, 1000, 2000, 5000, 10000]
    panels = [("laplace", "uniform"), ("uniform", "laplace")]
    styles = {"tanh": (ACCENT, "o", r"$\tanh u$"),
              "gauss": (GREEN, "s", r"$u\,e^{-u^2/2}$"),
              "pow3": (RED, "^", r"$u^3$")}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for ax, (target, other), tag in zip(axes, panels, ["(a)", "(b)"]):
        for k, (name, (g, dg)) in enumerate(NONLIN.items()):
            col, mk, lab = styles[name]
            Vg = _predicted(target, g, dg)
            means, ses = [], []
            for T in Ts:
                # 100 runs per batch bounds the large arrays at about 16 MB
                # each when T=10000; only ISR scalars survive between batches.
                out = [_one_unit_isr(rng, target, other, g, dg, T, 100) for _ in range(15)]
                mean, se, stats = _summarize_isr(out)
                assert stats["attempted"] == 1500
                means.append(mean)
                ses.append(se)
                failures = stats["attempted"] - stats["effective"]
                print(f"  {target:8s} {name:5s} T={T:5d} attempted={stats['attempted']} "
                      f"converged={stats['converged']} effective={stats['effective']} failures={failures} "
                      f"nonconverged={stats['nonconverged']} wrong_target={stats['wrong_target']} "
                      f"numerical={stats['numerical_failure']} max_iter={stats['max_iterations']} "
                      f"mean={mean:.6f} se={se:.6f}", flush=True)
            x = np.array(Ts) * (1 + 0.06 * (k - 1))
            ax.errorbar(x, means, yerr=2 * np.array(ses), fmt=mk, color=col, ms=4, lw=0.9,
                        capsize=2, label=lab)
            ax.axhline(Vg, color=col, lw=0.9, ls="--")
            print(f"  {target:8s} {name:5s} V_g={Vg:.3f} " + " ".join(f"{m:.2f}" for m in means), flush=True)
        if target == "laplace":
            ax.axhline(1.0, color=GRAY, lw=0.9, ls=":")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_locator(FixedLocator(Ts))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        yt = [1, 2, 4, 6] if target == "laplace" else [0.4, 0.5, 0.6, 0.8]
        ax.yaxis.set_major_locator(FixedLocator(yt))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_xlabel("$T$")
        ax.set_title(tag, pad=4)
        clean_axes(ax)
    axes[0].set_ylabel(r"$T\cdot\mathrm{ISR}$")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=10, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06))
    fig.subplots_adjust(wspace=0.28, bottom=0.25)
    with plt.rc_context({"svg.hashsalt": "ch10-isr"}):   # stable element ids
        save(fig, "ch10-isr")
