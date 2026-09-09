# data/

Everything in this directory is **gitignored**. The dataset is downloaded and
processed by the notebooks and by scripts in `scripts/`, so it can always be
rebuilt from scratch — keeping it out of git avoids a repo full of large files
and avoids merge conflicts on binary data.

Suggested layout:

```
data/
  raw/         # exactly as downloaded — never edited by hand
  processed/   # cleaned edge lists, node tables, pickled graphs
```

If a *small* processed file (say under a few MB) is genuinely worth sharing
rather than regenerating — a hand-corrected mapping, for example — force it in:

```bash
git add -f data/processed/character-aliases.csv
```

Otherwise, whoever needs the data regenerates it locally.
