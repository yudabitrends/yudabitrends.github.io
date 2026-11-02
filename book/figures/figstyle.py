"""Shared style and helpers for the ICA book figures (see make_figures.py)."""
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402,F401

OUT = Path(__file__).resolve().parents[2] / "docs" / "ica" / "fig"
OUT.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e8c"   # blue: sources, main curves
RED = "#b0413e"      # red: mixtures, contrasts
GREEN = "#4f7a3a"    # green: estimates
GRAY = "#6b6b6b"     # gray: whitened data, reference lines
LIGHT = "#d2d9e3"    # light gray: grid and axes at zero

plt.rcParams.update({
    "font.family": "STIXGeneral",
    "mathtext.fontset": "stix",
    "font.size": 10.5,
    "axes.titlesize": 10.5,
    "axes.labelsize": 10.5,
    "axes.edgecolor": "#3f3f3f",
    "axes.linewidth": 0.8,
    "xtick.color": "#3f3f3f",
    "ytick.color": "#3f3f3f",
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "svg.fonttype": "path",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
})

FIGS = {}


def figure(fn):
    """Register a figure function; its name (underscores -> hyphens) is the output file name."""
    FIGS[fn.__name__] = fn
    return fn


def save(fig, name):
    """Write docs/ica/fig/<name>.svg. Text becomes paths; dense scatters should use rasterized=True."""
    path = OUT / f"{name}.svg"
    fig.savefig(path, format="svg", dpi=220, metadata={"Date": None})
    plt.close(fig)
    print(f"wrote docs/ica/fig/{path.name}")


def whiten(X):
    """Center the rows of X (n x T) and whiten with the symmetric inverse square root."""
    X = X - X.mean(axis=1, keepdims=True)
    d, E = np.linalg.eigh(np.cov(X))
    V = E @ np.diag(d ** -0.5) @ E.T
    return V @ X, V


def kurt(y):
    y = y - y.mean()
    return np.mean(y ** 4) - 3 * np.mean(y ** 2) ** 2


def style_scatter(ax, title, lim=None):
    ax.set_title(title, pad=4)
    ax.set_aspect("equal")
    if lim is not None:
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
    ax.axhline(0, color=LIGHT, lw=0.6, zorder=0)
    ax.axvline(0, color=LIGHT, lw=0.6, zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def clean_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
