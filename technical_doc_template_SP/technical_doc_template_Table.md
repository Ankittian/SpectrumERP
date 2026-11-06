<!--
=====================================================================
TECHNICAL DOCUMENTATION TEMPLATE: DATABASE TABLES (FROM SQL SERVER)
=====================================================================

HOW TO USE THIS TEMPLATE:
1. Scope & Source of Truth:
   - Extract schema information directly from a live SQL Server connection
     or database dictionary scripts using system metadata catalogs:
     * sys.tables, sys.schemas (Table identification & storage)
     * sys.columns, sys.types (Exact data types, precision, scale, length)
     * sys.default_constraints (Default value expressions)
     * sys.key_constraints, sys.indexes (Primary keys, unique indexes)
     * sys.foreign_keys, sys.foreign_key_columns (Referential integrity & delete rules)
     * sys.check_constraints (Validation rules)
     * sys.extended_properties (MS_Description table/column comments)
   - Consolidate all database tables across the enterprise into a single
     technical documentation document.

2. Structure & Formatting Rules:
   - Document title: # Technical Documentation: Database Tables
   - Each table MUST be documented under its own H2 (##) heading:
     ## [{{schema}}].[{{TableName}}]
   - Each table entry MUST follow this standardized layout:
     * **Overview & Classification:** High-level architectural role
     * **Columns Table:** Exact SQL Server column specifications
     * **Constraints & Indexes:** PK, FKs, Unique Constraints, Indexes, Checks
     * **Referential Dependencies:** Parent (outbound) and Child (inbound) references
   - Followed immediately by the next table under its H2 heading.

3. T-SQL Metadata Extraction Script:
   To extract the columns metadata directly from SQL Server, execute:
   SELECT 
       s.name AS [Schema], t.name AS [Table], c.column_id AS [ColumnId],
       c.name AS [ColumnName],
       ty.name + 
           CASE 
               WHEN ty.name IN ('varchar', 'char', 'nvarchar', 'nchar') THEN '(' + CASE WHEN c.max_length = -1 THEN 'MAX' ELSE CAST(CASE WHEN ty.name LIKE 'n%' THEN c.max_length/2 ELSE c.max_length END AS VARCHAR) END + ')'
               WHEN ty.name IN ('decimal', 'numeric') THEN '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')'
               ELSE ''
           END AS [DataType],
       CASE WHEN c.is_nullable = 1 THEN 'YES' ELSE 'NO' END AS [IsNullable],
       CASE WHEN c.is_identity = 1 THEN 'IDENTITY(' + CAST(IDENT_SEED(s.name + '.' + t.name) AS VARCHAR) + ',' + CAST(IDENT_INCR(s.name + '.' + t.name) AS VARCHAR) + ')'
            WHEN dc.definition IS NOT NULL THEN 'DEFAULT ' + dc.definition
            ELSE ''
       END AS [DefaultOrIdentity],
       CASE WHEN pk.column_id IS NOT NULL THEN 'PK'
            WHEN fk.parent_column_id IS NOT NULL THEN 'FK'
            ELSE ''
       END AS [KeyType],
       ISNULL(CAST(ep.value AS VARCHAR(500)), '') AS [Description]
   FROM sys.tables t
   INNER JOIN sys.schemas s ON s.schema_id = t.schema_id
   INNER JOIN sys.columns c ON c.object_id = t.object_id
   INNER JOIN sys.types ty ON ty.user_type_id = c.user_type_id
   LEFT JOIN sys.default_constraints dc ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
   LEFT JOIN (
       SELECT ic.object_id, ic.column_id 
       FROM sys.index_columns ic
       INNER JOIN sys.indexes i ON i.object_id = ic.object_id AND i.index_id = ic.index_id
       WHERE i.is_primary_key = 1
   ) pk ON pk.object_id = c.object_id AND pk.column_id = c.column_id
   LEFT JOIN sys.foreign_key_columns fk ON fk.parent_object_id = c.object_id AND fk.parent_column_id = c.column_id
   LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
   WHERE t.is_ms_shipped = 0
   ORDER BY s.name, t.name, c.column_id;
=====================================================================
-->

# Technical Documentation: Database Tables

This document provides database-level technical documentation for all database tables across the SpectrumERP system, extracted directly from the SQL Server data dictionary. It details the relational schemas, exact column types, constraints, indexes, and referential dependencies for each table.

---

<!-- [REPEAT THIS BLOCK FOR EVERY DATABASE TABLE] -->

## [{{schema}}].[{{TableName}}]

**Overview & Classification:** {{Describe the architectural classification (e.g., Primary Master Entity, Multi-Company Distribution Junction, Child Specification Detail, Global Reference Catalog, or System / Audit Log) and its operational role in the enterprise data model.}}

### Columns
| Column Name | SQL Type & Precision | Nullable | Identity / Default | Key Type | Description / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `{{Column1}}` | `{{sql_type(len/prec,scale)}}` | NO / YES | `IDENTITY(1,1)` / `DEFAULT (...)` | PK | Primary key surrogate identifier |
| `{{Column2}}` | `{{sql_type(len/prec,scale)}}` | NO / YES | `DEFAULT (...)` / — | FK | Foreign key referencing `[{{ParentSchema}}].[{{ParentTable}}]({{ParentCol}})` |
| `{{Column3}}` | `{{sql_type(len/prec,scale)}}` | NO / YES | — | UK | Unique business code or natural key |
| `{{Column4}}` | `{{sql_type(len/prec,scale)}}` | NO / YES | `DEFAULT (...)` / — | — | Operational attribute description |
| `CreatedBy` | `int` | NO | — | FK | User identifier who created the record (references `Security.Login`) |
| `CreatedDate` | `datetime` | NO | `DEFAULT (getdate())` | — | System record creation timestamp |
| `ModifiedBy` | `int` | YES | `NULL` | FK | User identifier who last modified the record |
| `ModifiedDate` | `datetime` | YES | `NULL` | — | Timestamp of last modification |
| `AuthorizedBy`| `int` | YES | `NULL` | FK | User identifier who authorized the record |
| `AuthorizedDate`| `datetime` | YES | `NULL` | — | Timestamp of authorization |
| `DocumentStatusNo`| `tinyint` | NO | `DEFAULT ((30))` | — | Workflow status code (30 = Authorized) |

### Constraints & Indexes
* **Primary Key:** `PK_{{TableName}}` (CLUSTERED) on `({{PK_Columns}})`
* **Foreign Keys (Outbound):**
  * `FK_{{Name}}`: `{{Col}}` → `[{{ParentSchema}}].[{{ParentTable}}]({{ParentCol}})` [ON DELETE {{Action}} | ON UPDATE {{Action}}]
* **Unique Constraints / Unique Indexes:**
  * `UQ_{{Name}}` on `({{Columns}})`
* **Non-Clustered Indexes:**
  * `IX_{{Name}}` on `({{IndexColumns}})` INCLUDE `({{IncludedColumns}})`
* **Check Constraints:**
  * `CK_{{Name}}`: `({{Expression}})`

### Referential Dependencies
* **Parent Tables (Outbound):** `[{{ParentSchema}}].[{{ParentTable}}]`
* **Dependent Child Tables (Inbound):** `[{{ChildSchema}}].[{{ChildTable}}]`

---
