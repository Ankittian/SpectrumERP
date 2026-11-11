# Prompt: Find nested stored procedures referenced by the WinForm SP folders, save their code, and generate embedding text

## Goal
Each WinForm bundle has a `StoredProcedures\` folder holding the code of the SPs its data layer calls. Those SPs sometimes `EXEC` other SPs whose code is **not** in any such folder. These are **nested SPs**. For each phase, you will:
1. find the nested SPs and write a CSV (nested SP, the SP referencing it, the form it sits under, the phase),
2. collect the source code of every nested SP,
3. generate each nested SP's embedding text using `embedding_text_templates.md`.

Nothing here is tied to a specific phase, drive or folder name. Resolve everything from the questions below.

## Step 0: Ask first, then confirm
Ask the user the following (skip any they already answered), then restate the resolved values and proceed without further prompting:
1. **Phase directory**: the folder that contains the phase folders. Which phase folder(s) should be processed, and what label to use for each phase (default: the folder's name)?
2. **Form bundle layout**: confirm that inside each phase folder there is one sub-folder per form, each with a `StoredProcedures\` folder of `.sql` files (named `Schema.ProcName.sql`). If the layout differs, look at a real bundle and adapt, and tell the user what you found.
3. **Code source for nested SPs**: (a) a folder or zip of exported SP scripts (name it/where), or (b) SQL Server (read-only; connection method). Prefer the export if one is given; otherwise use SQL Server. If neither is available, stop and say so; never invent code.
4. **Output root**: where to write results (default: a `nested_sps` folder next to the phase directory). Each phase gets its own subfolder under it.
5. **Template file**: where `embedding_text_templates.md` is (default: search the repo for it).

## Definitions
- **Form SP folder SPs ("baseline")** = every `.sql` file under `<phase folder>\<form>\StoredProcedures\`, for the phase being processed. (The same SP file may appear under several forms.)
- **Nested SP** = an SP that a baseline SP, or another nested SP, `EXEC`s, whose code is not in the phase's baseline set.
- **Depth**: 1 = EXEC'd directly by a baseline SP; 2 = EXEC'd by a depth-1 nested SP; and so on. Recurse until no new SPs appear (stop at depth 8 and say so if reached).

## Step 1: Build the CSV (per phase)

**1.1 Index the baseline.** For the phase, list all `.sql` files under every form's `StoredProcedures\`. Build:
- `BASELINE` = set of `schema.name` (lowercase, from the file name).
- `forms_of[sp]` = the form folders that contain that SP file.

**1.2 Scan for references.** For each baseline SP file, then for each nested SP found later:
- Strip `/* ... */` and `-- ...` comments.
- Find `EXEC` / `EXECUTE` followed (optionally) by `@var =` and then a one- to three-part name, with or without `[ ]`. Lowercase and remove brackets.
- Ignore system procs (`sp_*`, `xp_*`, `sp_executesql`) and anything starting with `@` or `(`.
- If a name has no schema, resolve it from the code source (or `OBJECT_ID` on SQL Server) to the real schema; if it cannot be resolved, list it in the report as unresolved.
- `EXEC @var` / `EXEC(@sql)`: record as **dynamic** (variable, and the table/column it is read from if the code shows it). Do not guess targets. They go in the report, not the CSV.
- Also catch names inside dynamic SQL strings only when the SP name is a literal.
- Keep the caller, call count, and one sample call line (original case).

**1.3 Select nested SPs.** Targets not in `BASELINE` are nested SPs. For each, get its code (Step 2) and scan it the same way; new targets not in `BASELINE` and not already nested are added (depth + 1). Repeat to the depth limit.

**1.4 Resolve forms.** The form(s) of a nested SP are the form(s) of the SPs that reference it:
- depth 1: `forms_of[referencing SP]`;
- deeper: the forms of the depth-1 root(s) that lead to it (inherited through the chain).
The `phase` of every row is the phase being processed. If a nested SP is also a baseline SP in a **different** phase folder (check if more than one phase is being processed or the user asks), set `in_other_phase_baseline = yes` and name that phase.

**1.5 Write the CSV:** `<output root>\<phase label>\nested_sps_<phase label>.csv` (UTF-8 with BOM, one row per nested SP, sorted by schema then name). Columns:

| Column | Meaning |
|---|---|
| `nested_sp` | `schema.name`, original case if known (else lowercase) |
| `referenced_by_sp` | the SPs that EXEC it directly, `; `-separated (`schema.name`) |
| `form` | the form(s) containing those referencing SPs (for depth > 1, the root form(s)), `; `-separated |
| `phase` | phase label |
| `depth` | 1, 2, ... (minimum depth if reached several ways) |
| `call_count` | total EXEC occurrences |
| `sample_call` | one original-case call line |
| `in_other_phase_baseline` | yes/no (+ phase) |

Print row counts by `depth` and the number of distinct forms per phase before continuing.

## Step 2: Collect the source code
For each nested SP, get the definition and save it to `<output root>\<phase label>\code\<Schema>.<ProcName>.sql`:
- From the export folder/zip: find the file by schema and name, case-insensitively (file names or `CREATE PROCEDURE` headers; tolerate `dbo`-style prefixes and brackets).
- From SQL Server:
  ```sql
  SELECT s.name, p.name, m.definition
  FROM sys.procedures p
  JOIN sys.schemas s ON s.schema_id = p.schema_id
  JOIN sys.sql_modules m ON m.object_id = p.object_id
  WHERE LOWER(s.name) = LOWER(?) AND LOWER(p.name) = LOWER(?);
  ```
  Also fetch `sys.parameters` and `sys.sql_expression_dependencies` to cross-check parameters, Reads, Writes and Calls.
- Save the text exactly as obtained (no reformatting, trimming or edits), UTF-8, with the real original-case schema and name.
- If it is missing, encrypted (NULL definition), or not a procedure, mark `NOT FOUND` / `ENCRYPTED` / `NOT A PROCEDURE`. Never invent code. Keep the row in the CSV; its callees are unknown.

## Step 3: Generate the embedding text
Read `embedding_text_templates.md`, "Common structure (all labels)" and "Data layer > StoredProcedure". Use it as the **only** format reference (no other documentation template, no five-label technical-doc layout). For each SP with code, write `<output root>\<phase label>\embedding_text\<Schema>.<ProcName>.txt`:

```
[StoredProcedure] {schema.ProcName}
Stored procedure {schema.ProcName}[: {description}][. Called from {referencing SPs and forms}.]
Writes: {tables written}                      # limit 20, then " (+N more)"; exclude CATCH-block error-log tables
Reads: {tables read}                          # limit 25, then " (+N more)"
Parameters: {parameters}
Calls procedures: {SPs it EXECs}
Author: {author}, created {created}           # only if the code header has an author
Code:
{full SQL code}
```

- `{description}`: one short factual sentence from a header comment in the code if present; otherwise omit.
- "Called from": the `referenced_by_sps` followed by the `form` names, sorted and de-duplicated (mirrors `in[CALLS_SP]`).
- Writes/Reads: derive from INSERT/UPDATE/DELETE/MERGE/TRUNCATE (writes) and SELECT/JOIN/EXISTS (reads), schema-qualified, sorted, de-duplicated; a written table is not repeated in Reads. Leave out temp tables and table variables. Cross-check with `sys.sql_expression_dependencies` when on SQL Server.
- Parameters: `@Name type [= default] [OUTPUT]`, in declaration order.
- Calls: every `EXEC`/`EXECUTE` of another SP, schema-qualified, including literal names inside dynamic SQL.
- **Drop any line whose value would be empty** (never write `none`).
- **Do not write** `Parameters never sent by the data layer` or `Rules:` (the KG build adds those from graph edges).
- Use the same casing convention as the template/KG for `{schema.ProcName}`.
- Do not add anything the code does not support.

## Step 4: Report
Write `<output root>\<phase label>\status.csv`, one row per CSV row:
`nested_sp, depth, status (DONE | NOT FOUND | ENCRYPTED | NOT A PROCEDURE | ERROR), code_path, embedding_path, notes`.
Notes: dynamic SQL and unresolved target, unresolved no-schema EXEC names, very long code, wrappers around other SPs, mismatches against `sys.sql_expression_dependencies`.

## Rules
- Do not modify any existing file; write only under the output root.
- Read-only on the database. Never execute an SP, create objects or write data.
- Keep helper scripts in the scratchpad, not in the project folders.
- Work in batches of about 20 SPs; continue past individual failures.
- Process phases one at a time, each fully (CSV, code, embedding text, status), and report per phase.
- Final checks per phase, with the numbers: (1) number of `.sql` files = number of `.txt` files = number of `DONE` rows; `DONE` + other statuses = CSV rows; (2) no nested SP is in `BASELINE`; (3) every embedding text follows the template line order, has no empty lines, and its Parameters, Calls and tables match the code; (4) list every non-DONE SP, every dynamic EXEC with an unresolved target, and the largest depth reached.
