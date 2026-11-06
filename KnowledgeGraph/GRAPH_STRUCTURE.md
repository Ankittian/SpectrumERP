# SpectrumERP Knowledge Graph: Build Specification

**Audience:** a Claude Code session (or developer) that has **only the SpectrumERP form folders** and must build
the knowledge graph exactly as we build it.

This document is self-contained. Nothing else is needed besides the form folders. It contains:
1. **The complete builder source** (Appendix A). Recreate it file by file. It parses VB.NET and C# into syntax
   trees with **Roslyn** and T-SQL with **sqlglot**, builds the technical layer, applies the functional YAML, runs
   the checks and loads Neo4j.
2. **The graph model** (§3) and **the extraction rules** the builder implements (§4). These are a reference for
   reviewing the output; you do not implement them separately.
3. **Instructions for writing the functional layer** (§5): business processes, concepts, **business rules** and
   form docs. **Claude Code writes these itself** from the forms' code plus ERP domain knowledge.
4. The checks (§6), Neo4j loading (§7), optional embeddings (§8), keys to reuse (§9), a worked example (§10) and
   the step-by-step procedure with a ready prompt (§11).

**Fixed rules**
- **Technical layer:** create the Appendix A files exactly as shown and run them. Do not re-implement,
  reformat, rename or "improve" them; the ids and structure must match ours so the two graphs can be merged by
  simple union.
- **Functional layer:** written by Claude Code per §5, using only the YAML fields in §5.2.
- Do not add, rename or drop node labels, relationship types, id patterns or YAML fields.
- If something in the code does not fit the model, it shows up as a build warning. Report it; do not extend the
  model.
- Embeddings are **optional** (§8). Without them the graph is complete and searchable by Cypher and fulltext.

---

## 1. What gets created in the repository

```
<repo>/
  <form bundle folders ...>                  input (unchanged)
  KnowledgeGraph/
    pyproject.toml  kg.yaml  .env.example  .gitignore       Appendix A
    tools/RoslynExtractor/*.csproj, *.cs                     Appendix A (Roslyn AST extractor, .NET)
    src/spectrum_kg/...                                      Appendix A (Python builder)
    domain/                                                  written by Claude Code (§5)
      modules.yaml  concepts.yaml  rules.yaml
      processes/<process-key>.yaml
      forms/<FormClass>.yaml                                 one per form and per user control
    graph/graph.json                                         generated: kg build --dry-run graph/graph.json
    kg-graph.html                                            generated: kg export-html (interactive viewer)
    .venv/  .cache/  tools/bin/                              generated (git-ignored)
```

`KnowledgeGraph/` must sit at the repository root, next to the form folders: `kg.yaml` has `source_root: ..`.

**How the builder works** (`kg build` / `kg validate` / `kg build --dry-run`):
1. It finds the bundles (§2).
2. It builds the Roslyn extractor if needed (`dotnet build`) and runs it on every `.vb` / `.cs` file. The output is
   syntax facts as JSON, cached per file hash in `.cache/roslyn/`.
3. It interprets the facts into the code layer (§4.1-§4.5) and parses every `.sql` file (§4.7).
4. It resolves the cross-layer links (§4.6) and makes the display names consistent (§3.1).
5. It computes the derived edges (§4.8).
6. It applies `domain/` (§5): YAML references are checked, and unknown ids are errors.
7. It drops dangling edges, with a warning.
8. It generates `summary`, `text`, `modules` and `kind` (§4.9).
9. It runs the functional coverage checks (§6.2).
10. It writes `graph.json`, or embeds and loads into Neo4j (§7, §8).

---

## 2. Inputs: form bundles

A **bundle** is a top-level folder that contains `CONTENTS.md`, `Form/` or `StoredProcedures/`. Ignore `bin/`,
`obj/` and `.resx` files.

```
<FormName>/
  CONTENTS.md                         optional: original source paths, file list
  Form/<FormName>.vb + .Designer.vb   VB.NET form (partial class split across the two files)
  DataLayer/DT*.cs  DA*.cs  DAO*.cs   C# data layer
  StoredProcedures/<schema>.<Proc>.sql   one CREATE PROCEDURE per file
  <UserControlFolder>/...             optional embedded user control (own .cs/.Designer.cs + DT/DA/DAO)
```

**Code conventions the rules depend on:**
- **Call chain:** Form method → DT method → DA method → DAO constant → stored procedure, for example
  `ObjDT.Save()` → `new DAUnitMaster().Save(this)` → `LocalVariables.objBase.ExecuteProc(DAOUnitMaster.Save, dicPara)`
  → `"masterdata.MMUMSave"`.
- **DAO constants:** `public static readonly string Save = "masterdata.MMUMSave";` for procedures and
  `... UnitName = "@UnitName";` for parameters.
- **DA parameter dictionary:** `dicPara.Add(DAO.UnitName, ODT.UnitName)`.
- **Forms:**
  - Forms implement `IMDIFunctions` (Save, LoadData, FillValues, Delete, Open, NewRecord, Reset, Print, Preview,
    Email, Export).
  - Event handlers use `Handles ctl.Event`. User controls (C#) use `this.ctl.Event += new …(this.handler)`.
  - `Me.Tag` holds the SP prefix and `Me.Text` holds the window title.
- **Helper calls** (on `objBase` / `LocalVariables.objBase`):

| Kind | Methods |
|---|---|
| execute | `ExecuteProc`, `ExecuteQuery`, `ExecuteNonQuery`, `ExecuteDataset`, `ExecuteScalar` (first argument = SP) |
| mandatory fields | `CompulsaryField(New Control() {ctl1, ctl2})` (also accept `CompulsoryField`) |

If a bundle uses other helper names, extend these lists. Do not change the rules.

---

## 3. Graph model

### 3.1 Common to every node

| Property | Meaning |
|---|---|
| `id` | unique; patterns below. SQL-derived ids are **lowercase**. |
| `kind` | the node type (= Neo4j label) |
| `name` | display name |
| `summary` | one line (curated, or generated §4.9) |
| `text` | search text (generated §4.9) |
| `modules` | list of module codes (generated §4.9) |
| `embedding`, `embedding_hash` | optional (§8) |

Neo4j labels on every node: `:Searchable` plus `:<kind>`.

> Properties must be primitives or homogeneous lists. Omit null, empty-string and empty-list values. Store any
> dict as a JSON string.
> In JSON the node type is `kind`, because `label` is a real property of `Control` (its on-screen caption).

**Display-name normalisation (SQL objects)**
- A table or SP id is `schema.name` in lowercase.
- Its `name` is the most frequent spelling seen in the code (ties prefer mixed case).
- Each schema is then rewritten to its single most frequent spelling across all tables and SPs, e.g. `masterdata`
  rather than `Masterdata` or `MasterData`. Apply the same spelling to Column names.
- Do this **before** computing derived edges (§4.8).

### 3.2 Node labels

| kind | Layer | id pattern | Properties (besides the common ones) |
|---|---|---|---|
| Module | functional | `module:<CODE>` | code, summary, doc, status |
| BusinessProcess | functional | `process:<key>` | key, module, summary, doc, status (active / planned) |
| BusinessConcept | functional | `concept:<key>` | key, module, summary, doc, synonyms |
| BusinessRule | functional | `rule:<key>` | key, rule_type, summary, doc |
| Form | bridge | `form:<FormClass>` | title, sp_prefix, language, namespace, implements, bases, bundles, source_files; from YAML: summary, doc, module, form_kind, users, status |
| UserControl | bridge | `usercontrol:<Class>` | same as Form |
| FormMethod | code | `method:<Owner>.<Method>` | method, owner, method_kind (interface / handler / helper / constructor), events, implements, code, file, start_line, end_line, language, comments |
| Control | code | `control:<Owner>.<controlName>` | control, owner, type, label, text, max_length, visible, read_only, mandatory, tab, tab_key, parent |
| DTClass | code | `dtclass:<Class>` | namespace, language, bundles, source_files |
| DTMethod | code | `dtmethod:<Class>.<Method>` | method, class_name, code, file, start_line, end_line, language, bundles |
| DTProperty | code | `dtprop:<Class>.<Property>` | property, class_name, type, backing_field, bundles |
| DAClass | code | `daclass:<Class>` | namespace, language, bundles, source_files |
| DAMethod | code | `damethod:<Class>.<Method>` | method, class_name, code, file, start_line, end_line, language, bundles |
| StoredProcedure | data | `sp:<schema>.<proc>` | schema, procedure, code, author, created, description, parameters (list of `"@p type[ = default][ OUTPUT]"`), params_not_passed, dynamic_sql, ambiguous_columns, variants, missing_source, bundles, source_files |
| Table | data | `table:<schema>.<table>` | schema, table |
| Column | data | `column:<schema>.<table>.<column>` | table, column |

FormMethod `name` is `<Owner>.<Method>`. Control `name` is `<Owner>.<control>`. DT/DA node `name` is
`<Class>.<Member>`. SP `name` is `schema.Proc`. Column `name` is `schema.Table.Column`.

> **Stored procedures stay at procedure level.** An SP is one node holding its full code; its parameters are a
> property, not nodes, and result sets are not modelled. The SP is related to the DA methods that execute it
> (EXECUTES), to the tables and columns it reads and writes (READS, WRITES, USES_COLUMN), to other SPs (CALLS_SP),
> to the tables behind dynamic SQL (DYNAMIC_EXEC), to the forms that reach it (CALLS_SP, derived) and to business
> rules (IMPLEMENTED_BY).

### 3.3 Relationship types

| Type | From → To | Edge properties | Layer |
|---|---|---|---|
| HAS_PROCESS | Module → BusinessProcess | | functional |
| HAS_FORM | Module → Form / UserControl | | functional |
| HAS_CONCEPT | Module → BusinessConcept | | functional |
| HAS_STEP | BusinessProcess → Form | order, step, status, description | functional |
| LEADS_TO | BusinessProcess → BusinessProcess | | functional |
| INVOLVES | BusinessProcess → BusinessConcept | | functional |
| MANAGES | Form / UserControl → BusinessConcept | | functional |
| USES_CONCEPT | Form / UserControl → BusinessConcept | | functional |
| PARENT_OF | BusinessConcept → BusinessConcept | | functional |
| RELATED_TO | BusinessConcept → BusinessConcept | how | functional |
| PERSISTED_IN | BusinessConcept → Table | derived=true | functional |
| APPLIES_TO | BusinessRule → Form / UserControl / BusinessConcept | | functional |
| IMPLEMENTED_BY | BusinessRule → StoredProcedure / FormMethod / Table / Column | | functional |
| GOVERNS | BusinessRule → BusinessProcess | | functional |
| HAS_CONTROL | Form / UserControl → Control | | code |
| LABELS | Control (label) → Control (input) | | code |
| EMBEDS | Form → UserControl | control | code |
| HAS_METHOD | Form / UserControl → FormMethod; DTClass → DTMethod; DAClass → DAMethod | | code |
| HANDLES | FormMethod → Control / Form / UserControl | event | code |
| CALLS | FormMethod → FormMethod | line, via | code |
| REFERENCES | FormMethod → Control | | code |
| INVOKES | FormMethod → DTMethod | line, via | code |
| SETS | FormMethod → DTProperty | expr, grid_column, line | code |
| BINDS_TO | Control → DTProperty | expr, method, line | code |
| HAS_PROPERTY | DTClass → DTProperty | | code |
| DELEGATES_TO | DTMethod → DAMethod | line | code |
| PASSES | DAMethod → DTProperty | param (the SP parameter it is sent as), line | code |
| EXECUTES | DAMethod → StoredProcedure | via (DAO constant), line | code→data |
| READS | StoredProcedure → Table | lines | data |
| WRITES | StoredProcedure → Table | ops [insert / update / delete], lines, error_handling | data |
| USES_COLUMN | StoredProcedure → Column | ops [read / write], inferred | data |
| HAS_COLUMN | Table → Column | | data |
| CALLS_SP | Form / UserControl → StoredProcedure (derived=true, methods); StoredProcedure → StoredProcedure (`EXEC`, line) | | derived / data |
| DYNAMIC_EXEC | StoredProcedure → Table | variable, line, note | data |
| USES_TABLE | Form / UserControl → Table | derived=true, ops [read / write] | derived |
| SHARES_TABLE | Form / UserControl → Form / UserControl (treat as undirected) | derived=true, tables, count, write_conflict, conflict_tables | derived |

There is at most one edge per (source, type, target). When the same edge is produced again, merge its properties:
- **scalar properties** keep the first non-empty value;
- **list properties** take the union.

`ops`, `lines`, `methods`, `tables`, `bundles`, `source_files`, `synonyms`, `events`, `parameters` and
`params_not_passed` are lists.

---

## 4. Technical layer: extraction rules

> **Reference only.** The Appendix A builder implements every rule in this section. Use it to understand and
> review the output (`graph.json`, `kg-graph.html`) and to explain warnings. Do not implement it a second time.
> The facts come from Roslyn syntax trees: `tools/RoslynExtractor` emits, per file, the types, fields,
> properties and methods with exact code spans, `Handles` clauses, `+=` / `AddHandler` subscriptions,
> invocations, member accesses (`With`-block receivers resolved), assignments, locals and string literals.

### 4.1 Classes

- **Merging copies:**
  - Merge partial classes across files: `X.vb` + `X.Designer.vb`, and `X.cs` + `X.Designer.cs`.
  - The same class in several bundles, such as a shared user control copied into each bundle, is **one** set of
    nodes. Union its `bundles` / `source_files`, and do not duplicate its methods or fields.
- **Role detection** (by code shape, in this order):
  1. **UserControl:** the base type is `UserControl`.
  2. **Form:** the base type is `Form`, or the class has `InitializeComponent`.
  3. **DAO:** at least half of the fields (and at least one) are string literals of the form `"schema.Proc"` or
     `"@Param"`.
  4. **DA:** some method calls an *execute* helper.
  5. **DT:** some method creates an object of a DA class.
  6. Anything else is ignored (for example `LocalVariables`).

### 4.2 DAO

Build a constant map `"<DAOClass>.<Field>" → literal value`. Strip square brackets from SP names. A name without a
schema gets the default schema (`masterdata`).

### 4.3 DA

For each class, create `DAClass`. For each method, create a `DAMethod` (with its full code) and the edge
`HAS_METHOD`. Then:
- **EXECUTES:** for every *execute* helper call, take the first argument, resolve it through the DAO map (or use it
  directly if it is a string literal), and create `EXECUTES → sp:<schema.proc>` with `{via: argument text, line}`.
- **PASSES:** for every `<dict>.Add(<DAO param const>, <dtParam>.<Prop>)`, where `<dtParam>` is a method parameter
  whose type is a DT class, create `PASSES → dtprop:<DTClass>.<Prop>` with `{param: "@X", line}`.
- Remember `(damethod, sp, @param)` for the parameter check (§4.6).

### 4.4 DT

- Create `DTClass`.
- For each property, create a `DTProperty` with `type` and `backing_field`. The backing field is the identifier
  returned by the getter.
- For each method, create a `DTMethod` (with its full code).
- **DELEGATES_TO:** when a DT method calls method `M` on `new DAx(…)`, or on a local variable of DA type, and DA
  class `DAx` has a method `M`, create `DELEGATES_TO → damethod:DAx.M` with `{line}`.

### 4.5 Forms and user controls

**The node.** Create a `Form` or `UserControl` node from the merged class:
- `title`: the literal assigned to `Me.Text` / `this.Text` in `InitializeComponent`, ignored if it equals the class
  name;
- `sp_prefix`: the literal from `Me.Tag`;
- `implements`, `bases`, `language` (`vb` / `csharp`), `namespace`, `bundles`, `source_files`.

**Controls**
- Every field declared in the designer file is a control, except `components` / `IContainer`. Its `type` is the
  last segment of the field type (e.g. `UltraTextEditor`).
- **Properties** come from assignments `Me.<ctl>.<Prop> = …` inside `InitializeComponent`:

| Designer property | Graph property |
|---|---|
| `Text` (literal) | `text` |
| `Value` (literal) | caption of link labels |
| `MaxLength` | `max_length` |
| `Visible = False` | `visible=false` |
| `ReadOnly` | `read_only` |
| `Location (x, y)` | used only for label pairing |

- **parent:** taken from `Me.<P>.Controls.Add(Me.<ctl>)` / `AddRange(…)`. `Me.Controls.Add` means the form itself
  (no parent).
- **tab:** for a tab object `T`, assignments `T.TabPage = Me.<page>`, `T.Key = "…"` and `T.Text = "…"` define a tab
  page. A control's `tab` / `tab_key` come from the nearest ancestor page, found by walking up `parent`.
- **mandatory:** true for controls listed in a *mandatory* helper call anywhere in the class.
- **Label pairing:** controls whose type contains `Label` are labels. The candidate inputs are the other controls,
  excluding GroupBox, Panel, TabPageControl, TabControl, SharedControlsPage and Button.
  1. **Name stem first.** Strip the leading lowercase prefix (`ulblUnitName` → `UnitName`, `utxtUnitName` →
     `UnitName`). Equal stems (case-insensitive) pair up.
  2. **Then geometry.** An unpaired label pairs with the nearest unpaired input that has the same parent, a vertical
     distance of 8 px or less, and sits to the right of the label.
- The input control's `label` is the label's Text (or Value), with `&` removed, markup tags removed, whitespace
  collapsed and any trailing `:` dropped.
- **Edges:** `HAS_CONTROL` for every control, and `LABELS` from each label to its input. When a control's type is a
  UserControl class, also create `EMBEDS → usercontrol:<Type>` with `{control}`.

**Methods**
- Every method except `InitializeComponent` and the designer's `Dispose` becomes a `FormMethod`. It keeps the full
  code, `file`, line range and leading comments.
- `implements` lists the `Implements` clause members.
- `events` lists `"<target>.<Event>"` from the `Handles` clause, C# `+=` subscriptions and `AddHandler`.
- `method_kind`:
  - `interface` if it has an `Implements` clause;
  - otherwise `handler` if it has events;
  - otherwise `constructor` or `helper`.
- **HANDLES:** a target of `MyBase` / `Me` / `this` points to the form or user-control node itself. Any other target
  points to that control. The edge carries `{event}`.
- **Variable types** used by the rules below are the union of the class's fields, the method's parameters and the
  method's locals (`Dim x As New T`, `Dim x As T = …`). `DT vars` are those whose type is a DT class.
- **Calls and member accesses.** Treat VB member accesses without `()` as calls, e.g. `ObjDT.FillValues` and
  `ObjDT.SaveQC.CreateDataReader`.
  - **CALLS:** a call with no receiver, or with `Me` / `this` / `MyBase`, to another method of the same class
    (excluding itself and `InitializeComponent`). Also a call `<ctl>.M` where `<ctl>` is an embedded user control
    that has method `M`, which gives `CALLS → method:<UserControl>.M` with `{via: ctl}`.
  - **INVOKES:** a call or member access `<dtVar>.<M>` where `M` is a method of that DT class. The edge carries
    `{line, via: dtVar}`.
  - **REFERENCES:** every control whose name appears as a receiver, or anywhere in an assignment, in the method.
- **SETS / BINDS_TO:** for each assignment `<dtVar>.<Prop> = <expr>` where `Prop` is a DT property:
  - create `SETS → dtprop` with `{expr, line, grid_column}`. `grid_column` is the string literal inside
    `Columns("x")`, `Cells("x")`, `GetCellValue(..."x")` or `("x")`;
  - for each control identifier in `<expr>`, create `BINDS_TO` (Control → dtprop) with `{expr, method, line}`.

### 4.6 Cross-layer resolution (after SQL extraction, §4.7)

- **Missing SPs:** an SP named by `EXECUTES` that has no `.sql` file becomes a stub `StoredProcedure` with
  `missing_source=true`, plus a warning.
- **Parameter check:** for each remembered `(damethod, sp, @param)`, if the SP does not declare the parameter, record
  the warning `"<damethod> passes @p which <sp> does not declare"`.
- **params_not_passed:** for every SP that some DA method executes, list the declared parameters that no DA method
  passes. These always take their SQL default; for example, `@DocumentStatusNo = 30` means records are saved as
  authorized.

### 4.7 Stored procedures (T-SQL)

**Header**
- **Name:** the `CREATE [OR ALTER] PROC[EDURE] <name>` match; strip brackets and add the default schema if it is
  missing.
- **Header comments:** `-- Author:`, `-- Create date:` and `-- Description:` give `author`, `created` and
  `description`.
- **Parameters:** the text between the name and the first top-level `AS`. Each `@p type[(len)] [= default]
  [OUTPUT]` becomes one string in the SP's `parameters` list, e.g. `"@DocumentStatusNo tinyint = 30"`. They are not
  separate nodes.
- **code:** the full file text (BOM stripped, LF line endings).

**Statement splitting.** Tokenise the body, for example with the sqlglot tokenizer. Track parenthesis depth and
CASE depth, and split into top-level statements:
- **Boundaries:**
  - `;`
  - `BEGIN` / `END`, and `BEGIN|END TRY`, `BEGIN|END CATCH`, `BEGIN TRAN[SACTION]`, `COMMIT …`, `ROLLBACK …`.
    These wrappers are dropped.
  - `ELSE`.
  - Any statement keyword at depth 0 that starts a new statement: SELECT, INSERT, UPDATE, DELETE, DECLARE, SET,
    EXEC / EXECUTE, MERGE, TRUNCATE, IF, WHILE, RETURN, PRINT, RAISERROR, THROW.
- **Not boundaries:**
  - `END` that closes a `CASE`;
  - `SELECT` after `UNION` / `EXCEPT` / `INTERSECT` / `ALL`;
  - `SELECT` inside `INSERT … (cols) SELECT` (before any `VALUES`);
  - the first `SET` after `UPDATE`;
  - `SELECT` inside a CTE (`WITH name AS (…) SELECT`).
- Statements between `BEGIN CATCH` and `END CATCH` are flagged `in_catch`.

**Per statement.** First normalise `name .x` to `name.x`, and rewrite `DELETE FROM X FROM …` to `DELETE X FROM …`.
Then parse one statement at a time:

| Statement | Treatment |
|---|---|
| `SELECT @v = …` (assignment) | reads only |
| `DECLARE @v … = <expr>` / `SET @v = <expr>` | parse `SELECT <expr>` for reads |
| `IF` / `WHILE <cond>` containing a SELECT | parse `SELECT 1 WHERE <cond>` for reads |
| `EXEC (@v)` | dynamic SQL |
| `EXEC [@r =] proc …` | static call |

- **Write target:**
  - INSERT: its table. Write columns are the INSERT column list.
  - UPDATE / DELETE: the target. If the target is an alias (`UPDATE IM SET … FROM mItemMaster IM`,
    `DELETE sd FROM T sd`), resolve it through the FROM / JOIN aliases. UPDATE write columns are the `SET` targets.
- **Reads:** all other tables in the statement. Exclude `#temp` and `@table` variables and CTE names. A DELETE's own
  target is not a read.
- **Columns:**
  - qualified `a.col`: the table behind alias `a`;
  - unqualified, with exactly one table in the statement: that table;
  - otherwise ambiguous, with the statement's tables as candidates;
  - skip `@variables`, `*`, and ORDER BY references to output aliases.
  - `ops` is `write` for write columns and `read` for everything else.
- **Ambiguous columns:** after all SPs are parsed, build the set of (table, column) pairs that were resolved. Assign
  an ambiguous column if exactly one of its candidate tables has that column, with `inferred=true`. Otherwise list
  it on the SP as `ambiguous_columns: ["col (t1|t2)"]`.

**Edges per SP**
- **WRITES:** `WRITES → table` with `{ops: [insert|update|delete], lines, error_handling}`.
  `error_handling=true` if the statement is `in_catch` or the table is an error-log table (`masterdata.mErrorLog`).
- **READS / USES_COLUMN / HAS_COLUMN:**
  - `READS → table` with `{lines}`;
  - `USES_COLUMN → column` with `{ops}`;
  - `Table HAS_COLUMN Column` for every column observed.
- **Calls:**
  - a static `EXEC proc` gives `CALLS_SP` SP → SP `{line}`;
  - `EXEC(@v)` sets `dynamic_sql=true` and creates `DYNAMIC_EXEC → every table read by the statement that assigned @v`,
    with `{variable, line, note: "procedure name looked up at runtime from this table"}`.
- **Duplicates:** the same SP in several bundles is one node. Union its `bundles` / `source_files`. If the code
  differs between copies, set `variants = <number of distinct versions>`.

### 4.8 Derived edges (after name normalisation §3.1)

For each Form / UserControl `F`:
- **CALLS_SP:** the SP set is
  `F -HAS_METHOD-> FormMethod -INVOKES-> DTMethod -DELEGATES_TO-> DAMethod -EXECUTES-> SP`.
  Create `F CALLS_SP SP {derived: true, methods: [method names]}`. A user control's SPs belong to the user control,
  not to the forms that embed it.
- **USES_TABLE:** create `F USES_TABLE Table {derived: true, ops}` over those SPs' READS (`read`) and WRITES without
  `error_handling` (`write`).
- **SHARES_TABLE:** for each unordered pair of Form / UserControl nodes with common USES_TABLE tables, store **one**
  edge from the smaller id to the larger id, with these properties:
  - `derived: true`;
  - `tables`: sorted display names;
  - `count`;
  - `write_conflict`: true if both write at least one common table;
  - `conflict_tables`: those tables.

### 4.9 Generated properties (after the domain layer)

**`modules`**
- Start with each node's own `module` (a Module's own code).
- FormMethod and Control take the module of their owner.
- `CALLS_SP` / `USES_TABLE` targets take the source's modules.
- Then propagate, repeating the pass twice:
  - Table → HAS_COLUMN targets;
  - DAMethod ← EXECUTES (the DA method takes its SP's modules) and DTMethod ← DELEGATES_TO;
  - between DT / DA classes and their methods and properties.

**`summary`** (only if no curated summary exists)

| Node | Generated summary |
|---|---|
| FormMethod | `"<Kind> method <M> of <Owner> (<title>)[, handles <events>][, implements …]. [Executes: <SPs>.]"` |
| Control | `"<type> '<ctl>' on <Owner> (<title>)[, label '…'][, tab '…'][, mandatory][, max length n]."` |
| DTMethod | `"DT method <name>; called by <form methods>."` |
| DAMethod | `"DA method <name> executing <SPs>."` |
| DTProperty | `"Property <P> (<type>) of <Class>."` |
| StoredProcedure | `"Stored procedure <name>[: <description>]. [Called from <forms>.]"` |
| Table | `"Table <name>."` |
| Column | `"Column <c> of table <t>."` |
| DT / DA class | `"Data-transfer class X."` or `"Data-access class X."` |
| planned Form | `"Planned form (not built yet): <title>."` |

**`text`** is these lines, joined with newlines:
1. `[<kind>] <title or name>`
2. `Also known as: …` (only when there are synonyms)
3. `summary`
4. the context lines below (drop any line whose value is empty)
5. `doc` (at most 4000 characters)
6. `Code:\n<code>` (at most 6000 characters)

Context lines by node type:
- **Form / UserControl:** `Business processes: <process (step n)>`, `Manages: …`, `Stored procedures: …`,
  `Tables: …`, `Embeds: …`, `Embedded in: …`.
- **SP:** `Writes: …` (non-error), `Reads: …`, `Parameters: …`, `Parameters never sent by the data layer (SQL
  default applies): …`, `Calls procedures: …`, `Rules: …`, `Author: a, created d`.
- **Table:** `Business concept: …`, `Used by forms: …`, `Written by: …`, `Read by: …`, `Columns: …`.
- **Column:** `Used by: …`, `Rules: …`.
- **Control:** `Saved via: <dtprops>`, `Handled events: …`, `Used in methods: …`.
- **FormMethod:** `Calls: …`, `Controls used: …`.
- **BusinessProcess:** `Module: …`, `Concepts: …`, `Leads to: …`, `Rules: …`.
- **BusinessConcept:** `Maintained in forms: …`, `Used by forms: …`, `Part of: …; contains: …`,
  `Stored in tables: …`, `Rules: …`.
- **BusinessRule:** `Applies to: …`, `Implemented by: …`.
- **Module:** `Processes: …`, `Forms: …`.
- **DTProperty:** `Set from controls: …`, `Passed as SP parameters: @p of <sp>, …`.

---

## 5. Functional layer: curated YAML and how it maps to the graph

### 5.1 Authoring the functional layer (Claude Code writes it)

The whole functional layer is written by Claude Code: modules, concepts, business processes, **business rules**
and form docs. It has two sources:
- **the forms in scope**: their code, designer labels, messages and SQL;
- **ERP domain knowledge**: standard Material Management / Plant Maintenance practice for the entities and flows
  those forms belong to.

Section 9 lists keys that already exist in our graph. Reuse a key when your form fits it. Otherwise create new keys
following the same templates.

**Grounding rule: everything must trace back to the forms in scope.** ERP domain knowledge explains and connects
what the forms contain; it never adds business objects the forms do not touch. `kg validate` warns about anything
ungrounded:
- **Concept:** grounded if an in-scope form or user control MANAGES or USES it, or if one of its `tables` is used
  by an in-scope form. Do not create concepts for entities the forms never store or look up; spare parts, for
  example, only become a concept once a form handles them.
- **Process:** grounded if at least one of its steps is an in-scope form, or if it directly follows (`LEADS_TO`)
  such a process and involves a grounded concept. That second case is **one hop only**; for example, Payment Flow
  after Procure-to-Pay, because QC deductions, approved vendors and GST from the forms flow into it. Planned
  steps are allowed only inside grounded processes.
- **Rule:** grounded if it APPLIES_TO an in-scope form or user control, or a grounded concept. D2 domain rules must
  concern data the forms hold (§5.1 Step D).
- **Module:** only the modules of the forms in scope, plus modules named by the project scope (MM, PM).

**Evidence marking.** No YAML field exists for this, so the convention lives in the text. The **first line of every
`description`** of a concept, process and rule must be exactly one of:
- `Evidence: code`: everything stated is visible in the forms' code or SQL.
- `Evidence: code + ERP domain (inferred)`: the code shows the data or setting, and the business consequence comes
  from domain knowledge.
- `Evidence: ERP domain (inferred)`: standard ERP practice for this entity or flow; the forms only hold related data.

Never state as fact something the code contradicts. If the code shows that a domain rule is *not* enforced, write
that in the description, e.g. "not enforced on this screen".

Every reference is a node id (§3.2). SQL ids are matched case-insensitively. An unresolved reference is an
**error**.

#### Step A: understand each form

For every form and user control in scope, determine:
1. **The business entity** it maintains: the main table written by its Save SP. Read the SQL header description,
   the window title and the tab captions.
2. **Its kind:** a master, a transaction, a report, or a component (user control).
3. **Its actions:** the `IMDIFunctions` members with real code. Empty stubs are "not supported".
4. **The masters it looks up:** the tables read by its FillValues / LoadData SPs that belong to other entities.
   These become `uses_concepts`.
5. **Who uses it:** the roles. This comes from ERP domain knowledge, so mark it inferred in `purpose`.

#### Step B: concepts (`concepts.yaml`)

- Create one concept per business entity a form **manages**, and one per master it **uses** if that master is not
  already a concept. Do not create any other concepts (see the grounding rule above).
- Use standard ERP names with `synonyms`, e.g. "Unit of Measure" with synonyms UOM and Unit.
- `tables`: the tables that store the entity, including its `*CompanyDetail` and child-detail tables.
- `parent_of`: only for classification hierarchies, such as Category > Group > Sub Group > Item.
- `related_to`: domain relations, each with `how`. Examples: approved vendors of a sub group; the unit a parameter
  is measured in.

#### Step C: business processes (`processes/*.yaml`)

- Place every form as a step in at least one standard ERP flow of its module. Create only flows that contain an
  in-scope form, plus flows directly downstream of those that consume their data (grounding rule). Typical flows:

| Module | Typical flows |
|---|---|
| MM | Material master data setup · Procure-to-pay (indent → PO → GRN) · Goods receipt & quality inspection · Inventory storage & issue / transfer · Payment flow (bill → debit note → payment) · GST tax determination |
| PM | Equipment master setup · Preventive maintenance (schedule → work order → spares issue → completion) · Breakdown maintenance |

- **Ordering:** steps follow the real business order. Screens of the flow that are not in scope become steps with
  `status: planned`, using a placeholder form name in the same naming style (`f<Entity>`).
- **Reuse:** if a §9 process covers the flow, reuse its key. Add your step there, or replace its planned
  placeholder.
- `concepts`: the entities the flow involves.
- `leads_to`: the downstream flows. For example, master setup → procure-to-pay → goods receipt → payment.

#### Step D: business rules (`rules.yaml`), the core of the functional layer

Derive rules from **two sources** and write one rule per business statement.

**D1. Rules evidenced in code.** Scan every form for these patterns. The "Where to look" column tells you where to
find each one; `implemented_by` must point to that place.

| Pattern | Where to look | `type` |
|---|---|---|
| Mandatory fields | `CompulsaryField(...)`, `ValidateForm` messages ("Enter …", "Select valid …") | validation |
| Uniqueness | Validate SP duplicate messages ("Duplicate … is not allowed.") | validation |
| Length / format limits | `MaxLength`, SP parameter types, messages ("Code must be 2 digit.") | validation |
| Generated codes / numbering | Save SP `max(...)+1`, `REPLICATE`, prefix literals, code-generation methods | derivation |
| Recalculated / derived data | UPDATE of *other* tables in Save SPs (e.g. a full code rebuilt) | derivation |
| Defaults | SP parameter defaults, especially those in the SP's `params_not_passed` | default |
| Inheritance between masters | FillValuesDependent SPs copying a parent's details into the child | default |
| Per-company activation | Save SP inserting `*CompanyDetail` rows for every company; `Inactive` per company | integrity |
| Authorization / status | `DocumentStatusNo`, `AuthorizedBy` set on save; lookups filtering `AuthorizedBy is not null` | workflow |
| Detail replacement on save | Save SP deleting child rows before the form re-inserts them | integrity |
| Delete behaviour | Delete SP cascades, permission messages, dependency checks | integrity |
| Lookup restrictions | WHERE filters in FillValues (`Inactive = 0`, type codes such as `VendorTypeNo in (3,6)`) | control |
| Conditional UI | a field or tab shown or enabled by a flag (`Visible` toggled in a handler) | control |
| Tolerances / thresholds | percentage or limit columns and the messages that check them | control |
| Calculations | formulas in code or SQL (conversion factors, deductions) | calculation |
| Shared writes across forms | `SHARES_TABLE.write_conflict = true` | integrity |
| Atomic save | `BeginTransaction` / `CommitTransaction` around header + detail saves | integrity |

**D2. Rules from ERP domain knowledge.** For each concept and process, add the standard ERP rules that the
in-scope data **supports or drives downstream**. Examples:
- receipt tolerance limits GRN quantity against the PO;
- purchasing is restricted to approved vendors and makes;
- QC readings outside tolerance generate a quality deduction on the supplier bill;
- an inactive master cannot be used in new transactions;
- a work order consumes spares issued from stores.

Constraints for D2 rules:
- The rule must concern data that exists in the forms. `implemented_by` points to the column, table or SP that
  holds the setting. If nothing holds it, leave `implemented_by` empty.
- `processes` lists the flows where the rule applies, including planned steps.
- The description starts with `Evidence: ERP domain (inferred)` or `Evidence: code + ERP domain (inferred)`.
- Do not write generic ERP rules that no in-scope data relates to.

**Writing each rule**
- `key`: kebab-case and stable, e.g. `po-approved-vendor-only`.
- `name`: a short title.
- `summary`: one sentence stating the rule as a fact or constraint: "X must …", "X is …", "When X, Y".
- `description`: the evidence line, then conditions, thresholds, codes and their meaning, and **exact** messages in
  quotes.
- `applies_to`: the forms, user controls and concepts the rule constrains.
- `implemented_by`: the enforcement points (SP, method, table, column, param ids).
- `processes`: the flows it governs.
- **No duplicates:** when the same pattern holds in several forms (for example uniqueness, per-company activation
  or auto-authorization), write **one** rule and list every form in `applies_to` and every SP in
  `implemented_by`. Do not write one rule per form.

**Coverage required**
- every form and user control has at least one rule that `APPLIES_TO` it;
- every validation message found in code or SQL is quoted in some rule (and in the form doc);
- every `SHARES_TABLE` with `write_conflict = true` has an `integrity` rule;
- every process has at least one rule that `GOVERNS` it.

#### Step E: form docs (`forms/<Form>.yaml`)

Fill the template in §5.2:
- **`purpose` and `functional_description`:** written in business language with on-screen labels, covering
  header fields, grids, tabs and special modes such as fast entry or Excel import.
- **`actions`:** only the actions that are implemented.
- **`validations`:** the exact messages.
- **`manages` / `uses_concepts`:** from Steps A and B.
- **`method_notes`:** one-line business summaries of the key methods (Save chain, Load, Validate, important
  handlers).

### 5.2 Templates and mapping

**`domain/modules.yaml`**

```yaml
modules:
  - code: MM                      # -> Module {id: module:MM, name, code, summary, doc=description, status}
    name: Material Management
    status: active                # active | planned
    summary: ...
    description: |
      ...
```

**`domain/concepts.yaml`**

```yaml
concepts:
  - key: material-group           # -> BusinessConcept {id: concept:<key>, name, key, summary, doc=description, synonyms, module}
    name: Material Group
    module: MM                    # -> Module HAS_CONCEPT
    synonyms: [Item Group]
    summary: One sentence.
    description: |
      Evidence: code + ERP domain (inferred)
      Business definition.
    parent_of: [material-sub-group]                 # -> PARENT_OF
    related_to:                                     # -> RELATED_TO {how}; string or {concept, how}
      - {concept: qc-parameter, how: group-level default QC parameters}
    tables: [masterdata.mGroupMaster]               # -> PERSISTED_IN {derived: true}; table must exist
```

**`domain/rules.yaml`**

```yaml
rules:
  - key: unique-master-names      # -> BusinessRule {id: rule:<key>, name, key, summary, doc=description, rule_type=type}
    name: Names, codes and aliases must be unique
    type: validation              # validation | derivation | default | calculation | control | integrity | workflow
    summary: One sentence stating the rule.
    description: |
      Evidence: code
      Details, thresholds, exact messages ("Duplicate Unit Name is not allowed.").
    applies_to: [form:fUnitMaster, concept:unit-of-measure]   # -> APPLIES_TO (Form / UserControl / Concept ids)
    implemented_by: [sp:masterdata.MMUMValidate]              # -> IMPLEMENTED_BY (sp / method / table / column ids)
    processes: [material-master-setup]                        # -> GOVERNS
```

**`domain/processes/<key>.yaml`**

```yaml
key: procure-to-pay               # -> BusinessProcess {id: process:<key>, name, key, summary, module, status, doc}
name: Procure-to-Pay (PO Flow)
module: MM                        # -> Module HAS_PROCESS
status: active
summary: One sentence.
description: |
  Evidence: ERP domain (inferred)
  Business description of the flow.
steps:                            # -> HAS_STEP {order, step=name, status (default active), description}
  - order: 1
    name: Create purchase order to an approved vendor
    form: fPurchaseOrder          # Form class name. If it is not extracted, status must be `planned`.
    status: planned
    description: optional
concepts: [vendor, make]          # -> INVOLVES
leads_to: [payment-flow]          # -> LEADS_TO
```

- **Process `doc`** = `description` + `"\n\nSteps:\n"` + one line per step:
  `"<order>. <name> (<form>)[ [planned]][: <description>]"`.
- **Planned step forms:** a step whose form is not extracted and has `status: planned` creates
  `Form {id: form:<name>, name, title=<step name>, status: planned, summary=<step description>, module}` and
  `Module HAS_FORM` to it.
- **Replacing a placeholder:** when a real form implements a planned step, change `form:` to the real class name,
  delete the step's `status`, and write its form doc.
- A form appears at most once per process.

**`domain/forms/<FormClass>.yaml`**: one per extracted form or user control. It updates the extracted node.

```yaml
form: fUnitMaster                 # or `usercontrol: QCGroup`; must equal the extracted class
title: Unit Master                # -> title (overrides the extracted title)
module: MM                        # -> module; Module HAS_FORM
kind: master                      # -> form_kind: master | transaction | report | component
users: [Store administrator]      # -> users
summary: One sentence.            # -> summary
purpose: |                        # \
  Business purpose.               #  |
functional_description: |         #  |  -> doc = purpose + "\n\n" + functional_description
  Fields, grids, tabs, modes.     #  |         + "\n\nActions:\n- Save: ...\n- Open: ..."
actions:                          #  |         + "\n\nValidations:\n- ...\n- ..."
  Save: ...                       #  |         + "\n\nUsed by: <users joined with ', '>"
validations:                      #  |
  - "Duplicate Unit Name is not allowed."   # exact user-facing messages
manages: [unit-of-measure]        # -> MANAGES
uses_concepts: [unit-type]        # -> USES_CONCEPT
method_notes:                     # -> sets `summary` of method:<Form>.<Method> (the method must exist)
  SaveMain: Saves header via MMUMSave, then details, inside a transaction.
status: planned                   # only for a form doc whose form is not in the code yet
```

A form doc for a class that is not extracted, and is not marked `status: planned`, is an **error**. An extracted
Form or UserControl without a doc is a **warning**.

---

## 6. Output and checks

### 6.1 `graph/graph.json`

```json
{
  "nodes": [ { "id": "form:fUnitMaster", "kind": "Form", "name": "fUnitMaster", "title": "Unit Master", "...": "..." } ],
  "edges": [ { "src": "damethod:DAUnitMaster.Save", "type": "EXECUTES", "dst": "sp:masterdata.mmumsave",
               "via": "DAOUnitMaster.Save", "line": 48 } ]
}
```

Nodes are sorted by `id`, and edges by `(src, type, dst)`. All properties are flattened into the object.

### 6.2 Checks (the build must pass all of them)

`kg validate` runs all of these. Errors fail the build. Checks 2 and 9-10, and the §4.6 resolution
problems, are reported as warnings; a finished graph has **zero warnings**.

1. Every YAML reference resolves, so there are zero errors.
2. Every extracted Form / UserControl has a doc.
3. There are no dangling edges; drop any you find, with a warning.
4. Every StoredProcedure file is reachable from some form: it is a target of a derived `CALLS_SP`.
5. Every stored procedure named in a DAO has a `.sql` file (no `missing_source` stubs).
6. Every node and edge type is one of §3.2 / §3.3.
7. Every node has `kind`, `name` and `text`.
8. Report every warning from §4.6 in the build log.
9. The functional coverage rules of §5.1 Step D hold:
   - every form and user control has at least one rule;
   - every validation message is quoted in a rule;
   - every `write_conflict` has an integrity rule;
   - every process is governed by at least one rule.
10. Every concept, process and rule `description` starts with an `Evidence:` line (§5.1).
11. Every concept, process and rule is grounded in the forms in scope (§5.1 grounding rule).

**Sanity checks** that held for our 3 forms; expect the same kinds of results for yours:
- every Validate SP returns the duplicate messages that are quoted in the form doc;
- the Save SPs list `@DocumentStatusNo` in `params_not_passed`;
- tables written by two forms appear as `SHARES_TABLE.write_conflict=true`.

---

## 7. Loading into Neo4j (optional; Neo4j 5 / Aura)

1. Fill `KnowledgeGraph/.env`, copying it from `.env.example`: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, and
   `NEO4J_DATABASE` if not the default.
2. Run `.venv\Scripts\kg build --no-embed`.

The builder then does the following:
- It creates the constraint `kg_id` (unique `id` on `:Searchable`), the index `kg_kind`, the fulltext index
  `kg_fulltext` on `[name, title, summary, text]` and the vector index `kg_embedding`.
- It MERGEs nodes per kind and edges per type in batches, and writes the `KGMeta` node.
- It **prunes** every `:Searchable` node and edge that is not in the current build.

> **Prune warning.** Only build into a database that holds *only* the forms in this repository. Otherwise pass
> `--no-prune`, or merge both teams' bundles into one repository and build once.

The equivalent Cypher, for reference:

```cypher
CREATE CONSTRAINT kg_id IF NOT EXISTS FOR (n:Searchable) REQUIRE n.id IS UNIQUE;
CREATE INDEX kg_kind IF NOT EXISTS FOR (n:Searchable) ON (n.kind);
CREATE FULLTEXT INDEX kg_fulltext IF NOT EXISTS FOR (n:Searchable) ON EACH [n.name, n.title, n.summary, n.text];
UNWIND $rows AS row MERGE (n:Searchable {id: row.id}) SET n = row.props SET n:<Kind>;          // per kind
UNWIND $rows AS row MATCH (a:Searchable {id: row.src}) MATCH (b:Searchable {id: row.dst})
  MERGE (a)-[r:<TYPE>]->(b) SET r = row.props;                                                   // per type
```

---

## 8. Embeddings (optional, can be added later)

The graph is complete and usable without embeddings. To add semantic search:
1. Set `VOYAGE_API_KEY` in `.env`. Keep the defaults `VOYAGE_MODEL=voyage-code-3` and `EMBEDDING_DIMENSIONS=1024`.
2. Run `.venv\Scripts\kg build`, without `--no-embed`.

What happens:
- Each node's `text` (§4.9) is embedded with `input_type="document"`.
- Vectors are cached in `.cache/embeddings-<model>-<dims>.jsonl` by text hash. Re-runs embed only changed texts.
- The vector is stored in `n.embedding` and the hash in `n.embedding_hash`. The vector index is `kg_embedding`
  (1024 dimensions, cosine).

**Voyage free tier.** Without a payment method, Voyage allows only 3 requests and 10K tokens per minute. The
builder detects this and slows down automatically. To set that pace from the start:

```powershell
$env:VOYAGE_BATCH_TOKENS="9000"; $env:VOYAGE_MIN_INTERVAL="61"; .venv\Scripts\kg build
```

At that pace, about 140K tokens (our 3 forms) take about 20 minutes. Adding a payment method removes the limit,
and the free token allowance still applies.

---

## 9. Existing keys to reuse

Reuse these keys when your forms fit them **and they are grounded in your forms** (§5.1 grounding
rule), so that both graphs join on the same functional nodes. Do not copy keys your forms do not touch. Write their
YAML entries yourself following §5.1; the names and structure below are what our graph uses. New keys are
expected for entities, flows and rules that are not listed.

**Modules**
- `MM`: Material Management, active.
- `PM`: Plant Maintenance, planned. Set it to active when its first real form exists.

**Concepts** (key: name)

| Area | Concepts |
|---|---|
| Company | `company`: Company |
| Material hierarchy | `material-category`: Material Category · `material-group`: Material Group · `material-sub-group`: Material Sub Group · `material-item`: Material / Item |
| Units | `unit-of-measure`: Unit of Measure (UOM) · `unit-type`: Unit Type · `unit-conversion`: Unit Conversion Factor · `gst-uqc`: GST Unique Quantity Code |
| Quality | `qc-parameter`: QC Parameter · `qc-group`: QC Group · `qc-deduction`: Quality Deduction |
| Purchasing sources | `vendor`: Vendor / Supplier · `make`: Make / Brand |
| Storage | `warehouse`: Warehouse / Division · `bin`: Bin Card |
| Tax | `gst-category`: GST Category · `hsn-sac-code`: HSN / SAC Code |
| Controls and status | `tolerance`: Quantity Tolerance · `document-authorization`: Document Authorization Status |

Hierarchy: `material-category` PARENT_OF `material-group` PARENT_OF `material-sub-group` PARENT_OF `material-item`.

**Rules**
- `item-fullcode-composition`: Item FullCode = Category + Group + Sub Group + Item code (derivation)
- `mandatory-master-fields`: Mandatory fields and valid selections on master forms (validation)
- `unique-master-names`: Names, codes and aliases must be unique (validation)
- `unit-conversion-rows-valid`: Conversion factor and sub group rows must be complete and unique (validation)
- `unit-conversion-bidirectional`: Unit conversions are stored in both directions (derivation)
- `subgroup-inherits-group-qc`: Sub group inherits the group's QC parameters (default)
- `qc-deduction-calculation`: QC deduction beyond tolerance (calculation)
- `subgroup-unit-links-shared`: Sub group / unit links are editable from two forms (integrity)
- `fullcode-rebuilt-by-two-forms`: Item FullCode is rewritten from two forms (integrity)
- `master-per-company-activation`: Masters are created once and activated per company (integrity)
- `master-auto-authorization`: Master records are saved as authorized (status 30) (workflow)
- `master-delete-cascade`: Deleting a master removes its details and company rows (integrity)
- `approved-vendor-restriction`: Purchasing restricted to the sub group's approved vendors and makes (control)
- `receipt-tolerance`: Over / under receipt limited by sub group tolerance (control)
- `bin-management-optional`: Bin management only when IsBinApplicable (control)
- `gst-from-hsn`: GST rates derive from the sub group's HSN/SAC code (derivation)
- `spares-issued-against-work-order`: Maintenance spares are issued from MM stores against a work order (control)

When a new master follows the same pattern, extend the existing rule's `applies_to` / `implemented_by` lists rather
than creating a duplicate rule. This applies especially to `master-per-company-activation`,
`master-auto-authorization` and `unique-master-names`.

**Processes** (steps; *planned* = placeholder to replace when the real form exists)

| Process key | Name | Steps |
|---|---|---|
| `material-master-setup` | Material Master Data Setup | 1 fUnitMaster · 2 fCategoryMaster *planned* · 3 fMaterialGroup · 4 fMaterialSubGroupMaster · 5 fItemMaster *planned* |
| `procure-to-pay` | Procure-to-Pay (PO Flow) | 1 fMaterialSubGroupMaster · 2 fPurchaseIndent *planned* · 3 fPurchaseOrder *planned* · 4 fGoodsReceiptNote *planned* |
| `goods-receipt-quality-inspection` | Goods Receipt & Quality Inspection | 1 fQCParameterMaster *planned* · 2 fQCGroupMaster *planned* · 3 fMaterialGroup · 4 fMaterialSubGroupMaster · 5 fQualityInspection *planned* |
| `payment-flow` | Payment Flow (Purchase Bill to Vendor Payment) | 1 fPurchaseInvoice *planned* · 2 fDebitNote *planned* · 3 fVendorPayment *planned* |
| `inventory-storage` | Inventory Storage & Issue | 1 fMaterialSubGroupMaster · 2 fUnitMaster · 3 fMaterialIssue *planned* |
| `gst-tax-determination` | GST Tax Determination | 1 fMaterialSubGroupMaster · 2 fUnitMaster · 3 fPurchaseOrder *planned* |
| `preventive-maintenance` | Preventive & Breakdown Maintenance (PM) | 1 fEquipmentMaster *planned* · 2 fMaintenanceWorkOrder *planned* · 3 fMaterialIssue *planned* |

`leads_to` links:
- `material-master-setup` → procure-to-pay, inventory-storage, goods-receipt-quality-inspection, gst-tax-determination
- `procure-to-pay` → goods-receipt-quality-inspection, payment-flow
- `goods-receipt-quality-inspection` → payment-flow, inventory-storage
- `gst-tax-determination` → payment-flow
- `inventory-storage` → preventive-maintenance

The forms in our graph are `fMaterialGroup`, `fMaterialSubGroupMaster`, `fUnitMaster` and the user control
`QCGroup`. Steps that reference them are valid in your YAML only if those bundles are present too. Otherwise keep
those steps as they are and expect "unknown reference" errors for them only. Alternatively, mark them
`status: planned` in your copy until the graphs are merged.

---

## 10. Worked example (real output for `fUnitMaster`, abbreviated)

```json
{"id":"form:fUnitMaster","kind":"Form","name":"fUnitMaster","title":"Unit Master","sp_prefix":"MMUM","language":"vb",
 "implements":["IMDIFunctions"],"bases":["System.Windows.Forms.Form"],"bundles":["fUnitMaster"],"module":"MM",
 "form_kind":"master","status":"active","summary":"Create and maintain units of measure, ..."}
{"id":"method:fUnitMaster.SaveMain","kind":"FormMethod","method":"SaveMain","owner":"fUnitMaster","method_kind":"helper",
 "file":"fUnitMaster/Form/fUnitMaster.vb","start_line":595,"end_line":657,"code":"Private Function SaveMain() ..."}
{"id":"control:fUnitMaster.utxtUnitName","kind":"Control","control":"utxtUnitName","type":"UltraTextEditor",
 "label":"Unit Name","max_length":25,"mandatory":true,"parent":"ugbMain"}
{"id":"dtprop:DTUnitMaster.UnitName","kind":"DTProperty","property":"UnitName","type":"string","backing_field":"strUnitName"}
{"id":"sp:masterdata.mmumsave","kind":"StoredProcedure","name":"masterdata.MMUMSave","author":"Namrata","created":"20-Dec-11",
 "description":"Save Material Unit Master",
 "parameters":["@UnitNo smallint","@UnitName varchar(25)","@Alias varchar(6)","@UnitCategoryNo tinyint","@LoginNo int",
               "@DocumentStatusNo tinyint = 30","@GSTUQC tinyint"],
 "params_not_passed":["@DocumentStatusNo"],
 "ambiguous_columns":["companyno (masterdata.mUnitMasterCompanyDetail|masterdata.mCompanyMaster)"]}
{"id":"column:masterdata.munitmaster.unitname","kind":"Column","name":"masterdata.mUnitMaster.UnitName","table":"masterdata.mUnitMaster","column":"UnitName"}

{"src":"method:fUnitMaster.SaveMain","type":"INVOKES","dst":"dtmethod:DTUnitMaster.Save","line":619,"via":"ObjDTUnitMaster"}
{"src":"dtmethod:DTUnitMaster.Save","type":"DELEGATES_TO","dst":"damethod:DAUnitMaster.Save","line":134}
{"src":"damethod:DAUnitMaster.Save","type":"EXECUTES","dst":"sp:masterdata.mmumsave","via":"DAOUnitMaster.Save","line":48}
{"src":"damethod:DAUnitMaster.Save","type":"PASSES","dst":"dtprop:DTUnitMaster.UnitName","param":"@UnitName","line":41}
{"src":"control:fUnitMaster.utxtUnitName","type":"BINDS_TO","dst":"dtprop:DTUnitMaster.UnitName","expr":"utxtUnitName.Text.Trim","method":"ValidateForm","line":333}
{"src":"sp:masterdata.mmumsave","type":"USES_COLUMN","dst":"column:masterdata.munitmaster.unitname","ops":["write"]}
{"src":"sp:masterdata.mmumsave","type":"WRITES","dst":"table:masterdata.munitmaster","ops":["insert","update"],"lines":[31,72]}
{"src":"sp:masterdata.msgmfillvalues","type":"WRITES","dst":"table:masterdata.merrorlog","ops":["insert"],"error_handling":true,"lines":[191]}
{"src":"form:fUnitMaster","type":"CALLS_SP","dst":"sp:masterdata.mmumsave","derived":true,"methods":["SaveMain"]}
{"src":"form:fUnitMaster","type":"USES_TABLE","dst":"table:masterdata.munitmaster","derived":true,"ops":["read","write"]}
{"src":"form:fMaterialSubGroupMaster","type":"SHARES_TABLE","dst":"form:fUnitMaster","derived":true,"count":8,
 "write_conflict":true,"conflict_tables":["masterdata.mSubGroupUnitDetail"],"tables":["GlobalData.Unittype","masterdata.mCompanyMaster","..."]}
{"src":"process:material-master-setup","type":"HAS_STEP","dst":"form:fUnitMaster","order":1,"step":"Define units of measure and conversion factors","status":"active"}
```

---

## 11. Procedure and prompt for Claude Code

**Prerequisites**
- Windows.
- Python 3.11 or later (we use 3.13).
- .NET SDK 8 or later (`dotnet --list-sdks`).
- Internet access for pip and NuGet.
- Optional: a Neo4j 5 / Aura instance; a Voyage AI key.

**Procedure**
1. **Inventory the bundles** (§2). List each form folder with its Form / DataLayer / StoredProcedures / user-control
   files.
2. **Create the builder:** write every file of Appendix A at the path shown, exactly as shown. Create the empty
   folders `KnowledgeGraph/domain/forms/` and `KnowledgeGraph/domain/processes/`.
3. **Install:**
   ```powershell
   cd KnowledgeGraph
   py -3.13 -m venv .venv        # or: python -m venv .venv
   .venv\Scripts\python -m pip install -e ".[dev]"
   ```
4. **Extract the technical layer:** run `.venv\Scripts\kg validate`. The first run builds the Roslyn extractor
   with `dotnet build`. Read the counts and warnings:
   - `has no curated doc` is expected at this stage;
   - `executes X but no .sql file` means the bundle is missing an SP file;
   - `passes @p which X does not declare` means the data layer and the SP disagree (report it).
5. **Review the technical graph:**
   - `.venv\Scripts\kg build --dry-run graph/graph.json --no-strict`, then inspect `graph.json`;
   - `.venv\Scripts\kg export-html`, then open `kg-graph.html` in a browser.

   Note each form's SPs, the tables they write, `SHARES_TABLE.write_conflict`, the validation messages and the
   SPs' `params_not_passed`. These are the raw material for the rules.
6. **Scaffold the form docs:** run `.venv\Scripts\kg scaffold-doc <FormClass>` for every form and user control.
7. **Write the functional layer (§5.1, Steps A-E).** This is Claude Code's own work, based on the forms' code and
   SQL plus ERP domain knowledge:
   - `domain/modules.yaml`;
   - `domain/concepts.yaml`;
   - `domain/processes/*.yaml`, with planned steps for screens that are not in scope;
   - `domain/rules.yaml`: D1 rules found in the code and D2 rules from ERP domain knowledge, each starting with its
     evidence line;
   - complete every `domain/forms/<Form>.yaml`.

   Reuse the §9 keys where they fit.
8. **Validate until clean:** run `.venv\Scripts\kg validate`. It must print `valid`, with **zero errors and zero
   warnings**. The warnings include the coverage checks:
   - missing evidence line;
   - a form without any rule;
   - a process without any rule;
   - a validation message not quoted in a rule;
   - a write conflict without an integrity rule.
9. **Produce the outputs:**
   - `.venv\Scripts\kg build --dry-run graph/graph.json`
   - `.venv\Scripts\kg export-html`
10. **Optional:**
    - `.venv\Scripts\kg build --no-embed` loads Neo4j (§7);
    - `.venv\Scripts\kg build` loads Neo4j with embeddings (§8).

**Prompt**

> Read `GRAPH_STRUCTURE.md` completely and follow §11.
>
> 1. **Technical layer.** Create every Appendix A file exactly as shown (do not modify the code), install it and
>    run `kg validate` to extract the technical layer from the form folders with Roslyn and sqlglot.
> 2. **Functional layer.** Write it yourself in `KnowledgeGraph/domain/` per §5.1 Steps A-E:
>    - the concepts and the business processes of the forms in scope;
>    - the **business rules**: (D1) every rule the forms' code and SQL enforce, and (D2) the standard ERP Material
>      Management / Plant Maintenance rules that the in-scope data supports;
>    - a doc for every form and user control.
>
>    Start every concept, process and rule description with its `Evidence:` line, and never contradict the code.
>    Reuse the §9 keys where they fit. Use only the YAML fields of §5.2.
> 3. **Finish.** Iterate until `kg validate` prints `valid` with no errors and no warnings. Then run
>    `kg build --dry-run graph/graph.json` and `kg export-html`. Show me the node and edge counts and a table of the
>    rules (key, type, evidence, applies_to). Skip embeddings unless I ask for them.

<!-- APPENDICES: generated by tools/make_spec_appendix.py - do not edit below this line -->

## Appendix A: builder source (create every file exactly as shown)

25 files, 3277 lines. Paths are relative to the repository root. Create each file byte-for-byte with the content between the fences (UTF-8, no BOM). Do not reformat, rename or "improve" them: the graph's ids and structure depend on this exact code.

#### `KnowledgeGraph/pyproject.toml`

````toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "spectrum-kg"
version = "0.1.0"
description = "Knowledge graph (Neo4j GraphRAG) + agentic MCP server for the SpectrumERP codebase"
requires-python = ">=3.11"
dependencies = [
    "neo4j>=5.20",
    "neo4j-graphrag>=1.5",
    "voyageai>=0.3",
    "sqlglot>=25",
    "pyyaml>=6",
    "pydantic>=2.6",
    "python-dotenv>=1.0",
    "mcp>=1.2",
    "typer>=0.12",
]

[project.optional-dependencies]
dev = ["pytest>=8"]

[project.scripts]
kg = "spectrum_kg.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["live: needs a reachable Neo4j (and Voyage) configured in .env"]
````

#### `KnowledgeGraph/kg.yaml`

````yaml
# Build configuration for the SpectrumERP knowledge graph.
# Paths are relative to this file.

source_root: ..                 # repository root that holds the form bundles
bundles: auto                   # auto = every top-level folder containing CONTENTS.md, Form/ or StoredProcedures/
exclude: [KnowledgeGraph, .venv, .git, .vs, .claude]

domain_dir: domain              # curated functional docs (modules, concepts, processes, rules, forms)
cache_dir: .cache               # Roslyn facts + embedding cache (git-ignored)
roslyn_extractor: tools/bin/RoslynExtractor/RoslynExtractor.exe
roslyn_project: tools/RoslynExtractor/RoslynExtractor.csproj

sql:
  default_schema: masterdata    # schema assumed for unqualified table names
  error_log_tables: [masterdata.mErrorLog]   # writes to these (in CATCH blocks) are not business writes

datalayer:
  # Methods on the base helper that execute a stored procedure; first argument is the SP name/DAO constant.
  exec_methods: [ExecuteProc, ExecuteQuery, ExecuteNonQuery, ExecuteDataset, ExecuteScalar]
  param_add_methods: [Add]      # dicPara.Add(DAO.@Param, DT.Prop)

ui:
  mandatory_methods: [CompulsaryField, CompulsoryField]
  form_base_types: [Form, System.Windows.Forms.Form]
  usercontrol_base_types: [UserControl, System.Windows.Forms.UserControl]
````

#### `KnowledgeGraph/.env.example`

````ini
# Copy to .env (git-ignored) and fill in.

# Neo4j Aura: from the credentials file downloaded when the instance was created
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=
# Aura Free/Professional default database (leave empty to use the server default)
NEO4J_DATABASE=

# Voyage AI (https://dashboard.voyageai.com/). Note: without a payment method the API is limited to
# 3 requests/min and 10K tokens/min; the first build then takes a while (embeddings are cached in .cache/).
VOYAGE_API_KEY=
VOYAGE_MODEL=voyage-code-3
EMBEDDING_DIMENSIONS=1024
````

#### `KnowledgeGraph/.gitignore`

````text
.env
.cache/
tools/bin/
*.egg-info/
kg-graph.html
````

#### `KnowledgeGraph/tools/RoslynExtractor/RoslynExtractor.csproj`

````xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <RollForward>Major</RollForward>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <InvariantGlobalization>true</InvariantGlobalization>
    <RootNamespace>RoslynExtractor</RootNamespace>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.CodeAnalysis.CSharp" Version="4.12.0" />
    <PackageReference Include="Microsoft.CodeAnalysis.VisualBasic" Version="4.12.0" />
  </ItemGroup>

</Project>
````

#### `KnowledgeGraph/tools/RoslynExtractor/Program.cs`

````csharp
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using RoslynExtractor;

// Usage: RoslynExtractor --out facts.json <file-or-dir> [<file-or-dir> ...]
// Parses every .vb / .cs file (syntax only, no compilation/references needed) and writes a JSON array of FileFacts.

string? outPath = null;
var inputs = new List<string>();
for (int i = 0; i < args.Length; i++)
{
    if (args[i] == "--out" && i + 1 < args.Length) outPath = args[++i];
    else inputs.Add(args[i]);
}
if (inputs.Count == 0)
{
    Console.Error.WriteLine("usage: RoslynExtractor --out facts.json <file-or-dir>...");
    return 2;
}

var files = new List<string>();
foreach (var input in inputs)
{
    if (File.Exists(input)) files.Add(Path.GetFullPath(input));
    else if (Directory.Exists(input))
        files.AddRange(Directory.EnumerateFiles(input, "*.*", SearchOption.AllDirectories)
            .Where(f => f.EndsWith(".vb", StringComparison.OrdinalIgnoreCase) || f.EndsWith(".cs", StringComparison.OrdinalIgnoreCase))
            .Where(f => !f.Split(Path.DirectorySeparatorChar).Any(p => p is "bin" or "obj" or ".venv"))
            .Select(Path.GetFullPath));
}

var results = new List<FileFacts>();
foreach (var file in files.Distinct().OrderBy(f => f, StringComparer.OrdinalIgnoreCase))
{
    var text = File.ReadAllText(file, Encoding.UTF8);
    try
    {
        results.Add(file.EndsWith(".vb", StringComparison.OrdinalIgnoreCase)
            ? VbExtractor.Extract(file, text)
            : CSharpExtractor.Extract(file, text));
    }
    catch (Exception ex)
    {
        results.Add(new FileFacts { Path = file, Language = "error", Diagnostics = { ex.ToString() } });
    }
}

var json = JsonSerializer.Serialize(results, new JsonSerializerOptions
{
    WriteIndented = false,
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
});
if (outPath is null) Console.Out.Write(json);
else File.WriteAllText(outPath, json, new UTF8Encoding(false));
Console.Error.WriteLine($"parsed {results.Count} files");
return 0;
````

#### `KnowledgeGraph/tools/RoslynExtractor/Model.cs`

````csharp
namespace RoslynExtractor;

// Language-neutral syntax facts. Python (spectrum_kg.extract) interprets these into graph nodes.

public sealed class FileFacts
{
    public string Path { get; set; } = "";
    public string Language { get; set; } = "";          // "vb" | "csharp"
    public List<string> Imports { get; set; } = new();
    public List<TypeFacts> Types { get; set; } = new();
    public List<string> Diagnostics { get; set; } = new(); // syntax errors, if any
}

public sealed class TypeFacts
{
    public string Name { get; set; } = "";
    public string Kind { get; set; } = "";               // class | struct | interface | module | enum
    public string Namespace { get; set; } = "";
    public bool Partial { get; set; }
    public List<string> Bases { get; set; } = new();     // Inherits / base list
    public List<string> Implements { get; set; } = new();
    public List<FieldFacts> Fields { get; set; } = new();
    public List<PropertyFacts> Properties { get; set; } = new();
    public List<MethodFacts> Methods { get; set; } = new();
    public int StartLine { get; set; }
    public int EndLine { get; set; }
}

public sealed class FieldFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public List<string> Modifiers { get; set; } = new();
    public bool WithEvents { get; set; }
    public string? Initializer { get; set; }
    public int Line { get; set; }
}

public sealed class PropertyFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public string? BackingField { get; set; }
    public int Line { get; set; }
}

public sealed class ParamFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
}

public sealed class HandlesFacts
{
    public string Target { get; set; } = "";   // control / field name ("MyBase" for form events)
    public string Event { get; set; } = "";
}

public sealed class InvocationFacts
{
    public string Text { get; set; } = "";
    public string? Receiver { get; set; }      // text left of the final '.', With-target resolved
    public string Member { get; set; } = "";
    public List<string> Args { get; set; } = new();
    public int Line { get; set; }
}

public sealed class MemberAccessFacts
{
    public string Receiver { get; set; } = "";
    public string Member { get; set; } = "";
    public int Line { get; set; }
}

public sealed class AssignmentFacts
{
    public string Left { get; set; } = "";
    public string Right { get; set; } = "";
    public string Op { get; set; } = "=";      // "=", "+=", ...
    public int Line { get; set; }
}

public sealed class LocalFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public string? Initializer { get; set; }
    public int Line { get; set; }
}

public sealed class SubscriptionFacts
{
    public string Target { get; set; } = "";
    public string Event { get; set; } = "";
    public string Handler { get; set; } = "";
    public int Line { get; set; }
}

public sealed class MethodFacts
{
    public string Name { get; set; } = "";
    public string Kind { get; set; } = "";     // sub | function | method | constructor
    public string ReturnType { get; set; } = "";
    public List<string> Modifiers { get; set; } = new();
    public List<ParamFacts> Parameters { get; set; } = new();
    public List<HandlesFacts> Handles { get; set; } = new();
    public List<string> ImplementsMembers { get; set; } = new();
    public int StartLine { get; set; }
    public int EndLine { get; set; }
    public string Code { get; set; } = "";
    public string LeadingComments { get; set; } = "";
    public List<InvocationFacts> Invocations { get; set; } = new();
    public List<MemberAccessFacts> MemberAccesses { get; set; } = new();
    public List<AssignmentFacts> Assignments { get; set; } = new();
    public List<LocalFacts> Locals { get; set; } = new();
    public List<string> ObjectCreations { get; set; } = new();
    public List<SubscriptionFacts> Subscriptions { get; set; } = new();
    public List<string> StringLiterals { get; set; } = new();
}
````

#### `KnowledgeGraph/tools/RoslynExtractor/CSharpExtractor.cs`

````csharp
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace RoslynExtractor;

public static class CSharpExtractor
{
    public static FileFacts Extract(string path, string text)
    {
        var tree = CSharpSyntaxTree.ParseText(text, path: path);
        var root = tree.GetCompilationUnitRoot();
        var facts = new FileFacts { Path = path, Language = "csharp" };
        facts.Diagnostics.AddRange(tree.GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error).Select(d => d.ToString()));
        facts.Imports.AddRange(root.DescendantNodes().OfType<UsingDirectiveSyntax>().Select(u => u.Name?.ToString() ?? ""));

        foreach (var type in root.DescendantNodes().OfType<BaseTypeDeclarationSyntax>())
        {
            var tf = new TypeFacts
            {
                Name = type.Identifier.Text,
                Kind = type switch
                {
                    InterfaceDeclarationSyntax => "interface",
                    StructDeclarationSyntax => "struct",
                    EnumDeclarationSyntax => "enum",
                    RecordDeclarationSyntax => "record",
                    _ => "class",
                },
                Namespace = string.Join(".", type.Ancestors().OfType<BaseNamespaceDeclarationSyntax>().Reverse().Select(n => n.Name.ToString())),
                Partial = type.Modifiers.Any(m => m.IsKind(SyntaxKind.PartialKeyword)),
                StartLine = Line(type),
                EndLine = EndLine(type),
            };
            if (type.BaseList is not null)
                tf.Bases.AddRange(type.BaseList.Types.Select(t => t.Type.ToString()));

            if (type is TypeDeclarationSyntax tds)
            {
                foreach (var member in tds.Members)
                {
                    switch (member)
                    {
                        case FieldDeclarationSyntax f:
                            foreach (var v in f.Declaration.Variables)
                                tf.Fields.Add(new FieldFacts
                                {
                                    Name = v.Identifier.Text,
                                    Type = f.Declaration.Type.ToString(),
                                    Modifiers = f.Modifiers.Select(m => m.Text).ToList(),
                                    Initializer = v.Initializer?.Value.ToString(),
                                    Line = Line(v),
                                });
                            break;
                        case PropertyDeclarationSyntax p:
                            tf.Properties.Add(new PropertyFacts
                            {
                                Name = p.Identifier.Text,
                                Type = p.Type.ToString(),
                                BackingField = BackingField(p),
                                Line = Line(p),
                            });
                            break;
                        case MethodDeclarationSyntax m:
                            tf.Methods.Add(Method(m, m.Identifier.Text, "method", m.ReturnType.ToString(), m.Modifiers, m.ParameterList));
                            break;
                        case ConstructorDeclarationSyntax c:
                            tf.Methods.Add(Method(c, c.Identifier.Text, "constructor", "", c.Modifiers, c.ParameterList));
                            break;
                    }
                }
            }
            facts.Types.Add(tf);
        }
        return facts;
    }

    static string? BackingField(PropertyDeclarationSyntax p)
    {
        var getter = p.AccessorList?.Accessors.FirstOrDefault(a => a.IsKind(SyntaxKind.GetAccessorDeclaration));
        SyntaxNode? body = (SyntaxNode?)getter?.Body ?? getter?.ExpressionBody ?? (SyntaxNode?)p.ExpressionBody;
        var ret = body?.DescendantNodesAndSelf().OfType<ReturnStatementSyntax>().FirstOrDefault()?.Expression
                  ?? (body as ArrowExpressionClauseSyntax)?.Expression;
        return ret switch
        {
            IdentifierNameSyntax id => id.Identifier.Text,
            MemberAccessExpressionSyntax ma when ma.Expression is ThisExpressionSyntax => ma.Name.Identifier.Text,
            _ => null,
        };
    }

    static MethodFacts Method(BaseMethodDeclarationSyntax node, string name, string kind, string returnType,
        SyntaxTokenList modifiers, ParameterListSyntax parameters)
    {
        var mf = new MethodFacts
        {
            Name = name,
            Kind = kind,
            ReturnType = returnType,
            Modifiers = modifiers.Select(m => m.Text).ToList(),
            Parameters = parameters.Parameters.Select(p => new ParamFacts { Name = p.Identifier.Text, Type = p.Type?.ToString() ?? "" }).ToList(),
            StartLine = Line(node),
            EndLine = EndLine(node),
            Code = node.ToString(),
            LeadingComments = Comments(node),
        };
        SyntaxNode body = (SyntaxNode?)node.Body ?? (SyntaxNode?)node.ExpressionBody ?? node;

        foreach (var n in body.DescendantNodes())
        {
            switch (n)
            {
                case InvocationExpressionSyntax inv:
                    {
                        string? receiver = null; string member;
                        if (inv.Expression is MemberAccessExpressionSyntax ma) { receiver = ma.Expression.ToString(); member = ma.Name.Identifier.Text; }
                        else if (inv.Expression is MemberBindingExpressionSyntax mb) { member = mb.Name.Identifier.Text; }
                        else member = inv.Expression.ToString();
                        mf.Invocations.Add(new InvocationFacts
                        {
                            Text = Trunc(inv.ToString()),
                            Receiver = receiver,
                            Member = member,
                            Args = inv.ArgumentList.Arguments.Select(a => Trunc(a.ToString())).ToList(),
                            Line = Line(inv),
                        });
                        break;
                    }
                case MemberAccessExpressionSyntax ma2:
                    mf.MemberAccesses.Add(new MemberAccessFacts { Receiver = ma2.Expression.ToString(), Member = ma2.Name.Identifier.Text, Line = Line(ma2) });
                    break;
                case AssignmentExpressionSyntax asg:
                    {
                        var op = asg.OperatorToken.Text;
                        mf.Assignments.Add(new AssignmentFacts { Left = asg.Left.ToString(), Right = Trunc(asg.Right.ToString()), Op = op, Line = Line(asg) });
                        if (op == "+=" && asg.Left is MemberAccessExpressionSyntax evt)
                        {
                            var handler = asg.Right switch
                            {
                                ObjectCreationExpressionSyntax oc when oc.ArgumentList?.Arguments.Count == 1 => oc.ArgumentList.Arguments[0].ToString(),
                                _ => asg.Right.ToString(),
                            };
                            mf.Subscriptions.Add(new SubscriptionFacts
                            {
                                Target = StripThis(evt.Expression.ToString()),
                                Event = evt.Name.Identifier.Text,
                                Handler = StripThis(handler),
                                Line = Line(asg),
                            });
                        }
                        break;
                    }
                case LocalDeclarationStatementSyntax ld:
                    foreach (var v in ld.Declaration.Variables)
                        mf.Locals.Add(new LocalFacts
                        {
                            Name = v.Identifier.Text,
                            Type = ld.Declaration.Type.IsVar && v.Initializer?.Value is ObjectCreationExpressionSyntax oce ? oce.Type.ToString() : ld.Declaration.Type.ToString(),
                            Initializer = v.Initializer is null ? null : Trunc(v.Initializer.Value.ToString()),
                            Line = Line(v),
                        });
                    break;
                case ObjectCreationExpressionSyntax oc2:
                    mf.ObjectCreations.Add(oc2.Type.ToString());
                    break;
                case LiteralExpressionSyntax lit when lit.IsKind(SyntaxKind.StringLiteralExpression):
                    mf.StringLiterals.Add(lit.Token.ValueText);
                    break;
            }
        }
        return mf;
    }

    static string StripThis(string s) => s.StartsWith("this.") ? s[5..] : s;
    static string Trunc(string s) => s.Length > 400 ? s[..400] + "…" : s;
    static int Line(SyntaxNode n) => n.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
    static int EndLine(SyntaxNode n) => n.GetLocation().GetLineSpan().EndLinePosition.Line + 1;

    static string Comments(SyntaxNode n) => string.Join("\n", n.GetLeadingTrivia()
        .Where(t => t.IsKind(SyntaxKind.SingleLineCommentTrivia) || t.IsKind(SyntaxKind.MultiLineCommentTrivia)
                    || t.IsKind(SyntaxKind.SingleLineDocumentationCommentTrivia))
        .Select(t => t.ToFullString().Trim()));
}
````

#### `KnowledgeGraph/tools/RoslynExtractor/VbExtractor.cs`

````csharp
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.VisualBasic;
using Microsoft.CodeAnalysis.VisualBasic.Syntax;

namespace RoslynExtractor;

public static class VbExtractor
{
    public static FileFacts Extract(string path, string text)
    {
        var tree = VisualBasicSyntaxTree.ParseText(text, path: path);
        var root = (CompilationUnitSyntax)tree.GetRoot();
        var facts = new FileFacts { Path = path, Language = "vb" };
        facts.Diagnostics.AddRange(tree.GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error).Select(d => d.ToString()));
        facts.Imports.AddRange(root.Imports.SelectMany(i => i.ImportsClauses).Select(c => c.ToString()));

        foreach (var type in root.DescendantNodes().OfType<TypeBlockSyntax>())
        {
            var stmt = type.BlockStatement;
            var tf = new TypeFacts
            {
                Name = stmt.Identifier.Text,
                Kind = type switch
                {
                    ModuleBlockSyntax => "module",
                    StructureBlockSyntax => "struct",
                    InterfaceBlockSyntax => "interface",
                    _ => "class",
                },
                Namespace = string.Join(".", type.Ancestors().OfType<NamespaceBlockSyntax>().Reverse().Select(n => n.NamespaceStatement.Name.ToString())),
                Partial = stmt.Modifiers.Any(m => m.IsKind(SyntaxKind.PartialKeyword)),
                StartLine = Line(type),
                EndLine = EndLine(type),
            };
            tf.Bases.AddRange(type.Inherits.SelectMany(i => i.Types).Select(t => t.ToString()));
            tf.Implements.AddRange(type.Implements.SelectMany(i => i.Types).Select(t => t.ToString()));

            foreach (var member in type.Members)
            {
                switch (member)
                {
                    case FieldDeclarationSyntax f:
                        foreach (var d in f.Declarators)
                            foreach (var name in d.Names)
                                tf.Fields.Add(new FieldFacts
                                {
                                    Name = name.Identifier.Text,
                                    Type = AsType(d.AsClause),
                                    Modifiers = f.Modifiers.Select(m => m.Text).ToList(),
                                    WithEvents = f.Modifiers.Any(m => m.IsKind(SyntaxKind.WithEventsKeyword)),
                                    Initializer = d.Initializer?.Value.ToString() ?? (d.AsClause as AsNewClauseSyntax)?.NewExpression.ToString(),
                                    Line = Line(d),
                                });
                        break;
                    case PropertyBlockSyntax pb:
                        tf.Properties.Add(new PropertyFacts
                        {
                            Name = pb.PropertyStatement.Identifier.Text,
                            Type = AsType(pb.PropertyStatement.AsClause),
                            BackingField = pb.Accessors.FirstOrDefault(a => a.IsKind(SyntaxKind.GetAccessorBlock))?
                                .DescendantNodes().OfType<ReturnStatementSyntax>().FirstOrDefault()?.Expression?.ToString(),
                            Line = Line(pb),
                        });
                        break;
                    case PropertyStatementSyntax ps:
                        tf.Properties.Add(new PropertyFacts { Name = ps.Identifier.Text, Type = AsType(ps.AsClause), Line = Line(ps) });
                        break;
                    case MethodBlockSyntax mb:
                        tf.Methods.Add(Method(mb, mb.SubOrFunctionStatement));
                        break;
                    case ConstructorBlockSyntax cb:
                        tf.Methods.Add(Method(cb, cb.SubNewStatement));
                        break;
                }
            }
            facts.Types.Add(tf);
        }
        return facts;
    }

    static string AsType(AsClauseSyntax? clause) => clause switch
    {
        SimpleAsClauseSyntax s => s.Type.ToString(),
        AsNewClauseSyntax n => n.NewExpression is ObjectCreationExpressionSyntax oc ? oc.Type.ToString() : n.NewExpression.ToString(),
        _ => "",
    };

    static MethodFacts Method(MethodBlockBaseSyntax block, MethodBaseSyntax header)
    {
        var mf = new MethodFacts
        {
            Modifiers = header.Modifiers.Select(m => m.Text).ToList(),
            Parameters = header.ParameterList?.Parameters.Select(p => new ParamFacts
            {
                Name = p.Identifier.Identifier.Text,
                Type = AsType(p.AsClause),
            }).ToList() ?? new(),
            StartLine = Line(block),
            EndLine = EndLine(block),
            Code = block.ToString(),
            LeadingComments = Comments(block),
        };
        switch (header)
        {
            case MethodStatementSyntax ms:
                mf.Name = ms.Identifier.Text;
                mf.Kind = ms.IsKind(SyntaxKind.FunctionStatement) ? "function" : "sub";
                mf.ReturnType = AsType(ms.AsClause);
                if (ms.HandlesClause is not null)
                    mf.Handles.AddRange(ms.HandlesClause.Events.Select(e => new HandlesFacts
                    {
                        Target = e.EventContainer.ToString(),
                        Event = e.EventMember.Identifier.Text,
                    }));
                if (ms.ImplementsClause is not null)
                    mf.ImplementsMembers.AddRange(ms.ImplementsClause.InterfaceMembers.Select(i => i.ToString()));
                break;
            case SubNewStatementSyntax:
                mf.Name = "New";
                mf.Kind = "constructor";
                break;
        }

        foreach (var n in block.Statements.SelectMany(s => s.DescendantNodesAndSelf()))
        {
            switch (n)
            {
                case InvocationExpressionSyntax inv:
                    {
                        string? receiver = null; string member;
                        if (inv.Expression is MemberAccessExpressionSyntax ma) { receiver = Receiver(ma); member = ma.Name.Identifier.Text; }
                        else if (inv.Expression is null) { member = ""; }
                        else member = inv.Expression.ToString();
                        mf.Invocations.Add(new InvocationFacts
                        {
                            Text = Trunc(inv.ToString()),
                            Receiver = receiver,
                            Member = member,
                            Args = inv.ArgumentList?.Arguments.Select(a => Trunc(a.ToString())).ToList() ?? new(),
                            Line = Line(inv),
                        });
                        break;
                    }
                case MemberAccessExpressionSyntax ma2:
                    mf.MemberAccesses.Add(new MemberAccessFacts { Receiver = Receiver(ma2) ?? "", Member = ma2.Name.Identifier.Text, Line = Line(ma2) });
                    break;
                case AssignmentStatementSyntax asg:
                    mf.Assignments.Add(new AssignmentFacts { Left = ResolveWith(asg.Left), Right = Trunc(asg.Right.ToString()), Op = asg.OperatorToken.Text, Line = Line(asg) });
                    break;
                case LocalDeclarationStatementSyntax ld:
                    foreach (var d in ld.Declarators)
                        foreach (var name in d.Names)
                            mf.Locals.Add(new LocalFacts
                            {
                                Name = name.Identifier.Text,
                                Type = AsType(d.AsClause),
                                Initializer = d.Initializer is null ? null : Trunc(d.Initializer.Value.ToString()),
                                Line = Line(d),
                            });
                    break;
                case ObjectCreationExpressionSyntax oc:
                    mf.ObjectCreations.Add(oc.Type.ToString());
                    break;
                case AddRemoveHandlerStatementSyntax ah when ah.IsKind(SyntaxKind.AddHandlerStatement):
                    if (ah.EventExpression is MemberAccessExpressionSyntax evt)
                        mf.Subscriptions.Add(new SubscriptionFacts
                        {
                            Target = Receiver(evt) ?? "",
                            Event = evt.Name.Identifier.Text,
                            Handler = ah.DelegateExpression is UnaryExpressionSyntax u ? u.Operand.ToString() : ah.DelegateExpression.ToString(),
                            Line = Line(ah),
                        });
                    break;
                case LiteralExpressionSyntax lit when lit.IsKind(SyntaxKind.StringLiteralExpression):
                    mf.StringLiterals.Add(lit.Token.ValueText);
                    break;
            }
        }
        return mf;
    }

    // Receiver text of a member access; ".Foo" inside a With block resolves to the With target.
    static string? Receiver(MemberAccessExpressionSyntax ma)
    {
        if (ma.Expression is not null) return ResolveWith(ma.Expression);
        var with = ma.Ancestors().OfType<WithBlockSyntax>().FirstOrDefault();
        return with?.WithStatement.Expression.ToString();
    }

    static string ResolveWith(ExpressionSyntax e)
    {
        var text = e.ToString();
        if (!text.StartsWith(".")) return text;
        var with = e.Ancestors().OfType<WithBlockSyntax>().FirstOrDefault();
        return with is null ? text : with.WithStatement.Expression + text;
    }

    static string Trunc(string s) => s.Length > 400 ? s[..400] + "…" : s;
    static int Line(SyntaxNode n) => n.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
    static int EndLine(SyntaxNode n) => n.GetLocation().GetLineSpan().EndLinePosition.Line + 1;

    static string Comments(SyntaxNode n) => string.Join("\n", n.GetLeadingTrivia()
        .Where(t => t.IsKind(SyntaxKind.CommentTrivia) || t.IsKind(SyntaxKind.DocumentationCommentTrivia))
        .Select(t => t.ToFullString().Trim()));
}
````

#### `KnowledgeGraph/src/spectrum_kg/__init__.py`

````python
"""SpectrumERP knowledge graph: extractors, Neo4j loader and agentic MCP server."""
````

#### `KnowledgeGraph/src/spectrum_kg/config.py`

````python
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]  # .../KnowledgeGraph


@dataclass
class Settings:
    project_dir: Path
    source_root: Path
    domain_dir: Path
    cache_dir: Path
    roslyn_extractor: Path
    roslyn_project: Path
    bundles: str | list[str]
    exclude: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def sql(self) -> dict[str, Any]: return self.raw.get("sql", {})
    @property
    def datalayer(self) -> dict[str, Any]: return self.raw.get("datalayer", {})
    @property
    def ui(self) -> dict[str, Any]: return self.raw.get("ui", {})

    # --- environment (.env) ---
    @property
    def neo4j_uri(self) -> str: return _env("NEO4J_URI")
    @property
    def neo4j_user(self) -> str: return os.getenv("NEO4J_USERNAME", "neo4j")
    @property
    def neo4j_password(self) -> str: return _env("NEO4J_PASSWORD")
    @property
    def neo4j_database(self) -> str | None: return os.getenv("NEO4J_DATABASE") or None
    @property
    def voyage_api_key(self) -> str: return _env("VOYAGE_API_KEY")
    @property
    def voyage_model(self) -> str: return os.getenv("VOYAGE_MODEL", "voyage-code-3")
    @property
    def embedding_dims(self) -> int: return int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env in {PROJECT_DIR} and fill it in.")
    return v


def load_settings(config_path: Path | None = None) -> Settings:
    config_path = config_path or PROJECT_DIR / "kg.yaml"
    load_dotenv(config_path.parent / ".env")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    base = config_path.parent
    return Settings(
        project_dir=base,
        source_root=(base / raw.get("source_root", "..")).resolve(),
        domain_dir=(base / raw.get("domain_dir", "domain")).resolve(),
        cache_dir=(base / raw.get("cache_dir", ".cache")).resolve(),
        roslyn_extractor=(base / raw["roslyn_extractor"]).resolve(),
        roslyn_project=(base / raw["roslyn_project"]).resolve(),
        bundles=raw.get("bundles", "auto"),
        exclude=raw.get("exclude", []),
        raw=raw,
    )
````

#### `KnowledgeGraph/src/spectrum_kg/model.py`

````python
"""In-memory property graph built by the extractors before it is loaded into Neo4j."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable


def norm(s: str) -> str:
    """Case-insensitive key for SQL identifiers."""
    return s.strip().lower()


# ---- stable node ids -------------------------------------------------------------------------
def form_id(name: str) -> str: return f"form:{name}"
def ui_id(kind: str, name: str) -> str: return f"{'form' if kind == 'Form' else 'usercontrol'}:{name}"
def control_id(owner: str, name: str) -> str: return f"control:{owner}.{name}"
def method_id(owner: str, name: str) -> str: return f"method:{owner}.{name}"
def dtclass_id(name: str) -> str: return f"dtclass:{name}"
def dtprop_id(cls: str, name: str) -> str: return f"dtprop:{cls}.{name}"
def dtmethod_id(cls: str, name: str) -> str: return f"dtmethod:{cls}.{name}"
def daclass_id(name: str) -> str: return f"daclass:{name}"
def damethod_id(cls: str, name: str) -> str: return f"damethod:{cls}.{name}"
def sp_id(qualified: str) -> str: return f"sp:{norm(qualified)}"
def table_id(qualified: str) -> str: return f"table:{norm(qualified)}"
def column_id(table_qualified: str, col: str) -> str: return f"column:{norm(table_qualified)}.{norm(col)}"
def module_id(code: str) -> str: return f"module:{code}"
def process_id(key: str) -> str: return f"process:{key}"
def concept_id(key: str) -> str: return f"concept:{key}"
def rule_id(key: str) -> str: return f"rule:{key}"


@dataclass
class Node:
    id: str
    label: str
    props: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.props.get("name", self.id)


@dataclass
class Edge:
    src: str
    type: str
    dst: str
    props: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.src, self.type, self.dst)


LIST_PROPS = {"source_files", "bundles", "synonyms", "methods", "lines", "columns", "grid_columns", "events", "ops"}


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str, str], Edge] = {}
        self._name_votes: dict[str, Counter] = {}

    # Nodes merge: scalar props keep the first non-empty value, list props union.
    def add_node(self, id: str, label: str, /, **props: Any) -> Node:
        node = self.nodes.get(id)
        if node is None:
            node = self.nodes[id] = Node(id, label, {})
        _merge(node.props, props)
        return node

    def vote_name(self, id: str, display: str) -> None:
        """Pick the most frequent spelling of a case-insensitive SQL name for display."""
        self._name_votes.setdefault(id, Counter())[display] += 1

    def add_edge(self, src: str, type: str, dst: str, /, **props: Any) -> Edge:
        key = (src, type, dst)
        edge = self.edges.get(key)
        if edge is None:
            edge = self.edges[key] = Edge(src, type, dst, {})
        _merge(edge.props, props)
        return edge

    def finalize_names(self) -> None:
        for id, votes in self._name_votes.items():
            if id in self.nodes:
                # most common spelling; ties broken by preferring mixed case over all-lower
                best = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0] == kv[0].lower(), kv[0]))[0][0]
                self.nodes[id].props["name"] = best

    def out(self, src: str, type: str | None = None) -> Iterable[Edge]:
        return [e for e in self.edges.values() if e.src == src and (type is None or e.type == type)]

    def inc(self, dst: str, type: str | None = None) -> Iterable[Edge]:
        return [e for e in self.edges.values() if e.dst == dst and (type is None or e.type == type)]

    def by_label(self, label: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.label == label]

    def dangling_edges(self) -> list[Edge]:
        return [e for e in self.edges.values() if e.src not in self.nodes or e.dst not in self.nodes]

    def to_json(self) -> dict[str, Any]:
        return {
            # node type is `kind`; `label` is reserved for a property (a control's on-screen caption)
            "nodes": [{"id": n.id, **{k: v for k, v in n.props.items() if k != "kind"}, "kind": n.label}
                      for n in sorted(self.nodes.values(), key=lambda n: n.id)],
            "edges": [{"src": e.src, "type": e.type, "dst": e.dst, **e.props}
                      for e in sorted(self.edges.values(), key=lambda e: e.key)],
        }

    def stats(self) -> dict[str, dict[str, int]]:
        return {
            "nodes": dict(sorted(Counter(n.label for n in self.nodes.values()).items())),
            "edges": dict(sorted(Counter(e.type for e in self.edges.values()).items())),
        }


def _merge(target: dict[str, Any], props: dict[str, Any]) -> None:
    for k, v in props.items():
        if v is None or v == "" or v == []:
            continue
        if k in LIST_PROPS or isinstance(v, list):
            cur = target.get(k) or []
            vals = v if isinstance(v, list) else [v]
            for item in vals:
                if item not in cur:
                    cur.append(item)
            target[k] = cur
        elif k not in target or target[k] in (None, "", []):
            target[k] = v


def content_hash(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]
````

#### `KnowledgeGraph/src/spectrum_kg/schema.py`

````python
"""Self-description of the graph for agentic clients (served by describe_graph / kg://schema)."""
from __future__ import annotations

LABELS: dict[str, dict[str, str]] = {
    # functional layer
    "Module": {"layer": "functional", "means": "ERP module (Material Management, Plant Maintenance).",
               "key_props": "name, code, summary, doc, status"},
    "BusinessProcess": {"layer": "functional", "means": "End-to-end business flow, e.g. Procure-to-Pay (PO Flow), Payment Flow; ordered steps point to forms.",
                        "key_props": "name, key, summary, doc (includes ordered steps), status"},
    "BusinessConcept": {"layer": "functional", "means": "ERP domain entity (Material Group, Unit of Measure, QC Parameter, Vendor ...), with synonyms.",
                        "key_props": "name, key, summary, doc, synonyms"},
    "BusinessRule": {"layer": "functional", "means": "Business rule / policy and where it is enforced (SPs, methods, columns).",
                     "key_props": "name, summary, doc, rule_type"},
    "Form": {"layer": "bridge", "means": "WinForms screen. Curated doc (purpose, actions, validations) + extracted code. status=planned means a placeholder for a form not built yet.",
             "key_props": "name, title, summary, doc, module, sp_prefix, status"},
    "UserControl": {"layer": "bridge", "means": "Reusable UI component embedded in forms (e.g. QCGroup).",
                    "key_props": "name, title, summary, doc"},
    # technical layer
    "FormMethod": {"layer": "code", "means": "VB/C# method of a form or user control (event handler, IMDIFunctions action like Save/LoadData, helper).",
                   "key_props": "name, method, owner, method_kind, events, code, file, start_line"},
    "Control": {"layer": "code", "means": "UI control on a form (textbox, combo, grid, tab page ...), with its label, tab, mandatory flag.",
                "key_props": "name, control, type, label, tab, mandatory, max_length"},
    "DTClass": {"layer": "code", "means": "Data-transfer (active-record) class; forms set its properties and call its methods.", "key_props": "name"},
    "DTProperty": {"layer": "code", "means": "Property of a DT class; carries a form field value to an SP parameter.", "key_props": "name, property, type"},
    "DTMethod": {"layer": "code", "means": "DT method called by forms; delegates to a DA method.", "key_props": "name, code"},
    "DAClass": {"layer": "code", "means": "Data-access class.", "key_props": "name"},
    "DAMethod": {"layer": "code", "means": "Data-access method: builds the parameter dictionary and executes one stored procedure.", "key_props": "name, code"},
    "StoredProcedure": {"layer": "data", "means": "T-SQL stored procedure (one node, full code): header author/date/description, parameters list, params_not_passed (never sent by the data layer, SQL default applies).",
                        "key_props": "name, code, description, author, created, parameters, params_not_passed, dynamic_sql, ambiguous_columns"},
    "Table": {"layer": "data", "means": "Database table (schema.name).", "key_props": "name, schema, table"},
    "Column": {"layer": "data", "means": "Table column observed in SP code (no DDL available, so only used columns exist).",
               "key_props": "name, table, column"},
}

# type -> (from, to, meaning, follow when, derived)
RELATIONSHIPS: dict[str, dict[str, object]] = {
    "HAS_PROCESS": {"from": "Module", "to": "BusinessProcess", "means": "module owns the process"},
    "HAS_FORM": {"from": "Module", "to": "Form|UserControl", "means": "module owns the form"},
    "HAS_CONCEPT": {"from": "Module", "to": "BusinessConcept", "means": "module owns the concept"},
    "HAS_STEP": {"from": "BusinessProcess", "to": "Form", "means": "process step performed in the form; props order, step, status"},
    "LEADS_TO": {"from": "BusinessProcess", "to": "BusinessProcess", "means": "downstream process"},
    "INVOLVES": {"from": "BusinessProcess", "to": "BusinessConcept", "means": "concepts used by the process"},
    "MANAGES": {"from": "Form|UserControl", "to": "BusinessConcept", "means": "form creates/maintains this concept (its master)"},
    "USES_CONCEPT": {"from": "Form|UserControl", "to": "BusinessConcept", "means": "form references / looks up this concept"},
    "PARENT_OF": {"from": "BusinessConcept", "to": "BusinessConcept", "means": "classification hierarchy (Category > Group > Sub Group > Item)"},
    "RELATED_TO": {"from": "BusinessConcept", "to": "BusinessConcept", "means": "domain relationship; prop how"},
    "PERSISTED_IN": {"from": "BusinessConcept", "to": "Table", "means": "tables storing the concept", "derived": True},
    "APPLIES_TO": {"from": "BusinessRule", "to": "Form|UserControl|BusinessConcept", "means": "scope of the rule"},
    "IMPLEMENTED_BY": {"from": "BusinessRule", "to": "StoredProcedure|FormMethod|Table|Column", "means": "where the rule is enforced"},
    "GOVERNS": {"from": "BusinessRule", "to": "BusinessProcess", "means": "process governed by the rule"},
    "HAS_CONTROL": {"from": "Form|UserControl", "to": "Control", "means": "control on the form"},
    "LABELS": {"from": "Control", "to": "Control", "means": "label control captioning an input control"},
    "EMBEDS": {"from": "Form", "to": "UserControl", "means": "form hosts the user control"},
    "HAS_METHOD": {"from": "Form|UserControl|DTClass|DAClass", "to": "FormMethod|DTMethod|DAMethod", "means": "method of the class"},
    "HANDLES": {"from": "FormMethod", "to": "Control|Form|UserControl", "means": "event handler; prop event"},
    "CALLS": {"from": "FormMethod", "to": "FormMethod", "means": "method call (incl. into an embedded user control)"},
    "REFERENCES": {"from": "FormMethod", "to": "Control", "means": "method reads/writes the control"},
    "INVOKES": {"from": "FormMethod", "to": "DTMethod", "means": "form method calls DT method (data-layer entry)"},
    "SETS": {"from": "FormMethod", "to": "DTProperty", "means": "method assigns the DT property; props expr, grid_column"},
    "BINDS_TO": {"from": "Control", "to": "DTProperty", "means": "control value is copied into the DT property; props expr, method"},
    "HAS_PROPERTY": {"from": "DTClass", "to": "DTProperty", "means": "property of the DT class"},
    "DELEGATES_TO": {"from": "DTMethod", "to": "DAMethod", "means": "DT method calls DA method"},
    "PASSES": {"from": "DAMethod", "to": "DTProperty", "means": "DA method sends the DT property as SP parameter `param` (the SP it executes is the EXECUTES target)"},
    "EXECUTES": {"from": "DAMethod", "to": "StoredProcedure", "means": "DA method executes the SP"},
    "READS": {"from": "StoredProcedure", "to": "Table", "means": "SP reads the table"},
    "WRITES": {"from": "StoredProcedure", "to": "Table", "means": "SP inserts/updates/deletes; props ops, error_handling (CATCH-block error log)"},
    "USES_COLUMN": {"from": "StoredProcedure", "to": "Column", "means": "SP reads/writes the column; props ops, inferred"},
    "HAS_COLUMN": {"from": "Table", "to": "Column", "means": "column of the table"},
    "CALLS_SP": {"from": "Form|UserControl|StoredProcedure", "to": "StoredProcedure",
                 "means": "shortcut Form->...->SP (props methods); or SP EXEC of another SP", "derived": True},
    "DYNAMIC_EXEC": {"from": "StoredProcedure", "to": "Table", "means": "SP executes dynamic SQL whose procedure name is looked up in this table"},
    "USES_TABLE": {"from": "Form|UserControl", "to": "Table", "means": "shortcut: tables touched through the form's SPs; prop ops [read, write]", "derived": True},
    "SHARES_TABLE": {"from": "Form|UserControl", "to": "Form|UserControl",
                     "means": "shortcut: forms touching common tables; props tables, write_conflict, conflict_tables (treat as undirected)", "derived": True},
}

STRATEGIES = [
    {"name": "functional top-down",
     "path": "Module -HAS_PROCESS-> BusinessProcess -HAS_STEP-> Form -MANAGES/USES_CONCEPT-> BusinessConcept <-APPLIES_TO- BusinessRule",
     "use_for": "what a process/form does, who uses it, which rules apply"},
    {"name": "technical drill-down",
     "path": "Form -HAS_METHOD-> FormMethod -CALLS-> FormMethod -INVOKES-> DTMethod -DELEGATES_TO-> DAMethod -EXECUTES-> StoredProcedure -WRITES/READS-> Table -HAS_COLUMN-> Column",
     "use_for": "what happens on Save/Load/Delete, which SQL runs"},
    {"name": "field lineage",
     "path": "Control -BINDS_TO-> DTProperty <-PASSES {param}- DAMethod -EXECUTES-> StoredProcedure -WRITES-> Table -HAS_COLUMN-> Column",
     "use_for": "where a screen field is saved"},
    {"name": "impact analysis (bottom-up)",
     "path": "Column <-USES_COLUMN- StoredProcedure <-EXECUTES- DAMethod <-DELEGATES_TO- DTMethod <-INVOKES- FormMethod <-HAS_METHOD- Form <-HAS_STEP- BusinessProcess (shortcut: Table <-USES_TABLE- Form)",
     "use_for": "what breaks if a table/column/SP changes"},
    {"name": "lateral",
     "path": "Form -SHARES_TABLE- Form ; Form -USES_TABLE-> Table <-USES_TABLE- Form ; Form -EMBEDS-> UserControl <-EMBEDS- Form ; BusinessConcept -RELATED_TO- BusinessConcept",
     "use_for": "how forms relate / conflict"},
    {"name": "semantic jump",
     "path": "similar(id) or search(query, labels=[...])",
     "use_for": "no edge connects what you need, or you need an entry point"},
]

TIPS = [
    "Start with search() to get entry ids, read hop_hints, then expand() only the relationship types you need.",
    "Derived shortcut edges (derived=true) skip long chains; walk the full chain only when you need the code-level detail.",
    "Use get_node(id, detail='code') only for nodes whose code you must read; summaries are usually enough to decide the next hop.",
    "Forms with status=planned are placeholders for screens not built yet; they carry process context but no code.",
    "SQL ids are lowercase: table:masterdata.munitmaster, sp:masterdata.mmumsave, column:masterdata.munitmaster.unitname. SP parameters are a property of the SP, not nodes.",
    "WRITES edges with error_handling=true are CATCH-block error logging, not business writes.",
]


def instructions_text() -> str:
    lines = [
        "SpectrumERP knowledge graph (Material Management + Plant Maintenance).",
        "Agentic RAG: you choose the entry points and hops. Tools are small graph primitives:",
        "describe_graph (full map), search (entry points), get_node, expand (1 hop, batch), find_paths, similar, run_cypher (read-only).",
        "Layers: functional (Module, BusinessProcess, BusinessConcept, BusinessRule) -> Form/UserControl -> code (FormMethod, Control, DT*, DA*) -> data (StoredProcedure, Table, Column).",
        "Strategies:",
    ]
    lines += [f"- {s['name']}: {s['path']}" for s in STRATEGIES]
    lines += ["Tips:"] + [f"- {t}" for t in TIPS]
    return "\n".join(lines)
````

#### `KnowledgeGraph/src/spectrum_kg/extract/__init__.py`

````python
(empty file - create it with no content)
````

#### `KnowledgeGraph/src/spectrum_kg/extract/bundle.py`

````python
"""Discover form bundles (one folder per form: Form/, DataLayer/, StoredProcedures/, user controls...)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from ..config import Settings


@dataclass
class Bundle:
    name: str
    root: Path
    code_files: list[Path] = field(default_factory=list)   # .vb / .cs
    sql_files: list[Path] = field(default_factory=list)
    contents_md: Path | None = None

    def rel(self, p: Path, source_root: Path) -> str:
        return p.relative_to(source_root).as_posix()


def discover_bundles(settings: Settings) -> list[Bundle]:
    root = settings.source_root
    excluded = {e.lower() for e in settings.exclude}
    if settings.bundles == "auto":
        candidates = [
            d for d in sorted(root.iterdir())
            if d.is_dir() and d.name.lower() not in excluded and not d.name.startswith(".")
            and ((d / "CONTENTS.md").exists() or (d / "Form").is_dir() or (d / "StoredProcedures").is_dir())
        ]
    else:
        candidates = [root / b for b in settings.bundles]

    bundles: list[Bundle] = []
    for d in candidates:
        b = Bundle(name=d.name, root=d, contents_md=(d / "CONTENTS.md") if (d / "CONTENTS.md").exists() else None)
        for p in sorted(d.rglob("*")):
            if any(part.lower() in {"bin", "obj"} for part in p.parts):
                continue
            suffix = p.suffix.lower()
            if suffix in {".vb", ".cs"}:
                b.code_files.append(p)
            elif suffix == ".sql":
                b.sql_files.append(p)
        bundles.append(b)
    return bundles


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
````

#### `KnowledgeGraph/src/spectrum_kg/extract/roslyn.py`

````python
"""Run the .NET Roslyn extractor (tools/RoslynExtractor) and return syntax facts for .vb/.cs files.

Results are cached per file content hash in .cache/roslyn so unchanged files are not re-parsed.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ..config import Settings
from .bundle import file_sha


def ensure_extractor(settings: Settings) -> Path:
    exe = settings.roslyn_extractor
    sources = list(settings.roslyn_project.parent.glob("*.cs")) + [settings.roslyn_project]
    stale = not exe.exists() or max(s.stat().st_mtime for s in sources) > exe.stat().st_mtime
    if stale:
        subprocess.run(
            ["dotnet", "build", str(settings.roslyn_project), "-c", "Release", "-o", str(exe.parent), "-nologo", "-v", "q"],
            check=True,
        )
    return exe


def extract_code_facts(settings: Settings, files: list[Path]) -> dict[Path, dict[str, Any]]:
    cache_dir = settings.cache_dir / "roslyn"
    cache_dir.mkdir(parents=True, exist_ok=True)
    result: dict[Path, dict[str, Any]] = {}
    todo: list[tuple[Path, Path]] = []
    for f in files:
        cached = cache_dir / f"{file_sha(f)}.{f.suffix.lstrip('.').lower()}.json"
        if cached.exists():
            facts = json.loads(cached.read_text(encoding="utf-8"))
            facts["path"] = str(f)
            result[f] = facts
        else:
            todo.append((f, cached))

    if todo:
        exe = ensure_extractor(settings)
        out = cache_dir / "_batch.json"
        subprocess.run([str(exe), "--out", str(out), *[str(f) for f, _ in todo]], check=True, capture_output=True)
        by_path = {Path(item["path"]).resolve(): item for item in json.loads(out.read_text(encoding="utf-8"))}
        out.unlink(missing_ok=True)
        for f, cached in todo:
            facts = by_path[f.resolve()]
            if facts.get("language") == "error":
                raise RuntimeError(f"Roslyn failed on {f}: {facts.get('diagnostics')}")
            cached.write_text(json.dumps(facts), encoding="utf-8")
            result[f] = facts
    return result
````

#### `KnowledgeGraph/src/spectrum_kg/extract/code.py`

````python
"""Interpret Roslyn syntax facts (VB.NET + C#) into graph nodes/edges.

Roles are detected from code shape, not folder names, so new bundles with different layouts still work:
  DAO  - class whose fields are string constants holding SP names ("schema.Proc") / parameter names ("@X")
  DA   - class whose methods call an exec method (ExecuteProc ...) on the base helper
  DT   - class whose methods instantiate a DA class (Active-Record style transfer object)
  UI   - Form / UserControl (base type, or has InitializeComponent)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import model as M
from ..model import Graph

SP_LITERAL_RE = re.compile(r'^"?\s*(\[?[A-Za-z_]\w*\]?\s*\.\s*\[?[A-Za-z_]\w*\]?)\s*"?$')
PARAM_LITERAL_RE = re.compile(r'^"(@\w+)"$')
IDENT_RE = re.compile(r"[A-Za-z_]\w*")
GRID_COL_RE = re.compile(r'(?:Columns|Cells|GetCellValue|Item)\s*[\(\[]\s*"([^"]+)"|\w+\s*\(\s*"([^"]+)"\s*\)')
SELF_RECEIVERS = {None, "", "Me", "this", "MyBase", "MyClass", "base"}
LABEL_PREFIX_RE = re.compile(r"^([a-z]+)(?=[A-Z0-9])")


def last_segment(type_name: str) -> str:
    t = re.sub(r"\(.*$", "", type_name or "").strip()
    return t.split(".")[-1]


def strip_self(expr: str) -> str:
    for p in ("Me.", "this.", "MyBase."):
        if expr.startswith(p):
            return expr[len(p):]
    return expr


def literal(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('""', '"')
    return None


def clean_label(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)  # formatted link labels
    return re.sub(r"\s+", " ", text.replace("&", "")).strip().rstrip(":").strip()


@dataclass
class TypeInfo:
    name: str
    kind: str
    namespace: str
    bundles: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    fields: list[dict] = field(default_factory=list)
    properties: list[dict] = field(default_factory=list)
    methods: list[dict] = field(default_factory=list)
    language: str = ""
    role: str = "other"
    seen_files: set = field(default_factory=set)

    def method(self, name: str) -> dict | None:
        return next((m for m in self.methods if m["name"].lower() == name.lower()), None)


@dataclass
class CodeModel:
    types: dict[str, TypeInfo]
    dao_consts: dict[str, str]           # "DAOUnitMaster.Save" -> "masterdata.MMUMSave"
    da_sp_calls: list[tuple[str, str]]   # (damethod_id, sp qualified)
    param_feeds: list[tuple[str, str, str, str]]  # (damethod_id, dtprop_id, sp qualified, @param)


def collect_types(facts_by_file: dict[Path, dict[str, Any]], file_bundle: dict[Path, str], source_root: Path) -> dict[str, TypeInfo]:
    types: dict[str, TypeInfo] = {}
    for path, facts in facts_by_file.items():
        rel = path.relative_to(source_root).as_posix()
        for t in facts.get("types", []):
            ti = types.get(t["name"])
            if ti is None:
                ti = types[t["name"]] = TypeInfo(t["name"], t["kind"], t.get("namespace", ""), language=facts["language"])
            bundle = file_bundle[path]
            if bundle not in ti.bundles:
                ti.bundles.append(bundle)
            ti.files.append(rel)
            # identical copies of the same file in different bundles (e.g. QCGroup) are merged once
            sig = (Path(rel).name.lower(), len(t.get("methods", [])), len(t.get("fields", [])))
            if sig in ti.seen_files:
                continue
            ti.seen_files.add(sig)
            designer = ".designer." in rel.lower()
            for b in t.get("bases", []):
                if b not in ti.bases:
                    ti.bases.append(b)
            for b in t.get("implements", []):
                if b not in ti.implements:
                    ti.implements.append(b)
            for f in t.get("fields", []):
                ti.fields.append({**f, "file": rel, "designer": designer})
            for p in t.get("properties", []):
                ti.properties.append({**p, "file": rel})
            for m in t.get("methods", []):
                ti.methods.append({**m, "file": rel, "designer": designer})
    return types


def classify(types: dict[str, TypeInfo], settings_ui: dict, settings_dl: dict) -> None:
    exec_methods = set(settings_dl.get("exec_methods", ["ExecuteProc"]))
    form_bases = {last_segment(b) for b in settings_ui.get("form_base_types", ["Form"])}
    uc_bases = {last_segment(b) for b in settings_ui.get("usercontrol_base_types", ["UserControl"])}
    for ti in types.values():
        bases = {last_segment(b) for b in ti.bases}
        if bases & uc_bases:
            ti.role = "UserControl"
        elif bases & form_bases:
            ti.role = "Form"
        elif any(m["name"] == "InitializeComponent" for m in ti.methods):
            ti.role = "Form"
        elif ti.fields and sum(1 for f in ti.fields if literal(f.get("initializer")) and (
                SP_LITERAL_RE.match(f["initializer"]) or PARAM_LITERAL_RE.match(f["initializer"]))) >= max(1, len(ti.fields) // 2):
            ti.role = "DAO"
        elif any(inv["member"] in exec_methods for m in ti.methods for inv in m.get("invocations", [])):
            ti.role = "DA"
    da_names = {n for n, t in types.items() if t.role == "DA"}
    for ti in types.values():
        if ti.role == "other" and any(last_segment(oc) in da_names for m in ti.methods for oc in m.get("objectCreations", [])):
            ti.role = "DT"


def build_code_graph(g: Graph, types: dict[str, TypeInfo], settings_ui: dict, settings_dl: dict, default_schema: str) -> CodeModel:
    classify(types, settings_ui, settings_dl)
    dao_consts: dict[str, str] = {}
    for ti in types.values():
        if ti.role == "DAO":
            for f in ti.fields:
                val = literal(f.get("initializer"))
                if val is not None:
                    dao_consts[f"{ti.name}.{f['name']}"] = val

    cm = CodeModel(types, dao_consts, [], [])
    for ti in types.values():
        if ti.role == "DA":
            _build_da(g, ti, cm, settings_dl, types, default_schema)
    for ti in types.values():
        if ti.role == "DT":
            _build_dt(g, ti, types)
    for ti in types.values():
        if ti.role in ("Form", "UserControl"):
            _build_ui(g, ti, types, cm, settings_ui)
    return cm


# ---------------------------------------------------------------------------------------------
def _sp_name(raw: str, default_schema: str) -> str:
    parts = [p.strip().strip("[]") for p in raw.split(".")]
    return ".".join(parts) if len(parts) > 1 else f"{default_schema}.{parts[0]}"


def _build_da(g: Graph, ti: TypeInfo, cm: CodeModel, settings_dl: dict, types: dict[str, TypeInfo], default_schema: str) -> None:
    exec_methods = set(settings_dl.get("exec_methods", ["ExecuteProc"]))
    add_methods = set(settings_dl.get("param_add_methods", ["Add"]))
    g.add_node(M.daclass_id(ti.name), "DAClass", name=ti.name, namespace=ti.namespace, language=ti.language,
               bundles=ti.bundles, source_files=ti.files)
    for m in ti.methods:
        mid = M.damethod_id(ti.name, m["name"])
        dt_param_types = {p["name"]: last_segment(p["type"]) for p in m.get("parameters", [])}
        g.add_node(mid, "DAMethod", name=f"{ti.name}.{m['name']}", method=m["name"], class_name=ti.name,
                   code=m["code"], file=m["file"], start_line=m["startLine"], end_line=m["endLine"],
                   language=ti.language, bundles=ti.bundles)
        g.add_edge(M.daclass_id(ti.name), "HAS_METHOD", mid)
        sp_q = None
        for inv in m.get("invocations", []):
            if inv["member"] in exec_methods and inv.get("args"):
                arg0 = inv["args"][0].strip()
                raw = cm.dao_consts.get(arg0) or literal(arg0) or arg0
                if SP_LITERAL_RE.match(raw) or SP_LITERAL_RE.match(f'"{raw}"'):
                    sp_q = _sp_name(raw.strip('"'), default_schema)
                    cm.da_sp_calls.append((mid, sp_q))
                    g.add_edge(mid, "EXECUTES", M.sp_id(sp_q), via=arg0, line=inv["line"])
        for inv in m.get("invocations", []):
            if inv["member"] in add_methods and len(inv.get("args", [])) >= 2:
                p_raw = inv["args"][0].strip()
                param = cm.dao_consts.get(p_raw) or literal(p_raw)
                if not param or not param.startswith("@"):
                    continue
                val = inv["args"][1].strip()
                vm = re.match(r"^(\w+)\.(\w+)$", val)
                if vm and vm.group(1) in dt_param_types:
                    dt_cls, prop = dt_param_types[vm.group(1)], vm.group(2)
                    pid = M.dtprop_id(dt_cls, prop)
                    g.add_edge(mid, "PASSES", pid, param=param, line=inv["line"])
                    if sp_q:
                        cm.param_feeds.append((mid, pid, sp_q, param))


def _build_dt(g: Graph, ti: TypeInfo, types: dict[str, TypeInfo]) -> None:
    cid = M.dtclass_id(ti.name)
    g.add_node(cid, "DTClass", name=ti.name, namespace=ti.namespace, language=ti.language,
               bundles=ti.bundles, source_files=ti.files)
    for p in ti.properties:
        pid = M.dtprop_id(ti.name, p["name"])
        g.add_node(pid, "DTProperty", name=f"{ti.name}.{p['name']}", property=p["name"], class_name=ti.name,
                   type=p["type"], backing_field=p.get("backingField"), bundles=ti.bundles)
        g.add_edge(cid, "HAS_PROPERTY", pid)
    da_names = {n for n, t in types.items() if t.role == "DA"}
    for m in ti.methods:
        mid = M.dtmethod_id(ti.name, m["name"])
        g.add_node(mid, "DTMethod", name=f"{ti.name}.{m['name']}", method=m["name"], class_name=ti.name,
                   code=m["code"], file=m["file"], start_line=m["startLine"], end_line=m["endLine"],
                   language=ti.language, bundles=ti.bundles)
        g.add_edge(cid, "HAS_METHOD", mid)
        local_types = {l["name"]: last_segment(l["type"]) for l in m.get("locals", [])}
        for inv in m.get("invocations", []):
            recv = inv.get("receiver") or ""
            da_cls = None
            nm = re.match(r"^\(?\s*new\s+([\w\.]+)\s*\(", recv, re.IGNORECASE)
            if nm and last_segment(nm.group(1)) in da_names:
                da_cls = last_segment(nm.group(1))
            elif recv in local_types and local_types[recv] in da_names:
                da_cls = local_types[recv]
            if da_cls and types[da_cls].method(inv["member"]):
                g.add_edge(mid, "DELEGATES_TO", M.damethod_id(da_cls, types[da_cls].method(inv["member"])["name"]), line=inv["line"])


# ---------------------------------------------------------------------------------------------
def _build_ui(g: Graph, ti: TypeInfo, types: dict[str, TypeInfo], cm: CodeModel, settings_ui: dict) -> None:
    owner = ti.name
    uid = M.ui_id(ti.role, owner)
    init = next((m for m in ti.methods if m["name"] == "InitializeComponent"), None)
    init_assign = init.get("assignments", []) if init else []

    def self_prop(prop: str) -> str | None:
        for a in init_assign:
            if a["left"] in (f"Me.{prop}", f"this.{prop}", prop):
                return literal(a["right"])
        return None

    title = self_prop("Text")
    g.add_node(uid, ti.role, name=owner, title=clean_label(title) if title and title != owner else None,
               sp_prefix=self_prop("Tag"), language=ti.language, namespace=ti.namespace,
               implements=ti.implements, bases=ti.bases, bundles=ti.bundles, source_files=ti.files)

    # ---- controls ----------------------------------------------------------------------------
    ui_names = {n for n, t in types.items() if t.role in ("Form", "UserControl")}
    controls: dict[str, dict[str, Any]] = {}
    for f in ti.fields:
        if not f.get("designer"):
            continue
        ctype = last_segment(f["type"])
        if ctype in ("IContainer", "Container") or f["name"] == "components":
            continue
        controls[f["name"]] = {"name": f["name"], "type": ctype, "full_type": f["type"]}
    if not controls and init:
        for a in init_assign:
            m = re.match(r"^(?:Me\.|this\.)?(\w+)$", a["left"])
            nm = re.match(r"^New\s+([\w\.]+)\(|^new\s+([\w\.]+)\(", a["right"])
            if m and nm:
                controls[m.group(1)] = {"name": m.group(1), "type": last_segment(nm.group(1) or nm.group(2))}

    tabs_by_page: dict[str, dict[str, str]] = {}
    tab_props: dict[str, dict[str, str]] = {}
    for a in init_assign:
        left = strip_self(a["left"])
        parts = left.split(".")
        if len(parts) == 2 and parts[0] in controls:
            c = controls[parts[0]]
            prop, val = parts[1], a["right"]
            if prop in ("Text", "Value", "Tag", "NullText"):
                lit = literal(val)
                if lit is not None:
                    c[prop.lower()] = lit
            elif prop == "MaxLength" and val.isdigit():
                c["max_length"] = int(val)
            elif prop == "Visible":
                c["visible"] = val.lower() != "false"
            elif prop == "Location":
                pm = re.search(r"\((-?\d+)\s*,\s*(-?\d+)\)", val)
                if pm:
                    c["x"], c["y"] = int(pm.group(1)), int(pm.group(2))
            elif prop == "ReadOnly":
                c["read_only"] = val.lower() == "true"
        elif len(parts) == 2 and parts[1] in ("TabPage", "Key", "Text"):
            tp = tab_props.setdefault(parts[0], {})
            tp[parts[1]] = strip_self(a["right"]) if parts[1] == "TabPage" else (literal(a["right"]) or "")
    for tab, p in tab_props.items():
        if "TabPage" in p:
            tabs_by_page[p["TabPage"]] = {"key": p.get("Key", ""), "text": clean_label(p.get("Text", ""))}

    parent_of: dict[str, str] = {}
    for inv in (init.get("invocations", []) if init else []):
        recv = strip_self(inv.get("receiver") or "")
        if inv["member"] in ("Add", "AddRange") and recv.endswith("Controls"):
            parent = recv[: -len("Controls")].rstrip(".") or "__self__"
            parent = strip_self(parent) if parent != "__self__" else parent
            for arg in inv.get("args", []):
                for ident in IDENT_RE.findall(arg):
                    if ident in controls:
                        parent_of[ident] = parent

    def tab_of(name: str) -> dict[str, str] | None:
        seen = set()
        while name in parent_of and name not in seen:
            seen.add(name)
            name = parent_of[name]
            if name in tabs_by_page:
                return tabs_by_page[name]
        return None

    mandatory: set[str] = set()
    mand_methods = set(settings_ui.get("mandatory_methods", []))
    for m in ti.methods:
        for inv in m.get("invocations", []):
            if inv["member"] in mand_methods:
                for arg in inv.get("args", []):
                    mandatory.update(i for i in IDENT_RE.findall(arg) if i in controls)

    # label pairing: name stem, then geometry (same parent, same row, left of control)
    labels = {n: c for n, c in controls.items() if "Label" in c["type"]}
    inputs = {n: c for n, c in controls.items() if n not in labels and not any(
        k in c["type"] for k in ("GroupBox", "Panel", "TabPageControl", "TabControl", "SharedControlsPage", "Button"))}

    def stem(name: str) -> str:
        return LABEL_PREFIX_RE.sub("", name).lower()

    label_for: dict[str, str] = {}
    by_stem = {stem(n): n for n in inputs}
    for ln, lc in labels.items():
        target = by_stem.get(stem(ln))
        if target and target not in label_for:
            label_for[target] = ln
    for ln, lc in labels.items():
        if ln in label_for.values() or "y" not in lc:
            continue
        cands = [n for n, c in inputs.items() if n not in label_for and parent_of.get(n) == parent_of.get(ln)
                 and "y" in c and abs(c["y"] - lc["y"]) <= 8 and c.get("x", 0) > lc.get("x", 0)]
        if cands:
            best = min(cands, key=lambda n: inputs[n]["x"] - lc["x"])
            label_for[best] = ln

    for n, c in controls.items():
        cid = M.control_id(owner, n)
        tab = tab_of(n)
        lbl = label_for.get(n)
        label_text = None
        if lbl:
            label_text = clean_label(controls[lbl].get("text") or controls[lbl].get("value") or "")
        g.add_node(cid, "Control", name=f"{owner}.{n}", control=n, owner=owner, type=c["type"],
                   label=label_text or None, text=clean_label(c.get("text", "")) or None,
                   max_length=c.get("max_length"), visible=c.get("visible"), read_only=c.get("read_only"),
                   mandatory=n in mandatory or None, tab=tab["text"] if tab else None,
                   tab_key=tab["key"] if tab else None, parent=parent_of.get(n) if parent_of.get(n) != "__self__" else None)
        g.add_edge(uid, "HAS_CONTROL", cid)
        if lbl:
            g.add_edge(M.control_id(owner, lbl), "LABELS", cid)
        if c["type"] in ui_names and c["type"] != owner:
            g.add_edge(uid, "EMBEDS", M.ui_id(types[c["type"]].role, c["type"]), control=n)

    # ---- methods -----------------------------------------------------------------------------
    method_names = {m["name"] for m in ti.methods}
    dt_types = {n for n, t in types.items() if t.role == "DT"}
    field_types = {f["name"]: last_segment(f["type"]) for f in ti.fields}

    # event subscriptions wired in the designer (C# +=, VB AddHandler)
    subs: dict[str, list[tuple[str, str]]] = {}
    for m in ti.methods:
        for s in m.get("subscriptions", []):
            subs.setdefault(strip_self(s["handler"]), []).append((strip_self(s["target"]), s["event"]))

    for m in ti.methods:
        if m["name"] == "InitializeComponent" or (m.get("designer") and m["name"] == "Dispose"):
            continue
        mid = M.method_id(owner, m["name"])
        handles = [(h["target"], h["event"]) for h in m.get("handles", [])] + subs.get(m["name"], [])
        kind = "interface" if m.get("implementsMembers") else ("handler" if handles else
                                                                ("constructor" if m["kind"] == "constructor" else "helper"))
        g.add_node(mid, "FormMethod", name=f"{owner}.{m['name']}", method=m["name"], owner=owner, method_kind=kind,
                   implements=m.get("implementsMembers") or None, code=m["code"], file=m["file"],
                   start_line=m["startLine"], end_line=m["endLine"], language=ti.language,
                   comments=m.get("leadingComments") or None, events=[f"{t}.{e}" for t, e in handles] or None)
        g.add_edge(uid, "HAS_METHOD", mid)
        for target, event in handles:
            t = strip_self(target)
            if t in ("MyBase", "Me", "this", "base", "") or t == owner:
                g.add_edge(mid, "HANDLES", uid, event=event)
            elif t in controls:
                g.add_edge(mid, "HANDLES", M.control_id(owner, t), event=event)

        local_types = {l["name"]: last_segment(l["type"]) for l in m.get("locals", [])}
        param_types = {p["name"]: last_segment(p["type"]) for p in m.get("parameters", [])}
        var_types = {**field_types, **param_types, **local_types}
        dt_vars = {v: t for v, t in var_types.items() if t in dt_types}

        def norm_recv(r: str | None) -> str | None:
            return strip_self(r) if r else r

        calls = [(norm_recv(i.get("receiver")), i["member"], i["line"]) for i in m.get("invocations", [])]
        calls += [(norm_recv(a["receiver"]), a["member"], a["line"]) for a in m.get("memberAccesses", [])]
        referenced: set[str] = set()
        for recv, member, line in calls:
            if recv in SELF_RECEIVERS or recv is None:
                if member in method_names and member != m["name"] and member != "InitializeComponent":
                    g.add_edge(mid, "CALLS", M.method_id(owner, member), line=line)
            elif recv in dt_vars:
                dtm = types[dt_vars[recv]].method(member)
                if dtm:
                    g.add_edge(mid, "INVOKES", M.dtmethod_id(dt_vars[recv], dtm["name"]), line=line, via=recv)
            elif recv in controls:
                referenced.add(recv)
                ctype = controls[recv]["type"]
                if ctype in types and types[ctype].role == "UserControl" and types[ctype].method(member):
                    g.add_edge(mid, "CALLS", M.method_id(ctype, types[ctype].method(member)["name"]), line=line, via=recv)
            first = (recv or "").split(".")[0]
            if first in controls:
                referenced.add(first)

        # DT property assignments (control -> DT property)
        for a in m.get("assignments", []):
            left = strip_self(a["left"])
            lm = re.match(r"^(\w+)\.(\w+)$", left)
            if lm and lm.group(1) in dt_vars:
                dt_cls, prop = dt_vars[lm.group(1)], lm.group(2)
                if not any(p["name"] == prop for p in types[dt_cls].properties):
                    continue
                pid = M.dtprop_id(dt_cls, prop)
                right = a["right"]
                gc = GRID_COL_RE.search(right)
                grid_col = (gc.group(1) or gc.group(2)) if gc else None
                g.add_edge(mid, "SETS", pid, expr=right, line=a["line"], grid_column=grid_col)
                for ident in IDENT_RE.findall(right):
                    if ident in controls:
                        g.add_edge(M.control_id(owner, ident), "BINDS_TO", pid, expr=right, method=m["name"], line=a["line"])
            for ident in IDENT_RE.findall(left + " " + a["right"]):
                if ident in controls:
                    referenced.add(ident)
        for c in referenced:
            g.add_edge(mid, "REFERENCES", M.control_id(owner, c))
````

#### `KnowledgeGraph/src/spectrum_kg/extract/tsql.py`

````python
"""T-SQL stored-procedure extractor.

Hybrid approach (CREATE PROCEDURE bodies are not parseable as a whole by sqlglot):
  1. regex: procedure name, parameters, header comments (Author / Create date / Description)
  2. sqlglot tokenizer: split the body into top-level statements, tracking BEGIN/END, CASE/END,
     TRY/CATCH regions and UNION / INSERT..SELECT / UPDATE..SET continuations
  3. sqlglot parser (tsql dialect) per DML statement: tables, aliases, columns, read/write ops.
     Regex fallback when a statement does not parse.
The procedure stays one node: parameters are kept as a property, result sets are not modelled.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.tokens import TokenType

TSQL = sqlglot.Dialect.get_or_raise("tsql")

CREATE_RE = re.compile(
    r"CREATE\s+(?:OR\s+ALTER\s+)?PROC(?:EDURE)?\s+((?:\[[^\]]+\]|\w+)(?:\s*\.\s*(?:\[[^\]]+\]|\w+))?)",
    re.IGNORECASE,
)
HEADER_RE = {
    "author": re.compile(r"--\s*Author\s*:\s*(.+)", re.IGNORECASE),
    "created": re.compile(r"--\s*Create\s*date\s*:\s*(.+)", re.IGNORECASE),
    "description": re.compile(r"--\s*Description\s*:\s*(.+)", re.IGNORECASE),
}
PARAM_RE = re.compile(
    r"(@\w+)\s+(?:AS\s+)?([\w\.]+(?:\s*\(\s*[\w\s,]+\))?)\s*(?:=\s*((?:'[^']*'|[^,\s]+)))?\s*(OUTPUT|OUT|READONLY)?",
    re.IGNORECASE,
)
ASSIGN_SELECT_RE = re.compile(r"^\s*select\s+(?:top\s*\(?\s*\d+\s*\)?\s+)?@\w+\s*=", re.IGNORECASE)
DOUBLE_FROM_DELETE_RE = re.compile(r"^\s*delete\s+from\s+((?:\[[^\]]+\]|\w+)(?:\s*\.\s*(?:\[[^\]]+\]|\w+))?)\s+from\b", re.IGNORECASE)
SPACE_DOT_RE = re.compile(r"(\]|\w)\s+\.\s*(\[|\w)")
EXEC_DYNAMIC_RE = re.compile(r"^\s*exec(?:ute)?\s*\(\s*(@\w+)", re.IGNORECASE)
EXEC_STATIC_RE = re.compile(r"^\s*exec(?:ute)?\s+(?:@\w+\s*=\s*)?((?:\[[^\]]+\]|\w+)(?:\s*\.\s*(?:\[[^\]]+\]|\w+))?)", re.IGNORECASE)
FALLBACK_TABLE_RE = re.compile(
    r"\b(from|join|into|update|delete(?:\s+from)?)\s+((?:\[[^\]]+\]|[A-Za-z_]\w*)(?:\s*\.\s*(?:\[[^\]]+\]|[A-Za-z_]\w*))?)",
    re.IGNORECASE,
)

STATEMENT_STARTS = {
    TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE, TokenType.DECLARE,
    TokenType.SET, TokenType.EXECUTE, TokenType.MERGE, TokenType.TRUNCATE, TokenType.COMMIT,
    TokenType.ROLLBACK, TokenType.ELSE, TokenType.BEGIN, TokenType.END,
}
WORD_STARTS = {"IF", "WHILE", "RETURN", "PRINT", "RAISERROR", "THROW", "EXEC", "EXECUTE", "GOTO", "BREAK", "CONTINUE"}
SET_OPS = {TokenType.UNION, TokenType.EXCEPT, TokenType.INTERSECT, TokenType.ALL, TokenType.DISTINCT}


@dataclass
class ColumnUse:
    table: str | None          # normalised schema.table, None if ambiguous
    column: str
    op: str                    # read | write
    candidates: list[str] = field(default_factory=list)  # for ambiguous columns


@dataclass
class Statement:
    kind: str                  # select | assign | insert | update | delete | declare | set | if | exec | other
    text: str
    line: int
    in_catch: bool = False
    writes: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    columns: list[ColumnUse] = field(default_factory=list)
    exec_target: str | None = None
    dynamic_var: str | None = None
    assigned_vars: list[str] = field(default_factory=list)
    parse_fallback: bool = False


@dataclass
class Parameter:
    name: str
    type: str
    default: str | None
    direction: str = "in"


@dataclass
class StoredProc:
    schema: str
    name: str
    path: Path
    code: str
    author: str | None = None
    created: str | None = None
    description: str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    statements: list[Statement] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    dynamic_sql: bool = False
    table_display: dict[str, str] = field(default_factory=dict)  # norm -> spelling seen

    @property
    def qualified(self) -> str:
        return f"{self.schema}.{self.name}"


def _unbracket(part: str) -> str:
    part = part.strip()
    return part[1:-1] if part.startswith("[") and part.endswith("]") else part


def split_name(raw: str, default_schema: str) -> tuple[str, str]:
    parts = [_unbracket(p) for p in re.split(r"\s*\.\s*", raw.strip())]
    if len(parts) == 1:
        return default_schema, parts[0]
    return parts[-2] or default_schema, parts[-1]


def parse_sp_file(path: Path, default_schema: str = "dbo") -> StoredProc:
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    m = CREATE_RE.search(text)
    if not m:
        raise ValueError(f"no CREATE PROCEDURE in {path}")
    schema, name = split_name(m.group(1), default_schema)
    sp = StoredProc(schema=schema, name=name, path=path, code=text.strip())

    header_text = text[: m.start()]
    for key, rx in HEADER_RE.items():
        hm = rx.search(header_text)
        if hm:
            setattr(sp, key, hm.group(1).strip())

    # parameters: between the name and the first top-level AS keyword
    after = text[m.end():]
    as_m = re.search(r"(?im)^\s*AS\s*$|\)\s*AS\b|\bAS\s*\n|\bAS\s+BEGIN\b", after)
    params_text = after[: as_m.start()] if as_m else ""
    params_text = re.sub(r"--[^\n]*", "", params_text)
    for pm in PARAM_RE.finditer(params_text):
        sp.parameters.append(Parameter(
            name=pm.group(1), type=re.sub(r"\s+", "", pm.group(2)), default=pm.group(3),
            direction="out" if (pm.group(4) or "").upper().startswith("OUT") else "in",
        ))
    body_offset = m.end() + (as_m.end() if as_m else 0)
    body = text[body_offset:]
    body_line0 = text[:body_offset].count("\n") + 1
    sp.statements = list(_split_statements(body, body_line0))
    for st in sp.statements:
        _analyse(st, sp, default_schema)

    for st in sp.statements:
        if st.kind == "exec":
            if st.dynamic_var:
                sp.dynamic_sql = True
            elif st.exec_target:
                sp.calls.append(st.exec_target)
    return sp


# --------------------------------------------------------------------------------------------
# statement splitting
# --------------------------------------------------------------------------------------------
def _split_statements(body: str, line0: int):
    try:
        tokens = TSQL.tokenize(body)
    except Exception:  # pragma: no cover - tokenizer is very permissive
        yield Statement("other", body, line0, parse_fallback=True)
        return

    depth = 0
    case_depth = 0
    in_catch = False
    cur: list = []
    cur_kind: str | None = None
    insert_needs_select = False
    update_seen_set = False

    def flush():
        nonlocal cur, cur_kind, insert_needs_select, update_seen_set
        if cur:
            start, end = cur[0].start, cur[-1].end + 1
            st = Statement(cur_kind or "other", body[start:end].strip(), line0 + body[:start].count("\n"), in_catch)
            cur, cur_kind, insert_needs_select, update_seen_set = [], None, False, False
            return st
        cur, cur_kind = [], None
        return None

    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        tt = tok.token_type
        word = tok.text.upper()
        nxt = tokens[i + 1].text.upper() if i + 1 < n else ""

        if tt == TokenType.L_PAREN:
            depth += 1
        elif tt == TokenType.R_PAREN:
            depth = max(0, depth - 1)

        if depth == 0 and tt == TokenType.CASE:
            case_depth += 1
        elif depth == 0 and tt == TokenType.END and case_depth > 0:
            case_depth -= 1
            cur.append(tok); i += 1
            continue

        if depth == 0 and case_depth == 0:
            if tt == TokenType.SEMICOLON:
                st = flush()
                if st: yield st
                i += 1
                continue
            # control-flow wrappers: BEGIN [TRY|CATCH|TRAN], END [TRY|CATCH], COMMIT/ROLLBACK [TRAN]
            if tt in (TokenType.BEGIN, TokenType.END) or word in ("COMMIT", "ROLLBACK"):
                st = flush()
                if st: yield st
                if tt == TokenType.BEGIN and nxt == "CATCH":
                    in_catch = True
                elif tt == TokenType.END and nxt == "CATCH":
                    in_catch = False
                skip = 2 if nxt in ("TRY", "CATCH", "TRAN", "TRANSACTION") else 1
                i += skip
                continue
            if tt == TokenType.ELSE:
                st = flush()
                if st: yield st
                i += 1
                continue

            starts = tt in STATEMENT_STARTS or (word in WORD_STARTS and tt != TokenType.STRING)
            if word == "WITH" and not cur:
                starts = True
            if starts and cur:
                prev = cur[-1]
                cont = False
                if tt == TokenType.SELECT:
                    if prev.token_type in SET_OPS:
                        cont = True
                    elif cur_kind == "insert" and insert_needs_select:
                        cont = True
                    elif cur_kind == "with":
                        cont = True
                elif tt == TokenType.SET and cur_kind == "update" and not update_seen_set:
                    cont = True
                    update_seen_set = True
                elif cur_kind == "if" and False:
                    cont = True
                if not cont:
                    st = flush()
                    if st: yield st
            if not cur:
                cur_kind = {
                    TokenType.SELECT: "select", TokenType.INSERT: "insert", TokenType.UPDATE: "update",
                    TokenType.DELETE: "delete", TokenType.DECLARE: "declare", TokenType.SET: "set",
                    TokenType.EXECUTE: "exec", TokenType.MERGE: "merge",
                }.get(tt) or {"IF": "if", "WHILE": "if", "EXEC": "exec", "EXECUTE": "exec", "WITH": "with",
                              "RETURN": "other"}.get(word, "other")
                if cur_kind == "insert":
                    insert_needs_select = True
            if cur_kind == "insert" and tt == TokenType.VALUES:
                insert_needs_select = False
            if cur_kind == "if" and cur and tt in STATEMENT_STARTS and tt != TokenType.SELECT:
                pass
        cur.append(tok)
        i += 1

    st = flush()
    if st:
        yield st


# --------------------------------------------------------------------------------------------
# statement analysis
# --------------------------------------------------------------------------------------------
def _prep(sql: str) -> str:
    sql = SPACE_DOT_RE.sub(r"\1.\2", sql)
    dm = DOUBLE_FROM_DELETE_RE.match(sql)
    if dm:
        sql = sql[: dm.start()] + f"DELETE {dm.group(1)} FROM" + sql[dm.end():]
    return sql


def _qualify(t: exp.Table, default_schema: str) -> str | None:
    name = t.name
    if not name or name.startswith("#") or name.startswith("@"):
        return None
    schema = t.db or default_schema
    return f"{schema}.{name}"


def _analyse(st: Statement, sp: StoredProc, default_schema: str) -> None:
    text = _prep(st.text)
    kind = st.kind
    if kind == "select" and ASSIGN_SELECT_RE.match(text):
        kind = st.kind = "assign"
        st.assigned_vars = re.findall(r"(@\w+)\s*=", text.split("from")[0] if "from" in text.lower() else text)

    if kind == "exec":
        dm = EXEC_DYNAMIC_RE.match(text)
        if dm:
            st.dynamic_var = dm.group(1)
        else:
            sm = EXEC_STATIC_RE.match(text)
            if sm:
                s, n = split_name(sm.group(1), default_schema)
                st.exec_target = f"{s}.{n}"
        return

    sql = text
    if kind == "declare":
        dm = re.match(r"(?is)^\s*declare\s+(@\w+)\s+[^=]*?=\s*(.+)$", text)
        if not dm:
            return
        st.assigned_vars = [dm.group(1)]
        sql = f"SELECT {dm.group(2)}"
    elif kind == "set":
        sm = re.match(r"(?is)^\s*set\s+(@\w+)\s*=\s*(.+)$", text)
        if not sm:
            return
        st.assigned_vars = [sm.group(1)]
        sql = f"SELECT {sm.group(2)}"
    elif kind == "if":
        cond = re.sub(r"(?is)^\s*(if|while)\s+", "", text)
        if "select" not in cond.lower():
            return
        sql = f"SELECT 1 WHERE {cond}"
    elif kind not in ("select", "assign", "insert", "update", "delete", "merge", "with"):
        return

    try:
        tree = sqlglot.parse_one(sql, read="tsql")
    except Exception:
        tree = None
    if tree is None or isinstance(tree, exp.Command):
        _fallback(st, sp, sql, default_schema)
        return

    # alias -> qualified table
    alias_map: dict[str, str] = {}
    real_tables: list[str] = []
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        if t.name.lower() in cte_names:
            continue
        if not t.db and not t.alias and t.name.lower() in alias_map:
            continue
        q = _qualify(t, default_schema)
        if not q:
            continue
        if t.alias:
            alias_map[t.alias.lower()] = q
        if not t.db and not t.alias and isinstance(t.parent, (exp.Update, exp.Delete)):
            # UPDATE alias SET ... / DELETE alias FROM ... -> resolved below
            continue
        alias_map.setdefault(t.name.lower(), q)
        if q not in real_tables:
            real_tables.append(q)
        sp.table_display.setdefault(q.lower(), f"{t.db or default_schema}.{t.name}")

    def resolve(t: exp.Table) -> str | None:
        if not t.db and t.name.lower() in alias_map:
            return alias_map[t.name.lower()]
        return _qualify(t, default_schema)

    target: str | None = None
    write_cols: list[str] = []
    if isinstance(tree, exp.Insert):
        tgt = tree.this
        if isinstance(tgt, exp.Schema):
            write_cols = [c.name for c in tgt.expressions if isinstance(c, (exp.Identifier, exp.Column))]
            tgt = tgt.this
        if isinstance(tgt, exp.Table):
            target = resolve(tgt)
    elif isinstance(tree, (exp.Update, exp.Delete)):
        if isinstance(tree.this, exp.Table):
            target = resolve(tree.this)
        if isinstance(tree, exp.Update):
            for eq in tree.expressions:
                if isinstance(eq, exp.EQ) and isinstance(eq.this, exp.Column):
                    write_cols.append(eq.this.name)
    elif isinstance(tree, exp.Merge) and isinstance(tree.this, exp.Table):
        target = resolve(tree.this)

    if target:
        st.writes.append(target)
        if target not in real_tables:
            real_tables.insert(0, target)
    st.reads = [t for t in real_tables if t != target or _target_also_read(tree, target, resolve)]
    if isinstance(tree, exp.Delete) and target:
        st.reads = [t for t in st.reads if t != target]

    # columns
    proj_aliases = set()
    for sel in tree.find_all(exp.Select):
        for e in sel.expressions:
            if isinstance(e, exp.Alias):
                proj_aliases.add(e.alias.lower())
    single = real_tables[0] if len(real_tables) == 1 else None
    seen: set[tuple] = set()
    for col_name in write_cols:
        key = (target, col_name.lower(), "write")
        if target and key not in seen:
            seen.add(key)
            st.columns.append(ColumnUse(target, col_name, "write"))
    for c in tree.find_all(exp.Column):
        name = c.name
        if not name or name.startswith("@") or name == "*":
            continue
        if isinstance(tree, exp.Update) and isinstance(c.parent, exp.EQ) and c.parent.this is c and c.parent.parent is tree:
            continue  # SET target column (already recorded as write)
        qual = c.table.lower() if c.table else ""
        if qual:
            tbl = alias_map.get(qual)
            if not tbl:
                continue
            cu = ColumnUse(tbl, name, "read")
        elif name.lower() in proj_aliases and isinstance(c.parent, exp.Ordered):
            continue
        elif single:
            cu = ColumnUse(single, name, "read")
        else:
            cu = ColumnUse(None, name, "read", candidates=list(real_tables))
        key = (cu.table, name.lower(), cu.op)
        if key not in seen:
            seen.add(key)
            st.columns.append(cu)


def _target_also_read(tree: exp.Expression, target: str, resolve) -> bool:
    if isinstance(tree, exp.Insert):
        src = tree.expression
        return bool(src) and any(resolve(t) == target for t in src.find_all(exp.Table))
    return False


def _fallback(st: Statement, sp: StoredProc, sql: str, default_schema: str) -> None:
    st.parse_fallback = True
    for m in FALLBACK_TABLE_RE.finditer(sql):
        kw = m.group(1).lower()
        raw = m.group(2)
        if raw.startswith("@") or raw.startswith("#"):
            continue
        s, n = split_name(raw, default_schema)
        q = f"{s}.{n}"
        if kw in ("into", "update") or kw.startswith("delete"):
            if q not in st.writes:
                st.writes.append(q)
        elif q not in st.reads:
            st.reads.append(q)
````

#### `KnowledgeGraph/src/spectrum_kg/link.py`

````python
"""Turn parsed SPs into graph nodes, resolve cross-layer references and compute derived shortcut edges."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from . import model as M
from .extract.code import CodeModel
from .extract.tsql import StoredProc
from .model import Graph, content_hash, norm


def build_sql_graph(g: Graph, sps: Iterable[tuple[StoredProc, str, str]], error_log_tables: list[str]) -> dict[str, StoredProc]:
    """sps: (parsed SP, bundle name, repo-relative path). Identical SPs in several bundles merge into one node."""
    error_tables = {norm(t) for t in error_log_tables}
    by_q: dict[str, StoredProc] = {}
    hashes: dict[str, set[str]] = defaultdict(set)
    for sp, bundle, rel in sps:
        q = norm(sp.qualified)
        hashes[q].add(content_hash(sp.code))
        sid = M.sp_id(sp.qualified)
        g.add_node(sid, "StoredProcedure", name=sp.qualified, schema=sp.schema, procedure=sp.name, code=sp.code,
                   author=sp.author, created=sp.created, description=sp.description, dynamic_sql=sp.dynamic_sql or None,
                   parameters=[f"{p.name} {p.type}" + (f" = {p.default}" if p.default else "")
                               + (" OUTPUT" if p.direction == "out" else "") for p in sp.parameters],
                   bundles=[bundle], source_files=[rel])
        if q not in by_q:
            g.nodes[sid].props["_param_names"] = [p.name.lower() for p in sp.parameters]
        g.vote_name(sid, sp.qualified)
        if q in by_q:
            continue
        by_q[q] = sp

        assigned_by: dict[str, list[str]] = defaultdict(list)
        for st in sp.statements:
            for v in st.assigned_vars:
                assigned_by[v.lower()].extend(st.reads)
            for t in st.writes:
                _table(g, t, sp)
                err = st.in_catch or norm(t) in error_tables
                g.add_edge(sid, "WRITES", M.table_id(t), ops=[st.kind], error_handling=err or None,
                           lines=[st.line])
            for t in st.reads:
                _table(g, t, sp)
                g.add_edge(sid, "READS", M.table_id(t), lines=[st.line])
            for cu in st.columns:
                if cu.table:
                    _column(g, cu.table, cu.column, sp)
                    g.add_edge(sid, "USES_COLUMN", M.column_id(cu.table, cu.column), ops=[cu.op])
            if st.exec_target:
                g.add_edge(sid, "CALLS_SP", M.sp_id(st.exec_target), line=st.line)
            if st.dynamic_var:
                for t in assigned_by.get(st.dynamic_var.lower(), []):
                    g.add_edge(sid, "DYNAMIC_EXEC", M.table_id(t), variable=st.dynamic_var, line=st.line,
                               note="procedure name looked up at runtime from this table")

    # ambiguous (unqualified, multi-table) columns: attribute when exactly one candidate table has that column
    known = defaultdict(set)
    for n in g.by_label("Column"):
        known[norm(n.props["table"])].add(norm(n.props["column"]))
    for q, sp in by_q.items():
        sid = M.sp_id(sp.qualified)
        unresolved = []
        for st in sp.statements:
            for cu in st.columns:
                if cu.table is None:
                    hits = [t for t in cu.candidates if norm(cu.column) in known[norm(t)]]
                    if len(hits) == 1:
                        g.add_edge(sid, "USES_COLUMN", M.column_id(hits[0], cu.column), ops=[cu.op], inferred=True)
                    else:
                        unresolved.append(f"{cu.column} ({'|'.join(cu.candidates)})")
        if unresolved:
            g.nodes[sid].props["ambiguous_columns"] = sorted(set(unresolved))
        if len(hashes[q]) > 1:
            g.nodes[sid].props["variants"] = len(hashes[q])
    return by_q


def _table(g: Graph, qualified: str, sp: StoredProc) -> None:
    tid = M.table_id(qualified)
    schema, name = qualified.split(".", 1)
    g.add_node(tid, "Table", name=qualified, schema=schema.lower(), table=name)
    g.vote_name(tid, sp.table_display.get(qualified.lower(), qualified))


def _column(g: Graph, table_q: str, col: str, sp: StoredProc) -> None:
    _table(g, table_q, sp)
    cid = M.column_id(table_q, col)
    g.add_node(cid, "Column", name=f"{table_q}.{col}", table=table_q, column=col)
    g.add_edge(M.table_id(table_q), "HAS_COLUMN", cid)


# ---------------------------------------------------------------------------------------------
def resolve_code_to_sql(g: Graph, cm: CodeModel) -> list[str]:
    warnings: list[str] = []
    # SPs referenced by DA code but missing from the bundles -> stub node so the chain is visible
    for damethod, sp_q in cm.da_sp_calls:
        sid = M.sp_id(sp_q)
        if sid not in g.nodes:
            g.add_node(sid, "StoredProcedure", name=sp_q, missing_source=True)
            warnings.append(f"{damethod} executes {sp_q} but no .sql file was found")

    # parameters the data layer sends (DAMethod -PASSES {param}-> DTProperty) vs. parameters the SP declares
    passed: dict[str, set[str]] = defaultdict(set)
    for damethod, dtprop, sp_q, param in cm.param_feeds:
        sid = M.sp_id(sp_q)
        node = g.nodes.get(sid)
        if node is None or node.props.get("missing_source"):
            continue
        if param.lower() in node.props.get("_param_names", []):
            passed[sid].add(param.lower())
        else:
            warnings.append(f"{damethod} passes {param} which {sp_q} does not declare")
    executed = {e.dst for e in g.edges.values() if e.type == "EXECUTES"}
    for n in g.by_label("StoredProcedure"):
        names = n.props.pop("_param_names", [])
        if n.id in executed and names:
            missing = [p for p in n.props.get("parameters", []) if p.split()[0].lower() not in passed[n.id]]
            if missing:
                n.props["params_not_passed"] = [p.split()[0] for p in missing]
    return warnings


# ---------------------------------------------------------------------------------------------
def derive_shortcuts(g: Graph) -> None:
    """Form/UserControl -CALLS_SP-> SP, -USES_TABLE-> Table, Form -SHARES_TABLE-> Form (all derived:true)."""
    out = defaultdict(lambda: defaultdict(list))
    for e in g.edges.values():
        out[e.src][e.type].append(e)

    ui_nodes = [n for n in g.nodes.values() if n.label in ("Form", "UserControl")]
    usage: dict[str, dict[str, set[str]]] = {}
    for ui in ui_nodes:
        sps: dict[str, set[str]] = defaultdict(set)
        for hm in out[ui.id]["HAS_METHOD"]:
            for inv in out[hm.dst]["INVOKES"]:
                for dl in out[inv.dst]["DELEGATES_TO"]:
                    for ex in out[dl.dst]["EXECUTES"]:
                        sps[ex.dst].add(g.nodes[hm.dst].props["method"])
        for sid, methods in sps.items():
            g.add_edge(ui.id, "CALLS_SP", sid, derived=True, methods=sorted(methods))
        tables: dict[str, set[str]] = defaultdict(set)
        for sid in sps:
            for e in out[sid]["READS"]:
                tables[e.dst].add("read")
            for e in out[sid]["WRITES"]:
                if not e.props.get("error_handling"):
                    tables[e.dst].add("write")
        for tid, ops in tables.items():
            g.add_edge(ui.id, "USES_TABLE", tid, derived=True, ops=sorted(ops))
        usage[ui.id] = tables

    ids = sorted(usage)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            common = set(usage[a]) & set(usage[b])
            if not common:
                continue
            conflicts = sorted(g.nodes[t].props["name"] for t in common if "write" in usage[a][t] and "write" in usage[b][t])
            g.add_edge(a, "SHARES_TABLE", b, derived=True, tables=sorted(g.nodes[t].props["name"] for t in common),
                       write_conflict=bool(conflicts), conflict_tables=conflicts or None, count=len(common))
````

#### `KnowledgeGraph/src/spectrum_kg/domain.py`

````python
"""Curated functional layer: modules, business processes, concepts, rules and per-form docs (domain/*.yaml).

References between YAML and the extracted graph use node ids, e.g.
  form:fUnitMaster  usercontrol:QCGroup  sp:masterdata.MMUMSave  table:masterdata.mUnitMaster
  column:masterdata.mItemMaster.FullCode  method:fUnitMaster.SaveMain  concept:unit-of-measure
SQL ids are matched case-insensitively. Every reference is validated; unknown ids are reported as errors.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import model as M
from .model import Graph

SQL_PREFIXES = ("sp:", "table:", "column:")


def resolve_ref(g: Graph, ref: str) -> str | None:
    ref = ref.strip()
    if ref.startswith(SQL_PREFIXES):
        prefix, rest = ref.split(":", 1)
        cand = f"{prefix}:{rest.lower()}"
        return cand if cand in g.nodes else None
    if ref in g.nodes:
        return ref
    low = ref.lower()
    return next((k for k in g.nodes if k.lower() == low), None)


def _load_yaml(p: Path) -> Any:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_domain_files(domain_dir: Path) -> dict[str, Any]:
    d: dict[str, Any] = {"modules": [], "concepts": [], "rules": [], "processes": [], "forms": []}
    if not domain_dir.exists():
        return d
    for name in ("modules", "concepts", "rules"):
        p = domain_dir / f"{name}.yaml"
        if p.exists():
            d[name] = _load_yaml(p).get(name, [])
    for p in sorted((domain_dir / "processes").glob("*.yaml")):
        d["processes"].append({**_load_yaml(p), "_file": p.name})
    for p in sorted((domain_dir / "forms").glob("*.yaml")):
        d["forms"].append({**_load_yaml(p), "_file": p.name})
    return d


def _md_list(items: list[Any] | None) -> str:
    return "\n".join(f"- {i}" for i in items or [])


def apply_domain(g: Graph, domain_dir: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    d = load_domain_files(domain_dir)

    def link(src: str, rel: str, ref: str, ctx: str, **props: Any) -> None:
        dst = resolve_ref(g, ref)
        if dst is None:
            errors.append(f"{ctx}: unknown reference '{ref}'")
            return
        g.add_edge(src, rel, dst, **props)

    # ---- modules --------------------------------------------------------------------------
    for m in d["modules"]:
        mid = M.module_id(m["code"])
        g.add_node(mid, "Module", name=m["name"], code=m["code"], summary=m.get("summary"),
                   doc=m.get("description"), status=m.get("status", "active"))

    # ---- concepts -------------------------------------------------------------------------
    for c in d["concepts"]:
        cid = M.concept_id(c["key"])
        g.add_node(cid, "BusinessConcept", name=c["name"], key=c["key"], summary=c.get("summary"),
                   doc=c.get("description"), synonyms=c.get("synonyms"), module=c.get("module"))
        if c.get("module"):
            g.add_edge(M.module_id(c["module"]), "HAS_CONCEPT", cid)
    for c in d["concepts"]:
        cid = M.concept_id(c["key"])
        ctx = f"concepts.yaml:{c['key']}"
        for child in c.get("parent_of", []):
            link(cid, "PARENT_OF", f"concept:{child}", ctx)
        for rel in c.get("related_to", []):
            if isinstance(rel, dict):
                link(cid, "RELATED_TO", f"concept:{rel['concept']}", ctx, how=rel.get("how"))
            else:
                link(cid, "RELATED_TO", f"concept:{rel}", ctx)
        for t in c.get("tables", []):
            link(cid, "PERSISTED_IN", t if t.startswith("table:") else f"table:{t}", ctx, derived=True)

    # ---- forms (docs attach to extracted Form / UserControl nodes) ---------------------------
    documented: set[str] = set()
    for f in d["forms"]:
        ref = f"form:{f['form']}" if "form" in f else f"usercontrol:{f['usercontrol']}"
        fid = resolve_ref(g, ref)
        ctx = f"forms/{f['_file']}"
        if fid is None:
            if f.get("status") == "planned":
                fid = ref
                g.add_node(fid, "Form", name=f.get("form") or f.get("usercontrol"), status="planned")
            else:
                errors.append(f"{ctx}: no extracted {ref} (set status: planned for forms not built yet)")
                continue
        documented.add(fid)
        node = g.nodes[fid]
        doc_parts = [f.get("purpose", "").strip()]
        if f.get("functional_description"):
            doc_parts.append(f["functional_description"].strip())
        if f.get("actions"):
            doc_parts.append("Actions:\n" + "\n".join(f"- {k}: {v}" for k, v in f["actions"].items()))
        if f.get("validations"):
            doc_parts.append("Validations:\n" + _md_list(f["validations"]))
        if f.get("users"):
            doc_parts.append("Used by: " + ", ".join(f["users"]))
        node.props.update({k: v for k, v in {
            "title": f.get("title") or node.props.get("title"),
            "summary": f.get("summary"),
            "doc": "\n\n".join(p for p in doc_parts if p),
            "module": f.get("module"),
            "form_kind": f.get("kind"),
            "users": f.get("users"),
            "status": f.get("status", node.props.get("status", "active")),
        }.items() if v})
        if f.get("module"):
            link(M.module_id(f["module"]), "HAS_FORM", fid, ctx)
        for c in f.get("manages", []):
            link(fid, "MANAGES", f"concept:{c}", ctx)
        for c in f.get("uses_concepts", []):
            link(fid, "USES_CONCEPT", f"concept:{c}", ctx)
        for method, text in (f.get("method_notes") or {}).items():
            mid = resolve_ref(g, M.method_id(f.get("form") or f.get("usercontrol"), method))
            if mid:
                g.nodes[mid].props["summary"] = text
            else:
                warnings.append(f"{ctx}: method_notes refers to unknown method {method}")

    for n in g.nodes.values():
        if n.label in ("Form", "UserControl") and n.id not in documented:
            warnings.append(f"{n.id} has no curated doc in domain/forms/ (run: kg scaffold-doc {n.name})")

    # ---- processes ------------------------------------------------------------------------
    for p in d["processes"]:
        pid = M.process_id(p["key"])
        ctx = f"processes/{p['_file']}"
        steps = p.get("steps", [])
        step_text = "\n".join(
            f"{s.get('order', i + 1)}. {s['name']}" + (f" ({s['form']})" if s.get("form") else "")
            + (" [planned]" if s.get("status") == "planned" else "") + (f": {s['description']}" if s.get("description") else "")
            for i, s in enumerate(steps))
        g.add_node(pid, "BusinessProcess", name=p["name"], key=p["key"], summary=p.get("summary"),
                   doc="\n\n".join(x for x in [p.get("description", "").strip(), "Steps:\n" + step_text if steps else ""] if x),
                   module=p.get("module"), status=p.get("status", "active"))
        if p.get("module"):
            link(M.module_id(p["module"]), "HAS_PROCESS", pid, ctx)
        for i, s in enumerate(steps):
            if not s.get("form"):
                continue
            fref = s["form"] if ":" in s["form"] else f"form:{s['form']}"
            fid = resolve_ref(g, fref)
            if fid is None:
                if s.get("status") == "planned":
                    fid = fref
                    g.add_node(fid, "Form", name=fref.split(":", 1)[1], title=s.get("name"), status="planned",
                               summary=s.get("description"), module=p.get("module"))
                    if p.get("module"):
                        g.add_edge(M.module_id(p["module"]), "HAS_FORM", fid)
                else:
                    errors.append(f"{ctx}: step '{s['name']}' references unknown {fref}")
                    continue
            g.add_edge(pid, "HAS_STEP", fid, order=s.get("order", i + 1), step=s["name"],
                       status=s.get("status", "active"), description=s.get("description"))
        for c in p.get("concepts", []):
            link(pid, "INVOLVES", f"concept:{c}", ctx)
    for p in d["processes"]:
        for nxt in p.get("leads_to", []):
            link(M.process_id(p["key"]), "LEADS_TO", f"process:{nxt}", f"processes/{p['_file']}")

    # ---- rules ----------------------------------------------------------------------------
    for r in d["rules"]:
        rid = M.rule_id(r["key"])
        ctx = f"rules.yaml:{r['key']}"
        g.add_node(rid, "BusinessRule", name=r["name"], key=r["key"], summary=r.get("summary"),
                   doc=r.get("description"), rule_type=r.get("type"))
        for ref in r.get("applies_to", []):
            link(rid, "APPLIES_TO", ref, ctx)
        for ref in r.get("implemented_by", []):
            link(rid, "IMPLEMENTED_BY", ref, ctx)
        for ref in r.get("processes", []):
            link(rid, "GOVERNS", f"process:{ref}" if ":" not in ref else ref, ctx)

    warnings += coverage_warnings(g, d)
    return warnings, errors


EVIDENCE_LINES = ("Evidence: code", "Evidence: code + ERP domain (inferred)", "Evidence: ERP domain (inferred)")


def coverage_warnings(g: Graph, d: dict[str, Any]) -> list[str]:
    """Functional-layer quality checks (GRAPH_STRUCTURE.md §5.1 / §6.2 checks 9-10)."""
    out: list[str] = []
    for kind, items, keyf in (("concept", d["concepts"], "key"), ("rule", d["rules"], "key"),
                              ("process", d["processes"], "key")):
        for it in items:
            first = (it.get("description") or "").strip().splitlines()[:1]
            if not first or first[0].strip() not in EVIDENCE_LINES:
                out.append(f"{kind} {it[keyf]}: description must start with one of {list(EVIDENCE_LINES)}")
    rule_targets = {e.dst for e in g.edges.values() if e.type == "APPLIES_TO"}
    for n in g.nodes.values():
        if n.label in ("Form", "UserControl") and n.props.get("status") != "planned" and n.id not in rule_targets:
            out.append(f"{n.id}: no business rule APPLIES_TO it")
    governed = {e.dst for e in g.edges.values() if e.type == "GOVERNS"}
    for n in g.by_label("BusinessProcess"):
        if n.id not in governed:
            out.append(f"{n.id}: no business rule GOVERNS it")
    rule_text = "\n".join((r.get("description") or "") + " " + (r.get("summary") or "") for r in d["rules"]).lower()
    for f in d["forms"]:
        for msg in f.get("validations", []) or []:
            core = msg.strip().strip('"').rstrip(".").lower()
            if core and core not in rule_text:
                out.append(f"forms/{f['_file']}: validation message not quoted in any rule: \"{msg}\"")
    # grounding: functional nodes must trace back to the forms in scope
    real_ui = {n.id for n in g.nodes.values() if n.label in ("Form", "UserControl") and n.props.get("status") != "planned"}
    used_tables = {e.dst for e in g.edges.values() if e.type == "USES_TABLE" and e.src in real_ui}
    grounded_concepts = {e.dst for e in g.edges.values()
                         if (e.type in ("MANAGES", "USES_CONCEPT") and e.src in real_ui)
                         or (e.type == "PERSISTED_IN" and e.dst in used_tables)}
    grounded_concepts |= {e.src for e in g.edges.values() if e.type == "PERSISTED_IN" and e.dst in used_tables}
    for n in g.by_label("BusinessConcept"):
        if n.id not in grounded_concepts:
            out.append(f"{n.id}: not grounded - no in-scope form manages/uses it and none of its tables is used by one")
    # a process is grounded if an in-scope form is one of its steps, or - one hop only - it directly follows such a
    # process (LEADS_TO) and involves a grounded concept (e.g. Payment Flow after Procure-to-Pay)
    direct = {n.id for n in g.by_label("BusinessProcess") if any(e.dst in real_ui for e in g.out(n.id, "HAS_STEP"))}
    for n in g.by_label("BusinessProcess"):
        if n.id in direct:
            continue
        follows = any(e.src in direct for e in g.inc(n.id, "LEADS_TO"))
        involves = any(e.dst in grounded_concepts for e in g.out(n.id, "INVOLVES"))
        if not (follows and involves):
            out.append(f"{n.id}: not grounded - no in-scope form step, and it does not directly follow a grounded "
                       f"process while involving a grounded concept")
    for n in g.by_label("BusinessRule"):
        if not any(e.dst in real_ui or e.dst in grounded_concepts for e in g.out(n.id, "APPLIES_TO")):
            out.append(f"{n.id}: not grounded - applies to no in-scope form or grounded concept")
    applies = {}
    for e in g.edges.values():
        if e.type == "APPLIES_TO" and g.nodes.get(e.src, None) and g.nodes[e.src].props.get("rule_type") == "integrity":
            applies.setdefault(e.src, set()).add(e.dst)
    for e in g.edges.values():
        if e.type == "SHARES_TABLE" and e.props.get("write_conflict"):
            if not any({e.src, e.dst} <= targets for targets in applies.values()):
                out.append(f"{e.src} / {e.dst} write {e.props.get('conflict_tables')} but no integrity rule applies to both")
    return out
````

#### `KnowledgeGraph/src/spectrum_kg/embed.py`

````python
"""Text for search/embedding per node (role + graph context + doc/code) and the Voyage AI embedder."""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from .model import Graph, Node

CODE_CHARS = 6000          # code included in embedded text (full code stays in the `code` property)
DOC_CHARS = 4000


class _Index:
    def __init__(self, g: Graph):
        self.g = g
        self.out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.inc: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for e in g.edges.values():
            self.out[e.src][e.type].append(e)
            self.inc[e.dst][e.type].append(e)

    def names(self, edges: list, end: str = "dst", limit: int = 12) -> str:
        vals = []
        for e in edges:
            n = self.g.nodes.get(getattr(e, end))
            if n:
                vals.append(n.props.get("title") or n.props.get("name", n.id))
        vals = sorted(set(vals))
        more = f" (+{len(vals) - limit} more)" if len(vals) > limit else ""
        return ", ".join(vals[:limit]) + more

    def owner_title(self, owner: str) -> str:
        for pid in (f"form:{owner}", f"usercontrol:{owner}"):
            n = self.g.nodes.get(pid)
            if n:
                t = n.props.get("title")
                return f"{owner} ({t})" if t and t != owner else owner
        return owner


def assign_modules(g: Graph, ix: "_Index") -> None:
    """Stamp `modules` on every node (from its form / the forms that reach it) so search can filter by module."""
    mods: dict[str, set[str]] = defaultdict(set)
    for n in g.nodes.values():
        if n.props.get("module"):
            mods[n.id].add(n.props["module"])
        if n.label == "Module":
            mods[n.id].add(n.props["code"])
    for n in g.nodes.values():
        if n.label in ("FormMethod", "Control"):
            for pid in (f"form:{n.props['owner']}", f"usercontrol:{n.props['owner']}"):
                mods[n.id] |= mods.get(pid, set())
    for e in g.edges.values():
        if e.type in ("CALLS_SP", "USES_TABLE"):
            mods[e.dst] |= mods.get(e.src, set())
    # SP -> params/result sets; table -> columns; DA/DT methods -> via EXECUTES / DELEGATES_TO
    for _ in range(2):
        for e in g.edges.values():
            if e.type in ("HAS_PARAM", "RETURNS", "HAS_COLUMN"):
                mods[e.dst] |= mods[e.src]
            elif e.type in ("EXECUTES", "DELEGATES_TO"):
                mods[e.src] |= mods[e.dst]
            elif e.type in ("HAS_METHOD", "HAS_PROPERTY") and g.nodes[e.src].label in ("DTClass", "DAClass"):
                mods[e.src] |= mods[e.dst]
                mods[e.dst] |= mods[e.src]
    for nid, m in mods.items():
        if m and nid in g.nodes:
            g.nodes[nid].props["modules"] = sorted(m)


def enrich(g: Graph) -> None:
    """Set `summary` (if missing), `modules`, `kind` and `text` (search/embedding text) on every node."""
    ix = _Index(g)
    assign_modules(g, ix)
    for n in g.nodes.values():
        summary, context = _describe(n, ix)
        if summary and not n.props.get("summary"):
            n.props["summary"] = summary
        body = n.props.get("doc") or ""
        code = n.props.get("code") or ""
        parts = [f"[{n.label}] {n.props.get('title') or n.props.get('name', n.id)}"]
        if n.props.get("synonyms"):
            parts.append("Also known as: " + ", ".join(n.props["synonyms"]))
        if n.props.get("summary"):
            parts.append(n.props["summary"])
        parts += [c for c in context if c and not re.fullmatch(r"[^:]*:\s*(;[^:]*:\s*)?", c)]
        if body:
            parts.append(body[:DOC_CHARS])
        if code:
            parts.append("Code:\n" + code[:CODE_CHARS])
        n.props["text"] = "\n".join(parts)
        n.props["kind"] = n.label


def _describe(n: Node, ix: _Index) -> tuple[str | None, list[str]]:
    p, o, i, L = n.props, ix.out[n.id], ix.inc[n.id], n.label
    if L == "Module":
        return None, [f"Processes: {ix.names(o['HAS_PROCESS'])}", f"Forms: {ix.names(o['HAS_FORM'])}"]
    if L == "BusinessProcess":
        return None, [f"Module: {p.get('module')}", f"Concepts: {ix.names(o['INVOLVES'])}",
                      f"Leads to: {ix.names(o['LEADS_TO'])}", f"Rules: {ix.names(i['GOVERNS'], 'src')}"]
    if L == "BusinessConcept":
        return None, [f"Maintained in forms: {ix.names(i['MANAGES'], 'src')}",
                      f"Used by forms: {ix.names(i['USES_CONCEPT'], 'src')}",
                      f"Part of: {ix.names(i['PARENT_OF'], 'src')}; contains: {ix.names(o['PARENT_OF'])}",
                      f"Stored in tables: {ix.names(o['PERSISTED_IN'])}", f"Rules: {ix.names(i['APPLIES_TO'], 'src')}"]
    if L == "BusinessRule":
        return None, [f"Applies to: {ix.names(o['APPLIES_TO'])}", f"Implemented by: {ix.names(o['IMPLEMENTED_BY'])}"]
    if L in ("Form", "UserControl"):
        steps = ", ".join(sorted({f"{ix.g.nodes[e.src].props['name']} (step {e.props.get('order')})" for e in i["HAS_STEP"]}))
        s = None if p.get("status") != "planned" else f"Planned form (not built yet): {p.get('title') or p['name']}."
        return s, [f"Business processes: {steps}", f"Manages: {ix.names(o['MANAGES'])}",
                   f"Stored procedures: {ix.names(o['CALLS_SP'], limit=20)}",
                   f"Tables: {ix.names([e for e in o['USES_TABLE']], limit=20)}",
                   f"Embeds: {ix.names(o['EMBEDS'])}" if o["EMBEDS"] else "",
                   f"Embedded in: {ix.names(i['EMBEDS'], 'src')}" if i["EMBEDS"] else ""]
    if L == "FormMethod":
        owner = ix.owner_title(p["owner"])
        sps = set()
        for inv in o["INVOKES"]:
            for d in ix.out[inv.dst]["DELEGATES_TO"]:
                for ex in ix.out[d.dst]["EXECUTES"]:
                    sps.add(ix.g.nodes[ex.dst].props["name"])
        ev = f", handles {', '.join(p['events'])}" if p.get("events") else ""
        impl = f", implements {', '.join(p['implements'])}" if p.get("implements") else ""
        s = f"{p.get('method_kind', 'method').capitalize()} method {p['method']} of {owner}{ev}{impl}." + (
            f" Executes: {', '.join(sorted(sps))}." if sps else "")
        return s, [f"Calls: {ix.names(o['CALLS'])}", f"Controls used: {ix.names(o['REFERENCES'], limit=15)}"]
    if L == "Control":
        owner = ix.owner_title(p["owner"])
        bits = [f"{p['type']} '{p['control']}' on {owner}"]
        if p.get("label"): bits.append(f"label '{p['label']}'")
        if p.get("tab"): bits.append(f"tab '{p['tab']}'")
        if p.get("mandatory"): bits.append("mandatory")
        if p.get("max_length"): bits.append(f"max length {p['max_length']}")
        return ", ".join(bits) + ".", [
            f"Saved via: {ix.names(o['BINDS_TO'])}", f"Handled events: {ix.names(i['HANDLES'], 'src')}",
            f"Used in methods: {ix.names(i['REFERENCES'], 'src', limit=15)}"]
    if L in ("DTClass", "DAClass"):
        return f"{'Data-transfer' if L == 'DTClass' else 'Data-access'} class {p['name']}.", [f"Methods: {ix.names(o['HAS_METHOD'], limit=30)}"]
    if L == "DTMethod":
        return f"DT method {p['name']}; called by {ix.names(i['INVOKES'], 'src')}.", [f"Delegates to: {ix.names(o['DELEGATES_TO'])}"]
    if L == "DAMethod":
        return f"DA method {p['name']} executing {ix.names(o['EXECUTES'])}.", [f"Parameters from: {ix.names(o['PASSES'], limit=30)}"]
    if L == "DTProperty":
        return f"Property {p['property']} ({p.get('type')}) of {p['class_name']}.", [
            f"Set from controls: {ix.names(i['BINDS_TO'], 'src')}",
            "Passed as SP parameters: " + ", ".join(sorted({f"{e.props.get('param')} of {ix.names(ix.out[e.src]['EXECUTES'])}"
                                                          for e in i['PASSES']}))]
    if L == "StoredProcedure":
        forms = ix.names(i["CALLS_SP"], "src")
        w = [e for e in o["WRITES"] if not e.props.get("error_handling")]
        s = f"Stored procedure {p['name']}" + (f": {p['description']}" if p.get("description") else "") + (
            f". Called from {forms}." if forms else ".")
        return s, [f"Writes: {ix.names(w, limit=20)}", f"Reads: {ix.names(o['READS'], limit=25)}",
                   f"Parameters: {', '.join(p.get('parameters') or [])}",
                   f"Parameters never sent by the data layer (SQL default applies): {', '.join(p.get('params_not_passed') or [])}",
                   f"Calls procedures: {ix.names(o['CALLS_SP'])}",
                   f"Rules: {ix.names(i['IMPLEMENTED_BY'], 'src')}",
                   f"Author: {p.get('author')}, created {p.get('created')}" if p.get("author") else ""]
    if L == "Table":
        w = [e for e in i["WRITES"] if not e.props.get("error_handling")]
        return f"Table {p['name']}.", [
            f"Business concept: {ix.names(i['PERSISTED_IN'], 'src')}", f"Used by forms: {ix.names(i['USES_TABLE'], 'src')}",
            f"Written by: {ix.names(w, 'src', limit=20)}", f"Read by: {ix.names(i['READS'], 'src', limit=20)}",
            f"Columns: {', '.join(sorted(ix.g.nodes[e.dst].props['column'] for e in o['HAS_COLUMN']))}"]
    if L == "Column":
        return f"Column {p['column']} of table {p['table']}.", [
            f"Used by: {ix.names(i['USES_COLUMN'], 'src', limit=20)}",
            f"Rules: {ix.names(i['IMPLEMENTED_BY'], 'src')}"]
    return None, []


# --------------------------------------------------------------------------------------------
def text_hash(text: str, model: str, dims: int) -> str:
    return hashlib.sha256(f"{model}|{dims}|{text}".encode()).hexdigest()[:24]


class VoyageEmbedderCache:
    """Embeds texts with Voyage AI, caching vectors on disk by (model, dims, text) hash."""

    def __init__(self, api_key: str, model: str, dims: int, cache_dir: Path):
        import os

        import voyageai
        self.client = voyageai.Client(api_key=api_key, max_retries=0)  # retries/pacing handled in _run
        self.model, self.dims = model, dims
        # Per-request token budget and minimum seconds between requests. Defaults suit paid accounts; on the first
        # free-tier rate-limit error (3 RPM / 10K TPM) they switch to 9K tokens per request, one request per minute.
        self.batch_tokens = int(os.getenv("VOYAGE_BATCH_TOKENS", "90000"))
        self.min_interval = float(os.getenv("VOYAGE_MIN_INTERVAL", "0"))
        self._last_call = 0.0
        self._rate_limited = 0
        self.path = cache_dir / f"embeddings-{model}-{dims}.jsonl"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, list[float]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.cache[rec["h"]] = rec["v"]

    def embed_documents(self, texts: list[str], progress=None) -> list[list[float]]:
        hashes = [text_hash(t, self.model, self.dims) for t in texts]
        todo = [(h, t) for h, t in dict(zip(hashes, texts)).items() if h not in self.cache]
        queue = list(todo)
        done = 0
        while queue:
            batch: list[tuple[str, str]] = []
            budget = 0
            while queue and len(batch) < 64:
                est = len(queue[0][1]) // 3 + 1
                if batch and budget + est > self.batch_tokens:
                    break
                batch.append(queue.pop(0))
                budget += est
            if self._run(batch):
                done += len(batch)
                if progress:
                    progress(done, len(todo))
            else:
                queue = batch + queue          # retry with the (now smaller) budget
        return [self.cache[h] for h in hashes]

    def _run(self, batch: list[tuple[str, str]]) -> bool:
        """Embed one request. Returns False after a rate limit (budget/pacing adjusted, caller re-queues)."""
        import voyageai
        wait = self.min_interval - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        try:
            res = self.client.embed([t for _, t in batch], model=self.model, input_type="document",
                                    output_dimension=self.dims, truncation=True)
        except voyageai.error.RateLimitError as ex:
            self._last_call = time.time()
            self._rate_limited += 1
            if self._rate_limited > 60:
                raise
            msg = str(ex)
            if "3 RPM" in msg or "10K TPM" in msg:     # free tier without payment method
                self.batch_tokens = min(self.batch_tokens, 9000)
                self.min_interval = max(self.min_interval, 61.0)
            else:
                self.batch_tokens = max(2000, self.batch_tokens // 2)
                self.min_interval = max(self.min_interval, 20.0)
            return False
        self._last_call = time.time()
        with self.path.open("a", encoding="utf-8") as f:
            for (h, _), v in zip(batch, res.embeddings):
                self.cache[h] = v
                f.write(json.dumps({"h": h, "v": v}) + "\n")
        return True

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed([text], model=self.model, input_type="query", output_dimension=self.dims).embeddings[0]


def node_texts(g: Graph) -> dict[str, str]:
    return {n.id: n.props["text"] for n in g.nodes.values()}


def sanitize(props: dict[str, Any]) -> dict[str, Any]:
    """Neo4j properties: primitives or homogeneous lists only."""
    out: dict[str, Any] = {}
    for k, v in props.items():
        if v is None or v == [] or v == "":
            continue
        if isinstance(v, dict):
            out[k] = json.dumps(v)
        elif isinstance(v, (list, tuple)):
            vals = [x for x in v if x is not None]
            if vals and len({type(x) for x in vals}) > 1:
                vals = [str(x) for x in vals]
            if vals:
                out[k] = list(vals)
        else:
            out[k] = v
    return out
````

#### `KnowledgeGraph/src/spectrum_kg/load.py`

````python
"""Load the in-memory graph into Neo4j (Aura): constraints, vector + fulltext indexes, batched MERGE, prune."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict
from typing import Callable

import neo4j
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index

from .config import Settings
from .embed import sanitize
from .model import Graph
from .schema import LABELS, RELATIONSHIPS

VECTOR_INDEX = "kg_embedding"
FULLTEXT_INDEX = "kg_fulltext"
BASE_LABEL = "Searchable"
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def connect(settings: Settings) -> neo4j.Driver:
    driver = neo4j.GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password),
                                        notifications_min_severity="OFF")
    driver.verify_connectivity()
    return driver


def ensure_schema(driver: neo4j.Driver, settings: Settings) -> None:
    db = settings.neo4j_database
    driver.execute_query(f"CREATE CONSTRAINT kg_id IF NOT EXISTS FOR (n:{BASE_LABEL}) REQUIRE n.id IS UNIQUE", database_=db)
    driver.execute_query(f"CREATE INDEX kg_kind IF NOT EXISTS FOR (n:{BASE_LABEL}) ON (n.kind)", database_=db)
    create_vector_index(driver, VECTOR_INDEX, label=BASE_LABEL, embedding_property="embedding",
                        dimensions=settings.embedding_dims, similarity_fn="cosine", neo4j_database=db)
    create_fulltext_index(driver, FULLTEXT_INDEX, label=BASE_LABEL,
                          node_properties=["name", "title", "summary", "text"], neo4j_database=db)


def load_graph(driver: neo4j.Driver, settings: Settings, g: Graph, embeddings: dict[str, list[float]] | None,
               embedding_hashes: dict[str, str] | None, log: Callable[[str], None] = print, prune: bool = True) -> None:
    db = settings.neo4j_database
    ensure_schema(driver, settings)
    all_labels = sorted(set(LABELS) | {n.label for n in g.nodes.values()})
    remove_labels = ":".join(all_labels)

    by_label: dict[str, list[dict]] = defaultdict(list)
    for n in g.nodes.values():
        row = {"id": n.id, "props": {**sanitize(n.props), "id": n.id}}
        if embeddings and n.id in embeddings:
            row["embedding"] = embeddings[n.id]
            row["embedding_hash"] = embedding_hashes.get(n.id) if embedding_hashes else None
        else:
            row["embedding"] = None
            row["embedding_hash"] = None
        by_label[n.label].append(row)

    for label, rows in by_label.items():
        assert SAFE_NAME.match(label), label
        q = f"""
        UNWIND $rows AS row
        MERGE (n:{BASE_LABEL} {{id: row.id}})
        WITH n, row, n.embedding AS oldEmb, n.embedding_hash AS oldHash
        SET n = row.props
        SET n.embedding = CASE WHEN row.embedding IS NULL THEN oldEmb ELSE row.embedding END,
            n.embedding_hash = CASE WHEN row.embedding IS NULL THEN oldHash ELSE row.embedding_hash END
        REMOVE n:{remove_labels}
        SET n:{label}
        """
        for chunk in _chunks(rows, 200):
            driver.execute_query(q, rows=chunk, database_=db)
        log(f"  nodes {label}: {len(rows)}")

    by_type: dict[str, list[dict]] = defaultdict(list)
    for e in g.edges.values():
        by_type[e.type].append({"src": e.src, "dst": e.dst, "props": sanitize(e.props)})
    for rtype, rows in by_type.items():
        assert SAFE_NAME.match(rtype), rtype
        q = f"""
        UNWIND $rows AS row
        MATCH (a:{BASE_LABEL} {{id: row.src}})
        MATCH (b:{BASE_LABEL} {{id: row.dst}})
        MERGE (a)-[r:{rtype}]->(b)
        SET r = row.props
        """
        for chunk in _chunks(rows, 500):
            driver.execute_query(q, rows=chunk, database_=db)
        log(f"  edges {rtype}: {len(rows)}")

    if prune:
        ids = list(g.nodes)
        res = driver.execute_query(f"MATCH (n:{BASE_LABEL}) WHERE NOT n.id IN $ids DETACH DELETE n RETURN count(*) AS c",
                                   ids=ids, database_=db)
        stale_nodes = res.records[0]["c"]
        removed = 0
        for rtype, rows in by_type.items():
            pairs = [[r["src"], r["dst"]] for r in rows]
            res = driver.execute_query(
                f"MATCH (a:{BASE_LABEL})-[r:{rtype}]->(b:{BASE_LABEL}) WHERE NOT [a.id, b.id] IN $pairs DELETE r RETURN count(*) AS c",
                pairs=pairs, database_=db)
            removed += res.records[0]["c"]
        res = driver.execute_query(
            f"MATCH (:{BASE_LABEL})-[r]->(:{BASE_LABEL}) WHERE NOT type(r) IN $types DELETE r RETURN count(*) AS c",
            types=list(by_type), database_=db)
        removed += res.records[0]["c"]
        log(f"  pruned {stale_nodes} stale nodes, {removed} stale relationships")

    stats = g.stats()
    driver.execute_query(
        "MERGE (m:KGMeta {id: 'meta'}) SET m.built_at = $at, m.stats = $stats, m.embedding_model = $model, "
        "m.embedding_dims = $dims",
        at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), stats=json.dumps(stats),
        model=settings.voyage_model, dims=settings.embedding_dims, database_=db)


def _chunks(rows: list, n: int):
    for i in range(0, len(rows), n):
        yield rows[i:i + n]


def documented_types_check(g: Graph) -> list[str]:
    """Every label / relationship type in the graph must be described in schema.py (for describe_graph)."""
    problems = [f"label {l} missing from schema.LABELS" for l in {n.label for n in g.nodes.values()} - set(LABELS)]
    problems += [f"relationship {t} missing from schema.RELATIONSHIPS" for t in {e.type for e in g.edges.values()} - set(RELATIONSHIPS)]
    return problems
````

#### `KnowledgeGraph/src/spectrum_kg/build.py`

````python
"""Build the full in-memory graph: code + SQL extraction, linking, derived edges, curated domain layer."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import domain, link
from .config import Settings
from .embed import enrich
from .load import documented_types_check
from .extract.bundle import discover_bundles
from .extract.code import build_code_graph, collect_types
from .extract.roslyn import extract_code_facts
from .extract.tsql import parse_sp_file
from .model import Graph


@dataclass
class BuildReport:
    bundles: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_graph(settings: Settings, with_domain: bool = True) -> tuple[Graph, BuildReport]:
    g = Graph()
    report = BuildReport()
    bundles = discover_bundles(settings)
    report.bundles = [b.name for b in bundles]

    code_files = [f for b in bundles for f in b.code_files]
    file_bundle = {f: b.name for b in bundles for f in b.code_files}
    facts = extract_code_facts(settings, code_files)
    types = collect_types(facts, file_bundle, settings.source_root)
    cm = build_code_graph(g, types, settings.ui, settings.datalayer, settings.sql.get("default_schema", "dbo"))

    sps = []
    for b in bundles:
        for f in b.sql_files:
            try:
                sps.append((parse_sp_file(f, settings.sql.get("default_schema", "dbo")), b.name,
                            f.relative_to(settings.source_root).as_posix()))
            except Exception as ex:  # keep building; report the file
                report.errors.append(f"{f}: {ex}")
    link.build_sql_graph(g, sps, settings.sql.get("error_log_tables", []))
    report.warnings += link.resolve_code_to_sql(g, cm)
    g.finalize_names()
    _canonical_schema_names(g)
    link.derive_shortcuts(g)

    if with_domain:
        w, e = domain.apply_domain(g, settings.domain_dir)
        report.warnings += w
        report.errors += e

    for e in g.dangling_edges():
        report.warnings.append(f"dropped dangling edge {e.src} -{e.type}-> {e.dst}")
        del g.edges[e.key]
    enrich(g)
    report.warnings += documented_types_check(g)
    return g, report


def _canonical_schema_names(g: Graph) -> None:
    """Use one spelling per schema (most frequent) in Table/Column/SP display names."""
    from collections import Counter
    votes: dict[str, Counter] = {}
    for n in g.nodes.values():
        if n.label in ("Table", "StoredProcedure") and "." in n.props.get("name", ""):
            schema = n.props["name"].split(".", 1)[0]
            votes.setdefault(schema.lower(), Counter())[schema] += 1
    best = {k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0] == kv[0].lower(), kv[0]))[0][0] for k, v in votes.items()}
    for n in g.nodes.values():
        if n.label in ("Table", "Column", "StoredProcedure") and "." in n.props.get("name", ""):
            schema, rest = n.props["name"].split(".", 1)
            n.props["name"] = f"{best.get(schema.lower(), schema)}.{rest}"
            if n.label == "Column":
                n.props["table"] = f"{best.get(schema.lower(), schema)}.{n.props['table'].split('.', 1)[1]}"
        if n.label == "Table":
            n.props["schema"] = best.get(n.props["schema"], n.props["schema"])
````

#### `KnowledgeGraph/src/spectrum_kg/viz.py`

````python
"""Export the in-memory graph as a standalone interactive HTML network view (vis-network)."""
from __future__ import annotations

import json
from pathlib import Path

from .model import Graph
from .schema import LABELS, RELATIONSHIPS

STYLE = {
    "Module": ("#7c3aed", 34), "BusinessProcess": ("#db2777", 26), "BusinessConcept": ("#ea580c", 18),
    "BusinessRule": ("#ca8a04", 14), "Form": ("#2563eb", 24), "UserControl": ("#0891b2", 20),
    "FormMethod": ("#16a34a", 9), "Control": ("#84cc16", 7), "DTClass": ("#0d9488", 14), "DTMethod": ("#14b8a6", 8),
    "DTProperty": ("#5eead4", 6), "DAClass": ("#047857", 14), "DAMethod": ("#10b981", 8),
    "StoredProcedure": ("#dc2626", 13),
    "Table": ("#475569", 13), "Column": ("#94a3b8", 5),
}
DEFAULT_HIDDEN_LABELS = ["Column", "DTProperty", "Control"]
DEFAULT_HIDDEN_RELS = ["USES_COLUMN", "REFERENCES", "SETS", "PASSES"]
SKIP_PROPS = {"text", "embedding", "embedding_hash", "kind"}


def export_html(g: Graph, path: Path, title: str = "SpectrumERP Knowledge Graph") -> Path:
    nodes = []
    for n in g.nodes.values():
        props = {k: v for k, v in n.props.items() if k not in SKIP_PROPS}
        if isinstance(props.get("code"), str) and len(props["code"]) > 6000:
            props["code"] = props["code"][:6000] + "\n… (truncated)"
        nodes.append({"id": n.id, "label": n.label, "name": n.props.get("title") or n.props.get("name", n.id),
                      "planned": n.props.get("status") == "planned", "props": props})
    edges = [{"from": e.src, "to": e.dst, "type": e.type,
              "props": {k: v for k, v in e.props.items()}} for e in g.edges.values()]
    data = {
        "title": title, "nodes": nodes, "edges": edges, "style": STYLE,
        "layers": {k: v["layer"] for k, v in LABELS.items()},
        "labelMeans": {k: v["means"] for k, v in LABELS.items()},
        "relMeans": {k: v["means"] for k, v in RELATIONSHIPS.items()},
        "derived": [k for k, v in RELATIONSHIPS.items() if v.get("derived")],
        "hiddenLabels": DEFAULT_HIDDEN_LABELS, "hiddenRels": DEFAULT_HIDDEN_RELS,
    }
    payload = json.dumps(data, default=str).replace("</", "<\\/")
    path.write_text(TEMPLATE.replace("__TITLE__", title).replace("__DATA__", payload), encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  :root { --bg:#f8fafc; --panel:#ffffff; --fg:#0f172a; --muted:#64748b; --line:#e2e8f0; --accent:#2563eb; --code:#f1f5f9; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0b1220; --panel:#111827; --fg:#e5e7eb; --muted:#94a3b8; --line:#1f2937; --accent:#60a5fa; --code:#0f172a; } }
  * { box-sizing:border-box; }
  body { margin:0; font:13px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--fg); height:100vh; display:flex; flex-direction:column; }
  header { display:flex; gap:12px; align-items:center; padding:8px 14px; border-bottom:1px solid var(--line); background:var(--panel); flex-wrap:wrap; }
  header h1 { font-size:15px; margin:0 8px 0 0; }
  header input[type=search] { padding:5px 8px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); width:280px; }
  header button { padding:5px 10px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); cursor:pointer; }
  header button:hover { border-color:var(--accent); }
  .stat { color:var(--muted); }
  main { flex:1; display:flex; min-height:0; }
  #side { width:250px; overflow:auto; border-right:1px solid var(--line); background:var(--panel); padding:10px 12px; }
  #side h3 { font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); margin:14px 0 6px; }
  #side label { display:flex; align-items:center; gap:6px; padding:2px 0; cursor:pointer; white-space:nowrap; }
  .dot { width:10px; height:10px; border-radius:50%; flex:none; }
  .cnt { margin-left:auto; color:var(--muted); font-size:11px; }
  #net { flex:1; min-width:0; }
  #detail { width:420px; overflow:auto; border-left:1px solid var(--line); background:var(--panel); padding:12px 14px; }
  #detail h2 { font-size:15px; margin:0 0 2px; word-break:break-word; }
  .pill { display:inline-block; padding:1px 8px; border-radius:10px; color:#fff; font-size:11px; margin-right:4px; }
  .muted { color:var(--muted); }
  table.props { border-collapse:collapse; width:100%; margin-top:8px; }
  table.props td { border-top:1px solid var(--line); padding:3px 4px; vertical-align:top; word-break:break-word; }
  table.props td:first-child { color:var(--muted); width:110px; }
  pre { background:var(--code); padding:8px; border-radius:6px; overflow:auto; max-height:420px; font-size:11.5px; white-space:pre; }
  .doc { white-space:pre-wrap; }
  .nb a { color:var(--accent); cursor:pointer; text-decoration:none; }
  .nb a:hover { text-decoration:underline; }
  .nb li { margin:1px 0; }
  .nb ul { margin:2px 0 8px; padding-left:18px; }
  .hint { color:var(--muted); font-size:12px; }
  @media (max-width: 900px) { #side, #detail { display:none; } }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <input id="q" type="search" list="names" placeholder="Search nodes (name or id)…">
  <datalist id="names"></datalist>
  <button id="fit">Fit</button>
  <button id="all">Show all</button>
  <button id="reset">Default view</button>
  <label class="stat"><input type="checkbox" id="phys" checked> physics</label>
  <span class="stat" id="stat"></span>
</header>
<main>
  <aside id="side"></aside>
  <div id="net"></div>
  <aside id="detail"><p class="hint">Click a node to see its documentation, code and neighbours.<br><br>
    Double-click a node to focus on its neighbourhood (depth set below). Use the toggles on the left to show
    layers and relationship types; dense types (columns, parameters, controls) start hidden.</p>
    <p class="hint">Focus depth: <select id="depth"><option>1</option><option selected>2</option><option>3</option></select></p></aside>
</main>
<script>
const D = __DATA__;
const byId = new Map(D.nodes.map(n => [n.id, n]));
const labels = [...new Set(D.nodes.map(n => n.label))];
const layerOrder = ["functional", "bridge", "code", "data"];
labels.sort((a, b) => layerOrder.indexOf(D.layers[a]) - layerOrder.indexOf(D.layers[b]) || a.localeCompare(b));
const rels = [...new Set(D.edges.map(e => e.type))].sort();
const shownLabels = new Set(labels.filter(l => !D.hiddenLabels.includes(l)));
const shownRels = new Set(rels.filter(r => !D.hiddenRels.includes(r)));
let focusSet = null;

const nodesDS = new vis.DataSet(D.nodes.map(n => {
  const [color, size] = D.style[n.label] || ["#999", 8];
  return { id: n.id, label: ["Module","BusinessProcess","Form","UserControl","BusinessConcept"].includes(n.label) ? n.name : undefined,
           title: `${n.label}: ${n.name}`, size, shape: "dot",
           color: { background: color, border: n.planned ? "#94a3b8" : color, highlight: { background: color, border: "#111" } },
           opacity: n.planned ? 0.45 : 1, shapeProperties: { borderDashes: n.planned ? [4, 3] : false },
           borderWidth: n.planned ? 2 : 1, font: { size: 12, color: getComputedStyle(document.body).color } };
}));
const edgesDS = new vis.DataSet(D.edges.map((e, i) => ({
  id: i, from: e.from, to: e.to, type: e.type, title: e.type, arrows: { to: { enabled: true, scaleFactor: .4 } },
  dashes: D.derived.includes(e.type), color: { color: "rgba(100,116,139,.35)", highlight: "#2563eb" }, width: .6 })));

const nodesView = new vis.DataView(nodesDS, { filter: n => shownLabels.has(byId.get(n.id).label) && (!focusSet || focusSet.has(n.id)) });
const edgesView = new vis.DataView(edgesDS, { filter: e => shownRels.has(e.type) });
const net = new vis.Network(document.getElementById("net"), { nodes: nodesView, edges: edgesView }, {
  physics: { solver: "forceAtlas2Based", forceAtlas2Based: { gravitationalConstant: -45, springLength: 90, avoidOverlap: .3 },
             stabilization: { iterations: 250 } },
  interaction: { hover: true, tooltipDelay: 120, hideEdgesOnDrag: true },
  layout: { improvedLayout: false } });
net.once("stabilizationIterationsDone", () => { net.setOptions({ physics: { enabled: false } }); document.getElementById("phys").checked = false; });

function refresh() { nodesView.refresh(); edgesView.refresh(); stat(); }
function stat() { document.getElementById("stat").textContent = `${nodesView.length} / ${D.nodes.length} nodes · ${edgesView.getIds().length} edges shown` + (focusSet ? " · focus mode" : ""); }

// ---- sidebar toggles ----
const side = document.getElementById("side");
const labelCounts = {}; D.nodes.forEach(n => labelCounts[n.label] = (labelCounts[n.label] || 0) + 1);
const relCounts = {}; D.edges.forEach(e => relCounts[e.type] = (relCounts[e.type] || 0) + 1);
let html = "";
let lastLayer = null;
for (const l of labels) {
  if (D.layers[l] !== lastLayer) { lastLayer = D.layers[l]; html += `<h3>${lastLayer} layer</h3>`; }
  html += `<label title="${(D.labelMeans[l] || "").replace(/"/g, "&quot;")}"><input type="checkbox" data-l="${l}" ${shownLabels.has(l) ? "checked" : ""}>
    <span class="dot" style="background:${(D.style[l] || ["#999"])[0]}"></span>${l}<span class="cnt">${labelCounts[l]}</span></label>`;
}
html += `<h3>relationships <span class="muted">(dashed = derived)</span></h3>`;
for (const r of rels) html += `<label title="${(D.relMeans[r] || "").replace(/"/g, "&quot;")}"><input type="checkbox" data-r="${r}" ${shownRels.has(r) ? "checked" : ""}>${r}<span class="cnt">${relCounts[r]}</span></label>`;
side.innerHTML = html;
side.addEventListener("change", ev => {
  const t = ev.target;
  if (t.dataset.l) t.checked ? shownLabels.add(t.dataset.l) : shownLabels.delete(t.dataset.l);
  if (t.dataset.r) t.checked ? shownRels.add(t.dataset.r) : shownRels.delete(t.dataset.r);
  refresh();
});
function syncChecks() { side.querySelectorAll("input").forEach(i => i.checked = i.dataset.l ? shownLabels.has(i.dataset.l) : shownRels.has(i.dataset.r)); }

// ---- details ----
const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
function showDetail(id) {
  const n = byId.get(id); if (!n) return;
  const color = (D.style[n.label] || ["#999"])[0];
  const p = n.props;
  let h = `<span class="pill" style="background:${color}">${n.label}</span>${n.planned ? '<span class="pill" style="background:#94a3b8">planned</span>' : ""}
    <h2>${esc(n.name)}</h2><div class="muted">${esc(n.id)}</div>`;
  if (p.summary) h += `<p>${esc(p.summary)}</p>`;
  if (p.doc) h += `<div class="doc">${esc(p.doc)}</div>`;
  const rows = Object.entries(p).filter(([k]) => !["summary", "doc", "code", "name", "title"].includes(k));
  if (rows.length) h += `<table class="props">${rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(Array.isArray(v) ? v.join(", ") : v)}</td></tr>`).join("")}</table>`;
  const groups = {};
  D.edges.forEach(e => {
    if (e.from === id) (groups[`${e.type} →`] ||= []).push([e.to, e.props]);
    if (e.to === id) (groups[`← ${e.type}`] ||= []).push([e.from, e.props]);
  });
  h += `<h3 style="margin-top:14px">Neighbours</h3><div class="nb">`;
  for (const [k, list] of Object.entries(groups).sort()) {
    h += `<b>${esc(k)}</b> <span class="muted">(${list.length})</span><ul>` + list.slice(0, 60).map(([oid, ep]) => {
      const o = byId.get(oid); const extra = Object.entries(ep || {}).filter(([kk]) => !["derived", "lines", "line"].includes(kk))
        .map(([kk, vv]) => `${kk}=${Array.isArray(vv) ? vv.join("/") : vv}`).join(", ");
      return `<li><a data-id="${esc(oid)}">${esc(o ? o.name : oid)}</a> <span class="muted">${o ? o.label : ""}${extra ? " · " + esc(extra).slice(0, 120) : ""}</span></li>`;
    }).join("") + (list.length > 60 ? `<li class="muted">… ${list.length - 60} more</li>` : "") + `</ul>`;
  }
  h += `</div>`;
  if (p.code) h += `<h3>Code</h3><pre>${esc(p.code)}</pre>`;
  const det = document.getElementById("detail");
  det.innerHTML = h; det.scrollTop = 0;
}
document.getElementById("detail").addEventListener("click", ev => { const id = ev.target.dataset && ev.target.dataset.id; if (id) goTo(id); });

function goTo(id) {
  const n = byId.get(id); if (!n) return;
  if (!shownLabels.has(n.label)) { shownLabels.add(n.label); syncChecks(); }
  if (focusSet && !focusSet.has(id)) focusSet = null;
  refresh();
  showDetail(id);
  setTimeout(() => { net.selectNodes([id]); net.focus(id, { scale: 1.2, animation: { duration: 400 } }); }, 50);
}
function focusOn(id, depth) {
  const adj = new Map();
  D.edges.forEach(e => { if (!shownRels.has(e.type)) return;
    (adj.get(e.from) || adj.set(e.from, []).get(e.from)).push(e.to);
    (adj.get(e.to) || adj.set(e.to, []).get(e.to)).push(e.from); });
  focusSet = new Set([id]); let frontier = [id];
  for (let d = 0; d < depth; d++) { const next = []; frontier.forEach(x => (adj.get(x) || []).forEach(y => { if (!focusSet.has(y)) { focusSet.add(y); next.push(y); } })); frontier = next; }
  focusSet.forEach(x => shownLabels.add(byId.get(x).label)); syncChecks();
  refresh(); net.setOptions({ physics: { enabled: true } }); document.getElementById("phys").checked = true;
  setTimeout(() => net.fit({ animation: true }), 600);
}
net.on("click", p => { if (p.nodes.length) showDetail(p.nodes[0]); });
net.on("doubleClick", p => { if (p.nodes.length) focusOn(p.nodes[0], +document.getElementById("depth").value); });

// ---- header ----
document.getElementById("names").innerHTML = D.nodes.map(n => `<option value="${esc(n.id)}">${esc(n.name)} (${n.label})</option>`).join("");
document.getElementById("q").addEventListener("change", ev => {
  const v = ev.target.value.trim().toLowerCase(); if (!v) return;
  const hit = byId.get(ev.target.value) || D.nodes.find(n => n.id.toLowerCase() === v || n.name.toLowerCase() === v)
           || D.nodes.find(n => n.name.toLowerCase().includes(v) || n.id.toLowerCase().includes(v));
  if (hit) goTo(hit.id);
});
document.getElementById("fit").onclick = () => net.fit({ animation: true });
document.getElementById("all").onclick = () => { focusSet = null; labels.forEach(l => shownLabels.add(l)); rels.forEach(r => shownRels.add(r)); syncChecks(); refresh(); };
document.getElementById("reset").onclick = () => { focusSet = null; shownLabels.clear(); labels.filter(l => !D.hiddenLabels.includes(l)).forEach(l => shownLabels.add(l));
  shownRels.clear(); rels.filter(r => !D.hiddenRels.includes(r)).forEach(r => shownRels.add(r)); syncChecks(); refresh(); net.fit({ animation: true }); };
document.getElementById("phys").onchange = ev => net.setOptions({ physics: { enabled: ev.target.checked } });
stat();
</script>
</body>
</html>
"""
````

#### `KnowledgeGraph/src/spectrum_kg/cli.py`

````python
"""kg - build / validate / scaffold the SpectrumERP knowledge graph."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

from .build import build_graph
from .config import load_settings

app = typer.Typer(add_completion=False, help="SpectrumERP knowledge graph builder")


def _report(report, show_warnings: bool = True) -> None:
    typer.echo(f"bundles: {', '.join(report.bundles)}")
    if show_warnings:
        for w in report.warnings:
            typer.secho(f"  warning: {w}", fg="yellow")
    for e in report.errors:
        typer.secho(f"  error: {e}", fg="red")


@app.command()
def build(
    dry_run: Optional[Path] = typer.Option(None, "--dry-run", help="Write the graph to this JSON file instead of Neo4j."),
    no_embed: bool = typer.Option(False, "--no-embed", help="Load without (re)computing embeddings."),
    no_prune: bool = typer.Option(False, "--no-prune", help="Keep nodes/edges in Neo4j that are no longer extracted."),
    strict: bool = typer.Option(True, help="Abort when domain YAML has unresolved references."),
):
    """Extract code + SQL, apply curated domain docs, embed with Voyage AI and load into Neo4j."""
    settings = load_settings()
    g, report = build_graph(settings)
    _report(report)
    typer.echo(json.dumps(g.stats(), indent=1))
    if report.errors and strict:
        typer.secho("aborting: fix the errors above (or pass --no-strict)", fg="red")
        raise typer.Exit(1)
    if dry_run:
        dry_run.parent.mkdir(parents=True, exist_ok=True)
        dry_run.write_text(json.dumps(g.to_json(), indent=1, default=str), encoding="utf-8")
        typer.echo(f"wrote {dry_run}")
        return

    embeddings = hashes = None
    if not no_embed:
        from .embed import VoyageEmbedderCache, text_hash
        emb = VoyageEmbedderCache(settings.voyage_api_key, settings.voyage_model, settings.embedding_dims, settings.cache_dir)
        ids = list(g.nodes)
        texts = [g.nodes[i].props["text"] for i in ids]
        typer.echo(f"embedding {len(texts)} nodes with {settings.voyage_model} ({settings.embedding_dims}d)...")
        vecs = emb.embed_documents(texts, progress=lambda d, t: typer.echo(f"  embedded {d}/{t} new texts"))
        embeddings = dict(zip(ids, vecs))
        hashes = {i: text_hash(t, settings.voyage_model, settings.embedding_dims) for i, t in zip(ids, texts)}

    from .load import connect, load_graph
    driver = connect(settings)
    try:
        typer.echo(f"loading into {settings.neo4j_uri} ...")
        load_graph(driver, settings, g, embeddings, hashes, log=typer.echo, prune=not no_prune)
    finally:
        driver.close()
    typer.secho("done", fg="green")


@app.command()
def validate():
    """Build in memory and report unresolved references, undocumented forms and dangling edges."""
    settings = load_settings()
    g, report = build_graph(settings)
    _report(report)
    typer.echo(json.dumps(g.stats(), indent=1))
    if report.errors:
        raise typer.Exit(1)
    typer.secho("valid" if not report.warnings else f"valid with {len(report.warnings)} warnings",
                fg="green" if not report.warnings else "yellow")


@app.command()
def stats():
    """Node / edge counts of the extracted graph (no Neo4j needed)."""
    g, report = build_graph(load_settings())
    typer.echo(json.dumps(g.stats(), indent=1))


@app.command("export-html")
def export_html_cmd(
    out: Path = typer.Option(Path("kg-graph.html"), "--out", "-o", help="Output HTML file."),
):
    """Write the current graph as a standalone interactive network view (open in a browser)."""
    from .viz import export_html
    g, report = build_graph(load_settings())
    _report(report, show_warnings=False)
    path = export_html(g, out.resolve())
    typer.secho(f"wrote {path} ({len(g.nodes)} nodes, {len(g.edges)} edges)", fg="green")


@app.command("scaffold-doc")
def scaffold_doc(
    name: str = typer.Argument(..., help="Form or user-control name, e.g. fPurchaseOrder"),
    force: bool = typer.Option(False, help="Overwrite an existing doc."),
):
    """Create domain/forms/<name>.yaml pre-filled from the extracted code, to be completed by a human / Claude Code."""
    settings = load_settings()
    g, _ = build_graph(settings, with_domain=False)
    node = g.nodes.get(f"form:{name}") or g.nodes.get(f"usercontrol:{name}")
    if node is None:
        typer.secho(f"no extracted form or user control named {name}", fg="red")
        raise typer.Exit(1)
    target = settings.domain_dir / "forms" / f"{name}.yaml"
    if target.exists() and not force:
        typer.secho(f"{target} exists (use --force)", fg="red")
        raise typer.Exit(1)

    controls = [g.nodes[e.dst].props for e in g.out(node.id, "HAS_CONTROL")]
    fields = [f"{c.get('label') or c['control']} ({c['type']}{', mandatory' if c.get('mandatory') else ''}"
              f"{', tab ' + c['tab'] if c.get('tab') else ''})" for c in controls if c.get("label") or "Grid" in c["type"]]
    methods = sorted(g.nodes[e.dst].props["method"] for e in g.out(node.id, "HAS_METHOD"))
    sps = sorted(g.nodes[e.dst].props["name"] for e in g.out(node.id, "CALLS_SP"))
    tables = sorted(g.nodes[e.dst].props["name"] for e in g.out(node.id, "USES_TABLE"))
    msgs = sorted({lit for e in g.out(node.id, "HAS_METHOD") if g.nodes[e.dst].props["method"] == "ValidateForm"
                   for lit in __import__("re").findall(r'"([^"]{8,})"', g.nodes[e.dst].props.get("code", "")) if " " in lit})
    doc = {
        ("form" if node.label == "Form" else "usercontrol"): name,
        "title": node.props.get("title") or name,
        "module": "MM",
        "kind": "master | transaction | report | component",
        "users": ["TODO"],
        "summary": "TODO one sentence: what the form is for.",
        "purpose": "TODO business purpose.\n",
        "functional_description": "Fields:\n" + "\n".join(f"- {f}" for f in fields) + "\n",
        "actions": {"Save": "TODO", "Open": "TODO", "Delete": "TODO"},
        "validations": msgs or ["TODO"],
        "manages": ["TODO concept key from concepts.yaml"],
        "uses_concepts": [],
        "method_notes": {m: "TODO" for m in methods if m in ("SaveMain", "Save", "LoadData", "FillValues", "ValidateForm")},
    }
    header = (f"# Scaffolded from code. Fill the TODOs, add the form to a process in domain/processes/, then run `kg validate`.\n"
              f"# Stored procedures: {', '.join(sps)}\n# Tables: {', '.join(tables)}\n")
    target.write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    typer.secho(f"wrote {target}", fg="green")


if __name__ == "__main__":
    sys.exit(app())
````

## Appendix B: worked examples of curated YAML (reference only, do not copy)

These are our files for an existing form. They show the expected depth and style. Write your own for your forms following §5.

#### `KnowledgeGraph/domain/forms/fUnitMaster.yaml`

````yaml
form: fUnitMaster
title: Unit Master
module: MM
kind: master
users: [Store / inventory administrator, Purchase administrator, Master data team]
summary: Create and maintain units of measure, their GST UQC, conversion factors to other units and the sub groups that use them.
purpose: |
  Unit Master defines every unit of measure (Kg, Nos, Ltr ...) used for material quantities. A unit has a
  generated code (UM0001 ...), a name (max 25 chars), a short alias (max 6 chars), a unit category and the
  GST UQC it reports as. The form also maintains standard conversion factors between units and the
  material sub groups that use the unit for each unit type.
functional_description: |
  Header: Code (auto), Unit Name, Alias, Category, GST UQC, Inactive (per company).
  "Standard Conversion Factor" grid: Conversion Type (Fixed / Variable), Unit Value, target Unit, Conversion
  Value - one row stores both directions of the conversion.
  "Material Subgroup" grid: sub groups that use this unit and as which Unit Type; these links are the same
  ones maintained on the Material Sub Group UOM tab.
  "Fast Entry" grid / Excel import creates many units at once.
actions:
  Save: validate (unique name and alias), save the unit, then replace its conversion factors and sub group links in one transaction.
  Open: search existing units (search list configured in MMUMSearchData).
  Delete: delete the unit with its conversions, sub group links and company rows.
  Import: read units from an Excel sheet into the Fast Entry grid.
validations:
  - "Enter Unit Name."
  - "Enter Alias."
  - "Select valid Category Name."
  - "Duplicate Unit Name is not allowed."
  - "Duplicate Alias is not allowed."
  - "Enter Unit Value in row <n>."
  - "Enter Conversion Value in row <n>."
  - "Enter Unit in row <n>."
  - "Select valid Unit Type in row <n>."
  - "Duplicate Unit is not allowed."
  - "Duplicate Subgroup Name is not allowed."
manages: [unit-of-measure, unit-conversion]
uses_concepts: [unit-type, gst-uqc, material-sub-group, company, document-authorization]
method_notes:
  SaveMain: Saves header via MMUMSave, then conversion factors and sub group links, inside a transaction.
  SaveConversionFactor: Loops the conversion grid and calls MMUMSaveUnitConversionDetail per row.
  SaveSubGroupUnitDetail: Loops the material sub group grid and calls MMUMSaveSubGroupUnitDetail per row.
  ValidateForm: Mandatory checks, then MMUMValidate for duplicate name / alias.
````

#### `KnowledgeGraph/domain/processes/material-master-setup.yaml`

````yaml
key: material-master-setup
name: Material Master Data Setup
module: MM
status: active
summary: Build the material classification hierarchy and its defaults before any material can be purchased or stocked.
description: |
  Evidence: code + ERP domain (inferred)
  Masters are set up top-down. Units of measure come first because sub groups and items reference them.
  Category > Group > Sub Group defines classification and the FullCode prefix of every item; the sub group
  carries purchasing (approved vendors / makes, tolerances), storage (warehouse, bins), tax (GST, HSN) and
  quality (QC parameters, inherited from the group) defaults. Items are finally created under a sub group.
  Each master can also be bulk-created through its "Fast Entry" grid or an Excel import.
  Planned steps reference forms that are not in the repository yet (placeholder names).
steps:
  - order: 1
    name: Define units of measure and conversion factors
    form: fUnitMaster
  - order: 2
    name: Define material categories
    form: fCategoryMaster
    status: planned
  - order: 3
    name: Define material groups and default QC parameters
    form: fMaterialGroup
  - order: 4
    name: Define material sub groups with purchasing, storage, tax and quality defaults
    form: fMaterialSubGroupMaster
  - order: 5
    name: Create items under sub groups
    form: fItemMaster
    status: planned
concepts:
  - material-category
  - material-group
  - material-sub-group
  - material-item
  - unit-of-measure
  - unit-conversion
  - document-authorization
  - company
leads_to: [procure-to-pay, inventory-storage, goods-receipt-quality-inspection, gst-tax-determination]
````
