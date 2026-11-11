# SpectrumERP Knowledge Graph

A Neo4j knowledge graph of the SpectrumERP WinForms codebase, exposed to AI clients through an MCP server
(`spectrum-kg`) for **agentic RAG**: the client picks entry points and hops; the server only offers graph
primitives.

```
Module ─HAS_PROCESS→ BusinessProcess ─HAS_STEP→ Form ─MANAGES→ BusinessConcept ←APPLIES_TO─ BusinessRule
                                                 │
            Form ─HAS_METHOD→ FormMethod ─INVOKES→ DTMethod ─DELEGATES_TO→ DAMethod ─EXECUTES→ StoredProcedure
            Form ─HAS_CONTROL→ Control ─BINDS_TO→ DTProperty ─FEEDS→ SPParameter        ─WRITES/READS→ Table ─HAS_COLUMN→ Column
                               Control ─SHOWS→ ResultSet ─PROJECTS→ Column
  shortcuts (derived): Form ─CALLS_SP→ SP, Form ─USES_TABLE→ Table, Form ─SHARES_TABLE─ Form
```

* **Functional layer** (curated YAML in `domain/`): modules, business processes (Material Master Setup,
  Procure-to-Pay / PO Flow, Goods Receipt & QC, Payment Flow, Inventory, GST, Plant Maintenance), concepts, rules,
  per-form docs. Steps for screens that don't exist yet point at `status: planned` placeholder forms.
* **Technical layer** (extracted): VB.NET / C# parsed with **Roslyn** (`tools/RoslynExtractor`), T-SQL with
  **sqlglot** (hybrid splitter). Leaf nodes carry their code.
* Every node has `:Searchable`, `kind`, `summary`, `text` and a **Voyage AI** embedding (`voyage-code-3`, 1024d)
  in the `kg_embedding` vector index plus the `kg_fulltext` index.

## Setup

Prerequisites: Python 3.13, .NET SDK (8+), a Neo4j Aura instance, a Voyage AI API key.

```powershell
cd D:\SpectrumERP\KnowledgeGraph
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.example .env      # fill NEO4J_URI / NEO4J_PASSWORD / VOYAGE_API_KEY
.\.venv\Scripts\kg validate # offline: extraction + YAML reference check
.\.venv\Scripts\kg build    # embed + load into Aura (idempotent, only changed texts are re-embedded)
```

`kg export-html` writes `kg-graph.html`, an offline interactive view of the graph (no Neo4j needed).

The Roslyn extractor is built automatically on first use (`dotnet build`), results are cached in `.cache/`.

### MCP server

`run-mcp.cmd` starts the stdio server. In Claude Code it is registered as `spectrum-kg`; to register elsewhere:

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

## Adding a phase (2, 3, 4, ...) and the editable embedding-text store

Every node has a local text file holding exactly what gets embedded: `embedding_docs/<Label>/<name>.txt`
(`embedding_docs/manifest.json` records what the builder last wrote; do not edit it). Run all commands from
`KnowledgeGraph\` (shown with the venv path; skip the prefix if the venv is activated).

### Add a new phase

1. Put the phase in the same layout as the existing ones:
   `graphs-by-phase\phase-N\phase-N\<FormBundle>\...` and `graphs-by-phase\phase-N\phase-N\KnowledgeGraph\domain\...`.
   Nothing in the code or `kg.yaml` changes; `phase_globs` picks it up. Bundle names must be unique across phases.
2. Run, in order:

```powershell
.\.venv\Scripts\kg phases                              # 1. check phase-N is listed with its bundle count
.\.venv\Scripts\python scripts\merge_phase_domains.py  # 2. re-merge the curated domain layer (later phase wins on text)
.\.venv\Scripts\kg validate                            # 3. optional: build in memory, show warnings/errors
.\.venv\Scripts\kg docs sync                           # 4. write files for the new nodes, refresh untouched old ones
.\.venv\Scripts\kg build                               # 5. load into Neo4j; embeds only new or changed text
```

On the Voyage free tier use `kg build --embed-budget 0` then `kg embed-step` (see the next section) instead of step 5.

### Edit an embedding text

1. Open the file, e.g. `embedding_docs\Form\fUnitMaster.txt`, and change the text. Keep it plain text; line endings
   and trailing blanks don't matter. Don't rename or move the file.
2. Run `kg build` (or `kg embed-step`). Your version is embedded and used for fulltext search. Only edited nodes get
   new vectors.
3. An edited file is never overwritten by later syncs. Untouched files are refreshed when a new phase changes a node's
   generated text (e.g. a table used by more forms).

### Command reference

| Command | What it does |
|---|---|
| `kg phases` | Lists the discovered phases and how many form bundles each has. |
| `kg docs sync` | Builds the graph (all phases) and writes `embedding_docs\`: creates missing files (new nodes, or the first backfill of already-ingested ones), refreshes files you never edited, keeps edited ones. Prints counts: new / refreshed / unchanged / edited (drifted) / orphaned. |
| `kg docs sync --prune` | Same, and also deletes files of nodes that are no longer in the graph. Edited files are kept. |
| `kg docs status` | Dry run of the above: shows what would change and which files are hand-edited or drifted. Writes nothing. |
| `kg docs diff <node>` | Shows your file vs. the text the graph would generate now. `<node>` is an id (`form:fUnitMaster`, `sp:masterdata.mmumsave`) or a unique bare name (`fUnitMaster`). Use it on *drifted* nodes after adding a phase. |
| `kg docs reset <node> [<node> ...]` | Discards your edit: overwrites the file with the generated text. |
| `kg docs reset --all` | Same for every hand-edited file. |
| `kg build` | Syncs `embedding_docs\`, then loads the graph into Neo4j and embeds nodes whose text is new or changed. |
| `kg build --dry-run out.json` | Writes the graph to JSON; applies your edits but does not write any `embedding_docs\` file. |
| `kg embed-step` | One resumable embedding slice (also syncs the docs first). Use after editing when you build with `--embed-budget 0`. |

After `kg docs reset` run `kg build` (or `kg embed-step`) so the stored vector matches the restored text.

**Drifted** = you edited a file and the graph now generates different text than when you edited it (typically after a new
phase). Your edit still wins; compare with `kg docs diff` and merge by hand if the new context matters, or
`kg docs reset` to take the generated text.

Notes: the root `.gitignore` currently ignores `embedding_docs/`; remove that line to version your edits.
Re-run `kg docs sync` any time; it is idempotent.

## Combined Phase 0 + Phase 1 graph and the Voyage free tier

`kg.yaml` discovers every `graphs-by-phase/phase-*/phase-*` folder (`phase_globs`), so one build covers all
56 forms plus their 22 user controls (about 20K nodes, 85K relationships; fits Aura Free's 200K / 400K limits).
`domain/` is the union of both phases' curated layers, produced by `scripts/merge_phase_domains.py` (phase-1 wins on
scalar text, lists are unioned, process steps are interleaved and renumbered). Re-run it if a phase's domain changes.
Voyage's free tier allows about 3 requests and 10K tokens per minute, and the graph needs about 4M tokens of embeddings
(roughly 7 hours). So embedding is split from loading and runs in priority order (functional nodes, forms, tables first;
SPs and methods next; columns and controls last):

```powershell
.\.venv\Scripts\kg build --embed-budget 0   # load the whole graph now, no new vectors (fulltext search works at once)
.\.venv\Scripts\kg embed-step --budget 480000   # embed the next ~53 min slice and write the vectors to Neo4j
powershell -ExecutionPolicy Bypass -File scripts\schedule-embedding.ps1   # run embed-step hourly until done
```

`embed-step` is resumable (vectors are cached in `.cache/`), prints `REMAINING <n>`, and `embed-job.cmd` removes the
scheduled task when it prints `COMPLETE`. Progress is in `.cache/embed-job.log`. Nodes without a vector are still found by
fulltext search and by graph traversal; `similar` and vector search need the vector. Adding a payment method at Voyage
removes the limit (set `VOYAGE_FREE_TIER=0`), after which a plain `kg build` embeds everything in one go.

## Adding forms (Material Management, Plant Maintenance)

1. Drop the bundle next to the others (`<FormName>/Form`, `DataLayer`, `StoredProcedures`, user controls ...).
   Roles (Form / UserControl / DT / DA / DAO) are detected from code shape, not folder names.
2. `kg scaffold-doc <FormName>` → completes `domain/forms/<FormName>.yaml` with extracted fields, SPs, tables
   and validation messages; fill the TODOs (purpose, actions, concepts).
3. Add the form as a step to a process in `domain/processes/` (replace the `planned` placeholder if there is one)
   and add any new concepts / rules.
4. `kg validate` (must be clean) → `kg build`.

## Handover spec

`GRAPH_STRUCTURE.md` is a self-contained build specification for teams that only have form folders: graph model,
extraction rules, how Claude Code writes the functional layer (processes, concepts, business rules with evidence
lines), checks, loading, and - in Appendix A - the complete builder source. After changing the builder, regenerate
the appendix: `.venv\Scripts\python tools\make_spec_appendix.py`.

Voyage free tier (no payment method: 3 requests / 10K tokens per minute): the embedder detects it and paces itself;
to start at that pace set `VOYAGE_BATCH_TOKENS=9000` and `VOYAGE_MIN_INTERVAL=61`.

## Tests

```powershell
.\.venv\Scripts\python -m pytest            # offline tests against the real bundles
.\.venv\Scripts\python -m pytest -m live    # tool contracts against Aura (needs .env)
```

`eval/questions.yaml` holds agentic-RAG evaluation questions with the node ids a correct answer must reach.

## Layout

```
kg.yaml            build config (source root, exec/bind method names, SQL default schema)
domain/            curated functional docs (modules, concepts, rules, processes/, forms/)
src/spectrum_kg/   extract/ (bundle, roslyn, code, tsql) · link · domain · embed · load · queries · mcp_server · cli
tools/RoslynExtractor/  .NET syntax extractor (VB + C# → JSON facts)
```
