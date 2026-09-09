import pandas as pd
import pytest

from marvel import wiki


def test_user_agent_identifies_the_client():
    ua = wiki.session().headers["User-Agent"]
    assert ua.startswith("SixDegreesOfMarvel/")
    assert "github.com/02805-s224568-s224564/playground" in ua
    assert "python-requests/" in ua


def test_get_links_follows_continue(monkeypatch):
    pages = [
        {"continue": {"plcontinue": "T|X", "continue": "||"}, "query": {"pages": [{"title": "T", "links": [{"title": "A"}, {"title": "B"}]}]}},
        {"query": {"pages": [{"title": "T", "links": [{"title": "C"}]}]}},
    ]
    seen = []

    def fake_api_get(params, *, s=None, timeout=None):
        seen.append(dict(params))
        return pages[len(seen) - 1]

    monkeypatch.setattr(wiki, "api_get", fake_api_get)
    assert wiki.get_links("T") == ["A", "B", "C"]
    assert "plcontinue" not in seen[0]
    assert seen[1]["plcontinue"] == "T|X"


def test_get_wikitext_missing_page(monkeypatch):
    monkeypatch.setattr(wiki, "api_get", lambda params, *, s=None, timeout=None: {"query": {"pages": [{"title": "Nope", "missing": True}]}})
    with pytest.raises(wiki.PageNotFound):
        wiki.get_wikitext("Nope")


def test_api_error_raised(monkeypatch):
    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"error": {"code": "badtitle", "info": "Bad title"}}

    class Sess:
        def get(self, url, params=None, timeout=None):
            assert params["format"] == "json" and params["formatversion"] == "2"
            return Resp()

    monkeypatch.setattr(wiki, "_session", lambda s: Sess())
    with pytest.raises(RuntimeError, match="badtitle"):
        wiki.api_get({"action": "query"})


def test_wikitext_links_strips_labels_anchors_and_files():
    text = "See [[Spider-Man]] and [[Hulk|the Hulk]], [[Hulk#Powers]], [[File:x.png|thumb]], [[spider-Man]] again."
    assert wiki.wikitext_links(text) == ["Spider-Man", "Hulk"]


def test_title_to_node_id():
    nodes = pd.DataFrame(
        {
            "node_id": ["Abomination_(character)", "Anne_Weying"],
            "name": ["Abomination (character)", "She-Venom (Patricia Robertson)"],
            "wikidata_id": ["Q1", "Q2"],
            "url": ["https://en.wikipedia.org/wiki/Abomination_(character)", "https://en.wikipedia.org/wiki/Anne_Weying"],
            "description": ["a", "b"],
        }
    )
    assert wiki.title_to_node_id("Abomination (character)", nodes) == "Abomination_(character)"
    assert wiki.title_to_node_id("Anne Weying", nodes) == "Anne_Weying"
    assert wiki.title_to_node_id("She-Venom (Patricia Robertson)", nodes) == "Anne_Weying"
    assert wiki.title_to_node_id("Nobody", nodes) is None
    assert wiki.node_id_to_title("Abomination_(character)") == "Abomination (character)"
