# Spectrum ERP Knowledge Graph — Metrics & Architecture Summary

**Generated At:** 2026-11-12 (graph built 2026-11-12T11:37:16)  
**Total Nodes:** 90,734  
**Total Relationships:** 508,940  
**Embedding Model:** `Qwen/Qwen3-Embedding-0.6B` (1,024 dimensions)  
**Knowledge Graph Service:** `spectrum-kg`  
**Source:** `G:\AITests\KG-test\all phases\graph\graph.json`

> The graph grew about 4.5x since the 2026-11-06 snapshot (20,179 nodes). It now covers 10 modules instead of 4, and 402 forms instead of 56.

---

## 1. High-Level Summary

The Spectrum Knowledge Graph models the end-to-end architecture of Spectrum ERP across four cohesive layers: **Functional/Business**, **UI/Bridge**, **Application/Code**, and **Database/Schema**.

```
+-------------------------------------------------------------------+
|                   Functional / Business Layer                     |
|   Modules (10) -> Processes (77) -> Concepts (408) -> Rules (4,927)|
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                       UI & Bridge Layer                           |
|           Forms (402) / UserControls (23) -> Controls (15,936)    |
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                    Code & Application Layer                       |
|  FormMethods (16,375) -> DT (389 classes, 10,371 props, 3,649 methods)|
|                       -> DA (389 classes, 3,645 methods)          |
+---------------------------------+---------------------------------+
                                  |
+---------------------------------v---------------------------------+
|                    Database & Schema Layer                        |
|   Stored Procedures (4,619) -> Tables (3,404) -> Columns (26,109) |
+-------------------------------------------------------------------+
```

---

## 2. Modules

| Code | Module | Forms / UCs | Processes | Concepts |
|---|---|---|---|---|
| FI | Finance | 113 | 10 | 102 |
| MM | Material Management | 99 | 31 | 97 |
| MD | Master Data | 72 | 8 | 70 |
| PM | Plant Maintenance | 61 | 6 | 60 |
| SD | Sales and Distribution | 39 | 15 | 38 |
| ADM | Settings and Utilities | 15 | 3 | 15 |
| DRM | Discrete Raw Material | 11 | 1 | 11 |
| WB | Weigh Bridge | 8 | 1 | 8 |
| RPT | Reports | 5 | 1 | 5 |
| PP | Production Planning | 2 | 1 | 2 |
| | **Total** | **425** | **77** | **408** |

All 10 modules are `active`. Of the 402 Forms, 399 are `active` and 3 are `planned` (placeholders for screens not built yet).

---

## 3. Breakdown by Architectural Layer

### 🏛️ Functional & Business Layer
Captures business domain logic, workflows, classification hierarchies, and regulatory/operational policies.

| Label | Count | Description |
|---|---|---|
| **BusinessRule** | 4,927 | Validation, calculation, authorization, and workflow policies |
| **BusinessConcept** | 408 | Domain concepts (e.g., Material Item, Vendor, Make/Brand, UOM) |
| **BusinessProcess** | 77 | Ordered end-to-end business flows (e.g., Procure-to-Pay, Payment Flow) |
| **Module** | 10 | Top-level ERP functional modules (Material Management, Finance, Sales, Plant Maintenance, etc.) |

**Business rules by type:**

| Rule Type | Count |
|---|---|
| control | 1,255 |
| validation | 1,143 |
| calculation | 818 |
| integrity | 699 |
| workflow | 585 |
| derivation | 255 |
| default | 172 |

---

### 🖥️ UI & Bridge Layer
Captures user interaction surfaces and controls rendered by WinForms screens and embedded controls.

| Label | Count | Description |
|---|---|---|
| **Control** | 15,936 | UI controls (buttons, textboxes, UltraGrids, combos, tab pages) |
| **Form** | 402 | WinForms transaction, master, and report screens (399 active, 3 planned) |
| **UserControl** | 23 | Reusable embedded UI components (e.g., `TaxOnAmount`, `QCGroup`) |

---

### 💻 Code & Application Layer
Captures object-oriented data transfer (DT), data access (DA), and client-side UI method implementations.

| Label | Count | Description |
|---|---|---|
| **FormMethod** | 16,375 | UI event handlers, interface implementations (`IMDIFunctions`), and helpers |
| **DTProperty** | 10,371 | Data-Transfer properties binding UI inputs to SP parameters |
| **DTMethod** | 3,649 | Data-Transfer methods coordinating business validation and DA calls |
| **DAMethod** | 3,645 | Data-Access methods preparing parameter dictionaries and invoking SPs |
| **DTClass** | 389 | Active-record Data-Transfer classes |
| **DAClass** | 389 | Data-Access execution classes |

---

### 🗄️ Database & Schema Layer
Captures database persistence structures, relational columns, and executable stored procedure business logic. There is no DDL, so only columns seen in SP code exist as Column nodes.

| Label | Count | Description |
|---|---|---|
| **Column** | 26,109 | Table columns referenced in stored procedures |
| **Table** | 3,404 | Relational database tables across schemas |
| **StoredProcedure** | 4,619 | T-SQL stored procedures containing transactional logic and parameters |

**Top table schemas:**

| Schema | Tables |
|---|---|
| masterdata | 1,341 |
| GlobalData | 304 |
| Sales | 282 |
| Finance | 252 |
| Purchase | 181 |
| Inventory | 181 |
| EAM | 151 |
| Production | 108 |
| Customize | 91 |
| CustomerService | 66 |
| VTPL | 65 |
| payroll | 58 |
| DiscreteRM | 39 |
| ProcessProduction | 39 |
| FixedAsset | 37 |

---

### ⚙️ Graph Metadata
| Label | Count | Description |
|---|---|---|
| **KGMeta** | 1 | Graph build timestamp, embedding configuration, source file and stats |

---

## 4. Complete Node Count Table

| # | Node Label | Architectural Layer | Count |
|---|---|---|---|
| 1 | **Column** | Database | 26,109 |
| 2 | **FormMethod** | Code | 16,375 |
| 3 | **Control** | UI / Bridge | 15,936 |
| 4 | **DTProperty** | Code | 10,371 |
| 5 | **BusinessRule** | Functional | 4,927 |
| 6 | **StoredProcedure** | Database | 4,619 |
| 7 | **DTMethod** | Code | 3,649 |
| 8 | **DAMethod** | Code | 3,645 |
| 9 | **Table** | Database | 3,404 |
| 10 | **BusinessConcept** | Functional | 408 |
| 11 | **Form** | UI / Bridge | 402 |
| 12 | **DTClass** | Code | 389 |
| 13 | **DAClass** | Code | 389 |
| 14 | **BusinessProcess** | Functional | 77 |
| 15 | **UserControl** | UI / Bridge | 23 |
| 16 | **Module** | Functional | 10 |
| 17 | **KGMeta** | Metadata | 1 |
| **Total** | | | **90,734** |

---

## 5. Relationship Counts

### Functional layer
| Relationship | From | To | Count | Purpose |
|---|---|---|---|---|
| `HAS_PROCESS` | Module | BusinessProcess | 77 | Module owns the process |
| `HAS_FORM` | Module | Form / UserControl | 425 | Module owns the form |
| `HAS_CONCEPT` | Module | BusinessConcept | 408 | Module owns the concept |
| `HAS_STEP` | BusinessProcess | Form | 415 | Ordered UI forms used in the process flow |
| `LEADS_TO` | BusinessProcess | BusinessProcess | 14 | Downstream process |
| `INVOLVES` | BusinessProcess | BusinessConcept | 401 | Concepts used by the process |
| `MANAGES` | Form / UserControl | BusinessConcept | 399 | Master form that creates/updates the concept |
| `USES_CONCEPT` | Form / UserControl | BusinessConcept | 2,160 | Form referencing/reading the concept |
| `PARENT_OF` | BusinessConcept | BusinessConcept | 16 | Classification hierarchy (Category > Group > Sub Group > Item) |
| `RELATED_TO` | BusinessConcept | BusinessConcept | 47 | Domain relationship |
| `PERSISTED_IN` *(derived)* | BusinessConcept | Table | 1,727 | Tables storing the concept |
| `APPLIES_TO` | BusinessRule | Form / UserControl / BusinessConcept | 13,555 | Scope where the rule is enforced |
| `IMPLEMENTED_BY` | BusinessRule | StoredProcedure / FormMethod / Table / Column | 6,764 | Code or SQL object implementing the rule |
| `GOVERNS` | BusinessRule | BusinessProcess | 6,881 | Business flow controlled by the rule |

### UI & code layer
| Relationship | From | To | Count | Purpose |
|---|---|---|---|---|
| `HAS_CONTROL` | Form / UserControl | Control | 15,936 | Control on the form |
| `LABELS` | Control | Control | 4,715 | Label captioning an input control |
| `EMBEDS` | Form | UserControl | 654 | Form hosts the user control |
| `HAS_METHOD` | Form / UserControl / DTClass / DAClass | FormMethod / DTMethod / DAMethod | 23,669 | Method of the class |
| `HANDLES` | FormMethod | Control / Form / UserControl | 7,262 | Event handler |
| `CALLS` | FormMethod | FormMethod | 10,694 | Method call (incl. into embedded user controls) |
| `REFERENCES` | FormMethod | Control | 31,316 | Method reads/writes the control |
| `INVOKES` | FormMethod | DTMethod | 4,422 | Form method enters the data layer |
| `SETS` | FormMethod | DTProperty | 21,193 | Method assigns the DT property |
| `BINDS_TO` | Control | DTProperty | 5,369 | Control value copied into the DT property |
| `HAS_PROPERTY` | DTClass | DTProperty | 10,371 | Property of the DT class |
| `DELEGATES_TO` | DTMethod | DAMethod | 3,644 | DT method calls DA method |
| `PASSES` | DAMethod | DTProperty | 18,273 | DA method sends the property as an SP parameter |
| `EXECUTES` | DAMethod | StoredProcedure | 3,645 | DA method calling a specific stored procedure |

### Database layer
| Relationship | From | To | Count | Purpose |
|---|---|---|---|---|
| `READS` | StoredProcedure | Table | 35,958 | SP reads the table |
| `WRITES` | StoredProcedure | Table | 8,556 | SP inserts/updates/deletes (`error_handling=true` marks CATCH-block error logging) |
| `USES_COLUMN` | StoredProcedure | Column | 153,854 | SP reads/writes the column |
| `HAS_COLUMN` | Table | Column | 26,109 | Column of the table |
| `DYNAMIC_EXEC` | StoredProcedure | Table | 56 | SP runs dynamic SQL whose procedure name is looked up in this table |

### Derived shortcut edges
| Relationship | From | To | Count | Purpose |
|---|---|---|---|---|
| `CALLS_SP` | Form / UserControl / StoredProcedure | StoredProcedure | 5,246 | Form-to-SP shortcut, or SP calling another SP |
| `USES_TABLE` | Form / UserControl | Table | 17,145 | Tables touched through the form's SPs |
| `SHARES_TABLE` | Form / UserControl | Form / UserControl | 67,564 | Forms touching common tables (undirected; flags write conflicts) |

---

## 6. Traversal Strategies

| Strategy | Path | Use for |
|---|---|---|
| Functional top-down | Module → BusinessProcess → Form → BusinessConcept ← BusinessRule | What a process or form does, which rules apply |
| Technical drill-down | Form → FormMethod → DTMethod → DAMethod → StoredProcedure → Table → Column | What happens on Save/Load/Delete |
| Field lineage | Control → DTProperty ← DAMethod → StoredProcedure → Table → Column | Where a screen field is saved |
| Impact analysis | Column ← StoredProcedure ← DAMethod ← DTMethod ← FormMethod ← Form ← BusinessProcess | What breaks if a table, column or SP changes |
| Lateral | Form –SHARES_TABLE– Form; Form –EMBEDS→ UserControl | How forms relate or conflict |
| Semantic jump | `similar()` / `search()` | Entry points when no edge connects |
