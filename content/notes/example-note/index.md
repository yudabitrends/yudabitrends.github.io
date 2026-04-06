---
title: "Spectral Methods in Brain Network Analysis: A Quick Overview"
summary: "Notes on how graph Laplacian spectra can reveal community structure in functional brain networks, with key derivations and intuitions."
date: 2026-04-07
math: true
authors:
  - me
tags:
  - Spectral Methods
  - Brain Networks
  - Graph Theory
image:
  caption: ""
  focal_point: ""
---

These are example notes demonstrating the academic notes feature with full math support, images, and structured content. Replace this with your own research notes.

## Graph Laplacian and Brain Networks

Given a brain connectivity matrix $W \in \mathbb{R}^{n \times n}$ where $w_{ij}$ represents the functional connectivity between regions $i$ and $j$, the **normalized graph Laplacian** is defined as:

$$
\mathcal{L} = I - D^{-1/2} W D^{-1/2}
$$

where $D = \text{diag}(d_1, \ldots, d_n)$ is the degree matrix with $d_i = \sum_j w_{ij}$.

## Spectral Decomposition

The eigendecomposition of $\mathcal{L}$ yields:

$$
\mathcal{L} = U \Lambda U^T = \sum_{k=0}^{n-1} \lambda_k \mathbf{u}_k \mathbf{u}_k^T
$$

where $0 = \lambda_0 \leq \lambda_1 \leq \cdots \leq \lambda_{n-1} \leq 2$.

### Key Properties

1. **Number of zero eigenvalues** = number of connected components
2. The **Fiedler value** $\lambda_1$ measures algebraic connectivity
3. The **spectral gap** $\lambda_1 - \lambda_0$ indicates community separation strength

## Participation Ratio

The **effective rank** via participation ratio provides a model-free measure of spectral spread:

$$
\text{PR}(\boldsymbol{\lambda}) = \frac{\left(\sum_k \lambda_k\right)^2}{\sum_k \lambda_k^2}
$$

This metric ranges from 1 (single dominant eigenvalue) to $n$ (uniform spectrum), capturing the effective dimensionality of the network.

## Connection to Statistical Physics

The graph Laplacian connects to the partition function of a Gaussian field on the network:

$$
Z(\beta) = \int \exp\left(-\frac{\beta}{2} \mathbf{x}^T \mathcal{L} \mathbf{x}\right) d\mathbf{x} = \prod_{k=1}^{n-1} \sqrt{\frac{2\pi}{\beta \lambda_k}}
$$

The free energy $F = -\frac{1}{\beta}\ln Z$ encodes the thermodynamic properties of signal propagation on the network.

---

*This is an example note. You can add images, code blocks, and any Markdown content here.*
