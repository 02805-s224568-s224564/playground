"""Helpers for the weekly 02805 analyses of the Marvel/Wikipedia network.

    from marvel import load_graph, save_figure, apply_style

    G = load_graph()                      # 303 nodes, 1784 edges, isolates included
    snippet = save_figure(fig, "degree-distribution", week=1,
                          alt="Log-log degree distribution")
    print(snippet)                        # paste into the post

Notebooks live in notebooks/, so they add the repo root to sys.path first; the
template notebook does this for you.
"""

from .data import (
    EXPECTED,
    SnapshotError,
    ensure_snapshot,
    load_edges,
    load_graph,
    load_nodes,
)
from .figures import apply_style, save_figure
from .wiki import (
    USER_AGENT,
    PageNotFound,
    get_category_members,
    get_links,
    get_wikitext,
    session,
    title_to_node_id,
    wikitext_links,
)

__version__ = "0.1"

__all__ = [
    "EXPECTED",
    "PageNotFound",
    "SnapshotError",
    "USER_AGENT",
    "apply_style",
    "ensure_snapshot",
    "get_category_members",
    "get_links",
    "get_wikitext",
    "load_edges",
    "load_graph",
    "load_nodes",
    "save_figure",
    "session",
    "title_to_node_id",
    "wikitext_links",
]
