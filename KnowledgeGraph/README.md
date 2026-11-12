# SpectrumERP Knowledge Graph

A Neo4j knowledge graph of the SpectrumERP WinForms codebase (phases 0-13: about 400 forms, 23 user controls, 4,600
stored procedures, 3,400 tables), exposed to AI clients through an MCP server (`spectrum-kg`) for **agentic RAG**: the
client picks entry points and hops; the server only offers graph primitives.

```
Module ─HAS_PROCESS→ BusinessProcess ─HAS_STEP→ Form ─MANAGES→ BusinessConcept ←APPLIES_TO─ BusinessRule
                                                 │
            Form ─HAS_METHOD→ FormMethod ─INVOKES→ DTMethod ─DELEGATES_TO→ DAMethod ─EXECUTES→ StoredProcedure
            Form ─HAS_CONTROL→ Control ─BINDS_TO→ DTProperty <-PASSES- DAMethod          ─WRITES/READS→ Table ─HAS_COLUMN→ Column
  shortcuts (derived): Form ─CALLS_SP→ SP, Form ─USES_TABLE→ Table, Form ─SHARES_TABLE─ Form
```

* **Functional layer** (YAML in `domain/`): 10 modules, 77 business processes, concepts, rules and one doc per form.
  Phases 0-1 are hand curated; phases 2-13 were generated from the functional docs. The 3 screens with no source
  (`fMaintenanceWorkOrder`, `fOtherVoucher`, `fQCGroupMaster`) stay `status: planned` placeholders.
* **Technical layer** (extracted): VB.NET / C# parsed with **Roslyn** (`tools/RoslynExtractor`), T-SQL with
  **sqlglot**. Methods and stored procedures carry their full code in `code`.
* Every node has `:Searchable`, `kind`, `summary`, `text` and a 1024-d embedding (default: local
  `Qwen/Qwen3-Embedding-0.6B`; Voyage `voyage-code-3` optional) in the `kg_embedding` vector index, plus the
  `kg_fulltext` index. The embedded text includes the first 3,000 characters of a node's code.

## Where the graph comes from

The ERP source is not in this repo. The graph is built on the machine that has it, in **one build of all phases**
(so cross-phase links and summaries are computed once), and delivered as `graph/`:

| File | What |
|---|---|
| `graph/graph.json` | the graph (`kg build --dry-run` format, full code kept). ~275 MB, **not in git**. |
| `graph/MANIFEST.md` | builder version, inputs, validation result, counts, code-length checks, SHA-256 of graph.json |
| `graph/stats.json` | node / edge counts by type |
| `graph/build-log.txt` | full `kg validate` output (0 errors, 241 warnings, explained in the manifest) |
| `graph/forms.csv`, `graph/phase-map.csv` | every form / user control and every bundle with its phase |

`kg.yaml` has `graph_json: graph/graph.json`, so every command below loads that file instead of extracting from source.
`domain/` is the functional layer that build used; it is the input for the next build, not re-applied on load.

## Setup

Prerequisites: Python 3.11+ (3.13 recommended) and a Neo4j instance. The connection guide is the root
[`README.md`](../README.md); in short:

```powershell
cd D:\SpectrumERP\KnowledgeGraph
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env      # fill NEO4J_URI / NEO4J_PASSWORD; embedding provider
.\.venv\Scripts\kg stats    # offline: counts of graph/graph.json
.\.venv\Scripts\kg build    # embed + load into Neo4j (idempotent, only new or changed texts are embedded)
```

### MCP server

`run-mcp.cmd` starts the stdio server (`run-mcp-http.cmd` for HTTP on :8765). In Claude Code it is registered as
`spectrum-kg`; to register elsewhere:

```powershell
claude mcp add spectrum-kg -- cmd /c D:\SpectrumERP\KnowledgeGraph\run-mcp.cmd
```

| Tool | Purpose |
|---|---|
| `describe_graph` | The map: labels, relationship types (meaning, direction, derived), counts, id conventions, strategies |
| `search` | Entry points (hybrid / vector / fulltext) with `hop_hints`; filter by labels / module |
| `get_node` | One node (`summary` / `full` / `code`) + `hop_hints` |
| `expand` | One hop from a set of ids, filter by rel types / direction / labels, paginated |
| `find_paths` | Shortest paths between two nodes (avoid hubs, exclude shortcuts) |
| `similar` | Vector neighbours of a node (semantic hop) |
| `run_cypher` | Read-only Cypher escape hatch |

`hop_hints` = for each relationship type: direction, count and neighbour labels, so the client can decide the
next hop without fetching neighbours. Traversal strategies are listed by `describe_graph`.

## Commands

Run from `KnowledgeGraph\` (shown with the venv path; skip the prefix if the venv is activated).

| Command | What it does |
|---|---|
| `kg stats` | Node / edge counts (no Neo4j needed). |
| `kg validate` | Builds in memory and reports errors, warnings and dangling edges. |
| `kg build` | Syncs `embedding_docs\`, embeds nodes whose text is new or changed, loads everything into Neo4j. |
| `kg build --embed-budget 0` | Loads the whole graph without new vectors (fulltext search works at once); finish with `kg embed-step`. |
| `kg embed-step` | One resumable embedding slice; writes vectors to Neo4j as it goes; prints `REMAINING <n>` / `COMPLETE`. |
| `kg build --dry-run out.json` | Writes the graph to JSON instead of Neo4j. |
| `kg export-html` | Writes `kg-graph.html`, an offline interactive viewer (slow with 90K nodes: use its search box). |
| `kg docs sync / status / diff / reset` | The editable embedding-text store, see below. |
| `kg scaffold-doc <Form>` | Pre-fills `domain/forms/<Form>.yaml` from the graph (for a new form). |

Vectors are cached in `.cache/` (keyed by text and model), so re-running `kg build` or `kg embed-step` only embeds what
changed. Nodes without a vector are still found by fulltext search and graph traversal; `similar` and vector search
need the vector. Voyage free tier (3 requests / 10K tokens per minute): the embedder paces itself; set
`VOYAGE_BATCH_TOKENS=9000` and `VOYAGE_MIN_INTERVAL=61` to start at that pace.

## Editable embedding text

Every node has a local text file holding exactly what gets embedded: `embedding_docs/<Label>/<name>.txt`
(`embedding_docs/manifest.json` records what the builder last wrote; do not edit it). `kg docs sync` (and every
`kg build`) creates missing files, refreshes the ones you never edited and keeps the ones you did.

1. Open the file, e.g. `embedding_docs\Form\fUnitMaster.txt`, and change the text. Keep it plain text; line endings
   and trailing blanks don't matter. Don't rename or move the file.
2. Run `kg build` (or `kg embed-step`). Your version is embedded and used for fulltext search. Only edited nodes get
   new vectors.
3. An edited file is never overwritten. If a newer graph generates different text for that node it is reported as
   **drifted**: compare with `kg docs diff <node>` and merge by hand, or take the generated text with
   `kg docs reset <node>` (`--all` for every edited file), then `kg build`.

| Command | What it does |
|---|---|
| `kg docs sync [--prune]` | Write / refresh the files; `--prune` deletes unedited files of nodes no longer in the graph. |
| `kg docs status` | Dry run: what would change, which files are hand-edited or drifted. Writes nothing. |
| `kg docs diff <node>` | Your file vs. the text the graph generates now. `<node>` is an id (`form:fUnitMaster`) or a unique bare name. |
| `kg docs reset <node> ...` / `--all` | Discard edits: overwrite the file(s) with the generated text. |

The root `.gitignore` ignores `embedding_docs/`; remove that line to version your edits.

## Building from source

Only on a machine that has the ERP source (form bundles: one folder per form with `Form/`, `DataLayer/`,
`StoredProcedures/`, user controls ...) and the .NET SDK 8+. In `kg.yaml`, remove `graph_json` and list the bundle
folders under `source_roots` (bundle names must be unique across roots). Then:

1. New form: drop its bundle in a source root; `kg scaffold-doc <FormName>` writes `domain/forms/<FormName>.yaml` with
   the extracted fields, SPs, tables and validation messages; fill the TODOs (purpose, actions, concepts).
2. Add the form as a step of a process in `domain/processes/` (replace the `planned` placeholder if there is one) and
   add any new concepts / rules.
3. `kg validate` (0 errors), then `kg build --dry-run graph/graph.json` to produce a new `graph/`, or `kg build` to load
   directly. The Roslyn extractor is built on first use (`dotnet build`); its facts are cached in `.cache/`.

[`docs/reference/graph-build-spec.md`](../docs/reference/graph-build-spec.md) is the self-contained build
specification for teams that only have form folders: graph model, extraction rules, how Claude Code writes the
functional layer, checks, loading, and (Appendix A) the builder source. After changing the builder, regenerate the
appendix: `.venv\Scripts\python tools\make_spec_appendix.py`.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -m "not live"   # offline, against graph/graph.json (graph, T-SQL parser, embedding docs)
.\.venv\Scripts\python -m pytest -m live         # MCP tool contracts against Neo4j (needs .env)
```

`eval/questions.yaml` holds agentic-RAG evaluation questions with the node ids a correct answer must reach.

## Layout

```
kg.yaml                 config: graph source (graph_json or source_roots), exec/bind method names, SQL default schema
graph/                  the combined phase 0-13 graph (graph.json not in git) + manifest, stats, logs
domain/                 functional layer (modules, concepts, rules, processes/, forms/)
src/spectrum_kg/        mcp_server · queries · schema (MCP server)
                        build · extract/ (bundle, roslyn, code, tsql) · link · domain · embed · embedding_docs · load · viz · cli
tests/, eval/           tests, evaluation questions
tools/                  RoslynExtractor/ (.NET VB + C# extractor), make_spec_appendix.py
```
