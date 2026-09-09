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

## The course snapshot

You never download the shared Marvel snapshot by hand. `marvel.data` fetches
`week1_nodes.tsv`, `week1_edges.tsv` and `week4_edges_weighted.tsv` from the
course site into `data/raw/` the first time they are needed, and verifies each
file's sha256 against the constants in `marvel/data.py` on every load. A file
that is missing, edited or corrupt is re-downloaded; a file that keeps failing
verification raises `SnapshotError` with the expected and actual checksums.

```bash
.venv/bin/python -m marvel               # fetch everything and print a summary
```

To force a fresh copy, delete the file or call
`ensure_snapshot("week1_edges.tsv", force=True)`.

If a *small* processed file (say under a few MB) is genuinely worth sharing
rather than regenerating — a hand-corrected mapping, for example — force it in:

```bash
git add -f data/processed/character-aliases.csv
```

Otherwise, whoever needs the data regenerates it locally.
