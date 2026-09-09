"""Shared helpers for the go-nuts skill scripts.

Every script is run with the repo's venv Python from any working directory:

    .venv/bin/python .claude/skills/go-nuts/scripts/<script>.py ...
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import NoReturn

SKILL_DIR = Path(__file__).resolve().parents[1]  # .claude/skills/go-nuts
REPO_ROOT = SKILL_DIR.parents[2]  # .claude/skills/go-nuts -> .claude/skills -> .claude -> repo

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from marvel.wiki import USER_AGENT, session as _marvel_session
except Exception:  # marvel not importable: still identify ourselves
    USER_AGENT = "SixDegreesOfMarvel/0.1 (https://github.com/02805-s224568-s224564/playground)"
    _marvel_session = None

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
POST_FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-([a-z0-9][a-z0-9-]*)\.md$")


def http():
    """A requests session carrying the User-Agent and polite retries."""
    if _marvel_session is not None:
        return _marvel_session()
    import requests

    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def site_config() -> dict:
    import yaml

    with open(REPO_ROOT / "_config.yml", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def slugify(text: str, maxlen: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:maxlen].rstrip("-")


def rel(path: Path | str) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def die(msg: str, code: int = 1) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"ok: {msg}")


def read_front_matter(path: Path) -> tuple[dict, str]:
    """Split a Jekyll file into (front matter dict, body). Empty dict if there is none."""
    import yaml

    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", text, re.S)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{rel(path)}: front matter is not a mapping")
    return data, match.group(2)


def week_from_name(name: str) -> int | None:
    match = re.search(r"week(\d+)", name)
    return int(match.group(1)) if match else None


def git(*args: str, check: bool = True) -> str:
    import subprocess

    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()
