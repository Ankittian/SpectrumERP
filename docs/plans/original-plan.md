# Plan

1. Need to build a knowledge graph of this codebase that contains multiple winforms with its Data layer, FormUI, SPs, Tables, Columns, QCparatmers(optional)
2. The knowledge base need to cater fucntional as well as technical team.
3. The different form nodes need to be connected through a bussines rule node i.e PO Flow, Payment Flow etc.
4. for leaf nodes the actual codebases/code are the nodes whereas for higher level Bussiness rules and Form nodes. A compact documentation of that can be used to similarity search on that node and traverse to other connected nodes thorugh will be required.
5. For creating the Knowledge Graph you can use Neo4J Graph Rag with vector support.
6. The forms will be connected by common lower level tables , SPs as well as higher level bussiness concepts nodes that you need to form on the basis of ERP Domain knowledge by getting what the form is used for.
7. The knowledge base needs to exposed as an mcp server for ai clients to use and query the graph and ask questions based on it. need tools for it
8. Currently there are only 3 forms which will be extended to Material Management and Plant Mantainance Module.



---

# Plan: SpectrumERP Knowledge Graph (Neo4j GraphRAG + MCP server)

## Context
`D:\SpectrumERP` has 3 legacy WinForms bundles from the Material Management module: `fMaterialGroup`, `fMaterialSubGroupMaster` and `fUnitMaster`. Each bundle has VB forms, C# DA/DAO/DT classes, T-SQL SPs and, in two of them, a shared QC Group user control. More MM forms and Plant Maintenance forms will be added later.

The goal is a knowledge graph that serves both functional and technical teams:
- **Leaf nodes** hold the actual code: form methods, DA methods, SPs, tables and columns.
- **Higher-level nodes** hold compact, embedded docs: Business Process (PO Flow, Payment Flow, …), Business Concept, Business Rule, Form and Module.
- **Forms are connected** through shared tables and SPs, and through those business nodes.
- **AI clients query it** through an MCP server, as **agentic RAG**. The client LLM picks its own entry points and route through the graph, using generic graph tools that describe themselves. The server has no fixed retrieval pipeline.

`~/.claude.json` already registers an MCP server `spectrum-kg` → `D:\SpectrumERP\KnowledgeGraph\run-mcp.cmd`. That file is missing, which is why the connection fails. Building at that path makes the existing registration work.

**Decisions made:**
- Neo4j **Aura** (cloud).
- **Voyage AI** embeddings.
- Business docs are **curated YAML in the repo**. There is no LLM call at build time.

## Key facts from exploration (they drive the extractors)
- **Call chain is Form → DT → DA → DAO → SP.** Forms never call DA directly. Example: `ObjDTUnitMaster.Save()` → `DTUnitMaster.Save()` → `new DAUnitMaster().Save(this)` → `LocalVariables.objBase.ExecuteProc(DAOUnitMaster.Save, dicPara)` → `"masterdata.MMUMSave"`.
  - VB calls sometimes have no `()`.
  - DAO names are sometimes bracketed.
- **Forms:**
  - Forms implement `IMDIFunctions` (Save, LoadData, FillValues, Delete, Open, …).
  - Handlers are wired with `Handles ctl.Event`.
  - `Me.Tag` holds the SP prefix (MMIG, MSGM, MMUM).
  - `objBase.ControlValueFromProcedure(ctrl, dr("Col"))` maps a control to a DB column.
  - `FillControls/PopulateValueList/GrdSetDataSource(ds.Tables(n), ctrl)` maps a result set to a control.
- **Designer:**
  - Controls are declared as `Friend WithEvents name As Type` (Infragistics types).
  - Labels pair with fields by name stem first, then by position.
  - Mandatory fields come from `CompulsaryField(New Control(){...})`.
  - Grids have no designer columns. Their column keys appear only in code.
- **SPs:** 31 unique SPs. `QCFillValues*` are byte-identical in two folders, so dedupe them by hash.
  - CATCH blocks write `masterdata.mErrorLog`. Flag those writes and don't count them as business writes.
  - There are 2 dynamic `Exec(@Procedure)` calls (via `GlobalData.FormSearchDataDetail`).
  - Naming is messy: brackets, mixed case, `masterdata .x`, odd `DELETE … FROM … FROM`.
- **Cross-form connectors:**
  - `mSubGroupUnitDetail` is written by both Unit and SubGroup.
  - `mItemMaster.FullCode` is updated by both Group and SubGroup.
  - `mGroupMaster`, `mSubGroupMaster` and `mUnitMaster` are read across forms.
  - The QC tables are reached through the shared control.
- **Domain facts:**
  - The hierarchy is Category → Group → SubGroup → Item, and FullCode is the concatenation of their codes.
  - `DocumentStatusNo=30` means authorized.
  - Every master gets a per-company detail row (`*CompanyDetail`).
  - QC deduction rules apply at goods receipt.
  - Unit conversions are stored in both directions.
  - SubGroups carry approved vendors and makes, receipt and shipment tolerances, warehouse/bin, and GST/HSN.

## Project layout (new: `D:\SpectrumERP\KnowledgeGraph\`)
```
KnowledgeGraph/
  pyproject.toml        # python 3.13 (own .venv); deps: neo4j, neo4j-graphrag[voyageai], voyageai,
                        # sqlglot, pyyaml, pydantic, python-dotenv, mcp, typer; dev: pytest
  .env.example          # NEO4J_URI/USERNAME/PASSWORD/DATABASE, VOYAGE_API_KEY, VOYAGE_MODEL=voyage-code-3
  run-mcp.cmd           # activates .venv, runs `python -m spectrum_kg.mcp_server` (stdio)
  kg.yaml               # source roots (auto-discover */CONTENTS.md bundles), bundle→module map
  domain/               # curated docs (functional layer), reviewed in PRs
    modules.yaml        # Material Management, Plant Maintenance
    concepts.yaml       # Material Category/Group/SubGroup/Item, UOM, Unit Conversion, QC Group/Parameter,
                        # Vendor, Make, Warehouse/Division, Bin, GST Category/HSN, Company; synonyms; tables
    processes/*.yaml    # Material Master Setup, Procure-to-Pay (PO Flow), Goods Receipt & QC Inspection,
                        # Inventory Storage, GST Tax Determination, Payment Flow; ordered steps → forms
                        # (future forms listed as status: planned so new forms slot in)
    rules.yaml          # e.g. FullCode composition, SubGroup inherits Group QC, bidirectional conversion,
                        # authorization status 30, per-company activation; linked to forms/SPs/tables
    forms/<form>.yaml   # purpose, users, functional summary, fields, validations, concepts, process steps
  src/spectrum_kg/
    model.py            # Node/Edge pydantic models, stable ids (form:fUnitMaster, sp:masterdata.mmumsave, …)
    extract/bundle.py   # discover bundles, map file roles
    extract/vb_form.py  # methods, Handles, DT calls, control→DT prop, ds.Tables(n)→control, MDI calls
    extract/vb_designer.py  # controls, labels, MaxLength, tabs, mandatory fields, embedded user controls
    extract/csharp_datalayer.py  # DAO consts, DA methods (params→SP), DT props & methods; also QCGroup.cs
    extract/tsql.py     # hybrid: regex header/params + comment/TRY-CATCH strip + statement split +
                        # sqlglot(tsql) per DML stmt → tables/columns R/W, result-set index markers
    link.py             # resolve chains, dedupe SPs by hash, name normalisation, derived edges
    domain.py           # load + validate YAML refs against extracted ids
    embed.py            # text builders per label, Voyage batching, content-hash cache (skip unchanged)
    load.py             # constraints, vector + fulltext indexes, UNWIND MERGE batches, prune stale nodes
    queries.py          # Cypher templates shared by MCP tools
    cli.py              # kg build [--dry-run out.json] [--no-embed] | validate | scaffold-doc <form> | stats
    mcp_server.py       # FastMCP stdio server
  tests/                # pytest against the real bundles in the repo
```

## Graph schema
**Functional layer.** These nodes are embedded and carry the `:Searchable` label.
- `Module` -[:HAS_PROCESS]-> `BusinessProcess` -[:HAS_STEP {order, status}]-> `Form`
- `BusinessProcess` -[:INVOLVES]-> `BusinessConcept`
- `Form` -[:MANAGES]-> `BusinessConcept`
- `BusinessConcept` -[:PARENT_OF | RELATED_TO]-> `BusinessConcept`
- `BusinessConcept` -[:PERSISTED_IN]-> `Table`
- `BusinessRule` -[:APPLIES_TO]-> `Form | BusinessConcept`
- `BusinessRule` -[:IMPLEMENTED_BY]-> `StoredProcedure | FormMethod | Column`

**Technical layer.** These are the leaf nodes. Each embeds its code, or a generated description for tables and columns.
- `Form`:
  - -[:HAS_CONTROL]-> `Control {type, label, maxLength, mandatory, tab}`
  - -[:HAS_METHOD]-> `FormMethod {kind: interface|handler|helper, code}`
  - -[:EMBEDS]-> `UserControl` (QCGroup, a single node shared by both forms)
- `FormMethod`:
  - -[:HANDLES {event}]-> `Control`
  - -[:CALLS]-> `FormMethod`
  - -[:INVOKES]-> `DTMethod`
- `Control`:
  - -[:BINDS_TO]-> `DTProperty`
  - -[:SHOWS {result_set}]-> `ResultSet`
  - -[:MAPS_TO]-> `Column`
- `DTMethod` -[:DELEGATES_TO]-> `DAMethod`
- `DAMethod`:
  - -[:EXECUTES]-> `StoredProcedure {code, author, created, description}`
  - -[:PASSES {param}]-> `DTProperty`
- `StoredProcedure`:
  - -[:HAS_PARAM]-> `SPParameter`
  - -[:READS | WRITES {op}]-> `Table`
  - -[:USES_COLUMN {op}]-> `Column`
  - -[:RETURNS]-> `ResultSet {index}`
  - -[:DYNAMIC_EXEC]-> `Table` (FormSearchDataDetail)
- `Table` -[:HAS_COLUMN]-> `Column`. Unresolved columns are marked `ambiguous:true`.

**Derived edges** (computed after load):
- `Form` -[:SHARES_TABLE {tables, write_conflict}]-> `Form`
- `Form` -[:USES_TABLE {ops}]-> `Table`

**Indexes:**
- A uniqueness constraint on `id` for each label.
- One vector index `kg_embedding` on `:Searchable(embedding)`: 1024 dims, cosine, built with voyage-code-3, which handles both prose and code in one space.
- One fulltext index `kg_fulltext` on `:Searchable(name, title, summary, text)`.

## MCP server: agentic RAG, where the client drives the hops
`mcp_server.py` is a FastMCP stdio server that opens read-only Neo4j sessions.

**Principle.** The server does not run a fixed retrieval pipeline and makes no LLM calls. It exposes small graph tools that the client can combine, and that describe themselves. The client LLM decides:
- where to enter the graph,
- which edges to follow,
- how deep to go,
- when it has enough to answer.

Every response is compact. It returns node ids plus **`hop_hints`**, so the client can see its next options. `hop_hints` lists each relationship type the node has, with its direction, count and target labels, from one cheap COUNT query. Example: `{WRITES: {dir: out, count: 4, to: [Table]}, EXECUTES: {dir: in, count: 1, to: [DAMethod]}}`.

| Tool | Purpose |
|---|---|
| `describe_graph()` | The map. For every label: what it means, node counts, key properties. For every relationship type: source → target, what it means, when to follow it, and whether it is a `derived` shortcut. Also lists suggested traversal patterns. The same content is exposed as the resource `kg://schema` and as a summary in the server `instructions`. |
| `search(query, mode=hybrid\|vector\|fulltext, labels?, module?, top_k=8)` | Finds entry points only, with no expansion. Returns id, label, name, score, a one-line summary and `hop_hints`. Built on `neo4j_graphrag` `HybridRetriever`/`VectorRetriever` with `VoyageAIEmbeddings`. |
| `get_node(id, detail=summary\|full\|code)` | Properties plus `hop_hints`. Code is returned only when asked for, to save tokens. |
| `expand(ids[], rel_types?, direction?, target_labels?, limit=25, cursor?)` | Moves one hop out from a whole set of nodes at once. Results are grouped by relationship type, include edge properties (op, result_set, order, columns), and are paginated. |
| `find_paths(from_id, to_id, max_hops≤6, rel_types?, k=3)` | Shortest paths between two nodes. Use it to explain how two things are related. |
| `similar(id, labels?, top_k=5)` | A semantic hop: vector neighbours of a node, such as similar SPs or rules in other forms. |
| `run_cypher(query, params)` | Read-only escape hatch for counts and ad-hoc patterns. It runs in READ access mode, with a timeout and a row cap. |

**Traversal strategies.** These are documented in `describe_graph`. They are suggestions, not enforced:
- **Functional top-down:** Module → BusinessProcess -HAS_STEP→ Form -MANAGES→ BusinessConcept ← BusinessRule.
- **Technical drill-down:** Form → FormMethod → DTMethod → DAMethod → StoredProcedure → Table/Column.
- **Impact (bottom-up):** Column/Table ← USES_COLUMN/WRITES ← SP ← EXECUTES ← DAMethod … ← Form → BusinessProcess.
- **Lateral:** Form -USES_TABLE→ Table ←USES_TABLE- Form, or Concept ↔ Concept.
- **Semantic jump:** `similar`, or `search` with a label filter, when no edge connects the nodes.

**Shortcut edges.** Derived edges let the client take long routes in a single hop. Each one is marked `derived:true` in the schema, and the client can still walk the full chain when it needs the details:
- `Form-[:USES_TABLE]->Table`
- `Form-[:SHARES_TABLE]->Form`
- `Form-[:CALLS_SP]->StoredProcedure`
- `BusinessConcept-[:PERSISTED_IN]->Table`

**Embedded text includes the node's role.** Each node's text also states what kind of node it is and where it sits in the graph, for example "Stored procedure in fUnitMaster, Save action, writes mUnitMaster". That makes vector search land on the right entry point.

## Build steps
1. Scaffold the project, `.env.example`, `run-mcp.cmd`, `kg.yaml` and the venv (`py -3.13 -m venv`).
2. Write the extractors, including tests that use the real files. The T-SQL extractor is the hardest; follow the hybrid approach above.
3. Write `link.py`, then `kg build --dry-run graph.json` to produce the graph offline without Aura.
4. Write the `domain/` YAML for the 3 forms, concepts, processes and rules, from the exploration facts and ERP knowledge. Add `kg validate` to check that every referenced id exists and every form has a doc, and `kg scaffold-doc` to pre-fill YAML for future forms.
5. Write `embed.py` and `load.py`, then the full `kg build` against Aura. Build is idempotent and uses content hashes, so it only re-embeds what changed.
6. Write the MCP server and tools, and add a short `KnowledgeGraph/README.md`. The README covers setup and how to add a new form: drop the bundle in, run `kg scaffold-doc`, complete the YAML, then `kg build`.

## Verification
- **`pytest`.** Key assertions:
  - MMUMSave writes mUnitMaster, mUnitMasterCompanyDetail, mUnitConversionDetail and mSubGroupUnitDetail. Its mErrorLog write, if any, is flagged as catch-only.
  - The `fUnitMaster.SaveMain` chain reaches `masterdata.MMUMSaveUnitConversionDetail`.
  - There is a single `QCFillValues` node, embedded by 2 forms.
  - `mSubGroupUnitDetail` makes `fUnitMaster` and `fMaterialSubGroupMaster` share a table, with `write_conflict=true`.
- **`kg build --dry-run`.** Inspect node and edge counts per label, and check that `kg validate` reports no errors.
- **`kg build` against Aura.** Run sanity Cypher in Aura's browser: forms sharing tables, and the path from `BusinessProcess` to `Column`.
- **MCP tool tests.** `tests/test_mcp_tools.py` runs against Aura. It checks that:
  - `hop_hints` counts match the real edge counts;
  - `expand` pagination is correct;
  - `find_paths` connects `form:fUnitMaster` to `form:fMaterialSubGroupMaster` through `mSubGroupUnitDetail`;
  - `run_cypher` rejects writes.
- **Agentic eval.** `eval/questions.yaml` holds about 10 questions. Each one lists the node ids the answer must reach. Restart `spectrum-kg` via `/mcp` in Claude Code and run each question. Check that the client finds its own route using only the generic tools, and review the tool-call traces for wasted hops. Example questions:
  - "What happens when I save a Unit?"
  - "Which forms break if mSubGroupUnitDetail changes?"
  - "How does QC deduction relate to Material SubGroup?"
  - "Explain the Material Master setup process."
