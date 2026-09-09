"""A small MediaWiki API client for going beyond the frozen snapshot.

Wikipedia answers 403 to requests that do not carry a User-Agent identifying
the client (Wikimedia User-Agent policy). Every request from this repo goes
through session(), which sets one, and api_get(), which also throttles.

    from marvel import get_wikitext, wikitext_links, title_to_node_id

    text = get_wikitext("Spider-Man")
    links = wikitext_links(text)          # [[Page]] targets, the way the snapshot was built
    ids = [title_to_node_id(t) for t in links]
"""

from __future__ import annotations

import re
import time
import urllib.parse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

__all__ = [
    "API",
    "USER_AGENT",
    "PageNotFound",
    "api_get",
    "get_category_members",
    "get_links",
    "get_wikitext",
    "node_id_to_title",
    "session",
    "title_to_node_id",
    "wikitext_links",
]

# Format follows the Wikimedia policy: <client>/<version> (<contact>) <library>/<version>.
# The repository URL is the contact; add a course e-mail after it if you like.
USER_AGENT = (
    "SixDegreesOfMarvel/0.1 "
    "(https://github.com/02805-s224568-s224564/playground) "
    f"python-requests/{requests.__version__}"
)

API = "https://en.wikipedia.org/w/api.php"
MIN_INTERVAL = 0.1  # seconds between API calls
DEFAULT_TIMEOUT = 30

# Link targets in these namespaces are not articles and never became edges.
_SKIP_PREFIXES = ("file:", "image:", "category:", "wikipedia:", "template:", "help:", "wp:")
_WIKILINK = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")


class PageNotFound(LookupError):
    """The title does not exist on English Wikipedia."""


def session(*, retries: int = 3) -> requests.Session:
    """A requests session with the User-Agent header and polite retries."""
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    retry = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


_default_session: requests.Session | None = None
_last_call = 0.0


def _session(s: requests.Session | None) -> requests.Session:
    global _default_session
    if s is not None:
        return s
    if _default_session is None:
        _default_session = session()
    return _default_session


def api_get(params: dict, *, s: requests.Session | None = None, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """One call to the MediaWiki API, throttled, JSON decoded, API errors raised."""
    global _last_call
    wait = MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    query = {"format": "json", "formatversion": "2", **params}
    response = _session(s).get(API, params=query, timeout=timeout)
    _last_call = time.monotonic()
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"MediaWiki API error {err.get('code')}: {err.get('info')}")
    return data


def _paged(params: dict, *, s: requests.Session | None = None):
    """Yield every result page, following `continue` tokens."""
    cont: dict = {}
    while True:
        data = api_get({**params, **cont}, s=s)
        yield data
        cont = data.get("continue") or {}
        if not cont:
            return


def get_wikitext(title: str, *, s: requests.Session | None = None) -> str:
    """The raw wiki-source of an article, redirects resolved."""
    data = api_get(
        {
            "action": "query",
            "prop": "revisions",
            "rvslots": "main",
            "rvprop": "content",
            "titles": title,
            "redirects": "1",
        },
        s=s,
    )
    page = data["query"]["pages"][0]
    if page.get("missing"):
        raise PageNotFound(title)
    return page["revisions"][0]["slots"]["main"]["content"]


def get_links(title: str, *, namespace: int = 0, s: requests.Session | None = None) -> list[str]:
    """Titles linked from `title` according to Wikipedia's link index.

    Note the difference from the snapshot: the index counts links contributed by
    navigation templates too. The course edges came from the article text;
    use get_wikitext() + wikitext_links() to reproduce those.
    """
    links: list[str] = []
    for data in _paged(
        {
            "action": "query",
            "prop": "links",
            "titles": title,
            "plnamespace": namespace,
            "pllimit": "max",
            "redirects": "1",
        },
        s=s,
    ):
        page = data["query"]["pages"][0]
        if page.get("missing"):
            raise PageNotFound(title)
        links.extend(link["title"] for link in page.get("links", []))
    return links


def get_category_members(category: str, *, namespace: int = 0, s: requests.Session | None = None) -> list[str]:
    """Article titles in a category, e.g. "Category:Marvel Comics superheroes"."""
    if not category.startswith("Category:"):
        category = "Category:" + category
    members: list[str] = []
    for data in _paged(
        {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmnamespace": namespace,
            "cmlimit": "max",
        },
        s=s,
    ):
        members.extend(m["title"] for m in data["query"]["categorymembers"])
    return members


def wikitext_links(wikitext: str) -> list[str]:
    """[[Page name]] targets in wiki-source, in order, de-duplicated.

    This is how the snapshot's edges were harvested: internal links in the
    running text, not the link index. Section anchors and display labels are
    stripped; file, image and category links are skipped.
    """
    seen: dict[str, None] = {}
    for match in _WIKILINK.finditer(wikitext):
        target = match.group(1).strip()
        if not target or target.lower().startswith(_SKIP_PREFIXES):
            continue
        target = target[0].upper() + target[1:]
        seen.setdefault(target.replace("_", " "), None)
    return list(seen)


def node_id_to_title(node_id: str) -> str:
    """Roster node_id ("Abomination_(character)") to Wikipedia title ("Abomination (character)")."""
    return node_id.replace("_", " ")


def title_to_node_id(title: str, nodes=None) -> str | None:
    """Map a Wikipedia title (spaces or underscores) to a roster node_id.

    Matches on node_id, on the roster's display name, and on the tail of the
    roster URL. Returns None when the title is not one of the 303 characters.
    Pass the DataFrame from load_nodes() to avoid re-reading it in a loop.
    """
    key = title.strip().replace(" ", "_")
    if nodes is None:
        from .data import load_nodes

        nodes = load_nodes()
    ids = nodes["node_id"].tolist()
    if key in set(ids):
        return key
    by_name = {name.replace(" ", "_"): nid for nid, name in zip(ids, nodes["name"])}
    if key in by_name:
        return by_name[key]
    by_url = {urllib.parse.unquote(url.rsplit("/", 1)[-1]): nid for nid, url in zip(ids, nodes["url"])}
    return by_url.get(key)
