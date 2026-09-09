#!/usr/bin/env python
"""Scaffold notebooks/week<N>-<slug>.ipynb from the skill's template notebook.

    new_notebook.py 2 models-null-models

The template imports the loader, builds the graph roster-first, and ends with a
Findings cell the post is written from. Refuses to overwrite.
"""

from __future__ import annotations

import argparse
import sys

from _common import REPO_ROOT, SKILL_DIR, SLUG_RE, die, rel, warn

TEMPLATE = SKILL_DIR / "templates" / "notebook.ipynb"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("week", type=int)
    parser.add_argument("slug", help="short topic slug: lowercase letters, digits, hyphens")
    parser.add_argument("--force", action="store_true", help="overwrite an existing notebook")
    args = parser.parse_args(argv)

    if args.week < 1:
        die("week must be a positive integer")
    if not SLUG_RE.match(args.slug):
        die(f"slug {args.slug!r} must match {SLUG_RE.pattern}; use suggested_slug from the brief")

    notebooks = REPO_ROOT / "notebooks"
    dest = notebooks / f"week{args.week}-{args.slug}.ipynb"
    if dest.exists() and not args.force:
        die(f"{rel(dest)} exists; pass --force to overwrite it")
    for other in sorted(notebooks.glob(f"week{args.week}-*.ipynb")):
        if other != dest:
            warn(f"another notebook for week {args.week} exists: {rel(other)}")

    import nbformat

    nb = nbformat.read(TEMPLATE, as_version=4)
    topic = args.slug.replace("-", " ")
    topic = topic[0].upper() + topic[1:]
    brief = notebooks / "briefs" / f"week{args.week}.md"
    brief_line = (
        f"Brief: [briefs/week{args.week}.md](briefs/week{args.week}.md)"
        if brief.exists()
        else f"Brief: not fetched yet; run `fetch_brief.py {args.week}`."
    )
    for cell in nb.cells:
        cell.source = (
            cell.source.replace("__WEEK__", str(args.week)).replace("__TOPIC__", topic).replace("__BRIEF__", brief_line)
        )
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3 (ipykernel)", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nbformat.validate(nb)
    notebooks.mkdir(exist_ok=True)
    nbformat.write(nb, dest)
    print(f"created {rel(dest)}")
    print(f"open it with: jupyter lab {rel(dest)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
