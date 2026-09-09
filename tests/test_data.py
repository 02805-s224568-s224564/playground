import hashlib

import networkx as nx
import pytest

import marvel.data as md

NODES_TSV = (
    "# fake roster\n"
    "# second comment line\n"
    "node_id\tname\twikidata_id\turl\tdescription\n"
    'A_(x)\tA (x)\tQ1\thttps://en.wikipedia.org/wiki/A_(x)\tSays "hi" and is the #1 fan\n'
    "B\tB\tQ2\thttps://en.wikipedia.org/wiki/B\tPlain\n"
    "C\tC\tQ3\thttps://en.wikipedia.org/wiki/C\tNobody links here\n"
)
EDGES_TSV = "# fake edges\n# source\ttarget\nA_(x)\tB\nB\tA_(x)\n"


def _fake_snapshot(tmp_path, monkeypatch, nodes=NODES_TSV, edges=EDGES_TSV):
    """Write a tiny roster + edge list and point the module's checksums at them."""
    files = {"week1_nodes.tsv": nodes, "week1_edges.tsv": edges}
    snapshots = {}
    for name, text in files.items():
        data = text.encode()
        (tmp_path / name).write_bytes(data)
        snapshots[name] = md.Snapshot(name, hashlib.sha256(data).hexdigest(), len(data))
    monkeypatch.setattr(md, "SNAPSHOTS", snapshots)
    monkeypatch.setattr(md, "EXPECTED", {"nodes": 3, "edges": 2, "isolates": 1})
    return tmp_path


def test_read_tsv_keeps_quotes_and_hashes(tmp_path):
    path = tmp_path / "nodes.tsv"
    path.write_text(NODES_TSV)
    df = md._read_tsv(path)
    assert list(df.columns) == md.NODE_COLUMNS
    assert len(df) == 3
    assert df.loc[0, "description"] == 'Says "hi" and is the #1 fan'


def test_read_tsv_with_commented_header(tmp_path):
    path = tmp_path / "edges.tsv"
    path.write_text(EDGES_TSV)
    df = md._read_tsv(path, names=["source", "target"])
    assert df.to_dict("records") == [
        {"source": "A_(x)", "target": "B"},
        {"source": "B", "target": "A_(x)"},
    ]


def test_graph_keeps_isolates_and_attributes(tmp_path, monkeypatch):
    data_dir = _fake_snapshot(tmp_path, monkeypatch)
    G = md.load_graph(data_dir=data_dir)
    assert isinstance(G, nx.DiGraph)
    assert set(G) == {"A_(x)", "B", "C"}
    assert list(nx.isolates(G)) == ["C"]
    assert G.nodes["A_(x)"] == {
        "name": "A (x)",
        "wikidata_id": "Q1",
        "url": "https://en.wikipedia.org/wiki/A_(x)",
        "description": 'Says "hi" and is the #1 fan',
    }
    assert G.graph["weighted"] is False


def test_check_rejects_unknown_endpoint(tmp_path, monkeypatch):
    data_dir = _fake_snapshot(tmp_path, monkeypatch, edges="# source\ttarget\nA_(x)\tZ\nB\tA_(x)\n")
    with pytest.raises(md.SnapshotError, match="not in the roster"):
        md.load_graph(data_dir=data_dir)
    G = md.load_graph(data_dir=data_dir, check=False)
    assert "Z" in G


def test_check_reports_count_mismatch(tmp_path, monkeypatch):
    data_dir = _fake_snapshot(tmp_path, monkeypatch)
    monkeypatch.setattr(md, "EXPECTED", {"nodes": 303, "edges": 1784, "isolates": 17})
    with pytest.raises(md.SnapshotError, match="expected 303 nodes"):
        md.load_graph(data_dir=data_dir)


def test_checksum_mismatch_redownloads_once(tmp_path, monkeypatch):
    good = b"good bytes\n"
    monkeypatch.setattr(md, "SNAPSHOTS", {"x.tsv": md.Snapshot("x.tsv", hashlib.sha256(good).hexdigest(), len(good))})
    calls = []

    def fake_download(url, dest):
        calls.append(url)
        dest.write_bytes(good)

    monkeypatch.setattr(md, "_download", fake_download)
    path = tmp_path / "x.tsv"
    path.write_bytes(b"garbage")

    with pytest.warns(UserWarning, match="re-downloading"):
        assert md.ensure_snapshot("x.tsv", data_dir=tmp_path) == path
    assert path.read_bytes() == good
    assert calls == [md.BASE_URL + "x.tsv"]

    md.ensure_snapshot("x.tsv", data_dir=tmp_path)
    assert len(calls) == 1, "a verified file must not be downloaded again"


def test_persistent_checksum_mismatch_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(md, "SNAPSHOTS", {"x.tsv": md.Snapshot("x.tsv", "0" * 64, 1)})
    monkeypatch.setattr(md, "_download", lambda url, dest: dest.write_bytes(b"still wrong"))
    with pytest.raises(md.SnapshotError, match="expected 0{64}"):
        md.ensure_snapshot("x.tsv", data_dir=tmp_path)


def test_unknown_snapshot_name(tmp_path):
    with pytest.raises(md.SnapshotError, match="Unknown snapshot"):
        md.ensure_snapshot("nope.tsv", data_dir=tmp_path)


@pytest.mark.network
def test_real_graph_counts(snapshot_dir):
    G = md.load_graph(data_dir=snapshot_dir)
    assert G.number_of_nodes() == md.EXPECTED["nodes"] == 303
    assert G.number_of_edges() == md.EXPECTED["edges"] == 1784
    assert nx.number_of_isolates(G) == md.EXPECTED["isolates"] == 17
    assert "Spider-Man" in G
    assert all(G.nodes[n]["name"] and G.nodes[n]["url"].startswith("https://en.wikipedia.org/wiki/") for n in G)


@pytest.mark.network
def test_real_weighted_graph(snapshot_dir):
    G = md.load_graph(data_dir=snapshot_dir)
    Gw = md.load_graph(weighted=True, data_dir=snapshot_dir)
    weights = [d["weight"] for _, _, d in Gw.edges(data=True)]
    assert Gw.number_of_edges() == 1784
    assert min(weights) == 1 and max(weights) == 11
    assert set(Gw.edges()) == set(G.edges())


@pytest.mark.network
def test_edge_only_loading_drops_isolates(snapshot_dir):
    """Documents why load_graph adds the roster first: the naive way loses 17 characters."""
    edges = md.load_edges(data_dir=snapshot_dir)
    naive = nx.from_pandas_edgelist(edges, "source", "target", create_using=nx.DiGraph)
    assert naive.number_of_nodes() == 286
