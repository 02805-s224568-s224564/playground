#!/usr/bin/env python
"""Wait for the GitHub Pages deploy of HEAD and verify the live post and its assets.

    check_deploy.py                              # newest post, wait for the deploy of HEAD
    check_deploy.py _posts/2026-09-15-slug.md    # a specific post
    check_deploy.py https://.../2026/09/15/slug/ # a URL
    check_deploy.py --no-wait                    # one look at the latest run, no polling

Uses the public GitHub API (no gh CLI, no token needed for a public repo;
set GITHUB_TOKEN to raise the rate limit from 60 to 5000 requests per hour).

Exit codes: 0 deployed and every asset answers 200 · 1 run failed, asset
missing, or timeout · 2 nothing to check (HEAD is not pushed yet).
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

from _common import POST_FILENAME_RE, REPO_ROOT, die, git, http, rel, site_config, warn

WORKFLOW_FILE = "pages.yml"


def post_url(target: str | None, site: str) -> str:
    if target and target.startswith("http"):
        return target
    if target:
        path = Path(target)
    else:
        posts = sorted((REPO_ROOT / "_posts").glob("*.md"))
        if not posts:
            return site + "/"
        path = posts[-1]
    match = POST_FILENAME_RE.match(path.name)
    if not match:
        die(f"{path.name} is not a YYYY-MM-DD-slug.md post filename")
    year, month, day, slug = match.groups()
    return f"{site}/{year}/{month}/{day}/{slug}/"


def api_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def wait_for_run(session, repo: str, sha: str, timeout: int, interval: int, no_wait: bool) -> dict | None:
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/runs"
    deadline = time.monotonic() + timeout
    polls = 0
    chosen = None
    while True:
        response = session.get(url, params={"branch": "main", "per_page": 5}, headers=api_headers(), timeout=20)
        remaining = int(response.headers.get("X-RateLimit-Remaining", "60"))
        if response.status_code in (403, 429) and remaining == 0:
            reset = int(response.headers.get("X-RateLimit-Reset", "0"))
            pause = max(30, min(reset - time.time(), 900))
            warn(f"GitHub API rate limit hit; sleeping {pause:.0f}s (set GITHUB_TOKEN to avoid this)")
            time.sleep(pause)
            continue
        response.raise_for_status()
        runs = response.json().get("workflow_runs", [])
        polls += 1
        run = next((r for r in runs if r["head_sha"] == sha), None)
        if run is None and runs and (polls >= 3 or no_wait):
            run = runs[0]
            if chosen is None:
                warn(f"no run for {sha[:7]} yet; looking at the latest run instead ({run['head_sha'][:7]})")
        chosen = run
        if run is not None:
            print(f"run #{run['run_number']} for {run['head_sha'][:7]}: {run['status']} {run.get('conclusion') or ''}  {run['html_url']}")
            if run["status"] == "completed":
                return run
        else:
            print(f"no workflow run for {sha[:7]} yet")
        if no_wait:
            return run
        if time.monotonic() > deadline:
            print(f"timed out after {timeout}s waiting for the deploy", file=sys.stderr)
            return run
        if remaining < 3:
            warn("GitHub API budget nearly spent; waiting a minute")
            time.sleep(60)
        time.sleep(interval)


def verify_page(session, url: str, attempts: int = 6, pause: int = 15) -> bool:
    from bs4 import BeautifulSoup

    response = None
    for attempt in range(1, attempts + 1):
        response = session.get(url, timeout=20)
        if response.status_code == 200:
            break
        print(f"{url} answered {response.status_code} (attempt {attempt}/{attempts}); Pages CDN may lag, retrying in {pause}s")
        time.sleep(pause)
    if response is None or response.status_code != 200:
        print(f"FAIL  {url} is not reachable")
        return False

    soup = BeautifulSoup(response.text, "html.parser")
    if soup.select_one("article.prose") is None:
        print(f"FAIL  {url} does not render a post (no <article class=\"prose\">)")
        return False
    print(f"ok    {url}")

    assets = []
    for img in soup.find_all("img", src=True):
        assets.append(("img", urljoin(url, img["src"])))
    for frame in soup.find_all("iframe", src=True):
        assets.append(("iframe", urljoin(url, frame["src"])))
    for link in soup.find_all("link", rel="stylesheet", href=True):
        assets.append(("css", urljoin(url, link["href"])))

    all_ok = True
    for kind, asset in assets:
        head = session.head(asset, timeout=20, allow_redirects=True)
        status = head.status_code
        if status == 405:
            status = session.get(asset, timeout=20, stream=True).status_code
        mark = "ok  " if status == 200 else "FAIL"
        all_ok &= status == 200
        print(f"{mark}  {status}  {kind:6} {asset}")
    if not assets:
        print("note  the post embeds no figure; the rules ask for one figure or table")
    return all_ok


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", nargs="?", help="post file or URL (default: newest post)")
    parser.add_argument("--sha", help="commit to wait for (default: HEAD)")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--no-wait", action="store_true")
    args = parser.parse_args(argv)

    config = site_config()
    repo = config.get("repository")
    site = config.get("url", "").rstrip("/") + config.get("baseurl", "")
    if not repo or not site:
        die("_config.yml needs `repository`, `url` and `baseurl`")

    sha = args.sha or git("rev-parse", "HEAD")
    if not args.sha:
        if git("status", "--porcelain"):
            warn("working tree has uncommitted changes; they are not part of this deploy")
        upstream = git("rev-parse", "@{u}", check=False)
        if upstream and upstream != sha:
            print(f"HEAD {sha[:7]} is not pushed (origin has {upstream[:7]}); push first", file=sys.stderr)
            return 2

    url = post_url(args.target, site)
    print(f"post: {url}")
    session = http()
    run = wait_for_run(session, repo, sha, args.timeout, args.interval, args.no_wait)
    if run is None or run["status"] != "completed":
        return 1
    if run.get("conclusion") != "success":
        print(f"deploy {run.get('conclusion')}: {run['html_url']}", file=sys.stderr)
        return 1
    finished = run.get("updated_at", "")
    if finished:
        print(f"deployed at {finished} (UTC); now {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    return 0 if verify_page(session, url) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
