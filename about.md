---
layout: page
title: About the group
permalink: /about/
---

This site is the running coursework of a group taking **{{ site.course.code }}
{{ site.course.name }}** at the {{ site.course.university }}. Over the course of
the semester we publish one post per week, each one analysing a shared
Marvel/Wikipedia network dataset from a different angle.

## Who we are

<ul class="group-list">
{%- for member in site.group %}
  <li>
    <span class="group-list__name">{{ member.name }}</span>
    {%- if member.github %}
    <br><a class="group-list__handle" href="https://github.com/{{ member.github }}">@{{ member.github }}</a>
    {%- endif %}
  </li>
{%- endfor %}
</ul>

## How we work

The analysis and the website live in [the same
repository](https://github.com/{{ site.repository }}). Each weekly post is
backed by a Jupyter notebook under `notebooks/`, which reads the dataset from
`data/` and writes its plots into `assets/figures/`. Nothing on this site is a
figure we cannot regenerate from a notebook in that repo.

Posts are written in Markdown, and pushing to `main` rebuilds and redeploys the
site through GitHub Actions.

## Colophon

Built with [Jekyll](https://jekyllrb.com), deployed on GitHub Pages via GitHub
Actions. The layouts and stylesheet are our own — no theme gem — which is why
the site looks like this rather than like the Jekyll default. Analysis is done
in Python with [NetworkX](https://networkx.org), pandas and matplotlib.
