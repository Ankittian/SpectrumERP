"""MCP server (stdio) exposing the SpectrumERP knowledge graph as agentic-RAG primitives.

The server never decides the retrieval route. The client picks entry points (search), reads hop_hints and
chooses which relationships to follow (expand / find_paths / similar / run_cypher).
"""
from __future__ import annotations

import json
import logging
import sys
import time
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from .config import load_settings
from .queries import KGClient
from .schema import instructions_text

mcp = MCPServer(name="spectrum-kg", instructions=instructions_text())
_client: KGClient | None = None

# Per-call telemetry on stderr (stdout carries the MCP protocol). Logs sizes and timings only, never content.
telemetry = logging.getLogger("spectrum_kg.telemetry")


def kg() -> KGClient:
    global _client
    if _client is None:
        _client = KGClient(load_settings())
    return _client


def _safe(tool: str, fn, *args, **kwargs) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        out = fn(*args, **kwargs)
    except RuntimeError as ex:  # missing configuration
        out = {"error": str(ex)}
    except Exception as ex:  # connection / query problems surface to the client instead of killing the server
        out = {"error": f"{type(ex).__name__}: {ex}"}
    _telemetry(tool, t0, out)
    return out


def _telemetry(tool: str, t0: float, out: Any) -> None:
    if not telemetry.isEnabledFor(logging.INFO):
        return
    try:
        chars = len(json.dumps(out, default=str, ensure_ascii=False))
    except Exception:
        chars = -1
    flags = out if isinstance(out, dict) else {}
    telemetry.info("tool=%s ms=%.0f chars=%d approx_tokens=%d returned=%s truncated=%s error=%s", tool,
                   (time.perf_counter() - t0) * 1000, chars, max(chars, 0) // 4, flags.get("returned"),
                   flags.get("truncated"), "error" in flags)


Labels = Annotated[list[str] | None, Field(description="Restrict to node labels, e.g. ['Form','BusinessProcess'].")]
Profile = Annotated[Literal["compact", "standard", "detailed"] | None,
                    Field(description="Response size. compact (default): small limits, short hints. standard: previous defaults. detailed: largest.")]


@mcp.tool()
def describe_graph() -> dict[str, Any]:
    """Full map: labels and relationships (meaning, direction, counts, derived shortcuts), id conventions,
    strategies, tips, response rules and profile limits. Large output: call only when you need the map."""
    return _safe("describe_graph", kg().describe_graph)


@mcp.tool()
def search(
    query: Annotated[str, Field(description="Natural-language or keyword query (business terms, form names, table/SP names, code).")],
    mode: Annotated[Literal["hybrid", "vector", "fulltext"], Field(description="hybrid (default) = vector + keyword")] = "hybrid",
    labels: Labels = None,
    module: Annotated[str | None, Field(description="Module code filter, e.g. 'MM' or 'PM'.")] = None,
    top_k: Annotated[int | None, Field(description="Entry points (1-30). Default depends on profile (compact: 5).")] = None,
    profile: Profile = None,
) -> dict[str, Any]:
    """Find entry-point nodes: id, label, name, score, summary, hop_hints (relationships from each node with
    direction, count and neighbour labels). Does not expand: use expand() next."""
    return _safe("search", kg().search, query, mode, labels, module, top_k, profile)


@mcp.tool()
def get_node(
    id: Annotated[str, Field(description="Node id (e.g. form:fUnitMaster, sp:masterdata.mmumsave) or an exact name/title.")],
    detail: Annotated[Literal["summary", "full", "code"], Field(description="summary (default); full (all props, code cut at 2500 chars); code (one bounded page of code, plus cursor)")] = "summary",
    cursor: Annotated[str | None, Field(description="next_cursor from a previous detail='code' call.")] = None,
    max_chars: Annotated[int | None, Field(description="detail='code' page size in characters (500-60000). Default depends on profile.")] = None,
    profile: Profile = None,
) -> dict[str, Any]:
    """Properties of one node plus hop_hints. Use detail='code' only when you must read the code; it returns a
    bounded page with truncated and next_cursor."""
    return _safe("get_node", kg().get_node, id, detail, profile, cursor, max_chars)


@mcp.tool()
def expand(
    ids: Annotated[list[str], Field(description="One or more node ids to expand (a frontier).")],
    rel_types: Annotated[list[str] | None, Field(description="Only these relationship types, e.g. ['WRITES','READS'].")] = None,
    direction: Annotated[Literal["out", "in", "both"], Field(description="Relationship direction relative to the given ids.")] = "both",
    target_labels: Labels = None,
    limit: Annotated[int | None, Field(description="Max neighbours returned (1-100). Default depends on profile (compact: 10).")] = None,
    cursor: Annotated[str | None, Field(description="next_cursor from a previous call to page further.")] = None,
    profile: Profile = None,
) -> dict[str, Any]:
    """One hop from a set of nodes, grouped per source id and 'REL (dir)': neighbour id, label, name, summary and
    edge properties (e.g. ops, result_set, order, tables, write_conflict). Paginated: truncated=true means more."""
    return _safe("expand", kg().expand, ids, rel_types, direction, target_labels, limit, cursor, profile)


@mcp.tool()
def find_paths(
    from_id: Annotated[str, Field(description="Start node id or name.")],
    to_id: Annotated[str, Field(description="End node id or name.")],
    max_hops: Annotated[int, Field(description="Maximum path length (1-8).")] = 6,
    rel_types: Annotated[list[str] | None, Field(description="Allowed relationship types (all if omitted).")] = None,
    k: Annotated[int, Field(description="Max number of shortest paths.")] = 3,
    exclude_derived: Annotated[bool, Field(description="Ignore shortcut edges to see the full chain.")] = False,
    avoid_ids: Annotated[list[str] | None, Field(description="Hub nodes to route around, e.g. ['table:masterdata.mcompanymaster'].")] = None,
) -> dict[str, Any]:
    """Shortest paths between two nodes (undirected search; each step shows the real direction). Use it to explain
    how two things relate. CATCH-block error-log edges are always ignored."""
    return _safe("find_paths", kg().find_paths, from_id, to_id, max_hops, rel_types, k, exclude_derived, avoid_ids)


@mcp.tool()
def similar(
    id: Annotated[str, Field(description="Node id whose embedding is the query.")],
    labels: Labels = None,
    top_k: Annotated[int | None, Field(description="Neighbours (1-20). Default depends on profile (compact: 3).")] = None,
    profile: Profile = None,
) -> dict[str, Any]:
    """Semantic hop: nodes whose embedded text is closest to this node's (e.g. similar SPs or rules in other forms)."""
    return _safe("similar", kg().similar, id, labels, top_k, profile)


@mcp.tool()
def run_cypher(
    query: Annotated[str, Field(description="Read-only Cypher. All graph nodes carry label :Searchable and property kind=<label>.")],
    params: Annotated[dict[str, Any] | None, Field(description="Query parameters.")] = None,
    limit: Annotated[int | None, Field(description="Row cap (1-1000). Default depends on profile (compact: 50).")] = None,
    profile: Profile = None,
) -> dict[str, Any]:
    """Escape hatch for aggregations and ad-hoc patterns. Read-only transaction with a timeout; write clauses are
    rejected. Results are capped by rows and total size: truncated and truncated_reason say what was cut."""
    return _safe("run_cypher", kg().run_cypher, query, params, limit, profile)


@mcp.resource("kg://schema", name="graph-schema", description="Graph labels, relationships, strategies", mime_type="application/json")
def schema_resource() -> str:
    return json.dumps(_safe("kg://schema", kg().describe_graph), indent=1)


def _bearer_guard(app, token: str):
    """ASGI wrapper: reject HTTP requests that don't carry `Authorization: Bearer <token>`."""
    import hmac

    expected = f"Bearer {token}".encode()

    async def guarded(scope, receive, send):
        if scope["type"] == "http":
            auth = dict(scope.get("headers") or []).get(b"authorization", b"")
            if not hmac.compare_digest(auth, expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json"), (b"www-authenticate", b"Bearer")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await app(scope, receive, send)

    return guarded


def main() -> None:
    import argparse
    import os

    load_settings()  # loads .env so KG_MCP_TOKEN can live there
    if os.getenv("KG_MCP_TELEMETRY", "1") != "0":  # on by default; KG_MCP_TELEMETRY=0 silences it
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        telemetry.addHandler(handler)
        telemetry.setLevel(logging.INFO)
        telemetry.propagate = False
    p = argparse.ArgumentParser(description="spectrum-kg MCP server")
    p.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    p.add_argument("--host", default="0.0.0.0", help="HTTP bind address (0.0.0.0 = all interfaces / LAN)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--token", default=os.getenv("KG_MCP_TOKEN"),
                   help="Shared bearer token clients must send (default: $KG_MCP_TOKEN). Omit to run without auth.")
    args = p.parse_args()

    if args.transport == "stdio":
        mcp.run("stdio")
        return

    import uvicorn

    # Binding to 0.0.0.0 disables the SDK's localhost-only Host-header check, so LAN hostnames/IPs are accepted.
    app = mcp.streamable_http_app(host=args.host, stateless_http=True)
    if args.token:
        app = _bearer_guard(app, args.token)
    else:
        print("WARNING: no --token / KG_MCP_TOKEN set; anyone on the network can query the graph.", flush=True)
    print(f"spectrum-kg MCP listening on http://{args.host}:{args.port}/mcp", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
