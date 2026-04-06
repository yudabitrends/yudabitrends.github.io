---
title: ''
summary: ''
date: 2024-01-01
type: landing

design:
  spacing: '6rem'

sections:
  - block: resume-biography-3
    content:
      username: me
      text: ''
      button:
        text: Download CV
        url: uploads/resume.pdf
      headings:
        about: ''
        education: ''
        interests: ''
    design:
      background:
        gradient_mesh:
          enable: true
      name:
        size: lg
      avatar:
        size: medium
        shape: circle
  - block: markdown
    content:
      title: 'Research'
      subtitle: ''
      text: |-
        My research bridges **theoretical neuroscience**, **statistical physics**, and **deep learning**,
        with a focus on understanding the structural and functional organization of the brain.

        I develop multimodal vision transformer frameworks for brain imaging analysis, and investigate
        fundamental principles of information structure, redundancy, and spectral methods across
        neuroscience, finance, and AI.

        I am the founder of the **Structural Intelligence (SI)** framework — a unifying theoretical
        foundation for cross-disciplinary research.
    design:
      columns: '1'
  - block: collection
    id: papers
    content:
      title: Featured Publications
      filters:
        folders:
          - publications
        featured_only: true
    design:
      view: article-grid
      columns: 2
  - block: collection
    content:
      title: Recent Publications
      text: ''
      filters:
        folders:
          - publications
        exclude_featured: false
    design:
      view: citation
  - block: collection
    id: notes
    content:
      title: Recent Notes
      subtitle: ''
      text: ''
      page_type: notes
      count: 5
      filters:
        author: ''
        category: ''
        tag: ''
        exclude_featured: false
        exclude_future: false
        exclude_past: false
      offset: 0
      order: desc
    design:
      view: card
      spacing:
        padding: [0, 0, 0, 0]
---
