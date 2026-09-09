#!/usr/bin/env python
"""Scaffold _posts/<date>-<slug>.md with correct front matter and the four-part skeleton.

    new_post.py 1 "Who holds the Marvel universe together?"
    new_post.py 2 "Is it a power law?" --notebook notebooks/week2-models.ipynb --date 2026-09-21

Front matter is exactly title, week, authors (from _config.yml) and notebook.
No layout key: _config.yml supplies it. Refuses to overwrite.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from _common import REPO_ROOT, SKILL_DIR, die, read_front_matter, rel, site_config, slugify, warn

TEMPLATE = SKILL_DIR / "templates" / "post.md"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("week", type=int)
    parser.add_argument("title")
    parser.add_argument("--notebook", help="repo-relative notebook path (default: the week's single notebook)")
    parser.add_argument("--date", help="YYYY-MM-DD (default today)")
    parser.add_argument("--slug", help="URL slug (default: from the title)")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.week < 1:
        die("week must be a positive integer")
    title = args.title.strip()
    if not title:
        die("title must not be empty")

    try:
        date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    except ValueError:
        die(f"--date {args.date!r} is not YYYY-MM-DD")
    if date > dt.date.today():
        warn(f"{date} is in the future; Jekyll hides future-dated posts, so the post will not appear until then")

    slug = args.slug or slugify(title)
    if not slug:
        die("could not derive a slug from the title; pass --slug")

    posts = REPO_ROOT / "_posts"
    dest = posts / f"{date.isoformat()}-{slug}.md"
    if dest.exists() and not args.force:
        die(f"{rel(dest)} exists; pass --force to overwrite it")

    for existing in sorted(posts.glob("*.md")):
        try:
            data, _ = read_front_matter(existing)
        except Exception:
            continue
        if data.get("week") == args.week and existing != dest:
            warn(f"a post for week {args.week} already exists: {rel(existing)}")

    config = site_config()
    authors = [m["name"] for m in config.get("group", []) if isinstance(m, dict) and m.get("name")]
    if not authors:
        warn("no group members in _config.yml; authors left empty")

    if args.notebook:
        notebook = Path(args.notebook)
        if not (REPO_ROOT / notebook).exists():
            warn(f"{notebook} does not exist yet")
    else:
        candidates = sorted((REPO_ROOT / "notebooks").glob(f"week{args.week}-*.ipynb"))
        if len(candidates) == 1:
            notebook = candidates[0].relative_to(REPO_ROOT)
        elif candidates:
            die("several notebooks for week %d; pass --notebook:\n  %s" % (args.week, "\n  ".join(rel(c) for c in candidates)))
        else:
            notebook = None
            warn(f"no notebooks/week{args.week}-*.ipynb found; the notebook link is omitted")

    front = ["---", f"title: {json.dumps(title, ensure_ascii=False)}", f"week: {args.week}"]
    front.append("authors: [" + ", ".join(json.dumps(a, ensure_ascii=False) for a in authors) + "]")
    if notebook is not None:
        front.append(f"notebook: {notebook.as_posix()}")
    front.append("---")

    body = TEMPLATE.read_text(encoding="utf-8")
    body = body.replace("__WEEK__", str(args.week)).replace("__FIGURE_PREFIX__", f"/assets/figures/week{args.week}-")

    posts.mkdir(exist_ok=True)
    dest.write_text("\n".join(front) + "\n\n" + body, encoding="utf-8")
    print(f"created {rel(dest)}")
    print("fill every <!-- go-nuts: ... --> marker, then run: /go-nuts review " + rel(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
