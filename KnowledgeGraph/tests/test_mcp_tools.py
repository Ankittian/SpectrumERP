"""MCP tool contracts. Offline: server handshake + read-only guard. Live (Neo4j in .env): tool behaviour."""
import json
import logging
import subprocess
import sys

import pytest

from spectrum_kg.mcp_server import _safe
from spectrum_kg.queries import PROFILES, KGClient, _lucene_escape, bound_code, bound_rows, profile, shape_hints
from spectrum_kg.schema import instructions_text

from conftest import REPO

KG_DIR = REPO / "KnowledgeGraph"


def _rpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    if "id" not in msg:
        return None
    while True:
        line = proc.stdout.readline()
        assert line, proc.stderr.read()
        resp = json.loads(line)
        if resp.get("id") == msg["id"]:
            return resp


def test_stdio_server_lists_agentic_tools():
    proc = subprocess.Popen([sys.executable, "-m", "spectrum_kg.mcp_server"], cwd=KG_DIR, text=True,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    try:
        init = _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "pytest", "version": "0"}}})
        assert "agentic" in init["result"]["instructions"].lower()
        _rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        names = {t["name"] for t in tools}
        assert names == {"describe_graph", "search", "get_node", "expand", "find_paths", "similar", "run_cypher"}
        res = _rpc(proc, {"jsonrpc": "2.0", "id": 3, "method": "resources/list"})["result"]["resources"]
        assert any(r["uri"] == "kg://schema" for r in res)
    finally:
        proc.kill()


def test_run_cypher_rejects_writes_offline(settings):
    client = KGClient(settings, driver=object())  # guard runs before any DB access
    for q in ["CREATE (n:X) RETURN n", "MATCH (n) DETACH DELETE n", "MATCH (n) SET n.x = 1",
              "MERGE (a {id:'x'})", "CALL apoc.create.node(['X'], {})"]:
        assert "error" in client.run_cypher(q)


def test_lucene_escape():
    assert _lucene_escape("sp:masterdata.MMUMSave?") == "sp\\:masterdata.MMUMSave\\?"


# ------------------------------------------------------------------ offline: token-budget behaviour
def test_bound_code_pages_cover_full_text_without_gaps():
    code = "".join(f"line {i}\n" for i in range(3000))
    got, cursor, pages = "", None, 0
    while True:
        page = bound_code(code, cursor, 4000)
        assert len(page["code"]) <= 4000
        got += page["code"]
        pages += 1
        if not page["truncated"]:
            assert page["next_cursor"] is None
            break
        cursor = page["next_cursor"]
    assert got == code and pages > 1 and page["code_chars"] == len(code)


def test_bound_rows_reports_row_and_size_truncation():
    rows = [{"v": "x" * 100} for _ in range(10)]
    by_rows = bound_rows(rows[:3], limit=2, max_chars=10_000)  # look-ahead row marks row truncation
    assert by_rows["returned"] == 2 and by_rows["truncated"] and by_rows["truncated_reason"] == "row_limit"
    by_size = bound_rows(rows, limit=10, max_chars=350)
    assert by_size["returned"] >= 1 and by_size["truncated"] and by_size["truncated_reason"] == "size_limit"
    assert len(json.dumps(by_size["rows"])) <= 350 + 120
    whole = bound_rows(rows[:2], limit=10, max_chars=10_000)
    assert whole["returned"] == 2 and not whole["truncated"] and whole["truncated_reason"] is None


def test_profiles_order_by_size_and_compact_is_default():
    assert profile(None) is PROFILES["compact"]
    assert profile("nonsense") is PROFILES["compact"]
    for key in ("search_top_k", "expand_limit", "cypher_limit", "cypher_max_chars", "code_chars"):
        assert PROFILES["compact"][key] < PROFILES["standard"][key] < PROFILES["detailed"][key]


def test_compact_hints_keep_counts_and_labels_in_short_shape():
    hints = {"out": {"HAS_STEP": {"count": 4, "labels": ["Form", "Module", "BusinessConcept"]}}, "in": {}}
    compact = shape_hints(hints, PROFILES["compact"])
    assert compact == {"out": {"HAS_STEP": [4, ["Form", "Module", "BusinessConcept"][:PROFILES["compact"]["hint_labels"]]]}}
    assert shape_hints(hints, PROFILES["standard"]) is hints


def test_get_node_code_is_bounded_and_pageable(settings, monkeypatch):
    body = "x" * 15000
    client = KGClient(settings, driver=object())
    monkeypatch.setattr(client, "resolve_id", lambda i: ("sp:masterdata.mmumsave", []))
    monkeypatch.setattr(client, "_read", lambda q, **p: [{"p": {"id": "sp:masterdata.mmumsave", "kind": "StoredProcedure",
                                                               "name": "mmumsave", "code": body, "parameters": ["a"] * 500}}])
    first = client.get_node("sp:masterdata.mmumsave", detail="code")
    assert len(first["code"]) == PROFILES["compact"]["code_chars"] and first["truncated"]
    assert first["next_cursor"] == str(PROFILES["compact"]["code_chars"])
    assert "hop_hints" not in first and "parameters" not in first["node"]  # code detail returns only code + meta
    second = client.get_node("sp:masterdata.mmumsave", detail="code", cursor=first["next_cursor"])
    assert first["code"] + second["code"] == body[: len(first["code"]) + len(second["code"])]


def test_telemetry_logs_sizes_not_content(caplog):
    caplog.set_level(logging.INFO, logger="spectrum_kg.telemetry")
    secret = "CONFIDENTIAL_CODE_BODY"
    out = _safe("get_node", lambda: {"code": secret, "truncated": True, "returned": 1})
    assert out["code"] == secret  # the tool still returns the content
    text = caplog.text
    assert "tool=get_node" in text and "approx_tokens=" in text and "truncated=True" in text
    assert secret not in text


def test_instructions_are_a_short_operating_contract():
    text = instructions_text()
    assert "agentic" in text.lower()
    assert len(text) < 1000
    assert "describe_graph" in text and "kg://schema" in text


# ---------------------------------------------------------------------------------------- live
@pytest.mark.live
def test_hop_hints_match_edge_counts(live_client, graph):
    hints = live_client.hop_hints(["form:fUnitMaster"])["form:fUnitMaster"]
    expected = sum(1 for e in graph.edges.values() if e.src == "form:fUnitMaster" and e.type == "HAS_METHOD")
    assert hints["out"]["HAS_METHOD"]["count"] == expected


@pytest.mark.live
def test_expand_pagination(live_client):
    first = live_client.expand(["form:fMaterialSubGroupMaster"], rel_types=["HAS_CONTROL"], direction="out", limit=10)
    assert first["returned"] == 10 and first["next_cursor"] == "10"
    second = live_client.expand(["form:fMaterialSubGroupMaster"], rel_types=["HAS_CONTROL"], direction="out",
                                limit=10, cursor=first["next_cursor"])
    ids1 = {i["id"] for g in first["results"].values() for v in g.values() for i in v}
    ids2 = {i["id"] for g in second["results"].values() for v in g.values() for i in v}
    assert ids1 and ids2 and not ids1 & ids2


@pytest.mark.live
def test_find_paths_via_shared_table(live_client):
    res = live_client.find_paths("form:fUnitMaster", "form:fMaterialSubGroupMaster",
                                 rel_types=["USES_TABLE"], max_hops=2)
    mids = {s["id"] for p in res["paths"] for s in p["steps"] if "id" in s}
    assert "table:masterdata.msubgroupunitdetail" in mids


@pytest.mark.live
def test_run_cypher_read_and_write_rejected(live_client):
    assert live_client.run_cypher("MATCH (n:Searchable {kind:'Form'}) RETURN count(n) AS c")["rows"][0]["c"] >= 3
    assert "error" in live_client.run_cypher("CREATE (x:Bad) RETURN x")


@pytest.mark.live
def test_search_entry_points(live_client):
    res = live_client.search("unit of measure conversion factor", labels=["Form", "BusinessConcept"], top_k=5)
    ids = [r["id"] for r in res["results"]]
    assert "form:fUnitMaster" in ids or "concept:unit-conversion" in ids
    assert all(r["hop_hints"] is not None for r in res["results"])
