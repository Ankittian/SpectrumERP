"""MCP tool contracts. Offline: server handshake + read-only guard. Live (Neo4j in .env): tool behaviour."""
import json
import subprocess
import sys

import pytest

from spectrum_kg.queries import KGClient, _lucene_escape

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
