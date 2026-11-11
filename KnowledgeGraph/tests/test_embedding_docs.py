from spectrum_kg.embedding_docs import EmbeddingDocs, text_digest
from spectrum_kg.model import Graph


def _graph(*ids):
    g = Graph()
    for i in ids:
        g.add_node(i, "Table", name=i)
    return g


def test_new_refresh_edit_orphan(tmp_path):
    g = _graph("table:a", "table:b")
    s = EmbeddingDocs(tmp_path)
    rep, ov = s.plan(g, {"table:a": "A v1", "table:b": "B v1"}, write=True)
    assert len(rep.new) == 2 and not ov
    assert (tmp_path / "Table" / "a.txt").read_text() == "A v1\n"

    # user edits b; graph now generates new text for both (e.g. a later phase touched them)
    (tmp_path / "Table" / "b.txt").write_bytes(b"B mine\r\n")
    s = EmbeddingDocs(tmp_path)
    rep, ov = s.plan(g, {"table:a": "A v2", "table:b": "B v2"}, write=True)
    assert rep.refreshed == ["table:a"] and rep.edited == ["table:b"] and rep.drifted == ["table:b"]
    assert ov == {"table:b": "B mine\n"}
    assert (tmp_path / "Table" / "a.txt").read_text() == "A v2\n"
    assert (tmp_path / "Table" / "b.txt").read_bytes() == b"B mine\r\n"      # never overwritten

    # still edited on the next run, and an orphan is kept unless pruned
    s = EmbeddingDocs(tmp_path)
    rep, ov = s.plan(_graph("table:b"), {"table:b": "B v2"}, write=True)
    assert rep.edited == ["table:b"] and rep.orphaned == ["table:a"]
    rep, _ = EmbeddingDocs(tmp_path).plan(_graph("table:b"), {"table:b": "B v2"}, write=True, prune=True)
    assert rep.pruned == ["table:a"] and not (tmp_path / "Table" / "a.txt").exists()

    # reset takes the generated text again
    s = EmbeddingDocs(tmp_path)
    s.reset("table:b", "B v2")
    rep, ov = EmbeddingDocs(tmp_path).plan(_graph("table:b"), {"table:b": "B v2"})
    assert not ov and rep.unchanged == 1


def test_filenames_are_windows_safe_and_unique(tmp_path):
    g = _graph("table:x.cheque/dd", "table:X.Cheque/DD")
    rep, _ = EmbeddingDocs(tmp_path).plan(g, {i: "t" for i in g.nodes}, write=True)
    names = [p.name.lower() for p in (tmp_path / "Table").iterdir()]
    assert len(names) == len(set(names)) == 2 and not any("/" in n for n in names)


def test_digest_ignores_line_endings():
    assert text_digest("a\r\nb  \n\n") == text_digest("a\nb")
