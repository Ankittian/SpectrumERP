Goal: build an "enum dictionary" for SpectrumERP from the SQL Server database, so a
knowledge graph can translate numeric/code values (e.g. Status=3, Type=2) into names.

You have the full codebase and SQL Server access. Use READ-ONLY access only.

STEP 1: Find the global/master/lookup tables
- Query INFORMATION_SCHEMA / sys.tables / sys.columns / sys.foreign_keys.
- Candidates: tables in the masterdata schema (and similar), small row counts,
  tables referenced by foreign keys from many tables, tables with *Code/*Name/*Type/*Status
  columns (e.g. munitmaster).
- List each candidate with row count and which tables reference it.

STEP 2: Extract the values
- For each lookup table: SELECT the id/code column, the name/description column, and
  any active/flag column. Distinct code->name pairs only.
- Do NOT export transactional tables, personal data, prices, or any rows that
  are not reference data. Cap at ~500 rows per table; report if truncated.

STEP 3: Find the unlabeled numeric columns (the "magic number" columns)
- Columns of type tinyint/smallint/int/char(1)/varchar(small) named like
  Status, Type, Flag, Mode, Category, State, *Kind*, IsXxx with more than 2 values.
- For each: SELECT value, COUNT(*) GROUP BY value (counts only, no row data).
- Check for CHECK constraints and default constraints, which often reveal the meaning.

STEP 4: Infer names from the code
- In stored procedures, views, and C# code (DT/DA/Form methods), find comparisons and
  assignments against these columns: CASE WHEN, IF, WHERE col = 3, @Status = 2,
  C# enums/consts, combo box items, resource strings.
- Match each literal to its table.column and record the meaning the code gives it.
- Cross-check: if a lookup table AND code both define it, report any mismatch.

OUTPUT (files only; do not modify code or the knowledge graph):
enums.json: list of
{
  "enum_id": "...",
  "applies_to": ["schema.table.column", "sp.name.param", "..."],
  "source_table": "lookup table if any",
  "values": [{"value": 3, "name": "Approved", "meaning": "plain English",
              "source_type": "lookup_table|check_constraint|case_when|ui_binding|csharp_enum|inferred",
              "evidence": [{"file_or_object":"...","line":N,"snippet":"short"}],
              "confidence": "high|medium|low",
              "row_count": 1234}]
  "conflicts": "..."
}
unresolved.json: numeric columns seen with values but no name found.
README.md: tables scanned, tables skipped and why, anything truncated.

Rules:
- Scope meanings per column; the same number can mean different things in different tables.
- Never invent names. If you guess from usage, mark source_type "inferred", confidence "low".
- Lookup-table values = high confidence; code-literal evidence = medium; guessed = low.