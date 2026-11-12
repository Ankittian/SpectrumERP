# Plan: live source code access and push-driven incremental KG updates

Status: proposal. Nothing here is implemented yet.

## 1. Goals

1. Move the source code to Git so it is always current, and add an MCP `get_code` tool that reads it from there.
2. After each push, read the commit and update only the part of the KG that changed.
3. Keep the graph correct: derived edges, shared nodes and the curated domain layer must stay consistent after an incremental update.

## 2. What the KG stores today (verified from `model.py`, `build.py`, `load.py` and live queries)

| Item | Today | Problem for this plan |
|---|---|---|
| Code text | `code` property on FormMethod, DTMethod, DAMethod, StoredProcedure | Second copy of the source; goes stale after a push |
| Method location | `file`, `start_line`, `end_line` | Line numbers drift after any edit above the method; no commit recorded |
| Class and UI location | `source_files` list and `bundles` list, merged across bundles | Shared nodes (e.g. `usercontrol:QCGroup`, 14 files, 7 bundles) lose per-file provenance |
| Paths | Relative to `source_root`, e.g. `phase-0/phase-0/fMaterialGroup/...` | Not tied to a repo; layout must match Git exactly |
| Method id | `method:Owner.Name` (`model.py`) | Overloads share one id and merge (to be verified in the extractor) |
| Build metadata | `KGMeta`: `built_at`, `stats`, embedding model | No commit, repo or branch |
| Build | Always full; Roslyn facts and embeddings are cached by hash | Load rewrites every node and edge; `prune` deletes any id absent from the graph passed in, so a partial graph would wipe the rest |
| Derived edges | `USES_TABLE`, `SHARES_TABLE`, `CALLS_SP`, `PERSISTED_IN`, flagged `derived=true` | Span many bundles; cannot be rebuilt per bundle |

## 3. Proposed changes to what is stored (Phase 1)

Ordered by impact. Items A to D are required for the rest of the plan; E to H are strongly recommended.

### A. Add a `SourceFile` node

- id `file:<path-from-repo-root>`, props `path`, `repo`, `blob_sha` (Git blob hash), `commit` (last commit that touched it), `language`, `bundle`, `kind` (`vb`, `cs`, `sql`, `yaml`).
- New edge `DEFINED_IN` from Form, UserControl, DTClass, DAClass, FormMethod, DTMethod, DAMethod, StoredProcedure (and domain nodes, to their YAML file) to `SourceFile`.
- Replaces the `source_files` list and the `file` string. Keep the old props for one release for compatibility.
- Why: the unit of change in Git is a file. With this node, "which graph parts does this push affect" becomes a traversal from changed `SourceFile` nodes. Shared nodes like `QCGroup` keep one `DEFINED_IN` edge per copy instead of a merged list.

### B. Record the Git version

- `KGMeta`: add `repo`, `branch`, `commit`.
- `SourceFile.blob_sha` is the per-file version that `get_code` uses to detect staleness.

### C. Canonical repo-relative paths

- Store paths relative to the Git repo root, not to `source_root`. Add a `path_prefix` setting in `kg.yaml` so the build maps local layout to repo layout.
- Decide once and freeze the folder layout (including the `phase-N/phase-N/` prefix), because every stored pointer depends on it.

### D. Content hashes on nodes and edges

- Every node gets `content_hash` over its props (excluding embeddings). Every edge gets `content_hash` over its props.
- Used by the diff-load to write only what changed, and by the embedding step to skip unchanged text.

### E. Symbol anchors for methods

- Keep `start_line` and `end_line`, but add `owner`, `method` (already stored), `signature` and `code_hash`.
- `get_code` first tries the stored lines at the pinned commit. At a newer ref, it re-finds the method by `owner`, `signature` and file instead of trusting old line numbers.

### F. Unique method ids

- Make the id include the parameter signature or an ordinal, e.g. `method:Owner.Name(int,string)`, so overloads stop merging.
- First step: confirm with a Cypher query whether overload collisions exist in the current graph. If none, defer.

### G. Separate base and derived edges for pruning

- Keep `derived=true` on `USES_TABLE`, `SHARES_TABLE`, `CALLS_SP`, `PERSISTED_IN`.
- On every incremental load, delete all derived edges and recompute them from the full graph. They are cheap, and this avoids tracking which derived edge a changed SP affects.

### H. Decide the fate of the `code` property

- Option 1 (recommended for now): keep `code`, add `code_hash`. `search` and embeddings keep working; `get_code` is the source of truth for reading.
- Option 2 (later): drop `code`, store only `signature`, `code_hash` and a short summary. Smaller graph, no stale copy, but code-text search needs another route.

## 4. Phases

### Phase 0: Baseline and measurement

- Query the live graph: count overloaded method names, nodes with missing `file`, `SourceFile`-less nodes, shared nodes across bundles.
- Time a full build and a full load; record Roslyn and embedding cache hit rates.
- Exit: written baseline numbers; decision on item F.

### Phase 1: Schema and provenance (section 3)

- Implement A to E (and F, G if Phase 0 says so). Update `schema.py` so `describe_graph` documents `SourceFile` and `DEFINED_IN`.
- Rebuild the full graph once with the new props.
- Exit: every code node has a `DEFINED_IN` edge to a `SourceFile` with `blob_sha`; `KGMeta` has the commit; `documented_types_check` passes.

### Phase 2: Incremental load

- Change `load_graph` so it reads existing `id` + `content_hash` from Neo4j, writes only new or changed nodes and edges, and deletes only ids that disappeared.
- Make prune safe: it only runs against a full graph, never a partial one. Refuse to prune when the input graph has fewer nodes than a configured fraction of the stored graph.
- Always recompute derived edges (item G).
- Exit: a one-line change in one SP updates only that SP, the nodes derived from it, and the derived edges; a no-op rebuild writes zero nodes.

### Phase 3: `get_code` MCP tool

- Signature: `get_code(id, ref="pinned" | "latest", context_lines=5)`; also `get_code(path, start_line, end_line)`.
- Read the node's `DEFINED_IN` file, fetch it from the Git host at the pinned commit (or the branch head), slice the range, return text, `commit`, `blob_sha` and a `stale` flag.
- Server-side read-only token; allow-list of repo and path prefixes; size cap; cache keyed by `(repo, commit, path)`.
- Fall back to the embedded `code` if the Git host is unreachable, and mark the response as a fallback.
- Exit: for 50 sampled nodes, `get_code` text equals the stored `code`; for an edited file it returns the new text with `stale=true`.

### Phase 4: Push automation

- Trigger: CI job on push to the main branch (workflow file in the repo).
- Steps: checkout; restore .NET and `.cache`; build Roslyn extractor; `git diff --name-status <before> <after>`; run the build; diff-load; stamp commit on `KGMeta` and changed `SourceFile` nodes.
- Concurrency: one run at a time, queued by commit. Fail the job, and keep the old graph, if extraction reports errors.
- Secrets: Neo4j and Voyage keys in CI secrets.
- Exit: a test push appears in the graph within the agreed time; a failed build leaves the previous graph untouched.

### Phase 5: Hardening

- Nightly full rebuild with prune, plus a diff report against the incremental state (drift check).
- Handle renames and deletes (old ids pruned; `domain/` references to missing ids fail validation loudly).
- Alert when `KGMeta.commit` lags the branch head.

## 5. Acceptance tests

1. No-op push: zero node and edge writes.
2. Edit one method body: that method and its `code_hash` change; its `SourceFile` blob changes; line numbers of later methods in the file update; nothing else changes.
3. Edit an SP that writes a new table: new `WRITES` edge, new `Table` and `Column` nodes, derived edges updated for every form that reaches that SP.
4. Delete a file: its nodes disappear; shared nodes (e.g. `QCGroup`) survive if another copy still exists.
5. Incremental result equals a full rebuild: nightly drift report is empty.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Partial graph loaded with prune wipes data | Prune guard in Phase 2; always build the full in-memory graph |
| Derived edges go stale | Delete and recompute them on every load |
| Line numbers drift | Symbol anchors (E); `stale` flag in `get_code` |
| Folder layout changes break pointers | Freeze layout; `path_prefix` in config |
| Git host rate limits or outage | Cache by commit; fallback to embedded `code` |
| Overloaded methods merge | Item F, after the Phase 0 check |
| Embedding cost on large pushes | Existing hash cache; re-embed only changed text |

## 7. Open decisions

1. Git host (GitHub, Azure DevOps or other): affects auth, API and the CI file.
2. Keep or drop the embedded `code` (item H).
3. One repo or several: if several, `repo` must be per `SourceFile` (already in item A).
4. Acceptable latency from push to updated graph.
5. Whether `domain/` YAML lives in the same repo as the code.
