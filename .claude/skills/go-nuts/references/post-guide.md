# Writing and copyediting a post

## The file

- `_posts/YYYY-MM-DD-<slug>.md`. The date sets the URL (`/YYYY/MM/DD/<slug>/`) and the order on the front page. Jekyll hides future-dated posts.
- `scripts/new_post.py` creates it. Never create one by hand.

## Front matter: exactly these keys

```yaml
---
title: "Who holds the Marvel universe together?"
week: 1
authors: ["Johan Holmsteen", "Joes Hasselriis Nicolaisen"]
notebook: notebooks/week1-centrality.ipynb
---
```

- No `layout:`. `_config.yml` gives every post the `post` layout; adding it is noise and the hygiene check fails on it.
- `authors` come from `group:` in `_config.yml`.
- `notebook` renders as a link to the file on GitHub. It is what lets a reader check the work; keep it.

## The shape, and nothing else

1. **Lede paragraph.** The question and the short answer in one or two sentences. It becomes the front-page excerpt (first 45 words, HTML stripped), so it must stand alone: no figure, no include, no heading before it.
2. `## What we asked` — two to four sentences. The question, and why this week's tools fit it.
3. `## What we did` — the method in words. Name the measure, the choices (directed or undirected, weighted or not, which subset), the counts. No code unless the code is the point.
4. `## What we found` — exactly one figure or one table, with one or two sentences reading it.
5. `## What surprised us` — the one thing the group did not expect and what they make of it. "Nothing, and here is why" is allowed.

300 to 600 words. No headings beyond these four. A question makes the best title.

## Figures

- Only through the includes. `save_figure()` in the notebook writes the file and prints the exact line to paste:

  ```
  {% include figure.html src="/assets/figures/week1-degree.png" alt="..." caption="..." wide=true %}
  {% include interactive.html src="/assets/figures/week2-explorer.html" alt="..." height=480 %}
  ```

- Never `![](...)`. The site is served under `/playground`; a bare path works locally and 404s once deployed.
- `alt` says what the figure shows for someone who cannot see it: "Log-log in-degree distribution; the tail is roughly straight over two decades." `caption` says what to look at, and may contain markdown. Both are single lines.
- `wide=true` for network drawings and multi-panel plots.
- Files are `assets/figures/week<N>-<slug>.png` or `.html`, lowercase, hyphens.

## Tables

GFM tables, at most about eight rows, numbers exactly as the notebook prints them.

## Math

`$$…$$` and `$…$` both render through MathJax. Write `\$` for a literal dollar sign.

## Copyedit rules (mode `copyedit`)

Do:

- Fix grammar, spelling and punctuation. Keep the draft's variety of English.
- Tighten. Cut throat-clearing ("In this post we will…"), repeated sentences, stacked hedges, and any sentence that says the same thing as the figure caption.
- Enforce the shape above: five parts, in order, no extra headings.
- Fix include syntax, missing alt text, and front matter keys.
- Keep every number exactly as written. If a number looks wrong, ask; do not correct it.

Do not:

- Add a finding, an explanation, a comparison, a caveat or a number that is not in the draft or the notebook.
- Change what a sentence claims. Rephrase the claim; keep the claim.
- Pad to reach a length. Short is fine.
- Touch the notebook.

Report every edit as a one-line list, and separately list anything you left alone because it needed the authors' judgement.
