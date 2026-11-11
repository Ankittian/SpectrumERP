# Prompt: Extract code and generate embedding text for missing nested stored procedures

 Take every stored procedure (SP) listed in
`missing_nested_sps_unique.csv` (177 rows), **pull its source code from SQL Server**,
**save the code**, and **generate its KG embedding text**. 

## Inputs

| File | Use |
|---|---|
| `\missing_nested_sps_unique.csv` | The SP list. Columns: `missing_sp_id` (e.g. `sp:customize.amrrfinanceposting`), `schema`, `name` (both lowercased), `referenced_by_sps (in KG)`, `sample_call` (original-case call), and others. |
| `embedding_text_templates.md` | Section "Data layer > StoredProcedure" defines the embedding text format. |

## Step : Extract the code

For each CSV row, resolve the real SP name case-insensitively and fetch the definition:

```sql
SELECT s.name AS schema_name, p.name AS proc_name, m.definition
FROM sys.procedures p
JOIN sys.schemas s ON s.schema_id = p.schema_id
JOIN sys.sql_modules m ON m.object_id = p.object_id
WHERE LOWER(s.name) = LOWER(?) AND LOWER(p.name) = LOWER(?);
```

- Also fetch the parameters from `sys.parameters` (name, type, max_length/precision/scale, is_output, has_default_value).
- Also fetch `sys.sql_expression_dependencies` for the SP (referenced schema, name, and whether it is a table or procedure)
  to cross-check the Reads, Writes and Calls you derive from the code.
- If `definition` is NULL (encrypted), or the object is missing, or it is not a procedure, mark it
  `NOT FOUND` or `ENCRYPTED` in the status report. Do not invent code.

## Step 3: Save the code

Save each definition to:
`\missing_nested_sps\code\{Schema}.{ProcName}.sql`

- Use the real original-case schema and name from SQL Server.
- Save exactly as returned by `definition`: no reformatting, trimming or edits. UTF-8 encoding.

## Step 4: Generate the embedding text

Per SP, write `missing_nested_sps\embedding_text\{Schema}.{ProcName}.txt` in this
format (from `embedding_text_templates.md`):

```
Stored procedure {name}[: {description}][. Called from {referenced_by_sps}.]
Writes: {tables written}                      # limit 20, exclude error-log / error-handling tables
Reads: {tables read}                          # limit 25
Parameters: {parameters}
Parameters never sent by the data layer (SQL default applies): {omit, unknown for these SPs}
Calls procedures: {SPs it EXECs}
Rules: {omit, unknown for these SPs}
Author: {author}, created {created}           # only if the code header has an author
Code:
{full SQL code}
```

- `{name}` is `schema.ProcName` as in the existing KG convention. Use lowercase if the other KG embedding texts do.
- `{description}`: one short factual sentence taken from a header comment in the code if one exists. Otherwise omit it.
- "Called from" comes from the CSV column `referenced_by_sps (in KG)` (strip the `sp:` prefix).
- Writes and Reads: derive from INSERT / UPDATE / DELETE / MERGE / TRUNCATE (writes) and SELECT / JOIN (reads) in the code.
  Cross-check with the dependencies from Step 2. Include temp tables or table variables **only** if you label them as such;
  prefer leaving them out.
- Parameters: `@Name type [= default] [OUTPUT]`, comma-separated, in declaration order.
- Calls: every `EXEC` / `EXECUTE` of another SP, including those inside dynamic SQL when the name is a literal.
- Omit any line you cannot fill from the evidence. Do not add anything the code doesn't support.
- No technical-documentation paragraphs and no five-label sections.

## Step 5: Status report

Write `missing_nested_sps\status.csv` with columns:
`missing_sp_id, status (DONE | NOT FOUND | ENCRYPTED | ERROR), real_name, code_path, embedding_path, notes`.
Put in notes: wrappers around other SPs, dynamic SQL, very long code, and any mismatch between the code-derived Reads/Writes
and `sys.sql_expression_dependencies`.

## Rules

- Do not modify the input CSV or existing docs.
- Read-only on the database. Do not create objects or write data.
- Create the output folders if needed.
- Work in batches of about 20 SPs, and continue past individual failures.
- Final check: `.sql` files = `.txt` files = number of `DONE` rows, and `DONE` + the rest = 177.
  Report the counts and list every non-DONE SP with the reason.
