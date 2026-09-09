# The shared playground data

Base URL <https://sunelehmann.com/socialgraphs2026-web/data/>, a frozen snapshot
of English Wikipedia taken 26 August 2026.

| File | Bytes | sha256 (prefix) | Content |
|---|---|---|---|
| `week1_nodes.tsv` | 63413 | `a10ec309…` | 303 rows: `node_id`, `name`, `wikidata_id`, `url`, `description` |
| `week1_edges.tsv` | 61379 | `87be017a…` | 1784 rows: `source`, `target`. A → B when the text of A's article links B's |
| `week4_edges_weighted.tsv` | 65035 | `aea9d7f8…` | the same 1784 edges with `weight` = number of such links, 1 to 11 |

Full checksums live in `SNAPSHOTS` in `marvel/data.py`. Week 5 adds the raw
page text (served from DTU storage; not handled by the loader yet).

## Loading

```python
from marvel import load_graph, load_nodes

G = load_graph()                 # nx.DiGraph: 303 nodes, 1784 edges, 17 isolates
Gw = load_graph(weighted=True)   # same edges with an integer "weight" attribute
G.nodes["Spider-Man"]            # {'name': ..., 'wikidata_id': 'Q79037', 'url': ..., 'description': ...}
nodes = load_nodes()             # the roster as a DataFrame
```

Roster first, then edges. From the edge list alone you get 286 nodes: the 17
characters with no link in either direction vanish without a warning, and the
course says explicitly that they are worth a look. `load_graph` asserts
303 nodes, 1784 edges and 17 isolates and raises `SnapshotError` otherwise;
pass `check=False` only if the course re-releases the data.

For an undirected weighted network the course says to sum the two directions
(maximum 16). `G.to_undirected()` keeps one direction's weight, so build it by
hand:

```python
U = nx.Graph()
U.add_nodes_from(Gw.nodes(data=True))
for u, v, d in Gw.edges(data=True):
    U.add_edge(u, v, weight=U[u][v]["weight"] + d["weight"] if U.has_edge(u, v) else d["weight"])
```

## Format quirks the loader handles

- `#` comment headers. The edge files put their column names in a comment line, so pandas gets `names=` explicitly.
- Leading comment lines are skipped by count, not with `comment="#"`, which would also truncate a description containing `#`.
- The files never quote, but 35 descriptions contain `"`: `quoting=csv.QUOTE_NONE`.
- `node_id` is the Wikipedia title with underscores; `name` is the display name; redirects are resolved on both ends, so an alias and its character are one node.
- Edges come from article text, not from Wikipedia's link index, so shared navigation templates do not create edges.

## Where the files live

`data/raw/`, gitignored. Downloaded on first use, sha256-verified on every
load. To force a fresh copy delete the file or call
`ensure_snapshot("week1_edges.tsv", force=True)`. `python -m marvel` fetches
everything and prints a summary.

## Beyond the snapshot: the Wikipedia API (`marvel.wiki`)

- `session()` sets `User-Agent: SixDegreesOfMarvel/0.1 (https://github.com/02805-s224568-s224564/playground) python-requests/<version>`. Wikipedia answers 403 without one. Every helper below uses it.
- `get_wikitext(title)` returns the raw wiki-source; `wikitext_links(text)` extracts the `[[…]]` targets, which is how the snapshot's edges were harvested.
- `get_links(title)` returns Wikipedia's link index instead. It includes template links, so it will not match the snapshot; useful for showing the difference.
- `get_category_members("Marvel Comics superheroes")` lists a category, for the weeks 2 to 4 option of crawling a category of your own.
- `title_to_node_id(title, nodes)` maps a title back to the roster; `node_id_to_title` goes the other way.
- Calls use `formatversion=2`, follow `continue` tokens, retry on 429 and 5xx, and are throttled to ten per second.
