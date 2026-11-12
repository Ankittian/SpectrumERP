# spectrum-kg MCP: Token Usage Estimates

Estimates from reading `KnowledgeGraph/src/spectrum_kg/mcp_server.py`. Not measured.

## Fixed cost (every session)

| Item | Tokens |
|---|---|
| Server instructions (strategies, tips, response rules) | ~0.9-1.2k |
| Tool schemas (7 tools: `describe_graph`, `search`, `get_node`, `expand`, `find_paths`, `similar`, `run_cypher`) | ~1.2-1.8k |
| **Total** | **~2-3k** |

- Tool schemas may be deferred (names only) until a tool is first used.
- If the agent calls `describe_graph` first (as its docstring recommends), add ~3-6k once per session, depending on graph size.

## Per-query cost

| Call | Tokens returned |
|---|---|
| `search` (8 hits with summaries and `hop_hints`) | ~1.5-3k |
| `expand` (up to 25 neighbours, with edge properties) | ~2-5k |
| `get_node` with `summary` / `full` | ~0.5-1.5k |
| `get_node` with `detail='code'` | ~2-10k+ (largest single item) |
| `find_paths` / `similar` | ~1-3k |
| `run_cypher` (up to 200 rows) | ~1-10k (depends on the query) |

Typical question: 1 `search` + 2-3 `expand` + 1 `get_node` = **~8-15k tokens of tool output**. With a code read or a lineage chain: **~10-20k**.

Each tool call also re-reads the whole context (mostly from the prompt cache), so billed input across a multi-hop query is several times the raw output size.

## How to track

- **`/context`**: shows tokens taken by MCP tools, including the fixed cost. Run before and after a query.
- **`/cost` or status line**: session-level token and cost totals. Compare before and after a single query.
- **OpenTelemetry**: set `CLAUDE_CODE_ENABLE_TELEMETRY=1` to export per-request token usage. Best for tracking across users.
- **Server-side logging**: log the size and token estimate of each tool response in `_safe()` (`mcp_server.py:29`), the single choke point. This gives per-tool averages for the real graph. Not implemented yet.
