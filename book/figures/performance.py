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


def _one_unit_isr(rng, target, other, g, dg, T, R):
    """T * mean(eps^2) for one-unit FastICA started at the target direction (n = 2)."""
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
    for _ in range(200):
        y = np.einsum("ri,rit->rt", w, Z)
        wn = np.einsum("rit,rt->ri", Z, g(y)) / T - dg(y).mean(1)[:, None] * w
        wn /= np.linalg.norm(wn, axis=1, keepdims=True)
        delta = np.max(1 - np.abs(np.sum(wn * w, 1)))
        w = wn
        if delta < 1e-12:
            break
    q = np.einsum("ri,rij->rj", w, VA)
    ok = np.abs(q[:, 0]) > np.abs(q[:, 1])      # converged to the target, not the other source
    return T * (q[ok, 1] / q[ok, 0]) ** 2, np.count_nonzero(~ok)


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
            means, ses, lost = [], [], 0
            for T in Ts:
                out = [_one_unit_isr(rng, target, other, g, dg, T, 500) for _ in range(3)]
                vals = np.concatenate([o[0] for o in out])
                lost += sum(o[1] for o in out)
                means.append(vals.mean())
                ses.append(vals.std() / np.sqrt(vals.size))
            x = np.array(Ts) * (1 + 0.06 * (k - 1))
            ax.errorbar(x, means, yerr=2 * np.array(ses), fmt=mk, color=col, ms=4, lw=0.9,
                        capsize=2, label=lab)
            ax.axhline(Vg, color=col, lw=0.9, ls="--")
            print(f"  {target:8s} {name:5s} V_g={Vg:.3f} " + " ".join(f"{m:.2f}" for m in means) + f"  lost={lost}")
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
