#!/usr/bin/env python
"""Fetch a week's brief from the course site and extract the group exercise.

    fetch_brief.py 2                         # by week number
    fetch_brief.py https://.../weeks/week2.html
    fetch_brief.py 2 --no-write              # print only
    fetch_brief.py 2 --force                 # overwrite notebooks/briefs/week2.md

Writes notebooks/briefs/week<N>.md (Jekyll never serves notebooks/) and prints
the same markdown to stdout.

Exit codes: 0 ok · 1 error · 2 the week is not live yet (HTTP 404) ·
3 page is live but has no group-exercise section.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from _common import REPO_ROOT, die, http, rel, slugify, warn

WEEKS_BASE = "https://sunelehmann.com/socialgraphs2026-web/weeks/"
LICENCE = "Course content by Sune Lehmann, CC BY-SA 4.0."


def week_url(week: int) -> str:
    return f"{WEEKS_BASE}week{week}.html"


# --- HTML -> markdown -------------------------------------------------------


def _inline(node, base: str) -> str:
    from bs4 import NavigableString

    if isinstance(node, NavigableString):
        return re.sub(r"\s+", " ", str(node))
    inner = "".join(_inline(child, base) for child in node.children)
    name = node.name
    if name == "a":
        href = urljoin(base, node.get("href", ""))
        return f"[{inner.strip()}]({href})"
    if name == "code":
        return f"`{inner}`"
    if name in ("strong", "b"):
        return f"**{inner.strip()}**"
    if name in ("em", "i"):
        return f"*{inner.strip()}*"
    if name == "br":
        return "\n"
    return inner


def _list(node, base: str, depth: int = 0) -> str:
    lines = []
    ordered = node.name == "ol"
    for i, li in enumerate(node.find_all("li", recursive=False), 1):
        marker = f"{i}." if ordered else "-"
        text_parts, nested = [], []
        for child in li.children:
            if getattr(child, "name", None) in ("ol", "ul"):
                nested.append(child)
            else:
                text_parts.append(_inline(child, base))
        text = re.sub(r"\s+", " ", "".join(text_parts)).strip()
        lines.append("   " * depth + f"{marker} {text}")
        for sub in nested:
            lines.append(_list(sub, base, depth + 1))
    return "\n".join(lines)


def _blocks(node, base: str) -> list[str]:
    from bs4 import NavigableString

    out: list[str] = []
    for child in node.children:
        if isinstance(child, NavigableString):
            text = re.sub(r"\s+", " ", str(child)).strip()
            if text:
                out.append(text)
            continue
        name = child.name
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            out.append("### " + re.sub(r"\s+", " ", _inline(child, base)).strip())
        elif name == "p":
            out.append(re.sub(r"[ \t]+", " ", _inline(child, base)).strip())
        elif name in ("ol", "ul"):
            out.append(_list(child, base))
        elif name == "pre":
            out.append("```\n" + child.get_text().rstrip() + "\n```")
        elif name in ("div", "section", "blockquote", "details"):
            out.extend(_blocks(child, base))
        else:
            text = _inline(child, base).strip()
            if text:
                out.append(text)
    return out


def _ideas(div, base: str) -> tuple[str, str] | None:
    """The paragraph starting 'This week' and the list that follows it."""
    for p in div.find_all("p"):
        if p.get_text(" ", strip=True).lower().startswith("this week"):
            following = p.find_next_sibling()
            if following is not None and following.name in ("ol", "ul"):
                return _inline(p, base).strip(), _list(following, base)
    return None


# --- main -------------------------------------------------------------------


def build_markdown(week: int | None, url: str, soup) -> tuple[str, str, str | None, bool]:
    """Return (markdown, topic, ideas-or-None, group-exercise-found)."""
    h1 = soup.h1.get_text(" ", strip=True) if soup.h1 else ""
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    topic = h1 or re.sub(r"^\s*week\s*\d+\s*[·:—-]\s*", "", title, flags=re.I) or f"week {week}"
    h2s = [(h.get("id", ""), h.get_text(" ", strip=True)) for h in soup.find_all("h2")]

    div = soup.find(id="go-nuts")
    if div is None:
        for candidate in soup.select("div.exercise"):
            heading = candidate.find(["h3", "h4"])
            if heading and "go nuts" in heading.get_text(" ", strip=True).lower():
                div = candidate
    ideas = _ideas(div, url) if div is not None else None

    lines = [
        "---",
        f"week: {week if week is not None else 'null'}",
        f"topic: {json.dumps(topic)}",
        f"suggested_slug: {slugify(topic) or 'topic'}",
        f"source: {url}",
        f"fetched: {dt.date.today().isoformat()}",
        "---",
        "",
        f"# Week {week} — {topic}" if week is not None else f"# {topic}",
        "",
        f"Source: <{url}>. {LICENCE}",
        "",
        "## Sections on the page",
        "",
    ]
    lines += [f"- {text}" + (f" (#{hid})" if hid else "") for hid, text in h2s] or ["- (no h2 headings found)"]
    lines += ["", "## This week's ideas and tools", ""]
    if ideas:
        lines += [ideas[0], "", ideas[1]]
    else:
        lines += ["(no 'This week' list found in the group exercise; read the section below)"]
    lines += ["", "## Group exercise, verbatim", ""]
    lines += ["\n\n".join(_blocks(div, url))] if div is not None else ["(no group-exercise section on this page)"]
    return "\n".join(lines).rstrip() + "\n", topic, ideas[1] if ideas else None, div is not None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="week number or brief URL")
    parser.add_argument("--week", type=int, help="week number when it cannot be read from the URL")
    parser.add_argument("--out", help="output file (default notebooks/briefs/week<N>.md)")
    parser.add_argument("--no-write", action="store_true", help="print only")
    parser.add_argument("--force", action="store_true", help="overwrite an existing brief")
    args = parser.parse_args(argv)

    if args.target.isdigit():
        week, url = int(args.target), week_url(int(args.target))
    else:
        url = args.target
        match = re.search(r"week(\d+)\.html", url)
        week = args.week or (int(match.group(1)) if match else None)

    import requests

    try:
        response = http().get(url, timeout=20)
    except requests.RequestException as err:
        die(f"could not fetch {url}: {err}")
    if response.status_code == 404:
        label = f"Week {week}" if week is not None else url
        print(f"{label} is not live yet (HTTP 404 at {url}). Try again after the lecture.", file=sys.stderr)
        return 2
    if not response.ok:
        die(f"{url} answered HTTP {response.status_code}")

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    markdown, topic, ideas, found = build_markdown(week, url, soup)
    print(markdown)

    if not found:
        print(f"{url} is live but has no group-exercise section; headings are listed above.", file=sys.stderr)
        return 3

    if args.no_write:
        return 0
    if args.out:
        out = Path(args.out)
    elif week is not None:
        out = REPO_ROOT / "notebooks" / "briefs" / f"week{week}.md"
    else:
        die("cannot derive the week number from the URL; pass --week N or --no-write")
    if out.exists() and not args.force:
        die(f"{rel(out)} exists; pass --force to overwrite it")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(f"wrote {rel(out)}  (topic: {topic!r}, suggested slug: {slugify(topic)!r})", file=sys.stderr)
    if ideas is None:
        warn("no 'This week' ideas list was found; read the verbatim section instead")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
