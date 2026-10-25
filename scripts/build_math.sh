#!/usr/bin/env bash
# Typeset the displayed formulas of docs/index.html as SVG.
#
# Each formula is set with LaTeX (newtx: Times text and math, matching the
# page's Times New Roman) and converted with dvisvgm, glyphs as paths.
# Requires latex and dvisvgm (TeX Live). Run from anywhere:
#   bash scripts/build_math.sh
# then copy the printed width/height into the <img> tags if they changed.

set -euo pipefail

OUT="$(cd "$(dirname "$0")/.." && pwd)/docs/assets/math"
SCALE=1.1        # 12pt LaTeX at this scale sits slightly above 16px body text
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT"

mk() {
  local name=$1 body=$2
  cat > "$WORK/$name.tex" <<EOF
\\documentclass[12pt,border=1pt]{standalone}
\\usepackage{amsmath}
\\usepackage{newtxtext,newtxmath}
\\begin{document}
\$\\displaystyle $body\$
\\end{document}
EOF
  (cd "$WORK" && latex -interaction=nonstopmode -halt-on-error "$name.tex" >/dev/null)
  (cd "$WORK" && dvisvgm --no-fonts --exact-bbox --verbosity=1 -o "$name.svg" "$name.dvi" >/dev/null 2>&1)
  # Convert the pt dimensions to px at SCALE, keep the viewBox.
  awk -v s="$SCALE" '
    !done && /<svg / {
      match($0, /width=.[0-9.]+pt./);  w = substr($0, RSTART+7, RLENGTH-10)
      match($0, /height=.[0-9.]+pt./); h = substr($0, RSTART+8, RLENGTH-11)
      W = sprintf("%d", w * 4/3 * s + 0.5); H = sprintf("%d", h * 4/3 * s + 0.5)
      sub(/width=.[0-9.]+pt./,  "width=\x27" W "\x27")
      sub(/height=.[0-9.]+pt./, "height=\x27" H "\x27")
      printf "%-26s width=%s height=%s\n", FILENAME, W, H > "/dev/stderr"
      done = 1
    }
    { print }' "$WORK/$name.svg" > "$OUT/$name.svg"
}

# I. A 1/R law for kurtosis contrast in balanced mixtures
mk kurtosis-law '|\kappa(y)| \le \frac{\kappa_{\max}}{R_{\mathrm{eff}}}, \qquad R_{\mathrm{eff}} = \Bigl(\sum_{j} w_j^{4}\Bigr)^{-1}'

# II. Zeros that survive mixing
mk zeros-law '\Phi_{x}(\omega) = \prod_{j=1}^{q} \chi_j\bigl(a_j^{\top}\omega\bigr)'

# III. Normalization mismatch in ICA
mk normalization-law '\rho_g^2\,\tau_{g,N}^2 = \underbrace{v_g N\|A\|^2}_{\text{score exposure}} + \underbrace{\gamma_g^2 N\|A-W\|^2}_{\text{scale channel}} + \underbrace{\eta_g^2 N\|A-U\|^2}_{\text{location channel}}'
mk normalization-law-narrow '\begin{aligned} \rho_g^2\,\tau_{g,N}^2 &= \underbrace{v_g N\|A\|^2}_{\text{score exposure}} \\ &\quad + \underbrace{\gamma_g^2 N\|A-W\|^2}_{\text{scale channel}} \\ &\quad + \underbrace{\eta_g^2 N\|A-U\|^2}_{\text{location channel}} \end{aligned}'
mk normalization-remedy 'G_{\kappa,\vartheta}(y) = G(y) - \kappa y - \tfrac{1}{2}\vartheta y^2'

# IV. Sharp two-sided residual certificates
mk certificates-law '\frac{r(B)}{\sqrt{2}\,\Gamma} \le D(B) \le K(\eta)\,\frac{r(B)}{\gamma}'

# V. Heat constraints from exponential correlations
mk heat-law '\sigma \ge \frac{q^2}{2q + \Delta_C/D_X}, \qquad q = \frac{Q_X}{k_B T_X}'
mk heat-threshold '\Delta_C = 0,\; Q_X > 0 \quad\Longrightarrow\quad \sigma > \frac{Q_X}{2k_B T_X} \quad\text{and}\quad T_H > 2T_X'
mk heat-threshold-narrow '\begin{gathered} \Delta_C = 0,\; Q_X > 0 \;\Longrightarrow \\[4pt] \sigma > \frac{Q_X}{2k_B T_X}, \qquad T_H > 2T_X \end{gathered}'

# VI. Two probes recover the bath heat
mk probes-law '\frac{\dot{Q}_i}{k_B T_i} = \alpha_i - \beta'
mk probes-tails 'r_{k} = R_{+}\,a_1^{\,k-1}, \qquad r_{-k} = R_{-}\,a_2^{\,k-1}, \qquad a_i = e^{-\alpha_i \Delta}'
