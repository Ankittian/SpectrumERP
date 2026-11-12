# Plan: role-based behaviour + observability for the spectrum-kg MCP server

## Context
Today every client of the spectrum-kg MCP server sees the whole graph (functional + code + SQL layers) and gets one
set of instructions. Three audiences need different behaviour:
- **functional**: business users. Must never see code-level details (code names like `fUnitMaster`, methods,
  controls, DT/DA classes, SPs, tables, columns, file names). Answers in business terms only.
- **technical**: developers. Full graph access, code-first answers (forms, methods, SPs, tables, columns, lineage).
- **product**: hybrid. Same access as today, with the plain-language answer style we just added.

We also have no visibility into who uses the server and how. The goal is: (1) the role is decided server-side from the
caller's token, so a user can't change it; (2) the functional role is enforced by the server's data access, not
only by the prompt; (3) every tool call is written to an audit log that can be summarised.

Decisions (from the user): per-user token file → role; functional sees screens by **business title only**;
technical sees **everything**, code-first answers. Observability wasn't answered, so the default is **JSON-lines
audit log + `kg usage` report** (OpenTelemetry left out; can be added later).

## Design

### 1. Who is calling — `src/spectrum_kg/access.py` (new)
- `access.yaml` (git-ignored, path from `kg.yaml: access_file`, default `KnowledgeGraph/access.yaml`):
  ```yaml
  users:
    - user: priya
      role: functional          # functional | technical | product
      token_sha256: 3f9a...     # only the hash is stored
  ```
- `load_access(settings) -> dict[sha256 -> Principal(user, role)]`; `lookup(token)` hashes and compares with
  `hmac.compare_digest`.
- Backwards compatible: if no access file but `KG_MCP_TOKEN` is set, that token maps to `Principal("shared", "product")`.
- Stdio: `Principal(getpass.getuser(), role)` where role = `--role` flag, else `KG_ROLE` env, else `product`.
- CLI (in `cli.py`): `kg user add <name> --role functional` (generates `secrets.token_urlsafe(32)`, prints it once,
  stores the hash), `kg user list`, `kg user remove <name>`.

### 2. What each role can see — `src/spectrum_kg/roles.py` (new)
- Constants: `ROLES`, `FUNCTIONAL_LABELS = {Module, BusinessProcess, BusinessConcept, BusinessRule, Form, UserControl}`,
  `FUNCTIONAL_RELS = {HAS_PROCESS, HAS_FORM, HAS_CONCEPT, HAS_STEP, LEADS_TO, INVOLVES, MANAGES, USES_CONCEPT,
  PARENT_OF, RELATED_TO, APPLIES_TO, GOVERNS, EMBEDS}` (hidden: IMPLEMENTED_BY, PERSISTED_IN, SHARES_TABLE and all
  code/data edges). Display names: Form → `Screen`, UserControl → `Screen Component`.
- **Screen ids**: functional clients never see `form:fUnitMaster`; they see `screen:unit-master` (slug of the title;
  title falls back to a humanised code name for planned forms, e.g. `fPurchaseOrder` → "Purchase Order"). A
  two-way map is built once from the graph (`MATCH (n) WHERE n.kind IN ['Form','UserControl'] RETURN n.id, n.title, n.name`)
  and cached on the view.
- **Property allowlist** for functional nodes: `id, name/title, summary, doc, synonyms, module(s), status, users,
  form_kind, rule_type, key`. Everything else (code, file, start_line, sp_prefix, name of forms, …) is dropped.
  Edge props allowlist: `order, step, status, how`.
- **`scrub_text(text, screen_map)`** for summary/doc of functional nodes (the curated YAML contains code refs):
  - drop lines starting `Source:` / `Evidence:` (e.g. `Source: Functional_Doc_fAccountGroupMaster.md BR-10.`);
  - remove clauses `through <schema>.<Proc>` (form `actions`, e.g. `Saves the record through masterdata.MMUMSave.`);
  - replace form code names (`fUnitMaster`, also inside process step text `(fUnitMaster)`) with the screen title;
  - redact remaining `schema.Object` identifiers, file names (`*.md|vb|cs|sql|resx|yaml`), graph ids
    (`sp:`, `table:`, `method:`, …) and control-prefixed names (`txt|cmb|cbo|btn|chk|grd|dgv|lbl`+Capital).
- **`RoleView(client: KGClient, role)`**, same 7 methods as `KGClient` (`queries.py`). `technical`/`product` pass
  straight through. `functional`:
  - `describe_graph`: only functional labels/relationships, only the "functional top-down" + "semantic jump"
    strategies, functional tips, no code id conventions.
  - `search`: `labels` forced to ∩ FUNCTIONAL_LABELS (default = all of them, so `KGClient.search`'s ×6 pool applies);
    output projected; `hop_hints` filtered to functional rels/labels.
  - `get_node`: translate `screen:` ids; a hidden node returns the same `"no node"` error as a missing one;
    `detail` is ignored (always allowlisted props, never code).
  - `expand`: `rel_types`/`target_labels` forced to the functional sets (pushed into the existing Cypher, so
    pagination still works); results projected.
  - `find_paths`: `rel_types = FUNCTIONAL_RELS`, `exclude_derived=True`; projected.
  - `similar`: source must be functional; `labels` forced.
  - `run_cypher`: not available (the tool is not registered for this role).
  - Each method returns an internal `_audit` dict (`denied`, `filtered`, `scrubbed` counts) that the audit layer
    pops before the result goes to the client.

### 3. Per-role instructions — `src/spectrum_kg/schema.py`
- `instructions_text(role)`; keep `instructions_text()` = product (current text) for compatibility.
- **functional**: intro without layers/strategies about code; rules: plain business language (current rules 1–3),
  brief, clarify, label objects with business types (Module, Business Process, Screen, Business Concept, Business
  Rule); never discuss code, files, database objects even if asked — say this assistant covers business behaviour
  and the technical team can help with implementation.
- **technical**: full layers/strategies/tips; rules: precise technical terms, exact ids, show chains/lineage
  concisely, brief, clarify, label types.
- **product**: current text unchanged.

### 4. Server wiring — `src/spectrum_kg/mcp_server.py`
- Replace the module-level `mcp` with `build_server(role) -> MCPServer`: tools are registered as closures over a
  `RoleView`; `run_cypher` only when `role != "functional"`; `kg://schema` resource returns the role's describe_graph.
  One shared lazy `KGClient` (one Neo4j driver) across roles. Keep a module-level `mcp = build_server("product")`
  if anything imports it.
- Each tool takes the SDK-injected `ctx: Context` to read the caller identity (`ctx.headers`).
- **stdio**: `--role` flag (+ `KG_ROLE`) → `build_server(role).run("stdio")`.
- **http**: build the three role apps with `streamable_http_app(stateless_http=True, host=...)`. A parent ASGI app:
  1. reads the bearer token, `access.lookup()` → 401 if unknown (audit-logged with client IP, never the token);
  2. strips any client-sent `x-kg-user`/`x-kg-role` headers and injects the resolved ones (prevents spoofing);
  3. dispatches to that role's app.
  Its lifespan enters all three `session_manager.run()` contexts via `AsyncExitStack` (verify against the installed
  `mcp` 2.3.0 SDK that the session manager exists after `streamable_http_app()` is called).
  Replaces `_bearer_guard`; single URL `http://host:8765/mcp` stays the same.

### 5. Observability — `src/spectrum_kg/observe.py` (new)
- `audited(tool_name)` decorator around every tool: records `ts, user, role, transport, request_id, tool, args`
  (strings truncated to 500 chars, cypher to 2000), `duration_ms`, `result_count` (len of results/rows/paths),
  `error`, and the view's `_audit` counts (`denied/filtered/scrubbed`).
- Writer: stdlib `logging` + `TimedRotatingFileHandler` (daily, 30 days) to `logs/mcp-audit.jsonl`
  (`kg.yaml: audit_log_dir`, `KG_AUDIT_LOG=off` disables). Never writes to stdout (stdio protocol channel).
  In HTTP mode also a one-line stderr summary per call.
- `kg usage [--since 7d] [--by user|role|tool]` in `cli.py`: calls, error rate, p50/p95 latency, denied/filtered
  counts, top search queries, recent 401s.

### 6. Config, scripts, docs
- `config.py`: `access_file`, `audit_log_dir` properties (pattern of existing `docs_dir`/`cache_dir`).
- `.gitignore`: `access.yaml`, `logs/`. `.env.example`: `KG_ROLE`, `KG_AUDIT_LOG`.
- `run-mcp.cmd`: pass `%*` so `--role` works; README: "Roles & access" (adding users, registering in Claude Code per
  role, e.g. `claude mcp add spectrum-kg-functional -- run-mcp.cmd --role functional`) and "Audit log" sections.

## Files
- New: `src/spectrum_kg/access.py`, `roles.py`, `observe.py`; `tests/test_roles.py`, `tests/test_access_audit.py`
- Modified: `src/spectrum_kg/mcp_server.py`, `schema.py`, `cli.py`, `config.py`; `tests/test_mcp_tools.py`;
  `README.md`, `.gitignore`, `.env.example`, `run-mcp.cmd`
- Reused: `KGClient` methods and `resolve_id`/`hop_hints` (`queries.py`), `HIDDEN_PROPS`/`_short`, `load_settings`,
  `LABELS`/`RELATIONSHIPS`/`STRATEGIES`/`TIPS` (`schema.py`), `build_graph` fixture (`tests/conftest.py`).

## Verification
Run with `.venv/Scripts/python.exe -m pytest` from `KnowledgeGraph/`.
1. **Leak test (offline, strongest check)**: using the `graph` fixture, project every functional node through the
   functional view's projection + `scrub_text` and assert that no technical identifier from the graph appears
   (SP names, schema-qualified and bare table names, form code names, method names, file names; case-insensitive,
   word-bounded, length ≥ 5).
2. `scrub_text` unit tests on real lines from `domain/forms/fUnitMaster.yaml` (actions) and `domain/rules.yaml`
   (`Source:` lines); screen-id round trip.
3. `RoleView` with a fake `KGClient`: functional search drops SP/Table hits, `get_node("sp:…")` → "no node",
   `expand` forces rel types, `describe_graph` has no StoredProcedure; product/technical pass through.
4. Stdio handshake (`test_mcp_tools.py`): default role still lists the 7 tools; `--role functional` lists 6 (no
   `run_cypher`) and its instructions talk about business terms.
5. Access/HTTP: unknown token → 401; functional token with a spoofed `x-kg-role: product` header still gets
   functional tools; audit line written with user/role, no token in the file.
6. Live (`-m live`, Neo4j in `.env`): functional `search("unit of measure")` returns only functional labels and
   `screen:` ids; product search unchanged.
7. Manual: `kg user add tester --role functional`, start `run-mcp-http.cmd`, connect Claude Code with that token,
   ask "which table stores units?" → answer stays in business terms; then `kg usage` shows the calls.
