#!/usr/bin/env python
"""Verify the repo hygiene the weekly workflow depends on.

    check_hygiene.py            # WARN lines do not fail the run
    check_hygiene.py --strict   # WARN counts as FAIL (use before publishing)

Prints one PASS / WARN / FAIL line per check with a fix hint. Exit 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

from _common import POST_FILENAME_RE, REPO_ROOT, git, read_front_matter, rel, site_config

INCLUDE_RE = re.compile(r"{%-?\s*include\s+(figure|interactive)\.html\s+(.*?)-?%}", re.S)
SRC_RE = re.compile(r"""src=(?:"([^"]*)"|'([^']*)')""")
REQUIRED_EXCLUDES = {"notebooks/", "data/", "scripts/", "marvel/", "tests/", "pytest.ini", "requirements.txt", "*.ipynb"}

Result = tuple[str, str, str]  # status, check, detail


def _run(*cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


# --- checks -----------------------------------------------------------------


def check_python() -> Result:
    v = sys.version_info
    status = "PASS" if v >= (3, 12) else "FAIL"
    return status, f"Python {v.major}.{v.minor} (venv)", "" if status == "PASS" else "requirements need Python 3.12+"


def check_excludes() -> Result:
    excludes = set(site_config().get("exclude") or [])
    missing = sorted(REQUIRED_EXCLUDES - excludes)
    if missing:
        return "FAIL", "Jekyll excludes analysis files", f"add to exclude: in _config.yml: {', '.join(missing)}"
    return "PASS", "Jekyll excludes analysis files", ""


def check_gitattributes() -> Result:
    path = REPO_ROOT / ".gitattributes"
    text = path.read_text() if path.exists() else ""
    if re.search(r"^\*\.ipynb\s+filter=nbstripout", text, re.M):
        return "PASS", ".gitattributes routes notebooks through nbstripout", ""
    return "FAIL", ".gitattributes routes notebooks through nbstripout", "add `*.ipynb filter=nbstripout` to .gitattributes"


def check_nbstripout_installed() -> Result:
    result = _run(sys.executable, "-m", "nbstripout", "--is-installed")
    if result.returncode == 0:
        return "PASS", "nbstripout filter installed in this clone", ""
    return "FAIL", "nbstripout filter installed in this clone", "run ./scripts/dev-setup.sh (the filter lives in .git/config, not in the repo)"


def check_committed_notebooks() -> Result:
    listed = _run("git", "ls-files", "*.ipynb").stdout.split()
    dirty = []
    for path in listed:
        shown = _run("git", "show", f":{path}")
        if shown.returncode != 0:
            continue
        try:
            nb = json.loads(shown.stdout)
        except json.JSONDecodeError:
            dirty.append(f"{path} (not valid JSON)")
            continue
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code" and (cell.get("outputs") or cell.get("execution_count") is not None):
                dirty.append(path)
                break
    if dirty:
        return "FAIL", "staged notebooks have no outputs", "outputs in: " + ", ".join(dirty) + "; run ./scripts/dev-setup.sh then `git add` again"
    return "PASS", f"staged notebooks have no outputs ({len(listed)} notebook(s))", ""


def check_user_agent() -> Result:
    path = REPO_ROOT / "marvel" / "wiki.py"
    text = path.read_text() if path.exists() else ""
    if re.search(r"^USER_AGENT\s*=", text, re.M) and "SixDegreesOfMarvel/" in text:
        return "PASS", "Wikipedia client sends a User-Agent", ""
    return "FAIL", "Wikipedia client sends a User-Agent", "marvel/wiki.py must define USER_AGENT = 'SixDegreesOfMarvel/...'"


def check_requirements() -> Result:
    text = (REPO_ROOT / "requirements.txt").read_text()
    missing = [pkg for pkg in ("plotly", "pytest") if not re.search(rf"^{pkg}\b", text, re.M)]
    if missing:
        return "FAIL", "requirements.txt lists plotly and pytest", "add: " + ", ".join(missing)
    return "PASS", "requirements.txt lists plotly and pytest", ""


def check_layout_and_includes() -> Result:
    layout = (REPO_ROOT / "_layouts" / "default.html").read_text()
    problems = []
    if "mathjax.html" not in layout:
        problems.append("_layouts/default.html lacks {% include mathjax.html %}")
    for name in ("figure.html", "interactive.html", "mathjax.html"):
        if not (REPO_ROOT / "_includes" / name).exists():
            problems.append(f"_includes/{name} missing")
    if problems:
        return "FAIL", "layout loads MathJax and figure includes exist", "; ".join(problems)
    return "PASS", "layout loads MathJax and figure includes exist", ""


def check_data_ignored() -> Result:
    result = _run("git", "check-ignore", "-q", "data/raw/week1_edges.tsv")
    if result.returncode == 0:
        return "PASS", "data/raw/ is gitignored", ""
    return "FAIL", "data/raw/ is gitignored", "keep `data/*` in .gitignore; the snapshot is downloaded, never committed"


def _referenced_sources(posts: list[Path]) -> set[str]:
    refs = set()
    for post in posts:
        for _, params in INCLUDE_RE.findall(post.read_text(encoding="utf-8")):
            match = SRC_RE.search(params)
            if match:
                refs.add(match.group(1) or match.group(2))
    return refs


def check_posts() -> list[Result]:
    posts = sorted((REPO_ROOT / "_posts").glob("*.md"))
    if not posts:
        return [("PASS", "posts (none yet)", "")]
    results: list[Result] = []
    today = dt.date.today()
    for post in posts:
        name = rel(post)
        fails, warns = [], []
        match = POST_FILENAME_RE.match(post.name)
        if not match:
            fails.append("filename must be YYYY-MM-DD-slug.md with a lowercase slug")
        else:
            try:
                date = dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                if date > today:
                    warns.append(f"dated {date}, in the future: Jekyll will hide it")
            except ValueError:
                fails.append("filename date is not a real date")
        try:
            data, body = read_front_matter(post)
        except Exception as err:
            results.append(("FAIL", name, f"front matter does not parse: {err}"))
            continue
        if not data:
            fails.append("no front matter")
        if "layout" in data:
            fails.append("remove `layout:`; _config.yml sets it for every post")
        if "title" not in data:
            fails.append("front matter needs `title`")
        if "week" not in data:
            warns.append("front matter has no `week`")
        elif not isinstance(data["week"], int):
            fails.append("`week` must be an integer")
        notebook = data.get("notebook")
        if notebook and not (REPO_ROOT / notebook).exists():
            warns.append(f"notebook {notebook} does not exist")
        elif not notebook:
            warns.append("no `notebook:` link; readers cannot check the work")
        if re.search(r"!\[[^\]]*\]\(", body):
            fails.append("markdown image syntax breaks under /playground; use {% include figure.html %}")
        markers = body.count("<!-- go-nuts:")
        if markers:
            warns.append(f"{markers} unfilled <!-- go-nuts: --> marker(s)")
        for kind, params in INCLUDE_RE.findall(body):
            src = SRC_RE.search(params)
            if not src:
                fails.append(f"{kind}.html include without src=")
                continue
            target = (src.group(1) or src.group(2)).lstrip("/")
            if not (REPO_ROOT / target).exists():
                fails.append(f"figure missing: {target}")
            if not re.search(r"""alt=(?:"[^"]+"|'[^']+')""", params):
                fails.append(f"{kind}.html include without alt text")
        if fails:
            results.append(("FAIL", name, "; ".join(fails + warns)))
        elif warns:
            results.append(("WARN", name, "; ".join(warns)))
        else:
            results.append(("PASS", name, ""))
    return results


def check_figures() -> list[Result]:
    figures_dir = REPO_ROOT / "assets" / "figures"
    figures = sorted(p for p in figures_dir.glob("week*") if p.is_file())
    if not figures:
        return [("PASS", "figures (none yet)", "")]
    referenced = _referenced_sources(sorted((REPO_ROOT / "_posts").glob("*.md")))
    results: list[Result] = []
    examples = [rel(p) for p in figures if "-example" in p.name]
    if examples:
        results.append(("WARN", "template example figures still present", ", ".join(examples) + "; rename or delete them"))
    orphans = [rel(p) for p in figures if f"/{p.relative_to(REPO_ROOT).as_posix()}" not in referenced and "-example" not in p.name]
    if orphans:
        results.append(("WARN", "figures not referenced by any post", ", ".join(orphans)))
    if not results:
        results.append(("PASS", f"figures ({len(figures)}) are all referenced by a post", ""))
    return results


# --- main -------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="treat WARN as FAIL")
    args = parser.parse_args(argv)

    results: list[Result] = [
        check_python(),
        check_excludes(),
        check_gitattributes(),
        check_nbstripout_installed(),
        check_committed_notebooks(),
        check_user_agent(),
        check_requirements(),
        check_layout_and_includes(),
        check_data_ignored(),
        *check_posts(),
        *check_figures(),
    ]

    failed = 0
    for status, check, detail in results:
        if status == "WARN" and args.strict:
            status = "FAIL"
        if status == "FAIL":
            failed += 1
        line = f"{status:4}  {check}"
        if detail:
            line += f"  — {detail}"
        print(line)
    print()
    if failed:
        print(f"{failed} check(s) failed")
        return 1
    print("hygiene ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
