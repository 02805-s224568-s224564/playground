"""Load the frozen 02805 Marvel snapshot as a networkx DiGraph.

Why the roster comes first
--------------------------
17 of the 303 characters have no link in either direction. Build the graph from
the edge list alone and you get 286 nodes: the isolates vanish without a
warning, and the isolates are part of the story. So load_graph() adds every
node from week1_nodes.tsv first, then the edges, and asserts the counts.

Where the files come from
-------------------------
data/raw/ is gitignored. ensure_snapshot() downloads each file from the course
site on first use and verifies its sha256 against the constants below, so every
machine computes on identical bytes. A corrupt or edited file is re-downloaded.

    python -m marvel           # fetch everything and print a summary
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import pandas as pd
import requests

from .wiki import session

__all__ = [
    "BASE_URL",
    "EXPECTED",
    "NODE_COLUMNS",
    "SNAPSHOTS",
    "Snapshot",
    "SnapshotError",
    "default_data_dir",
    "ensure_all",
    "ensure_snapshot",
    "load_edges",
    "load_graph",
    "load_nodes",
    "repo_root",
    "sha256_of",
]

BASE_URL = "https://sunelehmann.com/socialgraphs2026-web/data/"
SNAPSHOT_DATE = "2026-08-26"


@dataclass(frozen=True)
class Snapshot:
    name: str
    sha256: str
    size: int

    @property
    def url(self) -> str:
        return BASE_URL + self.name


SNAPSHOTS: dict[str, Snapshot] = {
    s.name: s
    for s in (
        Snapshot("week1_nodes.tsv", "a10ec309ac60ea8b72bcc1a18aba801414896676dac172619def0435e585391e", 63413),
        Snapshot("week1_edges.tsv", "87be017a35e8f27a1f1bc0912ebb5723c0084e460cb2dbd0d2abd0e83fc644b2", 61379),
        Snapshot("week4_edges_weighted.tsv", "aea9d7f84f942b40befc04f87e482b06385c64ea0461b0af886ace442a059666", 65035),
    )
}

EXPECTED = {"nodes": 303, "edges": 1784, "isolates": 17}
NODE_COLUMNS = ["node_id", "name", "wikidata_id", "url", "description"]

NODES_FILE = "week1_nodes.tsv"
EDGE_FILES = {False: "week1_edges.tsv", True: "week4_edges_weighted.tsv"}


class SnapshotError(RuntimeError):
    """A snapshot file is missing, cannot be fetched, or does not match its checksum."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_data_dir() -> Path:
    return repo_root() / "data" / "raw"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, dest: Path) -> None:
    """Stream `url` to `dest` via a temporary file so a failed download leaves nothing behind."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    try:
        with session().get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(part, "wb") as fh:
                for chunk in response.iter_content(1 << 16):
                    fh.write(chunk)
        os.replace(part, dest)
    except requests.RequestException as err:
        part.unlink(missing_ok=True)
        raise SnapshotError(
            f"Could not download {url}: {err}\n"
            "Check that you are online. If the course site is down, ask a group "
            f"member for a copy and put it at {dest}."
        ) from err


def ensure_snapshot(name: str, data_dir: Path | str | None = None, force: bool = False) -> Path:
    """Return the local path of a snapshot file, downloading and verifying it as needed."""
    try:
        snap = SNAPSHOTS[name]
    except KeyError:
        raise SnapshotError(f"Unknown snapshot file {name!r}; known files: {sorted(SNAPSHOTS)}") from None
    path = Path(data_dir) / name if data_dir else default_data_dir() / name

    if path.exists() and not force:
        if sha256_of(path) == snap.sha256:
            return path
        warnings.warn(f"{path} does not match the expected checksum; re-downloading.", stacklevel=2)

    _download(snap.url, path)
    actual = sha256_of(path)
    if actual != snap.sha256:
        raise SnapshotError(
            f"{name} downloaded from {snap.url} does not match the expected checksum.\n"
            f"  expected {snap.sha256}\n"
            f"  actual   {actual}\n"
            f"The course may have re-released the file. Check {BASE_URL} and, if so, "
            "update SNAPSHOTS in marvel/data.py."
        )
    return path


def ensure_all(data_dir: Path | str | None = None) -> dict[str, Path]:
    return {name: ensure_snapshot(name, data_dir) for name in SNAPSHOTS}


def _leading_comment_lines(path: Path) -> int:
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            count += 1
    return count


def _read_tsv(path: Path, names: list[str] | None = None) -> pd.DataFrame:
    """Read a course TSV.

    Leading `#` lines are skipped by count rather than with pandas' `comment`
    option, which would also truncate a description containing `#`. The files
    never quote, but descriptions contain quotation marks, hence QUOTE_NONE.
    With `names`, the file has no header row (the edge files put theirs in a
    comment); without, the first non-comment row is the header.
    """
    skip = _leading_comment_lines(path)
    common = dict(sep="\t", skiprows=skip, quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False, encoding="utf-8")
    if names is None:
        return pd.read_csv(path, header=0, **common)
    return pd.read_csv(path, header=None, names=names, **common)


def load_nodes(data_dir: Path | str | None = None) -> pd.DataFrame:
    """The roster: one row per character with node_id, name, wikidata_id, url, description."""
    nodes = _read_tsv(ensure_snapshot(NODES_FILE, data_dir))
    missing = [c for c in NODE_COLUMNS if c not in nodes.columns]
    if missing:
        raise SnapshotError(f"{NODES_FILE} lacks expected columns {missing}; got {list(nodes.columns)}")
    return nodes[NODE_COLUMNS]


def load_edges(weighted: bool = False, data_dir: Path | str | None = None) -> pd.DataFrame:
    """The edge list (source, target[, weight]); weight is an int."""
    names = ["source", "target"] + (["weight"] if weighted else [])
    edges = _read_tsv(ensure_snapshot(EDGE_FILES[weighted], data_dir), names=names)
    if weighted:
        edges["weight"] = edges["weight"].astype(int)
    return edges


def load_graph(weighted: bool = False, data_dir: Path | str | None = None, check: bool = True) -> nx.DiGraph:
    """The Marvel network as a DiGraph with node attributes, isolates included.

    weighted=True uses the week 4 file, where each edge carries how many times
    A's article links to B's. check=True asserts the published counts.
    """
    nodes = load_nodes(data_dir)
    edges = load_edges(weighted, data_dir)

    G = nx.DiGraph(name="Marvel superheroes, Wikipedia links")
    G.graph.update(source=BASE_URL, snapshot=SNAPSHOT_DATE, weighted=weighted)
    G.add_nodes_from((row["node_id"], {k: row[k] for k in NODE_COLUMNS[1:]}) for row in nodes.to_dict("records"))
    if weighted:
        G.add_edges_from((u, v, {"weight": int(w)}) for u, v, w in edges.itertuples(index=False))
    else:
        G.add_edges_from(edges.itertuples(index=False))

    if check:
        _check(G, nodes, edges, weighted)
    return G


def _check(G: nx.DiGraph, nodes: pd.DataFrame, edges: pd.DataFrame, weighted: bool) -> None:
    edge_file = EDGE_FILES[weighted]
    endpoints = set(edges["source"]) | set(edges["target"])
    unknown = sorted(endpoints - set(nodes["node_id"]))
    if unknown:
        raise SnapshotError(
            f"{len(unknown)} edge endpoint(s) are not in the roster, e.g. {unknown[0]!r}. "
            f"Delete data/raw/{edge_file} and data/raw/{NODES_FILE} to re-download."
        )
    problems = []
    if G.number_of_nodes() != len(nodes):
        problems.append(f"graph has {G.number_of_nodes()} nodes but the roster has {len(nodes)}")
    if G.number_of_nodes() != EXPECTED["nodes"]:
        problems.append(f"expected {EXPECTED['nodes']} nodes, got {G.number_of_nodes()} (check {NODES_FILE})")
    if G.number_of_edges() != EXPECTED["edges"]:
        problems.append(f"expected {EXPECTED['edges']} edges, got {G.number_of_edges()} (check {edge_file})")
    isolates = nx.number_of_isolates(G)
    if isolates != EXPECTED["isolates"]:
        problems.append(f"expected {EXPECTED['isolates']} isolates, got {isolates}")
    if problems:
        raise SnapshotError(
            "Snapshot sanity check failed: " + "; ".join(problems) + ". "
            "Delete the file(s) under data/raw/ to re-download, or pass check=False if the course re-released the data."
        )


def _main() -> int:
    root = repo_root()
    for name, path in ensure_all().items():
        print(f"ok  {path.relative_to(root)}  ({SNAPSHOTS[name].size} bytes, sha256 verified)")
    G = load_graph()
    Gw = load_graph(weighted=True)
    print(
        f"unweighted: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, "
        f"{nx.number_of_isolates(G)} isolates"
    )
    total = sum(d["weight"] for _, _, d in Gw.edges(data=True))
    print(f"weighted:   {Gw.number_of_edges()} edges, total weight {total}")
    for node in ("Spider-Man", "Hulk"):
        attrs = G.nodes[node]
        print(f"{node}: in {G.in_degree(node)}, out {G.out_degree(node)}, {attrs['wikidata_id']}, {attrs['url']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(_main())
    except SnapshotError as err:
        print(f"error: {err}", file=sys.stderr)
        sys.exit(1)
