<!--
=====================================================================
TECHNICAL DOCUMENTATION TEMPLATE: STORED PROCEDURES (GLOBAL REPOSITORY)
=====================================================================

HOW TO USE THIS TEMPLATE:
1. Scope & Source of Truth:
   - Traverse the `StoredProcedures/` directories across ALL WinForms in the repository.
   - Document ALL distinct `.sql` stored procedures in a single consolidated document.
   - Do NOT reference or link to WinForms UI controls (textboxes, grids)
     or application DataLayer classes (DT, DA, DAO, C#, or VB.NET code).
   - Document strictly database-level behavior, schemas, parameters, CRUD
     operations, algorithms, return contracts, and transactions.

2. Structure & Formatting Rules:
   - Maintain ONE single consolidated document across the entire system.
   - Document title: # Technical Documentation: Stored Procedures
   - Each stored procedure MUST be an H2 (##) heading:
     ## [{{schema}}].[{{ProcedureName}}]
   - Each stored procedure documentation MUST be written as a single,
     self-contained technical paragraph using these 5 bold labels:
     **Purpose & Database Operations:**
     **Parameters:**
     **Tables Affected / Queried:**
     **Internal SQL Logic:**
     **Return Contract & Error Handling:**
   - Followed immediately by the next stored procedure entry.
=====================================================================
-->

# Technical Documentation: Stored Procedures

It details the operational characteristics, parameter contracts, database CRUD footprint, internal SQL algorithms, return formats, and error handling mechanisms for each procedure without coupling to user interface components or application data layers.

---

<!-- [REPEAT THIS BLOCK FOR EVERY STORED PROCEDURE ACROSS ALL FORMS] -->

## [{{schema}}].[{{ProcedureName}}]

**Purpose & Database Operations:** {{Describe the technical intent of the procedure (e.g., persistence/upsert, business validation, catalog lookup, sequential code generation, data retrieval, or cascade purge) and the primary database actions performed (SELECT, INSERT, UPDATE, DELETE).}}  
**Parameters:** {{List all parameters with exact SQL data types, precision, nullability, default values, and operational meaning (e.g., @Id smallint: pass 0 or NULL for insert, existing ID for update).}}  
**Tables Affected / Queried:** {{List all database tables queried, inserted into, updated, or deleted from, including multi-company detail tables and downstream cascade targets.}}  
**Internal SQL Logic:** {{Detail the core execution logic, including branching conditions (e.g., insert vs. update), identity retrieval (IDENT_CURRENT), key calculation algorithms, multi-company synchronization, downstream cascaded updates, foreign key deletion order, or dynamic SQL execution.}}  
**Return Contract & Error Handling:** {{Specify the exact output format returned on success and failure (e.g., SELECT 1, @Id vs. SELECT 0, ERROR_MESSAGE() / validation focus code, or the schemas and column names of returned DataTables), transaction boundaries (autonomous internal transaction vs. caller-managed), and error logging behavior (e.g., logging to masterdata.mErrorLog with FormCode).}}

---
