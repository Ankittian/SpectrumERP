# Embedding Text Templates (per node label)

Source: `KnowledgeGraph/src/spectrum_kg/embed.py` — `enrich()` builds `props["text"]`, and `_describe()` supplies the label-specific summary and context lines. Embedded with `Qwen/Qwen3-Embedding-0.6B` (default `EMBEDDING_PROVIDER=local`).

## Common structure (all labels)

```
[<Label>] <title or name>
Also known as: <synonyms>            # only if node has synonyms
<summary>                            # node's own summary, else the one from _describe()
<context line 1>
<context line 2>
...                                  # empty context lines are dropped
<doc[:4000]>                         # only if node has `doc`
Code:
<code[:3000]>                        # only if node has `code`; limit = EMBED_CODE_CHARS (default 3000)
```

- Context lines whose values are all empty (e.g. `Rules: `) are removed.
- Name lists come from `ix.names()`: sorted, de-duplicated, titles preferred over names, truncated to `limit` (default 12) with ` (+N more)`.
- Edge notation below: `out[X]` = outgoing edges of type X (shows dst), `in[X]` = incoming edges (shows src).

---

## Functional layer

### Module
Summary: none (uses the node's own `summary`).
```
Processes: {out[HAS_PROCESS]}
Forms: {out[HAS_FORM]}
```

### BusinessProcess
Summary: none (own `summary`).
```
Module: {module}
Concepts: {out[INVOLVES]}
Leads to: {out[LEADS_TO]}
Rules: {in[GOVERNS]}
```

### BusinessConcept
Summary: none (own `summary`).
```
Maintained in forms: {in[MANAGES]}
Used by forms: {in[USES_CONCEPT]}
Part of: {in[PARENT_OF]}; contains: {out[PARENT_OF]}
Stored in tables: {out[PERSISTED_IN]}
Rules: {in[APPLIES_TO]}
```

### BusinessRule
Summary: none (own `summary`/`description` via `doc`).
```
Applies to: {out[APPLIES_TO]}
Implemented by: {out[IMPLEMENTED_BY]}
```

---

## Bridge layer

### Form  /  UserControl
Summary: only if `status == planned` → `Planned form (not built yet): {title or name}.` (otherwise own `summary`).
```
Business processes: {process name (step N), ...}      # from in[HAS_STEP]
Manages: {out[MANAGES]}
Stored procedures: {out[CALLS_SP]}                     # limit 20
Tables: {out[USES_TABLE]}                              # limit 20
Embeds: {out[EMBEDS]}                                  # only if any
Embedded in: {in[EMBEDS]}                              # only if any
```

---

## Code layer

### FormMethod
Summary:
```
{Method_kind} method {method} of {owner (owner title)}[, handles {events}][, implements {implements}]. [Executes: {SPs reached via INVOKES→DELEGATES_TO→EXECUTES}.]
```
Context:
```
Calls: {out[CALLS]}
Controls used: {out[REFERENCES]}                       # limit 15
```
Plus `Code:` block (first 3000 chars).

### Control
Summary:
```
{type} '{control}' on {owner (title)}[, label '{label}'][, tab '{tab}'][, mandatory][, max length {max_length}].
```
Context:
```
Saved via: {out[BINDS_TO]}
Handled events: {in[HANDLES]}
Used in methods: {in[REFERENCES]}                      # limit 15
```

### DTClass
Summary: `Data-transfer class {name}.`
```
Methods: {out[HAS_METHOD]}                             # limit 30
```

### DAClass
Summary: `Data-access class {name}.`
```
Methods: {out[HAS_METHOD]}                             # limit 30
```

### DTMethod
Summary: `DT method {name}; called by {in[INVOKES]}.`
```
Delegates to: {out[DELEGATES_TO]}
```
Plus `Code:` block.

### DAMethod
Summary: `DA method {name} executing {out[EXECUTES]}.`
```
Parameters from: {out[PASSES]}                         # limit 30
```

### DTProperty
Summary: `Property {property} ({type}) of {class_name}.`
```
Set from controls: {in[BINDS_TO]}
Passed as SP parameters: {param of SP, ...}            # from in[PASSES] edge `param` + the DAMethod's EXECUTES target
```

---

## Data layer

### StoredProcedure
Summary: `Stored procedure {name}[: {description}][. Called from {in[CALLS_SP]}.]`
```
Writes: {out[WRITES] excluding error_handling}         # limit 20
Reads: {out[READS]}                                    # limit 25
Parameters: {parameters}
Parameters never sent by the data layer (SQL default applies): {params_not_passed}
Calls procedures: {out[CALLS_SP]}
Rules: {in[IMPLEMENTED_BY]}
Author: {author}, created {created}                    # only if author
```
Plus `Code:` block.

### Table
Summary: `Table {name}.`
```
Business concept: {in[PERSISTED_IN]}
Used by forms: {in[USES_TABLE]}
Written by: {in[WRITES] excluding error_handling}      # limit 20
Read by: {in[READS]}                                   # limit 20
Columns: {sorted column names via out[HAS_COLUMN]}
```

### Column
Summary: `Column {column} of table {table}.`
```
Used by: {in[USES_COLUMN]}                             # limit 20
Rules: {in[IMPLEMENTED_BY]}
```

---

## Notes
- Embedding is cached by `sha256(model|dims|text)`; changing any template invalidates the cached vectors for affected nodes.
- Relationships are embedded only as the plain-text name lists shown above — not as vectors.
- See also `node_types.md` for a summary table of the same content.
