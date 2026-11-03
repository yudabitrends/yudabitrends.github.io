# Authoring guide for *Independent Component Analysis: From Foundations to Frontiers*

A bilingual (English / Simplified Chinese) open book on ICA, published at
`https://yuda-bi.com/ica/`. Readers switch between English, Chinese, and both
languages paragraph by paragraph. Chapter 1 (`book/src/ica-problem.html`) is the
reference implementation of everything below: **read it fully before writing.**

## 1. Files

| What | Where |
|---|---|
| Chapter source (you write this) | `book/src/<slug>.html` |
| Figures for your chapter (optional) | `book/figures/<slug>.py` → `docs/ica/fig/<chNN>-<name>.svg` |
| Parts, titles, summaries, KaTeX macros | `book/book.json` (do not edit) |
| Build script | `book/build.mjs` (do not edit) |
| Styles | `docs/assets/book.css` (do not edit) |

Never edit files that belong to another chapter, the build script, the CSS, the
manifest or this guide. If you need a new macro or a style, say so in your report.

## 2. Build and check

```
node book/build.mjs --check --only <slug>     # renders into a temp dir, prints warnings
python3 book/figures/make_figures.py <slug>   # regenerates your figures
```

Your chapter is done only when `--check --only <slug>` prints **no warnings** for
it, except `unresolved reference` warnings for IDs that the registry (section 9)
assigns to chapters not yet written. KaTeX errors, unmatched `$`, duplicate IDs,
missing images and unbalanced languages must all be fixed.

## 3. Source format

A chapter file is an HTML fragment: a sequence of `<h2>` sections. The build adds
the chapter title, numbering, the contents sidebar and navigation. Write
attributes in the exact order shown (the build parses them with simple patterns):
`class` first, then the others.

### Bilingual blocks

Every block of prose comes as an English element immediately followed by its
Chinese twin, with the same content:

```html
<p lang="en">English paragraph with inline math $\bx = \bA\bs$.</p>
<p lang="zh-CN">中文段落，包含行内公式 $\bx = \bA\bs$。</p>

<ul lang="en"><li>…</li></ul>
<ul lang="zh-CN"><li>…</li></ul>
```

`p`, `ul`, `ol` and `dl` can carry `lang`. Headings, figure captions, table
cells and other short labels use paired spans:

```html
<h2 id="sec-whitening-matrices"><span lang="en">Whitening matrices</span><span lang="zh-CN">白化矩阵</span></h2>
```

Every `<h2>` needs an `id` (see the registry for required ones; otherwise use
`sec-<slug>-<topic>`). Use `<h3>` (with spans, no id needed) for subsections.
The build warns if the counts of `lang="en"` and `lang="zh-CN"` differ.

### Mathematics (KaTeX)

* Inline `$…$`, display `$$…$$`. Display math always sits in its own block:
  `<div class="eq" id="eq-…">$$…$$</div>` is **numbered** (the build appends
  `\tag{N.k}`; never write `\tag` yourself), `<div class="eq">$$…$$</div>` is
  unnumbered. Only give an `id` to equations you refer to.
* Math is shared between languages: put display equations **between** the
  bilingual paragraph pairs, not inside them. Inline math is repeated in both twins.
* Inside math you may write `<`, `>` and `&` directly (alignment `&` in
  `aligned`). Outside math, escape them as `&lt;`, `&gt;`, `&amp;`. A literal
  dollar sign in text is `\$`. Never put `$` in an attribute.
* Use `\begin{aligned}…\end{aligned}`, `\begin{cases}`, `\begin{pmatrix}`,
  `\bigl(\begin{smallmatrix}…\end{smallmatrix}\bigr)` for inline matrices.
  No `equation`, `align` or `\label`.
* Macros defined in `book.json` (use them, do not redefine):
  `\E \R \C \Ncal \Cov \Var \kurt \cum \diag \offdiag \tr \sign \rank \vecop
  \argmax \argmin \iid`, bold vectors `\bx \bs \by \bz \bw \ba \bb \bu \bv \be \bn
  \bq \bt \bzero`, bold matrices `\bA \bB \bC \bD \bF \bG \bH \bI \bJ \bK \bM \bP
  \bQ \bR \bS \bT \bU \bV \bW \bX \bY \bZ`, bold Greek `\bLambda \bPi \bSigma
  \bpsi \bphi \bmu \bomega \btheta \bepsilon`.

### Numbered environments

```html
<div class="env" data-kind="theorem" id="thm-comon" data-en="Comon" data-zh="Comon">
  <p lang="en">Statement…</p>
  <p lang="zh-CN">陈述……</p>
</div>
<div class="proof">
  <p lang="en">…</p>
  <p lang="zh-CN">……</p>
</div>
```

`data-kind` is one of `definition theorem lemma proposition corollary example
remark algorithm assumption fact`; all share one counter per chapter
("Theorem 4.3", "定理 4.3"). `data-en`/`data-zh` give an optional name shown in
parentheses. Proofs are `<div class="proof">` right after the statement (the
build adds "Proof." / "证明" and the end mark). An algorithm is an
`env` with `data-kind="algorithm"` holding an `<ol lang="en">` / `<ol lang="zh-CN">` pair of steps.

### Cross-references

```html
<a class="ref" data-ref="thm-comon"></a>          → "Theorem 4.2" / "定理 4.2", linked
<a class="ref" data-ref="eq-model"></a>           → "(1.1)"
<a class="ref" data-ref="whitening"></a>          → "Chapter 3" / "第 3 章" (a chapter slug)
<a class="ref" data-ref="sec-pca-vs-ica"></a>     → "Section 1.4" / "第 1.4 节"
<a class="ref" data-ref="thm-comon">Comon's theorem</a>   → your own link text
```

An empty ref produces the right label in each language, so write it the same
way in both twins. In Chinese, refer to sections as "第 1.4 节" (the build makes
that text), e.g. `由<a class="ref" data-ref="thm-comon"></a>可知`.

### Figures and tables

```html
<figure id="fig-kurtosis-landscape">
  <img src="fig/ch05-landscape.svg" width="620" height="230" alt="Plain English description of what the figure shows.">
  <figcaption><span lang="en">Caption…</span><span lang="zh-CN">图注……</span></figcaption>
</figure>

<figure class="table" id="tab-contrasts">
  <figcaption><span lang="en">Caption…</span><span lang="zh-CN">表注……</span></figcaption>
  <div><table>…</table></div>
</figure>
```

The build prefixes "Figure 5.1." / "图 5.1" and "Table 5.1." / "表 5.1".
Table header and text cells use paired spans; cells with only math need none.
Set `width`/`height` to the SVG's display size in CSS pixels (about 560–680 wide
for a full-width figure, keeping the aspect ratio of the file).

Figures are optional (0–2 per chapter) and must be computed, not drawn by hand:
add functions to `book/figures/<slug>.py` following `book/figures/ica-problem.py`
(`from figstyle import figure, save, …`; one `@figure` function per file
`ch<NN>-<name>`; fixed seeds). Labels inside figures must be language-neutral:
math symbols and numbers only, no English words; the bilingual caption explains.
Use `rasterized=True` for scatter plots with many points. Look at your output
(render with `rsvg-convert -z 1.5 file.svg -o out.png` and view it) before using it.

### Code

Short, runnable NumPy examples are welcome where they teach something (an
algorithm in 15–40 lines, a numerical check of a formula). Code is shared by
both languages, comments in English:

```html
<pre class="code" data-code="python"><code>import numpy as np
…</code></pre>
```

Escape `<`, `>`, `&` inside code as `&lt;`, `&gt;`, `&amp;`. **Run every snippet**
before including it, with a fixed seed, and quote real output only.

### Other blocks

* Key points, near the end of the chapter (before Exercises):
  ```html
  <div class="keypoints">
    <p class="kp-title" lang="en">Key points</p>
    <p class="kp-title" lang="zh-CN">本章要点</p>
    <ul lang="en">…</ul>
    <ul lang="zh-CN">…</ul>
  </div>
  ```
* Exercises: an `<h2>` "Exercises / 习题" holding 4–6 exercises:
  ```html
  <div class="exercise" id="ex-<topic>" data-level="basic|intermediate|advanced">
    <p lang="en">Problem…</p>
    <p lang="zh-CN">题目……</p>
    <details class="solution">
      <p lang="en">Complete solution…</p>
      <p lang="zh-CN">完整解答……</p>
    </details>
  </div>
  ```
  Mix levels: at least one `basic`, one `intermediate`, one `advanced`
  (`advanced` = a real derivation or proof, shown as 硬核 in Chinese). Solutions
  must be complete and correct, not hints.
* References: the last `<h2>` "References / 参考文献" (id `sec-<slug>-references`)
  with `<div class="references"><ol><li>…</li></ol></div>`, entries in English in
  the style of Chapter 1 (APA-like: authors, year, title, venue, volume(issue), pages).
  Cite in the text as "(Comon, 1994)" in both languages.

## 4. Writing

* Audience: a graduate student or researcher with linear algebra and probability.
  The book goes from first principles to research level ("从基础到硬核"):
  every chapter should start accessible and end rigorous.
* Precise and plain. State assumptions explicitly; define every symbol; prefer
  short declarative sentences; no hype ("powerful", "elegant", "crucial"),
  no filler ("it is worth noting that", "in this section we will"). Do not
  over-bold: bold only run-in labels.
* Structure per chapter: an opening section that motivates the question; 4–7
  content sections; key points; exercises; references. Roughly 2,200–3,500
  English words per chapter (Chinese of equal content), at least one worked
  example, and proofs of the central results (or a proof sketch plus a pointer to
  the full proof when it is long). Number only what you reference or what is a
  main result.
* Chinese must read as natural academic Chinese written by a native speaker, not
  a translation: restructure sentences freely, keep the same content and math.
  Use full-width punctuation （，。：；“”（）） in Chinese text, half-width inside
  math and in Latin names. Put a space between Chinese characters and Latin words,
  numbers or inline math (`与 $\bA$ 相同`, `第 3 章`), except next to Chinese
  punctuation. Author names stay in Latin script: “Comon（1994）证明了……” or
  “(Comon, 1994)”.
* Terminology (EN → ZH), use consistently:
  independent component analysis 独立成分分析; blind source separation 盲源分离;
  source 源（信号）; mixing matrix 混合矩阵; unmixing matrix 解混矩阵;
  global (gain) matrix 全局（增益）矩阵; whitening 白化; sphering 球化;
  kurtosis 峭度; skewness 偏度; cumulant 累积量; moment 矩;
  characteristic function 特征函数; differential entropy 微分熵; negentropy 负熵;
  mutual information 互信息; Kullback–Leibler divergence KL 散度;
  contrast function 对比函数; identifiability 可辨识性; score function 得分函数;
  Fisher information Fisher 信息; maximum likelihood 最大似然; likelihood 似然;
  natural gradient 自然梯度; relative gradient 相对梯度; equivariance 等变性;
  stability 稳定性; fixed point 不动点; deflation 逐个提取（紧缩）;
  symmetric orthogonalization 对称正交化; joint diagonalization 联合对角化;
  Jacobi rotation Jacobi 旋转; cumulant tensor 累积量张量;
  sub-Gaussian 亚高斯; super-Gaussian 超高斯; projection pursuit 投影寻踪;
  interference-to-signal ratio 干扰信号比（ISR）; Cramér–Rao bound Cramér–Rao 界;
  asymptotic variance 渐近方差; estimating equation 估计方程;
  model order 模型阶数; overcomplete 过完备; underdetermined 欠定;
  sparse component analysis 稀疏成分分析; nonlinear ICA 非线性 ICA;
  auxiliary variable 辅助变量; spatial ICA 空间 ICA; temporal ICA 时间 ICA;
  group ICA 组 ICA; back-reconstruction 反重建; dual regression 双回归;
  spatially constrained ICA 空间约束 ICA; independent vector analysis 独立向量分析（IVA）;
  functional network connectivity 功能网络连接（FNC）; time course 时间过程;
  spatial map 空间图; principal component analysis 主成分分析（PCA）;
  orthogonal matrix 正交矩阵; permutation matrix 置换矩阵.

## 5. Accuracy policy (most important)

This book will be read by students and researchers. Errors are worse than omissions.

* Include only established results. State each theorem with its exact hypotheses.
* Check every formula, constant and sign. Where possible, verify numerically with
  a few lines of Python (e.g. a kurtosis value, a variance formula, a stability
  condition, a Jacobi angle) before writing it down.
* Cite a work only if you are certain it exists and of its authors, year and
  venue; omit volume/pages you are unsure of rather than guess. Never invent a
  citation, a quotation, a number or an experimental result.
* If you are unsure of the exact form of a published result, state it
  qualitatively with a citation, or leave it out, and mention it in your report.
* Attribute results correctly (who proved what, when).

## 6. Notation (book-wide; Chapter 1, section 1.7)

* $n$ sources, $m$ sensors ($m \ge n$ unless stated), $T$ samples.
* $\bs = (s_1, \dots, s_n)^\top$ sources with densities $p_i$; unit variance
  $\E[s_i^2] = 1$ unless stated; zero mean.
* $\bx = \bA\bs$, $\bA \in \R^{m \times n}$ with columns $\ba_j$; $\bW$ unmixing,
  $\by = \bW\bx$; global matrix $\bP = \bW\bA$; separation means $\bP = \bPi\bD$.
* Whitening $\bz = \bV\bx$ with $\E[\bz\bz^\top] = \bI$; whitened mixing matrix
  $\tilde\bA = \bV\bA$ (orthogonal for unit-variance sources); orthogonal unmixing
  $\bU$ with $\by = \bU\bz$, so $\bW = \bU\bV$. Generic orthogonal matrix $\bQ$.
* One-unit methods: $\bw$ a unit vector, $y = \bw^\top\bz$; $\bq = \tilde\bA^\top\bw$
  the same direction in source coordinates.
* Score function $\psi_i = -p_i'/p_i$ (so $\psi(u) = u$ for $\Ncal(0,1)$);
  a generic nonlinearity is $\varphi$ (in gradient algorithms) or $g = G'$ (FastICA).
* $\kurt(y) = \E[y^4] - 3(\E[y^2])^2$ (fourth cumulant, unnormalized);
  $\kappa_i = \kurt(s_i)$ for unit-variance sources. $\cum(\cdot)$ cumulants.
* $H$ differential entropy, $J$ negentropy, $I$ mutual information, $D(p\,\|\,q)$ KL.
* Fisher information of a unit-variance source: $\mathcal{J}_i = \E[\psi_i(s_i)^2]$
  ($\ge 1$, with equality only for the Gaussian).
* $\Ncal(\mu, \sigma^2)$; $\nu$ denotes a standard Gaussian variable.
* fMRI chapters: data $\bX \in \R^{T \times V}$ ($T$ time points, $V$ voxels);
  spatial ICA $\bX = \bA\bS$ with time courses in the columns of $\bA$ and maps in
  the rows of $\bS$.

## 7. Chapter specifications

Each spec lists what the chapter must cover; organize and expand as you see fit,
keeping the required IDs.

### Ch. 2 `probability` — Independence, Cumulants and Entropy
Independence of random variables and vectors; equivalent forms (factorized density,
$\E[g(y_1)h(y_2)] = \E[g(y_1)]\E[h(y_2)]$); uncorrelated vs independent, with
examples; jointly Gaussian: uncorrelated ⇔ independent. Characteristic functions:
definition, independence ⇔ factorization, sums of independent variables. Moments
and cumulants from the log-characteristic function; first four cumulants in terms of
moments; multivariate fourth-order cumulant of zero-mean variables
$\cum(x_i,x_j,x_k,x_l)$; properties: symmetry, multilinearity, additivity under
independence, vanishing cross-cumulants for independent groups, all cumulants of
order ≥ 3 vanish for Gaussians (Marcinkiewicz: no other law has a polynomial
log-characteristic function). Kurtosis and skewness; a table of kurtoses for
uniform, Laplace, Gaussian, binary ±1, exponential, Student-t (ν > 4).
Differential entropy, its behaviour under $\bA$ ($H(\bA\by) = H(\by) + \log|\det\bA|$),
Gaussian maximizes entropy at fixed covariance; KL divergence; mutual information
as $D(p_{\by} \| \prod p_{y_i})$ and as $\sum H(y_i) - H(\by)$; negentropy, its
invariance and positivity. Required IDs: `def-independence`, `def-charfun`,
`def-cumulant`, `prop-cumulant-properties`, `def-kurtosis`, `def-entropy`,
`prop-entropy-linear`, `prop-gaussian-maxent`, `def-mutual-information`, `def-negentropy`.

### Ch. 3 `whitening` — Whitening and the Geometry of ICA
Centering, covariance and sample covariance. Whitening matrices: definition,
PCA whitening $\bLambda^{-1/2}\bE^\top$, symmetric (ZCA) whitening $\bC^{-1/2}$,
Cholesky; all whitening matrices differ by an orthogonal factor; after whitening,
$\bz = \tilde\bA\bs$ with $\tilde\bA$ orthogonal; the reduction $\bW = \bU\bV$ and the
parameter count; the rotation is what remains. Why second-order statistics cannot
do more (Gaussian rotation invariance; link to Ch. 4). PCA dimension reduction when
$m > n$ (signal subspace; noise; links to Chapters 11 and 14). Finite-sample whitening
and its cost (the orthogonality constraint transfers whitening error into the
separation; qualitative unless you are sure of a formula); conditioning; a figure
showing the geometry is welcome. Required IDs: `def-whitening`,
`prop-whitening-rotation`, `prop-whitened-mixing-orthogonal`, `eq-whitened-model`,
`sec-gaussian-rotation`, `sec-pca-reduction`.

### Ch. 4 `identifiability` — Identifiability
What identifiability means (the distribution of $\bx$ determines $\bA$ up to
$\bPi\bD$). Darmois–Skitovich theorem with a proof under the assumption that all
moments exist and the laws are determined by them (cross-cumulants
$\sum_i a_i^p b_i^q \kappa_{p+q}(s_i) = 0$, a Vandermonde argument on distinct ratios
$b_i/a_i$, Marcinkiewicz and Cramér's decomposition theorem), and a statement of the
general version (Kagan, Linnik & Rao, 1973). Comon's theorem: if $\bs$ has independent
components with at most one Gaussian and $\bP$ is invertible, pairwise independence
of the components of $\bP\bs$ forces $\bP = \bPi\bD$; full proof from
Darmois–Skitovich plus a covariance argument for the Gaussian column. Necessity:
two Gaussians give a continuum of solutions. Partial identifiability with several
Gaussians (non-Gaussian sources identified, Gaussian subspace identified only as a
subspace). Identifiability vs separability vs uniqueness (Eriksson & Koivunen, 2004);
preview of overcomplete (Ch. 12), temporal (Ch. 9) and nonlinear (Ch. 13) cases;
identifiable ≠ easy to estimate (near-Gaussian sources; Ch. 10). Required IDs:
`thm-darmois-skitovich`, `thm-comon`, `cor-one-gaussian`, `sec-gaussian-subspace`.

### Ch. 5 `kurtosis` — Non-Gaussianity and Kurtosis
Central-limit intuition and projection pursuit (Friedman & Tukey, 1974; Huber, 1985).
Kurtosis of a linear combination of independent sources,
$\kurt(\sum_i q_i s_i) = \sum_i q_i^4 \kappa_i$, and the bound on the sphere.
Theorem (Delfosse & Loubaton, 1995): for whitened data, the local maxima of
$|\kurt(\bw^\top\bz)|$ on the unit sphere are exactly $\pm$ the source directions
with nonzero kurtosis; full proof via Lagrange conditions in $\bq$-coordinates
(critical points $q_i^2 \propto 1/\kappa_i$ on a support set, second-order analysis).
Comon's multi-unit contrast $\sum_i \kurt(y_i)^2$ over orthogonal $\bU$. Gradient
ascent and a preview of FastICA's kurtosis iteration. Deflation. Statistical
weaknesses: variance of the sample kurtosis (depends on the 8th moment), outliers and
heavy tails, near-zero kurtosis sources; motivation for Chapter 6. A figure of the
kurtosis landscape on the circle for two whitened sources is welcome. Required IDs:
`prop-kurtosis-sum`, `thm-kurtosis-maxima`, `sec-clt-intuition`, `sec-kurtosis-robustness`.

### Ch. 6 `likelihood` — Negentropy, Mutual Information and Likelihood
Likelihood of $\bW$ by change of variables,
$\log L(\bW) = \sum_t \sum_i \log p_i(\bw_i^\top\bx(t)) + T\log|\det\bW|$; mutual
information of the outputs $I(\by) = \sum_i H(y_i) - H(\bx) - \log|\det\bW|$; the
decomposition of the expected log-likelihood into mutual information plus marginal
mismatch $\sum_i D(p_{y_i}\|p_i)$ (Cardoso, 1997/1998); for whitened data and
orthogonal $\bU$, $I(\by) = \text{const} - \sum_i J(y_i)$. Infomax (Bell & Sejnowski,
1995) and its equivalence to ML (Cardoso, 1997; Pearlmutter & Parra, 1997). Score
functions of common densities. Robustness to a misspecified source model: the
separating point always solves the estimating equations
$\E[\varphi_i(y_i)y_j] = 0$; only stability depends on the model (details in Ch. 7);
super/sub-Gaussian switching. Negentropy approximations: cumulant-based
$J \approx \tfrac{1}{12}\kappa_3^2 + \tfrac{1}{48}\kappa_4^2$ (Jones & Sibson, 1987) and
Hyvärinen's (1998) $J \approx c\,[\E G(y) - \E G(\nu)]^2$ with $\log\cosh$ and
$-e^{-u^2/2}$; why they are more robust than kurtosis. A summary table of contrasts.
Required IDs: `eq-likelihood`, `eq-mi-outputs`, `prop-ml-mi-decomposition`,
`prop-mi-negentropy`, `prop-infomax-ml`, `def-score`, `sec-negentropy-approx`.

### Ch. 7 `natural-gradient` — Natural Gradient, Infomax and Stability
Euclidean gradient of the log-likelihood, $\bW^{-\top} - \E[\bphi(\by)\bx^\top]$.
Relative gradient (Cardoso & Laheld, 1996) and natural gradient on the general
linear group (Amari, Cichocki & Yang, 1996; Amari, 1998):
$\Delta\bW = \mu\,(\bI - \E[\bphi(\by)\by^\top])\,\bW$. Equivariance: the trajectory of
$\bP = \bW\bA$ does not depend on $\bA$. Local stability of the separating point:
derive the linearization (with the normalization $\E[\varphi_i(s_i)s_i] = 1$; off-diagonal
pairs give the matrix $\bigl(\begin{smallmatrix} k_i\sigma_j^2 & 1\\ 1 & k_j\sigma_i^2\end{smallmatrix}\bigr)$),
and state the conditions $1 + m_i > 0$, $k_i > 0$, $\sigma_i^2\sigma_j^2k_ik_j > 1$ with
$k_i = \E[\varphi_i'(s_i)]$, $m_i = \E[\varphi_i'(s_i)s_i^2]$, $\sigma_i^2 = \E[s_i^2]$
(Amari, Chen & Cichocki, 1997); check them numerically; show that for the true score
($\E[\psi_i s_i] = 1$, $k_i = \mathcal{J}_i$, $\sigma_i^2\mathcal{J}_i \ge 1$) they hold whenever at
most one source is Gaussian. Infomax with the logistic nonlinearity and its natural-gradient
form; extended Infomax for mixed sub/super-Gaussian sources (Lee, Girolami & Sejnowski,
1999), with its switching rule; EASI (serial updating with whitening built in, Cardoso &
Laheld, 1996). Step sizes, batch vs online. A short NumPy implementation and a
demonstration that a mismatched nonlinearity fails. Required IDs: `eq-natural-gradient`,
`prop-equivariance`, `thm-stability`, `alg-infomax`, `sec-extended-infomax`.

### Ch. 8 `fastica` — FastICA
One-unit contrast $J_G(\bw) \propto [\E G(\bw^\top\bz) - \E G(\nu)]^2$ on the sphere; choices
$G(u) = \tfrac1a\log\cosh(au)$, $-e^{-u^2/2}$, $u^4/4$. Derivation as an approximate Newton
method (Lagrange condition, Jacobian approximation using whitening) giving
$\bw^+ = \E[\bz\,g(\bw^\top\bz)] - \E[g'(\bw^\top\bz)]\,\bw$, $\bw \leftarrow \bw^+/\|\bw^+\|$.
Kurtosis case in source coordinates: $q_i^+ = \kappa_i q_i^3$ exactly in expectation, hence
cubic convergence (Hyvärinen & Oja, 1997); quadratic convergence for general $g$
(Hyvärinen, 1999); convergence analysis references (Oja & Yuan, 2006). Deflation with
Gram–Schmidt vs symmetric orthogonalization $\bW \leftarrow (\bW\bW^\top)^{-1/2}\bW$ (link to
the polar decomposition in Appendix A); error accumulation; choice of $G$ (robustness,
speed, stability; the sign of $\E[s\,g(s) - g'(s)]$). A complete, short NumPy implementation
of symmetric FastICA with a demonstration (show convergence in a few iterations).
Required IDs: `alg-fastica-one-unit`, `eq-fastica-update`, `thm-fastica-convergence`,
`alg-symmetric-fastica`, `eq-symmetric-orthogonalization`.

### Ch. 9 `jade-sobi` — Tensor and Second-Order Methods: JADE and SOBI
Fourth-order cumulant tensor of whitened data, diagonal in the source basis:
$\cum(z_i,z_j,z_k,z_l) = \sum_p \kappa_p \tilde a_{ip}\tilde a_{jp}\tilde a_{kp}\tilde a_{lp}$.
Cumulant matrices $\bQ_{\bz}(\bM) = \tilde\bA\,\diag(\kappa_p\,\tilde\ba_p^\top\bM\tilde\ba_p)\,\tilde\bA^\top$;
FOBI (Cardoso, 1989) as the case $\bM = \bI$; joint approximate diagonalization; the
JADE contrast and algorithm (Cardoso & Souloumiac, 1993); Jacobi rotations with the
closed-form angle for joint diagonalization (Cardoso & Souloumiac, 1996), verified
numerically. Second-order methods: lagged covariances
$\bC_{\bx}(\tau) = \bA\,\diag(\rho_i(\tau))\,\bA^\top$; AMUSE (Tong et al., 1991) and its
condition (distinct $\rho_i(\tau)$); SOBI (Belouchrani et al., 1997) and its identifiability
condition (for every pair some lag distinguishes their autocorrelations), so Gaussian
sources with different spectra are separable; related TDSEP / Molgedey–Schuster.
Comparison table (statistics used, Gaussian sources allowed, cost). Short NumPy code for
AMUSE or a Jacobi joint diagonalizer. Required IDs: `eq-cumulant-tensor-ica`,
`prop-cumulant-matrices`, `alg-jade`, `eq-jacobi-angle`, `alg-sobi`, `thm-sobi-identifiability`.

### Ch. 10 `performance` — Asymptotic Performance and the Cramér–Rao Bound
The gain matrix near separation, $\bP = \bI + \bepsilon$ after fixing order and scale;
interference-to-signal ratio $\mathrm{ISR}_{ij} = \E[\epsilon_{ij}^2]$; Amari's performance
index. Estimating equations and asymptotic normality ($\sqrt T$ rate). One-unit
asymptotic variance (Hyvärinen, 1997; 1999):
$V_g = \bigl(\E[g^2(s)] - (\E[s\,g(s)])^2\bigr) / \bigl(\E[s\,g(s) - g'(s)]\bigr)^2$; the optimal
$g$ is (an affine function of) the score, giving $V = 1/(\mathcal{J} - 1)$; verify by
simulation (a figure comparing empirical and predicted variance is welcome).
Cramér–Rao bound (Tichavský, Koldovský & Oja, 2006; see also Pham & Garat, 1997):
$\mathrm{CRB}(\epsilon_{ij}) = \frac{1}{T}\,\frac{\mathcal{J}_j}{\mathcal{J}_i\mathcal{J}_j - 1}$, its meaning
(infinite when two sources are Gaussian), Fisher information of common laws (Gaussian 1,
Laplace 2, uniform: infinite and the regular theory breaks down). Symmetric FastICA and
EFICA performance (Koldovský, Tichavský & Oja, 2006) as stated in those papers.
Equivariance ⇒ performance independent of $\bA$. Required IDs: `def-gain-matrix`, `def-isr`,
`thm-asymptotic-one-unit`, `prop-optimal-nonlinearity`, `thm-crb`, `sec-amari-index`.

### Ch. 11 `model-order` — Noise, Model Order and Reliability
Noisy model $\bx = \bA\bs + \bn$: what noise does (bias of whitening, sources not
recoverable exactly, cumulants of order ≥ 3 blind to Gaussian noise, bias-corrected
whitening $\bC_{\bx} - \sigma^2\bI$); probabilistic PCA (Tipping & Bishop, 1999). PCA
reduction and the choice of $n$: information criteria on eigenvalues (Akaike, 1974;
Rissanen, 1978; Wax & Kailath, 1985), Minka (2000); dependent samples and the effective
sample size, i.i.d. subsampling for fMRI (Li, Adalı & Calhoun, 2007). Under- and
over-estimating the order: merged and split components. Reliability: random
initializations and local optima; ICASSO (Himberg, Hyvärinen & Esposito, 2004),
RAICAR (Yang et al., 2008), split-half reproducibility; what a stability index does and
does not certify. Required IDs: `sec-noisy-ica`, `sec-model-order-selection`, `sec-icasso`,
`sec-split-components`.

### Ch. 12 `overcomplete` — Overcomplete ICA and Sparse Component Analysis
Model with $m < n$. Identifiability of $\bA$ when all sources are non-Gaussian and no two
columns are collinear (Eriksson & Koivunen, 2004, building on Kagan, Linnik & Rao) vs
non-recoverability of $\bs$ from $\bx$ (the affine solution set). Source recovery given
$\bA$: MAP with priors; Laplace prior ⇒ $\ell_1$ (basis pursuit, Chen, Donoho & Saunders,
1998). Cumulant tensors as symmetric CP decompositions of rank $n > m$; uniqueness via
Kruskal's condition (Kruskal, 1977); FOOBI (De Lathauwer, Castaing & Cardoso, 2007);
characteristic-function methods (Comon & Rajih, 2006). Sparse component analysis:
single-source points, clustering of directions, time–frequency methods (DUET, Jourjine,
Rickard & Yılmaz, 2000), Bofill & Zibulevsky (2001), Georgiev, Theis & Cichocki (2005).
Learning overcomplete representations (Lewicki & Sejnowski, 2000). Why estimation is
harder than in the square case (more parameters, no whitening shortcut, flatter
likelihoods). Required IDs: `thm-overcomplete-identifiability`, `sec-source-recovery`,
`sec-tensor-rank`, `sec-sca`.

### Ch. 13 `nonlinear` — Nonlinear ICA
Model $\bx = \mathbf{f}(\bs)$. Non-identifiability (Hyvärinen & Pajunen, 1999): the
Darmois / Gram–Schmidt construction with conditional CDFs produces independent
components from any $\bx$; measure-preserving transforms of independent Gaussians;
proof of the construction. Restricted models that are identifiable: post-nonlinear
mixtures (Taleb & Jutten, 1999). Identifiability from structure: time-contrastive learning
for nonstationary sources (Hyvärinen & Morioka, 2016), permutation-contrastive learning for
temporally dependent sources (Hyvärinen & Morioka, 2017), auxiliary variables and
generalized contrastive learning (Hyvärinen, Sasaki & Turner, 2019), identifiable VAEs
(Khemakhem, Kingma, Monti & Hyvärinen, 2020): state the theorem with its "sufficient
variability" assumption and what is identified (components up to permutation and
componentwise invertible transformations). Relation to disentanglement and the
impossibility result of Locatello et al. (2019). Required IDs: `thm-nonlinear-nonidentifiable`,
`sec-tcl`, `thm-auxiliary-identifiability`, `sec-ivae`.

### Ch. 14 `fmri-ica` — Spatial ICA of fMRI
BOLD data as a $T \times V$ matrix; preprocessing. Spatial ICA $\bX = \bA\bS$ with
independent maps (McKeown et al., 1998) vs temporal ICA; why spatial ICA dominates
($V \gg T$); Calhoun et al. (2001, spatial vs temporal). PCA reduction and model order
in fMRI. Algorithms in practice: Infomax (GIFT), FastICA, probabilistic ICA (MELODIC,
Beckmann & Smith, 2004), ICASSO. Reading components: scaling to z-scores, sign convention,
thresholding, resting-state networks (Beckmann et al., 2005; Damoiseaux et al., 2006;
Smith et al., 2009), artifacts and their classification (ICA-FIX, Salimi-Khorshidi et al.,
2014, Griffanti et al., 2014; ICA-AROMA, Pruim et al., 2015). Is spatial independence the
right assumption? (Daubechies et al., 2009 and the reply by Calhoun et al., 2013.)
A small synthetic spatial-ICA example in NumPy is welcome. Required IDs:
`eq-spatial-ica-model`, `sec-spatial-vs-temporal`, `sec-component-interpretation`.

### Ch. 15 `group-ica` — Group ICA, Dual Regression and IVA
The correspondence problem across subjects. Temporal concatenation group ICA with
subject- and group-level PCA (Calhoun et al., 2001); back-reconstruction (GICA1, GICA3;
Erhardt et al., 2011). Dual regression (Beckmann et al., 2009; Filippini et al., 2009;
Nickerson et al., 2017): stage-1 spatial regression on the group maps, stage-2 temporal
regression; closed forms. Spatially constrained ICA and group-information-guided ICA
(Lin et al., 2010; Du & Fan, 2013); NeuroMark (Du et al., 2020). Independent vector
analysis (Kim, Eltoft & Lee, 2006; Lee et al., 2008; Anderson, Adalı & Li, 2012; Adalı,
Anderson & Fu, 2014). Functional network connectivity (Jafri et al., 2008) and dynamic FNC
(Allen et al., 2014). Multimodal fusion: joint ICA (Calhoun et al., 2006) and parallel ICA
(Liu et al., 2009). Required IDs: `eq-temporal-concatenation`, `sec-back-reconstruction`,
`sec-dual-regression`, `sec-constrained-ica`, `sec-iva`, `sec-fnc`, `sec-fusion`.

### App. A `math-background` — Mathematical Background
Orthogonal group (dimension $n(n-1)/2$, Givens rotations), permutation and signed
permutation matrices. Symmetric eigendecomposition, positive (semi)definite matrices,
matrix functions, $\bC^{1/2}$ and $\bC^{-1/2}$. SVD and the polar decomposition; the
closest orthogonal matrix in Frobenius norm is $(\bW\bW^\top)^{-1/2}\bW$ (proof).
Kronecker products, vec, $\vecop(\bA\bX\bB) = (\bB^\top\otimes\bA)\vecop(\bX)$; tensors,
outer products, CP rank, multilinear transformation of cumulant tensors. Matrix
calculus: $\partial \log|\det\bW|/\partial\bW = \bW^{-\top}$, traces. Optimization on the
sphere and on $O(n)$: Lagrange conditions, tangent spaces, Riemannian gradient
(skew-symmetric directions), retractions. Asymptotic statistics: delta method,
M-estimators and the sandwich covariance, Fisher information and the Cramér–Rao bound.
Required IDs: `sec-orthogonal-matrices`, `sec-polar-decomposition`, `prop-closest-orthogonal`,
`sec-kronecker-tensors`, `sec-matrix-calculus`, `sec-sphere-optimization`, `sec-asymptotics`.

## 8. Report

When done, report: the sections and their IDs, every numbered result you added, the
figures and code you added (and that you ran them), the final `--check` output for your
chapters, and any statement you were not fully sure of.

## 9. Registry of IDs (for cross-references)

Chapter 1 `ica-problem` (exists): `eq-model`, `asm-ica`, `def-ica`, `prop-indeterminacy`,
`sec-ambiguities`, `sec-pca-vs-ica`, `sec-first-look`, `sec-notation`, `fig-scatter`.
All other required IDs are listed in each chapter spec above. Chapters can always be
referenced by slug: `ica-problem probability whitening identifiability kurtosis
likelihood natural-gradient fastica jade-sobi performance model-order overcomplete
nonlinear fmri-ica group-ica math-background`.


## Automated validation and reading tools (2026-11-03)

Use data-code="python" on runnable pre.code blocks, and data-code="output" on printed results. Python blocks share a namespace within a chapter; chapters execute in separate processes. The build derives downloadable docs/ica/code/*.py files and a local bilingual search index from the same sources; do not edit these generated files.

Validation commands:

    python -m pip install -r book/requirements-examples.txt
    node book/build.mjs --strict
    python scripts/check_book.py --run-code
    python scripts/test_book_quality.py
    python scripts/check_site_quality.py

The example runner checks syntax and execution, not mathematical truth or every printed claim. Add numerical assertions and inspect outputs when changing an algorithm or example. Proofs, assumptions and bilingual equivalence still require substantive review. See book/VALIDATION.md.
